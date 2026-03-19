"""
dspy_react.py
Legacy backend de ejecución basado en DSPy ReAct.

Ejecuta instrucciones usando DSPy ReAct con TaskExecutionSignature,
streaming de StatusMessages y herramientas del registry.

Extraído de executor_helpers.py y adaptado al protocolo ExecutorBackend.
Contiene también las utilidades de extracción de costes y archivos
modificados desde el historial y trajectory de DSPy.
"""

import logging
from datetime import datetime
from typing import Callable, Awaitable, List

import dspy
from dspy.streaming import StatusMessage

from autocode.core.ai.dspy_utils import get_dspy_lm, prepare_chat_tools
from autocode.core.ai.streaming import AutocodeStatusProvider
from autocode.core.ai.signatures import TaskExecutionSignature
from autocode.core.planning.models import ExecutionStep
from autocode.core.planning.backends.base import ExecutorBackend, ExecutionResult

logger = logging.getLogger(__name__)


# ============================================================================
# CONSTANTS
# ============================================================================

# Tools que modifican archivos (para extraer files_changed de la trajectory)
WRITE_TOOLS = {"write_file_content", "replace_in_file", "delete_file"}

# Tools disponibles para el executor
EXECUTOR_TOOLS = [
    "read_file_content",
    "write_file_content",
    "replace_in_file",
    "delete_file",
    "get_code_summary",
]


# ============================================================================
# BACKEND
# ============================================================================


class DspyReactBackend(ExecutorBackend):
    """Legacy backend que ejecuta planes usando DSPy ReAct.

    Utiliza dspy.ReAct con TaskExecutionSignature y streamify para
    ejecutar instrucciones, emitiendo pasos en tiempo real vía on_step.
    """

    name = "dspy"

    async def execute(
        self,
        instruction: str,
        cwd: str,
        model: str,
        on_step: Callable[[ExecutionStep], Awaitable[None]],
    ) -> ExecutionResult:
        """Ejecuta una instrucción vía DSPy ReAct con streaming.

        Args:
            instruction: Instrucción markdown a ejecutar.
            cwd: Directorio de trabajo (se pasa como file_path a la signature).
            model: Modelo de inferencia (e.g. 'openrouter/openai/gpt-4o').
            on_step: Callback async invocado para cada paso de ejecución.

        Returns:
            ExecutionResult con el resultado de la ejecución.
        """
        try:
            lm = get_dspy_lm(model or "openrouter/openai/gpt-4o")
            tools = prepare_chat_tools(EXECUTOR_TOOLS)

            react = dspy.ReAct(TaskExecutionSignature, tools=tools, max_iters=8)

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

            steps: List[ExecutionStep] = []
            prediction = None

            with dspy.context(lm=lm):
                async for chunk in stream_program(
                    task_instruction=instruction, file_path=cwd
                ):
                    if isinstance(chunk, StatusMessage) and chunk.message:
                        step = ExecutionStep(
                            timestamp=datetime.now().isoformat(),
                            type="status",
                            content=chunk.message,
                        )
                        steps.append(step)
                        await on_step(step)
                    elif isinstance(chunk, dspy.Prediction):
                        prediction = chunk

            # Extract cost from LM history
            cost_info = extract_cost_from_history(lm)

            # files_changed is now computed by ExecutionSandbox in the executor
            files_changed = []

            # Clear LM history to avoid accumulating between calls
            if hasattr(lm, "history"):
                lm.history.clear()

            if prediction is None:
                return ExecutionResult(
                    success=False,
                    steps=steps,
                    error="No prediction received from LLM",
                    total_tokens=cost_info["total_tokens"],
                    total_cost=cost_info["total_cost"],
                )

            # Add final summary step
            summary = getattr(prediction, "completion_summary", "")
            if summary:
                final_step = ExecutionStep(
                    timestamp=datetime.now().isoformat(),
                    type="text",
                    content=summary,
                )
                steps.append(final_step)
                await on_step(final_step)

            return ExecutionResult(
                success=True,
                files_changed=files_changed,
                steps=steps,
                total_tokens=cost_info["total_tokens"],
                total_cost=cost_info["total_cost"],
            )

        except Exception as e:
            logger.error(f"DspyReact backend error: {e}", exc_info=True)
            return ExecutionResult(
                success=False,
                error=str(e),
            )


# ============================================================================
# UTILITY FUNCTIONS (extracted from executor_helpers.py)
# ============================================================================


def extract_files_changed(trajectory) -> List[str]:
    """Extrae paths de archivos modificados de la trajectory de ReAct.

    Recorre las tool calls de la trajectory y extrae los paths
    de las operaciones que modifican archivos (write, replace, delete).

    Args:
        trajectory: Dict con la trajectory de ReAct
            (Action_N, Action_N_args, etc.)

    Returns:
        Lista de paths únicos de archivos modificados.
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


def extract_cost_from_history(lm) -> dict:
    """Extrae métricas de coste del historial de llamadas al LM.

    Recorre lm.history sumando tokens y costes de cada llamada.
    Compatible con la estructura de LiteLLM/DSPy.

    Args:
        lm: Language Model con historial de llamadas.

    Returns:
        Dict con prompt_tokens, completion_tokens, total_tokens, total_cost.
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
            or ((call.get("response") or {}).get("_hidden_params") or {}).get(
                "response_cost"
            )
        )
        total_cost += cost or 0

    return {
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "total_tokens": prompt_tokens + completion_tokens,
        "total_cost": total_cost,
    }
