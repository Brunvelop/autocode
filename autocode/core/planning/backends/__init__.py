"""
backends — Motores de ejecución pluggables para commit plans.

Cada backend implementa el protocolo ExecutorBackend y puede ser
seleccionado al momento de ejecutar un plan.
"""

from .base import ExecutorBackend, ExecutionResult
from .subprocess_base import SubprocessBackend
from .opencode import OpenCodeBackend
from .cline import ClineBackend
from .dspy_react import DspyReactBackend


def get_backend(name: str) -> ExecutorBackend:
    """Resolve backend name to an instance.

    Args:
        name: Backend identifier ("opencode", "cline", "dspy").

    Returns:
        An ExecutorBackend instance.

    Raises:
        ValueError: If the backend name is unknown.
    """
    if name == "opencode":
        return OpenCodeBackend()
    if name == "cline":
        return ClineBackend()
    if name == "dspy":
        return DspyReactBackend()
    raise ValueError(f"Unknown backend '{name}'. Available: cline, dspy, opencode")


__all__ = [
    "ExecutorBackend",
    "ExecutionResult",
    "SubprocessBackend",
    "OpenCodeBackend",
    "ClineBackend",
    "DspyReactBackend",
    "get_backend",
]
