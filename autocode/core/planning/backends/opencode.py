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
from typing import Optional

from autocode.core.planning.models import ExecutionStep
from autocode.core.planning.backends.subprocess_base import SubprocessBackend


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


class OpenCodeBackend(SubprocessBackend):
    """Backend que ejecuta planes usando OpenCode CLI."""

    name = "opencode"

    def build_command(self, instruction: str, cwd: str, model: str) -> list:
        """Construye los args CLI para lanzar opencode run."""
        cmd = ["opencode", "run", "--format", "json"]
        if model:
            cmd.extend(["-m", model])
        cmd.extend(["--dir", cwd, instruction])
        return cmd

    def parse_event(self, event: dict) -> Optional[ExecutionStep]:
        """
        Convierte un evento JSON de opencode a ExecutionStep.

        Como side-effect, actualiza self._session_id, self._tokens y
        self._cost cuando el evento contenga esa información.

        Retorna None para eventos que no generan un paso visible
        (step_start, step_finish).
        """
        # Side-effects: extraer session_id del primer evento que lo tenga
        if not self._session_id:
            self._session_id = event.get("sessionID", "")

        # Acumular tokens y costes de step_finish durante el stream
        if event.get("type") == "step_finish":
            part = event.get("part", {})
            self._cost += part.get("cost", 0.0)
            tokens = part.get("tokens", {})
            self._tokens += tokens.get("total", 0)

        # Parsear evento a ExecutionStep
        event_type = event.get("type", "")
        timestamp = self._epoch_ms_to_iso(event.get("timestamp", 0))
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
        return None

    async def fetch_post_metadata(self, session_id: str, cwd: str) -> tuple:
        """
        Obtiene metadatos precisos de tokens/coste de `opencode export`.

        Retorna (total_tokens, total_cost). Si falla, retorna (0, 0.0)
        y execute() usará los valores acumulados del stream.
        """
        export = await self._fetch_session_export(session_id, cwd)
        tokens = export.get("tokens", {}).get("total", 0)
        cost = export.get("cost", 0.0)
        return (tokens, cost)

    async def _fetch_session_export(self, session_id: str, cwd: str) -> dict:
        """
        Llama a `opencode export {session_id}` para obtener datos precisos de
        coste y tokens de la sesión.

        Retorna el dict parseado del JSON, o {} en caso de error.
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
        except (FileNotFoundError, OSError, json.JSONDecodeError, ValueError, TypeError):
            return {}
