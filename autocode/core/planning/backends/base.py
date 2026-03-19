"""
base.py
ABC y resultado base para backends de ejecución de planes.

Define el contrato que todo backend (opencode, cline, dspy) debe cumplir
para ser utilizado por el executor como motor de ejecución.
"""

from abc import ABC, abstractmethod
from typing import Callable, Awaitable, List
from dataclasses import dataclass, field

from autocode.core.planning.models import ExecutionStep


@dataclass
class ExecutionResult:
    """Resultado de ejecutar un plan via un backend."""

    success: bool
    files_changed: List[str] = field(default_factory=list)
    steps: List[ExecutionStep] = field(default_factory=list)
    total_tokens: int = 0
    total_cost: float = 0.0
    session_id: str = ""
    error: str = ""


class ExecutorBackend(ABC):
    """ABC que todo backend de ejecución debe implementar."""

    name: str

    @abstractmethod
    async def execute(
        self,
        instruction: str,
        cwd: str,
        model: str,
        on_step: Callable[[ExecutionStep], Awaitable[None]],
    ) -> ExecutionResult: ...

    def abort(self) -> None:
        """Kill the running process immediately. Default no-op."""
        pass
