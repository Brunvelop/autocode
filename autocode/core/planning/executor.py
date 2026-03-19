"""
executor.py
Ejecuta planes de commit delegando a backends pluggables (opencode, cline, dspy).
Emite SSE events para feedback en tiempo real.

Flujo:
1. Carga y valida el plan (status debe ser draft/ready/failed)
2. Marca el plan como 'executing'
3. Resuelve el backend (opencode, cline, etc.)
4. Construye instrucción desde plan.title + plan.description
5. Delega ejecución al backend via backend.execute()
6. Almacena resultado (steps, files_changed, cost, session_id)
7. Post-ejecución: review según review_mode
   - "human": pending_review (humano aprueba/revierte)
   - "auto": auto_review con quality gates → approved → commit / rejected → pending_review
8. Emite SSE events: plan_start, step, review_start, review_complete, plan_complete

SSE events:
  plan_start    → {plan_id, title, backend, model}
  step          → {type, content, tool, path, timestamp}
  heartbeat     → {elapsed_s}
  review_start  → {review_mode, files_changed}
  review_complete → {verdict, summary, review_mode, issues}
  plan_complete → {success, files_changed, commit_hash, total_tokens, total_cost, status}
  error         → {message, success: false}
"""

import asyncio
import json
import logging
import os
import time
from datetime import datetime
from typing import AsyncGenerator

from autocode.core.registry import register_function
from autocode.core.models import GenericOutput
from autocode.core.ai.streaming import _format_sse
from autocode.core.planning.models import (
    CommitPlan,
    ExecutionStep,
    PlanExecutionState,
    ReviewResult,
)
from autocode.core.planning.backends import get_backend
from autocode.core.planning.backends.base import ExecutionResult
from autocode.core.vcs.git import git_add_and_commit
from autocode.core.vcs.execution import ExecutionSandbox
from autocode.core.planning.persistence import save_plan, load_plan
from autocode.core.planning.transitions import can_execute
from autocode.core.planning.reviewer import auto_review, compute_review_metrics

logger = logging.getLogger(__name__)


# ============================================================================
# INSTRUCTION BUILDER
# ============================================================================


def _build_instruction(plan: CommitPlan) -> str:
    """Build a markdown instruction from the plan's title and description.

    Args:
        plan: The commit plan.

    Returns:
        Markdown string suitable as an LLM instruction.
    """
    parts = [f"## Commit: {plan.title}"]
    if plan.description:
        parts.append(f"\n{plan.description}")
    return "\n".join(parts)


# ============================================================================
# HEARTBEAT WRAPPER
# ============================================================================


async def _with_heartbeat(
    async_gen: AsyncGenerator,
    interval: float = 8.0,
) -> AsyncGenerator:
    """Wraps an async generator, interleaving heartbeat SSE events.

    Runs a heartbeat timer in parallel with the source generator.
    Every ``interval`` seconds of silence, emits a heartbeat SSE event
    to keep the connection alive and provide elapsed time feedback.

    Args:
        async_gen: The source async generator to wrap.
        interval: Seconds between heartbeats (default 8s).

    Yields:
        Items from the source generator, interleaved with heartbeat SSE strings.
    """
    queue: asyncio.Queue = asyncio.Queue()
    _SENTINEL = object()
    start_time = time.monotonic()

    async def _producer():
        try:
            async for item in async_gen:
                await queue.put(item)
        except Exception as exc:
            await queue.put(exc)
        finally:
            await queue.put(_SENTINEL)

    async def _heartbeat():
        while True:
            await asyncio.sleep(interval)
            elapsed = time.monotonic() - start_time
            await queue.put(
                _format_sse(
                    "heartbeat",
                    {
                        "elapsed_s": round(elapsed, 1),
                        "timestamp": datetime.now().isoformat(),
                    },
                )
            )
            if elapsed > 60 and int(elapsed) % 60 < int(interval):
                logger.warning(f"  ⚠ Execution: {elapsed:.0f}s elapsed, still running")

    producer_task = asyncio.create_task(_producer())
    heartbeat_task = asyncio.create_task(_heartbeat())

    try:
        while True:
            item = await queue.get()
            if item is _SENTINEL:
                break
            if isinstance(item, Exception):
                raise item
            yield item
    finally:
        heartbeat_task.cancel()
        try:
            await heartbeat_task
        except asyncio.CancelledError:
            pass
        if not producer_task.done():
            producer_task.cancel()
            try:
                await producer_task
            except asyncio.CancelledError:
                pass


# ============================================================================
# STREAM GENERATOR (core orchestrator)
# ============================================================================


async def stream_execute_plan(
    plan_id: str,
    backend: str = "opencode",
    model: str = "",
    review_mode: str = "human",
) -> AsyncGenerator[str, None]:
    """Async generator that executes a plan via a pluggable backend and emits SSE events.

    Orchestration flow:
    1. Load plan, validate FSM (can_execute), mark 'executing'.
    2. Resolve backend instance.
    3. Build instruction from plan.title + plan.description.
    4. Emit plan_start SSE.
    5. Call backend.execute() — each step emitted as SSE 'step' event.
    6. Store result (files_changed, steps, cost, session_id) in plan.execution.
    7. Review flow (human → pending_review / auto → quality gates).
    8. Emit plan_complete SSE.

    Args:
        plan_id: ID of the plan to execute.
        backend: Backend name ("opencode", "cline").
        model: Model identifier to pass to the backend.
        review_mode: "human" or "auto".

    Yields:
        SSE-formatted strings.
    """
    plan_start_time = time.monotonic()
    plan = None  # Safety net: track plan so outer except can persist 'failed' status

    try:
        # ------------------------------------------------------------------
        # 1. Load and validate
        # ------------------------------------------------------------------
        plan = load_plan(plan_id)
        if not plan:
            yield _format_sse(
                "error",
                {"message": f"Plan '{plan_id}' not found", "success": False},
            )
            return

        if not can_execute(plan):
            yield _format_sse(
                "error",
                {
                    "message": f"Cannot execute plan in status '{plan.status}'",
                    "success": False,
                },
            )
            return

        # ------------------------------------------------------------------
        # 2. Mark as executing
        # ------------------------------------------------------------------
        plan.status = "executing"
        plan.execution = PlanExecutionState(
            started_at=datetime.now().isoformat(),
            model_used=model,
        )
        save_plan(plan)

        # ------------------------------------------------------------------
        # 3. Resolve backend
        # ------------------------------------------------------------------
        backend_instance = get_backend(backend)

        # ------------------------------------------------------------------
        # 4. Build instruction
        # ------------------------------------------------------------------
        instruction = _build_instruction(plan)
        # NOTE: os.getcwd() assumes the server process runs from the target repo root.
        # This is correct for CLI usage (single repo). If this evolves to a multi-repo
        # service, cwd should be a parameter of stream_execute_plan or a field of CommitPlan.
        cwd = os.getcwd()

        # Snapshot HEAD before execution so we can detect (and undo) any
        # commits the agent makes on its own during execution.
        sandbox = ExecutionSandbox(cwd)
        await sandbox.snapshot()

        logger.info(
            f"▶ Executing plan '{plan.id}': {plan.title} "
            f"(backend={backend_instance.name}, model={model})"
        )

        # ------------------------------------------------------------------
        # 5. Emit plan_start
        # ------------------------------------------------------------------
        yield _format_sse(
            "plan_start",
            {
                "plan_id": plan.id,
                "title": plan.title,
                "backend": backend_instance.name,
                "model": model,
            },
        )

        # ------------------------------------------------------------------
        # 6. Execute via backend — emit steps in real-time via Queue bridge
        # ------------------------------------------------------------------
        collected_steps: list[ExecutionStep] = []
        step_queue: asyncio.Queue = asyncio.Queue()
        _DONE = object()

        async def _on_step(step: ExecutionStep) -> None:
            """Callback: emit immediately to queue as SSE (real-time streaming)."""
            collected_steps.append(step)
            await step_queue.put(
                _format_sse(
                    "step",
                    {
                        "type": step.type,
                        "content": step.content,
                        "tool": step.tool,
                        "path": step.path,
                        "timestamp": step.timestamp,
                    },
                )
            )

        async def _run_backend():
            """Task: execute backend and put result (or exception) into queue."""
            try:
                result = await backend_instance.execute(
                    instruction=instruction,
                    cwd=cwd,
                    model=model,
                    on_step=_on_step,
                )
                await step_queue.put(result)
            except Exception as exc:
                await step_queue.put(exc)
            finally:
                await step_queue.put(_DONE)

        async def _backend_execution():
            """Generator: consumes from queue, yielding SSE events in real-time."""
            task = asyncio.create_task(_run_backend())
            try:
                while True:
                    item = await step_queue.get()
                    if item is _DONE:
                        break
                    if isinstance(item, Exception):
                        raise item
                    yield item  # SSE string or ExecutionResult
            except (asyncio.CancelledError, GeneratorExit):
                backend_instance.abort()
                task.cancel()
                raise
            finally:
                if not task.done():
                    task.cancel()

        execution_result: ExecutionResult | None = None

        try:
            async for item in _with_heartbeat(_backend_execution()):
                if isinstance(item, ExecutionResult):
                    execution_result = item
                else:
                    yield item
        except (asyncio.CancelledError, GeneratorExit):
            logger.info(f"⏹ Execution cancelled for plan '{plan_id}'")
            backend_instance.abort()
            await sandbox.revert()
            plan.status = "failed"
            plan.execution.completed_at = datetime.now().isoformat()
            save_plan(plan)
            return

        # Fallback if backend didn't return a result (shouldn't happen)
        if execution_result is None:
            execution_result = ExecutionResult(
                success=False,
                error="No result from backend execution",
            )

        # ------------------------------------------------------------------
        # Collect changed files via sandbox.
        # collect_changes() handles the safety net automatically: if the
        # agent committed during execution (HEAD moved), it first runs
        # git reset --mixed to bring those commits back to the working tree,
        # then diffs against the pre-execution HEAD.
        # ------------------------------------------------------------------
        files_changed = await sandbox.collect_changes()

        # ------------------------------------------------------------------
        # 7. Store execution result in plan
        # ------------------------------------------------------------------
        plan.execution.steps = collected_steps
        plan.execution.files_changed = files_changed
        plan.execution.total_tokens = execution_result.total_tokens
        plan.execution.total_cost = execution_result.total_cost
        plan.execution.backend = backend_instance.name
        plan.execution.session_id = execution_result.session_id

        # ------------------------------------------------------------------
        # 8. Handle failure or review
        # ------------------------------------------------------------------
        commit_hash = ""

        if not execution_result.success:
            plan.execution.completed_at = datetime.now().isoformat()
            plan.status = "failed"
            save_plan(plan)
        else:
            # Run review flow — yields only SSE strings; commit_hash is read
            # directly from plan.execution after the flow completes.
            async for sse_event in _run_review_flow(
                plan, review_mode, files_changed
            ):
                yield sse_event
            commit_hash = plan.execution.commit_hash if plan.execution else ""

        # ------------------------------------------------------------------
        # 9. Emit plan_complete
        # ------------------------------------------------------------------
        plan_elapsed = time.monotonic() - plan_start_time
        success = execution_result.success
        result_icon = "✅" if success else "❌"
        logger.info(
            f"{result_icon} Plan '{plan.id}' finished in {plan_elapsed:.1f}s — "
            f"status={plan.status}, "
            f"{execution_result.total_tokens} tokens, ${execution_result.total_cost:.4f}"
        )

        yield _format_sse(
            "plan_complete",
            {
                "success": success,
                "files_changed": files_changed,
                "commit_hash": commit_hash,
                "total_tokens": execution_result.total_tokens,
                "total_cost": execution_result.total_cost,
                "status": plan.status,
                "review_mode": review_mode,
            },
        )

    except Exception as e:
        logger.error(f"Executor error: {e}", exc_info=True)
        # Safety net: ensure plan doesn't stay stuck in 'executing' forever.
        # Without this, any unexpected exception after marking 'executing' would
        # create a zombie plan that can never be re-executed.
        if plan is not None and plan.status == "executing":
            plan.status = "failed"
            if plan.execution:
                plan.execution.completed_at = datetime.now().isoformat()
                plan.execution.error = str(e)
            save_plan(plan)
        yield _format_sse("error", {"message": str(e), "success": False})


# ============================================================================
# REVIEW FLOW
# ============================================================================


async def _run_review_flow(
    plan: CommitPlan,
    review_mode: str,
    files_changed: list,
) -> AsyncGenerator:
    """Post-execution review flow: auto or human mode.

    After this coroutine completes, ``plan.execution.commit_hash`` contains
    the hash of the auto-commit (auto mode + approved) or ``""`` otherwise.
    Callers read the commit hash directly from the plan rather than from a
    yielded value, keeping the protocol uniform: every item yielded is an
    SSE-formatted string.

    Args:
        plan: The executed plan (mutated in-place: status, execution fields).
        review_mode: "auto" or "human".
        files_changed: List of file paths changed during execution.

    Yields:
        str: SSE event strings (``review_start``, ``review_complete``).
    """
    # 1. Emit review_start
    yield _format_sse(
        "review_start",
        {
            "review_mode": review_mode,
            "files_changed": files_changed,
        },
    )

    # 2. Run review
    review_result = None
    commit_hash = ""

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

    # 3. Store review
    plan.execution.review = review_result

    # 4. Emit review_complete
    yield _format_sse(
        "review_complete",
        {
            "verdict": review_result.verdict,
            "summary": review_result.summary,
            "review_mode": review_mode,
            "issues": review_result.issues,
        },
    )

    # 5. Determine final status
    if review_mode == "auto" and review_result.verdict == "approved":
        # Auto-approved → commit and mark completed
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

    # 6. Finalize
    plan.execution.completed_at = datetime.now().isoformat()
    save_plan(plan)


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
    backend: str = "opencode",
    model: str = "",
    review_mode: str = "human",
) -> GenericOutput:
    """Ejecuta un plan de commit delegando a un backend pluggable.

    El backend (opencode, cline) ejecuta la instrucción del plan y reporta
    pasos en tiempo real. Post-ejecución, se aplica review según review_mode.

    Reads the final result from persisted plan state (not from SSE parsing),
    which is more robust and decoupled from the SSE wire format.

    Args:
        plan_id: ID del plan a ejecutar
        backend: Backend de ejecución (opencode, cline)
        model: Modelo de inferencia a utilizar
        review_mode: Modo de review post-ejecución ("human" o "auto")
    """
    import asyncio

    async def _drain():
        """Consume all SSE events from stream_execute_plan, discarding them.

        The side-effects (plan persistence) happen inside stream_execute_plan;
        we only need to drive the generator to completion.
        """
        async for _ in stream_execute_plan(plan_id, backend, model, review_mode):
            pass

    asyncio.run(_drain())

    # Read authoritative final state from persistence — no SSE string parsing needed.
    plan = load_plan(plan_id)
    if not plan or not plan.execution:
        return GenericOutput(
            success=False,
            result={},
            message="Plan not found or not executed",
        )

    return GenericOutput(
        success=plan.status in ("completed", "pending_review"),
        result=plan.execution.model_dump() if plan.execution else {},
        message=f"Plan {plan.status}",
    )
