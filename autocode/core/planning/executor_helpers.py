"""
executor_helpers.py
Low-level helpers for plan executor.

Contains:
- Single task execution with ReAct + DSPy
- Heartbeat wrapper for long-running async generators
- Prompt construction helpers
- Trajectory parsing utilities
- Cost extraction from LM history
- Tool filtering
"""

import asyncio
import logging
import time
from datetime import datetime
from typing import AsyncGenerator, List, Union

import dspy
from dspy.streaming import StatusMessage

from autocode.core.ai.dspy_utils import prepare_chat_tools
from autocode.core.ai.streaming import AutocodeStatusProvider, _format_sse
from autocode.core.ai.signatures import TaskExecutionSignature
from autocode.core.ai.models import DspyOutput
from autocode.core.planning.models import CommitPlan

# Temporary stubs — PlanTask/TaskExecutionResult removed in model simplification (C2).
# executor_helpers.py is fully rewritten in Phase 2 (C11).
try:
    from autocode.core.planning.models import PlanTask  # type: ignore[attr-defined]
except ImportError:
    PlanTask = None  # type: ignore[assignment,misc]

try:
    from autocode.core.planning.models import TaskExecutionResult  # type: ignore[attr-defined]
except ImportError:
    TaskExecutionResult = None  # type: ignore[assignment,misc]

logger = logging.getLogger(__name__)


# ============================================================================
# CONSTANTS
# ============================================================================

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
# PRIVATE: HEARTBEAT WRAPPER
# ============================================================================


async def _with_heartbeat(
    async_gen: AsyncGenerator[Union[str, TaskExecutionResult], None],
    task_index: int,
    interval: float = 8.0,
) -> AsyncGenerator[Union[str, TaskExecutionResult], None]:
    """Wraps an async generator, interleaving heartbeat SSE events.

    Runs a heartbeat timer in parallel with the source generator.
    Every `interval` seconds of silence, emits a heartbeat SSE event
    to keep the connection alive and provide elapsed time feedback.

    Args:
        async_gen: The source async generator to wrap
        task_index: Task index for heartbeat event metadata
        interval: Seconds between heartbeats (default 8s)

    Yields:
        Items from the source generator, interleaved with heartbeat SSE strings
    """
    queue: asyncio.Queue = asyncio.Queue()
    _SENTINEL = object()
    start_time = time.monotonic()

    async def _producer():
        """Consume source generator and put items into queue."""
        try:
            async for item in async_gen:
                await queue.put(item)
        except Exception as e:
            await queue.put(e)
        finally:
            await queue.put(_SENTINEL)

    async def _heartbeat():
        """Emit heartbeat events at regular intervals."""
        while True:
            await asyncio.sleep(interval)
            elapsed = time.monotonic() - start_time
            heartbeat_event = _format_sse(
                "heartbeat",
                {
                    "task_index": task_index,
                    "elapsed_s": round(elapsed, 1),
                    "timestamp": datetime.now().isoformat(),
                },
            )
            await queue.put(heartbeat_event)
            if elapsed > 60 and int(elapsed) % 60 < int(interval):
                logger.warning(
                    f"  ⚠ Task {task_index}: {elapsed:.0f}s elapsed, still running"
                )

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
        # Ensure producer finishes (it should already be done)
        if not producer_task.done():
            producer_task.cancel()
            try:
                await producer_task
            except asyncio.CancelledError:
                pass


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
