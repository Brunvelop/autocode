"""
opencode.py
Backend de ejecución basado en OpenCode CLI.

Ejecuta instrucciones via `opencode run --format json` y parsea
los eventos JSON de stdout para construir ExecutionStep objects.

Formato real de eventos JSON (NDJSON, un objeto por línea):

    {"type":"step_start","timestamp":1773780143463,"sessionID":"ses_...",
     "part":{"type":"step-start","snapshot":"..."}}

    {"type":"text","timestamp":1773780143463,"sessionID":"ses_...",
     "part":{"type":"text","text":"HELLO","time":{...}}}

    {"type":"tool_use","timestamp":1773780153760,"sessionID":"ses_...",
     "part":{"type":"tool","callID":"toolu_...","tool":"read",
             "state":{"status":"completed",
                      "input":{"filePath":"/tmp/test/README.md"},
                      "output":"...",
                      "title":"README.md",
                      "metadata":{...},
                      "time":{...}}}}

    {"type":"step_finish","timestamp":1773780143488,"sessionID":"ses_...",
     "part":{"type":"step-finish","reason":"stop",
             "cost":0.07447875,
             "tokens":{"total":11902,"input":2,"output":5,
                       "reasoning":0,"cache":{"read":0,"write":11895}}}}
"""

import asyncio
import json
from datetime import datetime, timezone
from typing import Callable, Awaitable, List, Optional

from autocode.core.planning.models import ExecutionStep
from autocode.core.planning.backends.base import ExecutionResult


# Mapeo de nombres de herramienta de OpenCode → nombres normalizados
_TOOL_NAME_MAP = {
    "read": "read_file",
    "write": "write_file",
    "edit": "edit_file",
    "bash": "execute_command",
    "glob": "list_files",
    "grep": "search_files",
    "fetch": "fetch_url",
    "todoread": "todo_read",
    "todowrite": "todo_write",
}


def _epoch_ms_to_iso(epoch_ms: int) -> str:
    """Convierte un timestamp en milisegundos epoch a ISO 8601."""
    try:
        dt = datetime.fromtimestamp(epoch_ms / 1000, tz=timezone.utc)
        return dt.isoformat()
    except (TypeError, ValueError, OSError):
        return ""


def _extract_tool_path(state: dict) -> str:
    """Extrae la ruta de archivo del state de una herramienta OpenCode."""
    input_data = state.get("input", {})
    # Intentar filePath primero (read, write, edit)
    path = input_data.get("filePath", "")
    if not path:
        # Fallback a pattern (glob, grep)
        path = input_data.get("pattern", "")
    if not path:
        # Fallback a command (bash)
        path = input_data.get("command", "")
    if not path:
        # Último recurso: title del state
        path = state.get("title", "")
    return path


class OpenCodeBackend:
    """Backend que ejecuta planes usando OpenCode CLI."""

    name = "opencode"

    def __init__(self):
        self._process: Optional[asyncio.subprocess.Process] = None

    async def execute(
        self,
        instruction: str,
        cwd: str,
        model: str,
        on_step: Callable[[ExecutionStep], Awaitable[None]],
    ) -> ExecutionResult:
        """Ejecuta una instrucción via opencode run --format json."""
        cmd = ["opencode", "run", "--format", "json"]
        if model:
            cmd.extend(["-m", model])
        cmd.extend(["--dir", cwd, instruction])

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
                error=f"Failed to start opencode: {exc}",
            )

        self._process = proc

        steps: List[ExecutionStep] = []
        total_tokens = 0
        total_cost = 0.0
        session_id = ""

        async for line in proc.stdout:
            text = line.decode("utf-8", errors="replace").strip()
            if not text:
                continue
            try:
                event = json.loads(text)
            except json.JSONDecodeError:
                continue

            # Extraer session_id del primer evento que lo tenga
            if not session_id:
                session_id = event.get("sessionID", "")

            # Acumular tokens y costes de step_finish
            if event.get("type") == "step_finish":
                part = event.get("part", {})
                total_cost += part.get("cost", 0.0)
                tokens = part.get("tokens", {})
                total_tokens += tokens.get("total", 0)

            # Parsear evento a ExecutionStep (puede ser None si se debe omitir)
            step = self._parse_event(event)
            if step is not None:
                steps.append(step)
                await on_step(step)

        # Esperar a que el proceso termine (con timeout y fallback a terminate/kill)
        # IMPORTANTE: proc.stderr.read() se hace DESPUÉS de que el proceso haya muerto.
        # Si se hiciera antes y el proceso sigue vivo, stderr no llega a EOF y bloquea.
        try:
            await asyncio.wait_for(proc.wait(), timeout=15)
        except asyncio.TimeoutError:
            proc.terminate()
            try:
                await asyncio.wait_for(proc.wait(), timeout=5)
            except asyncio.TimeoutError:
                proc.kill()
            await proc.wait()

        # Proceso ya muerto: stderr.read() retorna inmediatamente
        stderr_data = await proc.stderr.read()

        files = await self._git_diff_name_only(cwd)

        # Post-execution: enrich tokens/cost from `opencode export` (more accurate than stream)
        export_data = await self._fetch_session_export(session_id, cwd)
        if export_data:
            total_cost = export_data.get("cost", total_cost)
            tokens_data = export_data.get("tokens", {})
            if tokens_data:
                total_tokens = tokens_data.get("total", total_tokens)

        return ExecutionResult(
            success=proc.returncode == 0,
            files_changed=files,
            steps=steps,
            total_tokens=total_tokens,
            total_cost=total_cost,
            session_id=session_id,
            error="" if proc.returncode == 0 else stderr_data.decode("utf-8", errors="replace"),
        )

    def _parse_event(self, event: dict) -> Optional[ExecutionStep]:
        """
        Convierte un evento JSON de opencode a ExecutionStep.

        Retorna None para eventos que no generan un paso visible
        (step_start, step_finish).
        """
        event_type = event.get("type", "")
        timestamp = _epoch_ms_to_iso(event.get("timestamp", 0))
        part = event.get("part", {})

        if event_type == "text":
            return ExecutionStep(
                timestamp=timestamp,
                type="text",
                content=part.get("text", ""),
            )

        if event_type == "tool_use":
            tool_raw = part.get("tool", "")
            tool_name = _TOOL_NAME_MAP.get(tool_raw, tool_raw)
            state = part.get("state", {})
            path = _extract_tool_path(state)
            # Contenido: output si completado, sino un resumen
            status = state.get("status", "")
            if status == "completed":
                content = state.get("output", "")
            else:
                content = state.get("title", str(state.get("input", "")))
            return ExecutionStep(
                timestamp=timestamp,
                type="tool_use",
                content=content,
                tool=tool_name,
                path=path,
            )

        # step_start y step_finish no generan pasos visibles
        # (step_finish se procesa en execute() para acumular metadata)
        return None

    def abort(self) -> None:
        """Kill the subprocess if running."""
        if self._process and self._process.returncode is None:
            self._process.kill()

    async def _fetch_session_export(self, session_id: str, cwd: str) -> dict:
        """
        Post-execution: calls `opencode export {session_id}` to get accurate
        session metadata (tokens, cost) not available during streaming.

        Returns the parsed JSON dict on success, or an empty dict on any failure
        (binary not found, non-zero exit, invalid JSON, empty session_id).
        """
        if not session_id:
            return {}
        try:
            proc = await asyncio.create_subprocess_exec(
                "opencode", "export", session_id,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=cwd,
            )
            stdout, _ = await proc.communicate()
            if proc.returncode != 0:
                return {}
            return json.loads(stdout.decode("utf-8", errors="replace"))
        except (FileNotFoundError, OSError, json.JSONDecodeError, ValueError):
            return {}

    async def _git_diff_name_only(self, cwd: str) -> List[str]:
        """Obtiene archivos cambiados via git diff --name-only."""
        try:
            proc = await asyncio.create_subprocess_exec(
                "git", "diff", "--name-only", "HEAD",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=cwd,
            )
            stdout, _ = await proc.communicate()
            if proc.returncode == 0:
                return [f for f in stdout.decode().strip().split("\n") if f]
            return []
        except (FileNotFoundError, OSError):
            return []
