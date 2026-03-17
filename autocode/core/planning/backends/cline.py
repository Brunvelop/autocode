"""
cline.py
Backend de ejecución basado en Cline CLI.

Ejecuta instrucciones via `cline task --json --yolo --act` y parsea
los eventos JSON de stdout para construir ExecutionStep objects.

Formato real de eventos JSON (NDJSON, un objeto por línea):

    {"type":"task_started","taskId":"1773780171429"}

    {"ts":1773780171439,"type":"say","say":"task",
     "text":"...",
     "modelInfo":{"providerId":"anthropic","modelId":"claude-opus-4-6","mode":"act"},
     "conversationHistoryIndex":-1}

    {"ts":1773780172034,"type":"say","say":"api_req_started",
     "text":"{JSON request body}",
     "modelInfo":{...},"conversationHistoryIndex":-1}

    {"ts":1773780174146,"type":"say","say":"reasoning",
     "text":"Let me read the README.md file first...",
     "partial":false,"modelInfo":{...},"conversationHistoryIndex":0}

    {"ts":1773780175028,"type":"say","say":"tool",
     "text":"{\\"tool\\":\\"readFile\\",\\"path\\":\\"README.md\\",\\"content\\":\\"...\\",\\"operationIsLocatedInWorkspace\\":true}",
     "partial":false,"modelInfo":{...},"conversationHistoryIndex":0}

    {"ts":1773780177205,"type":"say","say":"task_progress",
     "text":"- [x] Read README.md\\n- [ ] Create hello.txt",
     "modelInfo":{...},"conversationHistoryIndex":1}

    {"ts":1773780189208,"type":"say","say":"completion_result",
     "text":"I read the README.md file and created hello.txt.",
     "modelInfo":{...},"conversationHistoryIndex":5}
"""

import asyncio
import json
from datetime import datetime, timezone
from typing import Callable, Awaitable, List, Optional

from autocode.core.planning.models import ExecutionStep
from autocode.core.planning.backends.base import ExecutionResult


# Mapeo de nombres de herramienta de Cline → nombres normalizados
_TOOL_NAME_MAP = {
    "readFile": "read_file",
    "read_file": "read_file",
    "writeToFile": "write_file",
    "write_to_file": "write_file",
    "newFileCreated": "write_file",
    "editedExistingFile": "edit_file",
    "replace_in_file": "edit_file",
    "listFiles": "list_files",
    "list_files": "list_files",
    "searchFiles": "search_files",
    "search_files": "search_files",
    "executeCommand": "execute_command",
    "execute_command": "execute_command",
    "listCodeDefinitionNames": "list_definitions",
    "list_code_definition_names": "list_definitions",
    "attemptCompletion": "completion",
    "attempt_completion": "completion",
    "planModeRespond": "plan_respond",
    "plan_mode_respond": "plan_respond",
    "accessMcpResource": "mcp_resource",
    "useMcpTool": "mcp_tool",
}

# Tipos de evento "say" que producen pasos visibles
_VISIBLE_SAY_TYPES = {"reasoning", "tool", "completion_result", "text", "error"}

# Tipos de evento "say" que se omiten (metadata interna)
_SKIP_SAY_TYPES = {"task", "api_req_started", "api_req_finished", "task_progress"}


def _epoch_ms_to_iso(epoch_ms: int) -> str:
    """Convierte un timestamp en milisegundos epoch a ISO 8601."""
    try:
        dt = datetime.fromtimestamp(epoch_ms / 1000, tz=timezone.utc)
        return dt.isoformat()
    except (TypeError, ValueError, OSError):
        return ""


def _parse_tool_text(text: str) -> dict:
    """Parsea el campo text de un evento say:tool (es JSON embebido)."""
    try:
        return json.loads(text)
    except (json.JSONDecodeError, TypeError):
        return {}


class ClineBackend:
    """Backend que ejecuta planes usando Cline CLI."""

    name = "cline"

    def __init__(self, timeout: int = 0):
        self.timeout = timeout

    async def execute(
        self,
        instruction: str,
        cwd: str,
        model: str,
        on_step: Callable[[ExecutionStep], Awaitable[None]],
    ) -> ExecutionResult:
        """Ejecuta una instrucción via cline task --json --yolo --act."""
        cmd = ["cline", "task", "--json", "--yolo", "--act"]
        if model:
            cmd.extend(["-m", model])
        if self.timeout:
            cmd.extend(["--timeout", str(self.timeout)])
        cmd.extend(["--cwd", cwd, instruction])

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
                error=f"Failed to start cline: {exc}",
            )

        steps: List[ExecutionStep] = []
        session_id = ""
        api_cost_accum: dict = {"tokens": 0, "cost": 0.0}

        async for line in proc.stdout:
            text = line.decode("utf-8", errors="replace").strip()
            if not text:
                continue
            try:
                event = json.loads(text)
            except json.JSONDecodeError:
                continue

            # Extraer task_id como session_id
            if event.get("type") == "task_started":
                session_id = event.get("taskId", "")
                continue

            # Acumular tokens/cost de api_req_finished durante el stream
            if event.get("type") == "say" and event.get("say") == "api_req_finished":
                self._accumulate_api_cost(event, api_cost_accum)
                continue

            # Parsear evento a ExecutionStep
            step = self._parse_event(event)
            if step is not None:
                steps.append(step)
                await on_step(step)

        stderr_data = await proc.stderr.read()
        await proc.wait()

        files = await self._git_diff_name_only(cwd)

        # Start with streamed accumulation as baseline
        total_tokens = api_cost_accum["tokens"]
        total_cost = api_cost_accum["cost"]

        # Post-execution: enrich tokens/cost from `cline history` (more accurate)
        history_data = await self._fetch_task_history(session_id, cwd)
        if history_data:
            total_tokens = history_data.get("totalTokensUsed", total_tokens)
            total_cost = history_data.get("totalCost", total_cost)

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
        Convierte un evento JSON de Cline a ExecutionStep.

        Retorna None para eventos internos que no generan pasos visibles
        (task_started, api_req_started, task_progress, task).
        """
        event_type = event.get("type", "")
        timestamp = _epoch_ms_to_iso(event.get("ts", 0))

        # Solo procesamos eventos de tipo "say"
        if event_type != "say":
            return None

        say_type = event.get("say", "")

        # Omitir eventos internos
        if say_type in _SKIP_SAY_TYPES:
            return None

        if say_type == "reasoning":
            return ExecutionStep(
                timestamp=timestamp,
                type="thinking",
                content=event.get("text", ""),
            )

        if say_type == "tool":
            tool_data = _parse_tool_text(event.get("text", ""))
            tool_raw = tool_data.get("tool", "")
            tool_name = _TOOL_NAME_MAP.get(tool_raw, tool_raw)
            path = tool_data.get("path", "")
            content = tool_data.get("content", "")
            return ExecutionStep(
                timestamp=timestamp,
                type="tool_use",
                content=content,
                tool=tool_name,
                path=path,
            )

        if say_type == "completion_result":
            return ExecutionStep(
                timestamp=timestamp,
                type="completion",
                content=event.get("text", ""),
            )

        if say_type == "text":
            return ExecutionStep(
                timestamp=timestamp,
                type="text",
                content=event.get("text", ""),
            )

        if say_type == "error":
            return ExecutionStep(
                timestamp=timestamp,
                type="error",
                content=event.get("text", ""),
            )

        # Cualquier otro say_type desconocido: omitir
        return None

    def _accumulate_api_cost(self, event: dict, _accum: dict) -> None:
        """
        Extrae tokens/cost de un evento api_req_finished.

        El campo ``text`` es un JSON embebido con los campos:
        ``tokensIn``, ``tokensOut``, ``cost`` (y posiblemente ``cacheWrites``,
        ``cacheReads``).  Los valores se acumulan en el dict ``_accum``.
        """
        text = event.get("text", "")
        try:
            data = json.loads(text)
            _accum["tokens"] += data.get("tokensIn", 0) + data.get("tokensOut", 0)
            _accum["cost"] += data.get("cost", 0.0)
        except (json.JSONDecodeError, TypeError):
            pass

    async def _fetch_task_history(self, task_id: str, cwd: str) -> dict:
        """
        Post-execution: calls `cline history` to get accurate task metadata
        (totalTokensUsed, totalCost) not available during streaming.

        Returns the history entry dict matching ``task_id`` on success, or an
        empty dict on any failure (binary not found, non-zero exit, invalid
        JSON, empty task_id, task not found in history).
        """
        if not task_id:
            return {}
        try:
            proc = await asyncio.create_subprocess_exec(
                "cline", "history",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=cwd,
            )
            stdout, _ = await proc.communicate()
            if proc.returncode != 0:
                return {}
            history = json.loads(stdout.decode("utf-8", errors="replace"))
            if isinstance(history, list):
                for entry in history:
                    if str(entry.get("id", "")) == str(task_id):
                        return entry
            return {}
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
