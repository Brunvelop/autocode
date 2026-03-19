"""
subprocess_base.py
ABC base para backends que ejecutan via CLI subprocess + NDJSON.

Define la lógica compartida de spawn, lectura de NDJSON, timeout/kill
y consolidación de metadata post-ejecución. Los backends concretos
(OpenCodeBackend, ClineBackend) heredan de aquí e implementan los 3
métodos abstractos: build_command, parse_event y fetch_post_metadata.
"""

import asyncio
import json
from abc import abstractmethod
from datetime import datetime, timezone
from typing import Callable, Awaitable, List, Optional

from autocode.core.planning.models import ExecutionStep
from autocode.core.planning.backends.base import ExecutorBackend, ExecutionResult


class SubprocessBackend(ExecutorBackend):
    """Base para backends que ejecutan via CLI subprocess + NDJSON."""

    _process: Optional[asyncio.subprocess.Process] = None
    _session_id: str = ""
    _tokens: int = 0
    _cost: float = 0.0

    # ------------------------------------------------------------------
    # Abstract interface — cada backend concreto los implementa
    # ------------------------------------------------------------------

    @abstractmethod
    def build_command(self, instruction: str, cwd: str, model: str) -> list:
        """
        Construye los args CLI para lanzar el proceso.

        Retorna una lista de strings lista para pasar a
        asyncio.create_subprocess_exec(*cmd, ...).
        """
        ...

    @abstractmethod
    def parse_event(self, event: dict) -> Optional[ExecutionStep]:
        """
        Parsea un evento JSON del stream a ExecutionStep.

        Retorna None si el evento no genera un paso visible.

        Como side-effect, debe actualizar self._session_id, self._tokens
        y self._cost cuando el evento contenga esa información.
        """
        ...

    @abstractmethod
    async def fetch_post_metadata(
        self, session_id: str, cwd: str
    ) -> tuple:
        """
        Obtiene metadatos precisos de tokens/coste post-ejecución.

        Retorna una tupla (total_tokens: int, total_cost: float).
        Si falla o no hay datos, retorna (0, 0.0) y execute() usará
        los valores acumulados del stream.
        """
        ...

    # ------------------------------------------------------------------
    # Virtual — se puede overridear para hacer break antes del EOF
    # ------------------------------------------------------------------

    def is_final_event(self, event: dict) -> bool:
        """
        Retorna True si el evento indica que la ejecución ha terminado.

        Default: False (lee hasta EOF). ClineBackend lo overridea para
        salir en completion_result/error sin esperar al cierre de stdout.
        """
        return False

    # ------------------------------------------------------------------
    # Static helper — idéntico en ambos backends originales
    # ------------------------------------------------------------------

    @staticmethod
    def _epoch_ms_to_iso(epoch_ms: int) -> str:
        """Convierte un timestamp en milisegundos epoch a ISO 8601."""
        try:
            dt = datetime.fromtimestamp(epoch_ms / 1000, tz=timezone.utc)
            return dt.isoformat()
        except (TypeError, ValueError, OSError):
            return ""

    # ------------------------------------------------------------------
    # Concrete: lógica de subprocess compartida
    # ------------------------------------------------------------------

    async def execute(
        self,
        instruction: str,
        cwd: str,
        model: str,
        on_step: Callable[[ExecutionStep], Awaitable[None]],
    ) -> ExecutionResult:
        """
        Ejecuta la instrucción lanzando un subproceso y parseando NDJSON.

        Flujo:
        1. build_command() → args CLI
        2. create_subprocess_exec (FileNotFoundError/OSError → error result)
        3. Reset state, NDJSON loop: parse_event → on_step → is_final_event
        4. Wait con timeout + terminate/kill fallback
        5. fetch_post_metadata → consolidar tokens/cost
        6. Retornar ExecutionResult
        """
        cmd = self.build_command(instruction, cwd, model)

        try:
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=cwd,
            )
        except (FileNotFoundError, OSError) as exc:
            return ExecutionResult(
                success=False,
                error=f"Failed to start {cmd[0]}: {exc}",
            )

        self._process = proc
        self._session_id = ""
        self._tokens = 0
        self._cost = 0.0

        steps: List[ExecutionStep] = []

        async for line in proc.stdout:
            text = line.decode("utf-8", errors="replace").strip()
            if not text:
                continue
            try:
                event = json.loads(text)
            except json.JSONDecodeError:
                continue

            # parse → on_step → is_final (este orden es importante para
            # Cline: el evento de completion se emite ANTES del break)
            step = self.parse_event(event)
            if step is not None:
                steps.append(step)
                await on_step(step)

            if self.is_final_event(event):
                break

        # Esperar a que el proceso termine con timeout y fallback a
        # terminate/kill. stderr.read() se llama DESPUÉS de que el proceso
        # haya muerto para evitar que bloquee indefinidamente.
        try:
            await asyncio.wait_for(proc.wait(), timeout=15)
        except asyncio.TimeoutError:
            proc.terminate()
            try:
                await asyncio.wait_for(proc.wait(), timeout=5)
            except asyncio.TimeoutError:
                proc.kill()
            await proc.wait()

        stderr_data = await proc.stderr.read()

        meta_tokens, meta_cost = await self.fetch_post_metadata(
            self._session_id, cwd
        )

        # Preferir metadatos post-ejecución; fallback a valores del stream
        final_tokens = meta_tokens if meta_tokens else self._tokens
        final_cost = meta_cost if meta_cost else self._cost

        return ExecutionResult(
            success=proc.returncode == 0,
            files_changed=[],
            steps=steps,
            total_tokens=final_tokens,
            total_cost=final_cost,
            session_id=self._session_id,
            error=(
                ""
                if proc.returncode == 0
                else stderr_data.decode("utf-8", errors="replace")
            ),
        )

    def abort(self) -> None:
        """Kill the subprocess immediately if it is still running."""
        if self._process and self._process.returncode is None:
            self._process.kill()
