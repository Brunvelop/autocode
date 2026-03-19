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

__all__ = [
    "ExecutorBackend",
    "ExecutionResult",
    "SubprocessBackend",
    "OpenCodeBackend",
    "ClineBackend",
    "DspyReactBackend",
]
