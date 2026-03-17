"""
cline.py
Backend de ejecución basado en Cline CLI.

Ejecuta instrucciones via `cline task --json --yolo --act` y parsea
los eventos JSON de stdout para construir ExecutionStep objects.
"""

import asyncio
import json
from typing import Callable, Awaitable, List

from autocode.core.planning.models import ExecutionStep
from autocode.core.planning.backends.base import ExecutionResult


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
        stderr_data = b""

        async for line in proc.stdout:
            text = line.decode("utf-8", errors="replace").strip()
            if not text:
                continue
            try:
                event = json.loads(text)
                step = self._parse_event(event)
                steps.append(step)
                await on_step(step)
            except json.JSONDecodeError:
                continue

        stderr_data = await proc.stderr.read()
        await proc.wait()

        files = await self._git_diff_name_only(cwd)

        return ExecutionResult(
            success=proc.returncode == 0,
            files_changed=files,
            steps=steps,
            error="" if proc.returncode == 0 else stderr_data.decode("utf-8", errors="replace"),
        )

    def _parse_event(self, event: dict) -> ExecutionStep:
        """Convierte un evento JSON de cline a ExecutionStep."""
        return ExecutionStep(
            type=event.get("type", "unknown"),
            content=event.get("content", str(event)),
            tool=event.get("tool", ""),
            path=event.get("path", ""),
        )

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
