"""
backends — Motores de ejecución pluggables para commit plans.

Cada backend implementa el protocolo ExecutorBackend y puede ser
seleccionado al momento de ejecutar un plan.
"""

from .base import ExecutorBackend, ExecutionResult

__all__ = ["ExecutorBackend", "ExecutionResult"]
