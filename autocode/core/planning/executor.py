"""
executor.py
Ejecuta planes de commit de forma autónoma usando ReAct + file tools.
Emite SSE events para feedback en tiempo real.

Flujo:
1. Carga y valida el plan (status debe ser draft/ready/failed)
2. Marca el plan como 'executing'
3. Para cada task: ejecuta un agente ReAct con file tools
4. Emite SSE events: plan_start, task_start, status, task_debug, task_complete/error, plan_complete
5. Opcionalmente hace git add + commit al finalizar
"""

import json
import logging
import subprocess
from datetime import datetime
from typing import AsyncGenerator, List, Union

import dspy
from dspy.streaming import StatusMessage

from autocode.interfaces.registry import register_function
from autocode.interfaces.models import GenericOutput
from autocode.core.ai.dspy_utils import (
    get_dspy_lm,
    ModelType,
    prepare_chat_tools,
)
from autocode.core.ai.streaming import AutocodeStatusProvider, _format_sse
from autocode.core.ai.signatures import TaskExecutionSignature
from autocode.core.ai.models import DspyOutput
from autocode.core.planning.models import (
    CommitPlan,
    PlanTask,
    PlanContext,
    TaskExecutionResult,
    PlanExecutionState,
)
from autocode.core.planning.planner import _save_plan, _load_plan

logger = logging.getLogger(__name__)


# ============================================================================
# CONSTANTS
# ============================================================================

# Statuses desde los que se puede ejecutar un plan
EXECUTOR_ALLOWED_STATUSES = {"draft", "ready", "failed"}

# Tools que modifican archivos (para extraer files_changed de la trajectory)
WRITE_TOOLS = {"write_file_content", "replace_in_file", "delete_file"}

# Tools disponibles para el executor
EXECUTOR_TOOLS = {
    "read_file_content",
    "write_file_content",
    "replace_in_file",
    "delete_file",
    "get_code_summary",
}


# ============================================================================
# STREAM GENERATOR
# ============================================================================


async def stream_execute_plan(
    plan_id: str,
    model: ModelType = "openrouter/z-ai/glm-5",
    max_tokens: int = None,
    temperature: float = 0.3,
    auto_commit: bool = True,
) -> AsyncGenerator[str, None]:
    """Async generator que ejecuta un plan y emite SSE events.

    Args:
        plan_id: ID del plan a ejecutar
        model: Modelo de inferencia a utilizar
        max_tokens: Número máximo de tokens por iteración
        temperature: Temperature para generación (baja para código preciso)
        auto_commit: Si hacer git commit automático al terminar exitosamente

    Yields:
        Strings formateados como eventos SSE
    """
    try:
        # 1. Cargar y validar plan
        plan = _load_plan(plan_id)
        if not plan:
            yield _format_sse(
                "error",
                {"message": f"Plan '{plan_id}' not found", "success": False},
            )
            return

        if plan.status not in EXECUTOR_ALLOWED_STATUSES:
            yield _format_sse(
                "error",
                {
                    "message": f"Cannot execute plan in status '{plan.status}'",
                    "success": False,
                },
            )
            return

        # 2. Marcar como executing
        plan.status = "executing"
        plan.execution = PlanExecutionState(
            started_at=datetime.now().isoformat(),
            model_used=model,
        )
        _save_plan(plan)

        yield _format_sse(
            "plan_start",
            {
                "plan_id": plan.id,
                "title": plan.title,
                "total_tasks": len(plan.tasks),
                "model": model,
            },
        )

        # 3. Configurar LM y tools
        lm = get_dspy_lm(model, max_tokens=max_tokens, temperature=temperature)
        tools = _get_executor_tools()

        # 4. Loop por tasks
        all_files_changed: List[str] = []
        tasks_completed = 0
        tasks_failed = 0
        plan_total_tokens = 0
        plan_total_cost = 0.0

        for i, task in enumerate(plan.tasks):
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
                # Consume the async generator — SSE events yielded in real-time
                task_result = None
                async for item in _execute_single_task(
                    task, plan, lm, tools, i
                ):
                    if isinstance(item, str):
                        # SSE event string — forward immediately to client
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

                if task_result.status == "completed":
                    tasks_completed += 1
                    all_files_changed.extend(task_result.files_changed)
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
                    yield _format_sse(
                        "task_error",
                        {
                            "task_index": i,
                            "status": "failed",
                            "error": task_result.error,
                        },
                    )
            except Exception as e:
                tasks_failed += 1
                task_result = TaskExecutionResult(
                    task_index=i, status="failed", error=str(e)
                )
                plan.execution.task_results.append(task_result)
                yield _format_sse(
                    "task_error",
                    {"task_index": i, "status": "failed", "error": str(e)},
                )

        # 5. Auto-commit si procede
        commit_hash = ""
        if auto_commit and tasks_failed == 0 and all_files_changed:
            try:
                unique_files = list(
                    dict.fromkeys(all_files_changed)
                )  # Dedup preservando orden
                commit_hash = _git_add_and_commit(unique_files, plan.title)
                plan.execution.commit_hash = commit_hash
            except Exception as e:
                logger.error(f"Auto-commit failed: {e}")

        # 6. Finalizar plan
        plan.execution.completed_at = datetime.now().isoformat()
        plan.execution.total_tokens = plan_total_tokens
        plan.execution.total_cost = plan_total_cost
        plan.status = "completed" if tasks_failed == 0 else "failed"
        _save_plan(plan)

        yield _format_sse(
            "plan_complete",
            {
                "success": tasks_failed == 0,
                "tasks_completed": tasks_completed,
                "tasks_failed": tasks_failed,
                "commit_hash": commit_hash,
                "total_tokens": plan_total_tokens,
                "total_cost": plan_total_cost,
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
    max_tokens: int = None,
    temperature: float = 0.3,
    auto_commit: bool = True,
) -> GenericOutput:
    """Ejecuta un plan de commit de forma autónoma.

    Usa un agente ReAct con file tools para implementar cada tarea del plan.
    Emite SSE events en tiempo real para feedback de progreso.
    Opcionalmente hace git commit al finalizar exitosamente.

    Args:
        plan_id: ID del plan a ejecutar
        model: Modelo de inferencia a utilizar
        max_tokens: Número máximo de tokens por iteración
        temperature: Temperature para generación (baja para código preciso)
        auto_commit: Si hacer git commit automático al terminar exitosamente
    """
    # Sync fallback: recolecta eventos del stream y retorna resultado final
    import asyncio

    final_result = None

    async def _collect():
        nonlocal final_result
        async for event in stream_execute_plan(
            plan_id, model, max_tokens, temperature, auto_commit
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
# PRIVATE: SINGLE TASK EXECUTION (ASYNC GENERATOR)
# ============================================================================


async def _execute_single_task(
    task: PlanTask,
    plan: CommitPlan,
    lm: dspy.LM,
    tools: list,
    task_index: int,
) -> AsyncGenerator[Union[str, TaskExecutionResult], None]:
    """Ejecuta una task con ReAct + streamify.

    Yields SSE events en tiempo real durante la ejecución,
    y como último item el TaskExecutionResult.

    Args:
        task: La tarea a ejecutar
        plan: El plan completo (para contexto)
        lm: Language Model configurado
        tools: Lista de tools DSPy
        task_index: Índice de la tarea en el plan

    Yields:
        str: SSE event strings (status messages)
        TaskExecutionResult: Final result (always last item)
    """
    started_at = datetime.now().isoformat()
    instruction = _build_task_instruction(task, plan)

    # Crear ReAct module
    react = dspy.ReAct(TaskExecutionSignature, tools=tools, max_iters=8)

    # Streamify
    stream_listeners = [
        dspy.streaming.StreamListener(
            signature_field_name="completion_summary", allow_reuse=True
        )
    ]
    stream_program = dspy.streamify(
        react,
        stream_listeners=stream_listeners,
        status_message_provider=AutocodeStatusProvider(),
    )

    # Ejecutar y yield events en tiempo real
    prediction = None
    with dspy.context(lm=lm):
        async for chunk in stream_program(
            task_instruction=instruction, file_path=task.path
        ):
            if isinstance(chunk, StatusMessage) and chunk.message:
                # Yield SSE event IMMEDIATELY — no buffering
                yield _format_sse(
                    "status",
                    {"task_index": task_index, "message": chunk.message},
                )
            elif isinstance(chunk, dspy.Prediction):
                prediction = chunk

    # Capturar métricas de coste del historial del LM
    cost_info = _extract_cost_from_history(lm)

    # Capturar y normalizar trajectory para debug
    trajectory_raw = getattr(prediction, "trajectory", {}) if prediction else {}
    normalized_trajectory = (
        DspyOutput.normalize_trajectory(trajectory_raw)
        if trajectory_raw
        else []
    )

    # Serializar history del LM para debug
    serialized_history = None
    if hasattr(lm, "history") and lm.history:
        try:
            serialized_history = DspyOutput.serialize_value(lm.history)
        except Exception as e:
            logger.warning(f"Could not serialize lm.history: {e}")

    # Emitir evento de debug con trajectory + history + cost
    yield _format_sse(
        "task_debug",
        {
            "task_index": task_index,
            "trajectory": (
                DspyOutput.serialize_value(normalized_trajectory)
                if normalized_trajectory
                else []
            ),
            "history": serialized_history or [],
            **cost_info,
        },
    )

    # Limpiar history para que la siguiente task no acumule métricas anteriores
    if hasattr(lm, "history"):
        lm.history.clear()

    files_changed = _extract_files_changed(trajectory_raw)

    if prediction is None:
        yield TaskExecutionResult(
            task_index=task_index,
            status="failed",
            started_at=started_at,
            completed_at=datetime.now().isoformat(),
            error="No prediction received from LLM",
            **cost_info,
        )
    else:
        summary = getattr(prediction, "completion_summary", "")
        yield TaskExecutionResult(
            task_index=task_index,
            status="completed",
            started_at=started_at,
            completed_at=datetime.now().isoformat(),
            llm_summary=summary,
            files_changed=files_changed,
            **cost_info,
        )


# ============================================================================
# PRIVATE HELPERS
# ============================================================================


def _build_task_instruction(task: PlanTask, plan: CommitPlan) -> str:
    """Construye prompt compuesto para la task.

    Combina la descripción de la task, detalles, criterios de aceptación,
    y contexto del plan en una instrucción completa para el agente.

    Args:
        task: La tarea individual
        plan: El plan completo (para contexto global)

    Returns:
        String con la instrucción completa
    """
    parts = [f"## Task: {task.description}"]

    if task.details:
        parts.append(f"\n### Details:\n{task.details}")

    if task.acceptance_criteria:
        criteria = "\n".join(f"- {c}" for c in task.acceptance_criteria)
        parts.append(f"\n### Acceptance Criteria:\n{criteria}")

    parts.append(f"\n### Target file: {task.path}")
    parts.append(f"\n### Operation type: {task.type}")

    if plan.description:
        parts.append(f"\n### Plan context:\n{plan.description}")

    if plan.context and plan.context.architectural_notes:
        parts.append(
            f"\n### Architectural notes:\n{plan.context.architectural_notes}"
        )

    return "\n".join(parts)


def _extract_files_changed(trajectory) -> List[str]:
    """Extrae paths de archivos modificados de la trajectory de ReAct.

    Recorre las tool calls de la trajectory y extrae los paths
    de las operaciones que modifican archivos (write, replace, delete).

    Args:
        trajectory: Dict con la trajectory de ReAct (Action_N, Action_N_args, etc.)

    Returns:
        Lista de paths únicos de archivos modificados
    """
    if not trajectory or not isinstance(trajectory, dict):
        return []

    files: List[str] = []
    for key, value in trajectory.items():
        if key.endswith("_args") and isinstance(value, dict):
            # Determinar si la acción correspondiente es una escritura
            action_key = key.replace("_args", "")
            action_name = trajectory.get(action_key, "")
            if action_name in WRITE_TOOLS and "path" in value:
                path = value["path"]
                if path not in files:
                    files.append(path)
    return files


def _extract_cost_from_history(lm) -> dict:
    """Extrae métricas de coste del historial de llamadas al LM.

    Recorre lm.history sumando tokens y costes de cada llamada.
    Compatible con la estructura de LiteLLM/DSPy.

    Args:
        lm: Language Model con historial de llamadas

    Returns:
        Dict con prompt_tokens, completion_tokens, total_tokens, total_cost
    """
    if not hasattr(lm, "history") or not lm.history:
        return {
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "total_tokens": 0,
            "total_cost": 0.0,
        }

    prompt_tokens = 0
    completion_tokens = 0
    total_cost = 0.0

    for call in lm.history:
        if not isinstance(call, dict):
            continue

        # DSPy/LiteLLM history puede tener usage en diferentes lugares
        usage = call.get("usage") or {}
        if isinstance(usage, dict):
            prompt_tokens += usage.get("prompt_tokens", 0) or usage.get(
                "input_tokens", 0
            )
            completion_tokens += usage.get("completion_tokens", 0) or usage.get(
                "output_tokens", 0
            )

        # LiteLLM puede poner el coste en varios lugares
        cost = (
            call.get("cost")
            or call.get("response_cost")
            or (call.get("_hidden_params") or {}).get("response_cost")
            or (
                (call.get("response") or {}).get("_hidden_params") or {}
            ).get("response_cost")
        )
        total_cost += cost or 0

    return {
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "total_tokens": prompt_tokens + completion_tokens,
        "total_cost": total_cost,
    }


def _get_executor_tools() -> list:
    """Obtiene las tools filtradas para el executor.

    Usa prepare_chat_tools con la lista de tools permitidas
    para el executor (file ops + code summary).

    Returns:
        Lista de funciones wrapper listas para DSPy
    """
    return prepare_chat_tools(list(EXECUTOR_TOOLS))


def _git_add_and_commit(files: List[str], message: str) -> str:
    """Ejecuta git add + git commit.

    Args:
        files: Lista de archivos a incluir en el commit
        message: Mensaje del commit

    Returns:
        Hash del commit creado
    """
    for f in files:
        subprocess.run(["git", "add", f], check=True)
    subprocess.run(["git", "commit", "-m", message], check=True)
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout.strip()
