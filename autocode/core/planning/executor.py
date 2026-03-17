"""
executor.py
Ejecuta planes de commit de forma autónoma usando ReAct + file tools.
Emite SSE events para feedback en tiempo real.

Flujo:
1. Carga y valida el plan (status debe ser draft/ready/failed)
2. Marca el plan como 'executing'
3. Para cada task: ejecuta un agente ReAct con file tools
4. Emite SSE events: plan_start, task_start, status, task_debug, task_complete/error
5. Post-ejecución: review según review_mode
   - "human": pending_review (humano aprueba/revierte)
   - "auto": auto_review con quality gates → approved → commit / rejected → pending_review
6. Emite review_start, review_complete, plan_complete
"""

import asyncio
import json
import logging
import time
from datetime import datetime
from typing import AsyncGenerator, List, Union

from autocode.core.registry import register_function
from autocode.core.models import GenericOutput
from autocode.core.ai.providers import ModelType
from autocode.core.ai.dspy_utils import get_dspy_lm
from autocode.core.ai.streaming import _format_sse
from autocode.core.planning.models import (
    CommitPlan,
    TaskExecutionResult,
    PlanExecutionState,
    ReviewResult,
)
from autocode.core.vcs.git import git_add_and_commit
from autocode.core.planning.planner import _save_plan, _load_plan
from autocode.core.planning.transitions import can_execute
from autocode.core.planning.reviewer import auto_review, compute_review_metrics
from autocode.core.planning.executor_helpers import (
    _execute_single_task,
    _with_heartbeat,
    _build_task_instruction,
    _extract_files_changed,
    _extract_cost_from_history,
    _get_executor_tools,
    WRITE_TOOLS,
    EXECUTOR_TOOLS,
)

logger = logging.getLogger(__name__)


# ============================================================================
# STREAM GENERATOR
# ============================================================================


async def stream_execute_plan(
    plan_id: str,
    model: ModelType = "openrouter/z-ai/glm-5",
    max_tokens: int = 100000,
    temperature: float = 0.3,
    review_mode: str = "human",
) -> AsyncGenerator[str, None]:
    """Async generator que ejecuta un plan y emite SSE events.

    Thin orchestrator that delegates to:
    - _validate_and_prepare_plan: load, validate, mark executing, configure LM/tools
    - _execute_task_loop: loop over tasks with heartbeat
    - _run_review_flow: post-execution review + optional commit

    Args:
        plan_id: ID del plan a ejecutar
        model: Modelo de inferencia a utilizar
        max_tokens: Número máximo de tokens por iteración
        temperature: Temperature para generación (baja para código preciso)
        review_mode: Modo de review post-ejecución ("human" o "auto")

    Yields:
        Strings formateados como eventos SSE
    """
    plan_start_time = time.monotonic()
    try:
        # 1. Validate and prepare
        plan = None
        lm = None
        tools = None
        async for item in _validate_and_prepare_plan(plan_id, model, max_tokens, temperature):
            if isinstance(item, tuple):
                plan, lm, tools = item
            else:
                yield item

        if plan is None:
            return  # Error was already yielded

        # 2. Execute task loop
        metrics = None
        async for item in _execute_task_loop(plan, lm, tools):
            if isinstance(item, dict):
                metrics = item
            else:
                yield item

        tasks_completed = metrics["tasks_completed"]
        tasks_failed = metrics["tasks_failed"]
        unique_files = metrics["all_files_changed"]
        plan_total_tokens = metrics["plan_total_tokens"]
        plan_total_cost = metrics["plan_total_cost"]

        # Store files_changed in execution
        plan.execution.files_changed = unique_files

        # 3. Post-execution review or failure
        commit_hash = ""
        if tasks_failed > 0:
            plan.execution.completed_at = datetime.now().isoformat()
            plan.execution.total_tokens = plan_total_tokens
            plan.execution.total_cost = plan_total_cost
            plan.status = "failed"
            _save_plan(plan)
        else:
            plan.execution.total_tokens = plan_total_tokens
            plan.execution.total_cost = plan_total_cost
            async for item in _run_review_flow(plan, review_mode, unique_files):
                if isinstance(item, dict):
                    commit_hash = item.get("commit_hash", "")
                else:
                    yield item

        # 4. Final logging and plan_complete event
        plan_elapsed = time.monotonic() - plan_start_time
        result_icon = "✅" if tasks_failed == 0 else "❌"
        logger.info(
            f"{result_icon} Plan '{plan.id}' finished in {plan_elapsed:.1f}s — "
            f"{tasks_completed} completed, {tasks_failed} failed, "
            f"status={plan.status}, "
            f"{plan_total_tokens} tokens, ${plan_total_cost:.4f}"
        )

        yield _format_sse(
            "plan_complete",
            {
                "success": tasks_failed == 0,
                "tasks_completed": tasks_completed,
                "tasks_failed": tasks_failed,
                "commit_hash": commit_hash,
                "total_tokens": plan_total_tokens,
                "total_cost": plan_total_cost,
                "status": plan.status,
                "review_mode": review_mode,
            },
        )
    except Exception as e:
        logger.error(f"Executor error: {e}", exc_info=True)
        yield _format_sse("error", {"message": str(e), "success": False})


# ============================================================================
# REGISTERED ENDPOINT
# ============================================================================


@register_function(
    http_methods=["POST"],
    interfaces=["api"],
    streaming=True,
    stream_func=stream_execute_plan,
)
def execute_commit_plan(
    plan_id: str,
    model: ModelType = "openrouter/z-ai/glm-5",
    max_tokens: int = 100000,
    temperature: float = 0.3,
    review_mode: str = "human",
) -> GenericOutput:
    """Ejecuta un plan de commit de forma autónoma.

    Usa un agente ReAct con file tools para implementar cada tarea del plan.
    Emite SSE events en tiempo real para feedback de progreso.
    El review_mode controla el flujo post-ejecución:
    - "human": siempre queda en pending_review para aprobación manual
    - "auto": ejecuta quality gates, si pasan → commit automático

    Args:
        plan_id: ID del plan a ejecutar
        model: Modelo de inferencia a utilizar
        max_tokens: Número máximo de tokens por iteración
        temperature: Temperature para generación (baja para código preciso)
        review_mode: Modo de review post-ejecución ("human" o "auto")
    """
    # Sync fallback: recolecta eventos del stream y retorna resultado final
    import asyncio

    final_result = None

    async def _collect():
        nonlocal final_result
        async for event in stream_execute_plan(
            plan_id, model, max_tokens, temperature, review_mode
        ):
            if "plan_complete" in event or "error" in event:
                final_result = event

    asyncio.run(_collect())

    if final_result:
        try:
            data = json.loads(final_result.split("data: ")[1].split("\n")[0])
        except (IndexError, json.JSONDecodeError):
            data = {}
    else:
        data = {}

    return GenericOutput(
        success=data.get("success", False),
        result=data,
        message=str(data),
    )


# ============================================================================
# PRIVATE: DECOMPOSED STREAM HELPERS
# ============================================================================


async def _validate_and_prepare_plan(
    plan_id: str,
    model: str,
    max_tokens: int,
    temperature: float,
) -> AsyncGenerator:
    """Load, validate, mark executing, configure LM/tools.

    Yields SSE events during preparation, and as the LAST item yields
    a tuple (plan, lm, tools) if successful.

    If the plan is not found or not executable, yields a single error SSE
    event and returns.

    Args:
        plan_id: ID del plan a ejecutar
        model: Modelo de inferencia
        max_tokens: Número máximo de tokens
        temperature: Temperature para generación

    Yields:
        str: SSE event strings
        tuple: (plan, lm, tools) as the final item on success
    """
    # 1. Load plan
    plan = _load_plan(plan_id)
    if not plan:
        yield _format_sse(
            "error",
            {"message": f"Plan '{plan_id}' not found", "success": False},
        )
        return

    # 2. Check can_execute
    if not can_execute(plan):
        yield _format_sse(
            "error",
            {
                "message": f"Cannot execute plan in status '{plan.status}'",
                "success": False,
            },
        )
        return

    # 3. Mark as executing
    plan.status = "executing"
    plan.execution = PlanExecutionState(
        started_at=datetime.now().isoformat(),
        model_used=model,
    )
    _save_plan(plan)

    # 4. Log execution start
    logger.info(
        f"▶ Executing plan '{plan.id}': {plan.title} "
        f"({len(plan.tasks)} tasks, model={model})"
    )

    # 5. Yield plan_start SSE event
    yield _format_sse(
        "plan_start",
        {
            "plan_id": plan.id,
            "title": plan.title,
            "total_tasks": len(plan.tasks),
            "model": model,
        },
    )

    # 6. Configure LM and tools
    lm = get_dspy_lm(model, max_tokens=max_tokens, temperature=temperature)
    tools = _get_executor_tools()

    # 7. Yield the prepared tuple as the last item
    yield (plan, lm, tools)


async def _execute_task_loop(
    plan: CommitPlan,
    lm,
    tools: list,
) -> AsyncGenerator:
    """Loop over tasks, execute each with heartbeat, yield SSE events.

    As the LAST item, yields a dict with accumulated metrics.

    Args:
        plan: The plan to execute (must have status='executing')
        lm: Configured language model
        tools: List of DSPy tools

    Yields:
        str: SSE event strings (task_start, status, task_debug, task_complete, task_error)
        dict: Final metrics summary as the last item
    """
    all_files_changed: List[str] = []
    tasks_completed = 0
    tasks_failed = 0
    plan_total_tokens = 0
    plan_total_cost = 0.0

    for i, task in enumerate(plan.tasks):
        task_start_mono = time.monotonic()
        logger.info(
            f"  ▶ Task {i}/{len(plan.tasks)-1}: [{task.type}] {task.path} — {task.description}"
        )

        yield _format_sse(
            "task_start",
            {
                "task_index": i,
                "task": {
                    "type": task.type,
                    "path": task.path,
                    "description": task.description,
                },
                "status": "running",
            },
        )

        try:
            task_result = None
            task_gen = _with_heartbeat(
                _execute_single_task(task, plan, lm, tools, i),
                task_index=i,
            )

            async for item in task_gen:
                if isinstance(item, str):
                    yield item
                elif isinstance(item, TaskExecutionResult):
                    task_result = item

            if task_result is None:
                task_result = TaskExecutionResult(
                    task_index=i,
                    status="failed",
                    error="No result from task execution",
                )

            plan.execution.task_results.append(task_result)

            # Accumulate cost metrics
            plan_total_tokens += task_result.total_tokens
            plan_total_cost += task_result.total_cost

            task_elapsed = time.monotonic() - task_start_mono
            if task_result.status == "completed":
                tasks_completed += 1
                all_files_changed.extend(task_result.files_changed)
                logger.info(
                    f"  ✅ Task {i} completed in {task_elapsed:.1f}s "
                    f"({task_result.total_tokens} tokens, ${task_result.total_cost:.4f})"
                )
                yield _format_sse(
                    "task_complete",
                    {
                        "task_index": i,
                        "status": "completed",
                        "summary": task_result.llm_summary,
                        "files_changed": task_result.files_changed,
                        "total_tokens": task_result.total_tokens,
                        "total_cost": task_result.total_cost,
                    },
                )
            else:
                tasks_failed += 1
                logger.warning(
                    f"  ❌ Task {i} failed in {task_elapsed:.1f}s: {task_result.error}"
                )
                yield _format_sse(
                    "task_error",
                    {
                        "task_index": i,
                        "status": "failed",
                        "error": task_result.error,
                    },
                )
        except Exception as e:
            task_elapsed = time.monotonic() - task_start_mono
            tasks_failed += 1
            logger.error(
                f"  ❌ Task {i} exception after {task_elapsed:.1f}s: {e}",
                exc_info=True,
            )
            task_result = TaskExecutionResult(
                task_index=i, status="failed", error=str(e)
            )
            plan.execution.task_results.append(task_result)
            yield _format_sse(
                "task_error",
                {"task_index": i, "status": "failed", "error": str(e)},
            )

    # Yield final metrics summary
    yield {
        "tasks_completed": tasks_completed,
        "tasks_failed": tasks_failed,
        "all_files_changed": list(dict.fromkeys(all_files_changed)),
        "plan_total_tokens": plan_total_tokens,
        "plan_total_cost": plan_total_cost,
    }


async def _run_review_flow(
    plan: CommitPlan,
    review_mode: str,
    files_changed: list,
) -> AsyncGenerator:
    """Post-execution review flow: auto or human mode.

    As the LAST item, yields a dict with {"commit_hash": ...}.

    Args:
        plan: The executed plan
        review_mode: "auto" or "human"
        files_changed: List of file paths changed during execution

    Yields:
        str: SSE event strings (review_start, review_complete)
        dict: {"commit_hash": str} as the last item
    """
    # 1. Yield review_start SSE event
    yield _format_sse(
        "review_start",
        {
            "review_mode": review_mode,
            "files_changed": files_changed,
        },
    )

    # 2. Initialize
    review_result = None
    commit_hash = ""

    # 3. Run review based on mode
    if review_mode == "auto":
        try:
            review_result = auto_review(
                files_changed,
                parent_commit=plan.parent_commit or "HEAD",
            )
        except Exception as e:
            logger.error(f"Auto-review failed: {e}")
            review_result = ReviewResult(
                mode="auto",
                verdict="needs_changes",
                summary=f"Auto-review error: {e}",
                reviewed_by="auto",
            )
    else:
        # Human mode: compute metrics only, no verdict
        try:
            file_metrics = compute_review_metrics(
                files_changed,
                parent_commit=plan.parent_commit or "HEAD",
            )
        except Exception as e:
            logger.warning(f"Could not compute review metrics: {e}")
            file_metrics = []
        review_result = ReviewResult(
            mode="human",
            verdict="needs_changes",
            summary="Awaiting human review",
            file_metrics=file_metrics,
            reviewed_by="",
        )

    # 5. Store review result
    plan.execution.review = review_result

    # 6. Yield review_complete SSE event
    yield _format_sse(
        "review_complete",
        {
            "verdict": review_result.verdict,
            "summary": review_result.summary,
            "review_mode": review_mode,
            "issues": review_result.issues,
        },
    )

    # 7. Determine final status
    if review_mode == "auto" and review_result.verdict == "approved":
        # Auto-approved → commit and complete
        if files_changed:
            try:
                commit_hash = git_add_and_commit(files_changed, plan.title)
                plan.execution.commit_hash = commit_hash
            except Exception as e:
                logger.error(f"Auto-commit failed: {e}")
        plan.status = "completed"
    else:
        # Human mode or auto-rejected → pending_review
        plan.status = "pending_review"

    # 8. Finalize plan
    plan.execution.completed_at = datetime.now().isoformat()
    _save_plan(plan)

    # 9. Yield final dict
    yield {"commit_hash": commit_hash}




