"""
Tests for ClineBackend.

All tests mock subprocess to avoid requiring the cline CLI.
"""

import asyncio
import json
import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from autocode.core.planning.backends.cline import ClineBackend
from autocode.core.planning.backends.base import ExecutionResult
from autocode.core.planning.models import ExecutionStep


@pytest.fixture
def backend():
    return ClineBackend()


@pytest.fixture
def on_step():
    return AsyncMock()


def _make_process(stdout_lines=None, stderr=b"", returncode=0):
    """Create a mock async subprocess."""
    proc = AsyncMock()
    proc.returncode = returncode

    lines = stdout_lines or []
    encoded = []
    for l in lines:
        if isinstance(l, dict):
            encoded.append(json.dumps(l).encode() + b"\n")
        else:
            encoded.append(l.encode() + b"\n")

    async def _iter():
        for line in encoded:
            yield line

    proc.stdout = _iter()
    proc.stderr = AsyncMock()
    proc.stderr.read = AsyncMock(return_value=stderr)
    proc.wait = AsyncMock(return_value=returncode)
    return proc


class TestClineBackend:
    """Tests for ClineBackend."""

    def test_name(self, backend):
        assert backend.name == "cline"

    @pytest.mark.asyncio
    async def test_builds_correct_command(self, backend, on_step):
        """Verifies that cline task --json --yolo --act is called."""
        with patch("asyncio.create_subprocess_exec", new_callable=AsyncMock) as mock_exec, \
             patch.object(backend, "_git_diff_name_only", return_value=[]):
            mock_exec.return_value = _make_process(returncode=0)
            await backend.execute("do stuff", "/tmp/cwd", "", on_step)

            args = mock_exec.call_args[0]
            assert args[0] == "cline"
            assert "task" in args
            assert "--json" in args
            assert "--yolo" in args
            assert "--act" in args
            assert "do stuff" in args

    @pytest.mark.asyncio
    async def test_passes_model_flag(self, backend, on_step):
        """Verifies -m model is passed when model is set."""
        with patch("asyncio.create_subprocess_exec", new_callable=AsyncMock) as mock_exec, \
             patch.object(backend, "_git_diff_name_only", return_value=[]):
            mock_exec.return_value = _make_process(returncode=0)
            await backend.execute("do stuff", "/tmp/cwd", "anthropic/claude-3.5-sonnet", on_step)

            args = mock_exec.call_args[0]
            assert "-m" in args
            idx = args.index("-m")
            assert args[idx + 1] == "anthropic/claude-3.5-sonnet"

    @pytest.mark.asyncio
    async def test_passes_cwd(self, backend, on_step):
        """Verifies --cwd is passed."""
        with patch("asyncio.create_subprocess_exec", new_callable=AsyncMock) as mock_exec, \
             patch.object(backend, "_git_diff_name_only", return_value=[]):
            mock_exec.return_value = _make_process(returncode=0)
            await backend.execute("do stuff", "/my/project", "", on_step)

            args = mock_exec.call_args[0]
            assert "--cwd" in args
            idx = args.index("--cwd")
            assert args[idx + 1] == "/my/project"

    @pytest.mark.asyncio
    async def test_parses_json_events_to_steps(self, backend, on_step):
        """Verifies JSON events from stdout are parsed to ExecutionStep."""
        events = [
            {"type": "thinking", "content": "Analyzing the codebase..."},
            {"type": "tool_use", "content": "Reading file", "tool": "read_file", "path": "src/api.py"},
        ]
        with patch("asyncio.create_subprocess_exec", new_callable=AsyncMock) as mock_exec, \
             patch.object(backend, "_git_diff_name_only", return_value=[]):
            mock_exec.return_value = _make_process(stdout_lines=events, returncode=0)
            result = await backend.execute("do stuff", "/tmp", "", on_step)

            assert len(result.steps) == 2
            assert result.steps[0].type == "thinking"
            assert result.steps[0].content == "Analyzing the codebase..."
            assert result.steps[1].type == "tool_use"
            assert result.steps[1].tool == "read_file"
            assert result.steps[1].path == "src/api.py"

    @pytest.mark.asyncio
    async def test_calls_on_step_for_each_event(self, backend, on_step):
        """Verifies on_step callback is invoked for each event."""
        events = [
            {"type": "thinking", "content": "Step 1"},
            {"type": "text", "content": "Step 2"},
            {"type": "tool_use", "content": "Step 3", "tool": "write_file", "path": "x.py"},
        ]
        with patch("asyncio.create_subprocess_exec", new_callable=AsyncMock) as mock_exec, \
             patch.object(backend, "_git_diff_name_only", return_value=[]):
            mock_exec.return_value = _make_process(stdout_lines=events, returncode=0)
            await backend.execute("do stuff", "/tmp", "", on_step)

            assert on_step.call_count == 3

    @pytest.mark.asyncio
    async def test_detects_files_changed_via_git_diff(self, backend, on_step):
        """Verifies post-execution git diff --name-only is used."""
        with patch("asyncio.create_subprocess_exec", new_callable=AsyncMock) as mock_exec, \
             patch.object(backend, "_git_diff_name_only", return_value=["src/api.py", "src/models.py"]):
            mock_exec.return_value = _make_process(returncode=0)
            result = await backend.execute("do stuff", "/tmp", "", on_step)

            assert result.files_changed == ["src/api.py", "src/models.py"]

    @pytest.mark.asyncio
    async def test_returns_execution_result(self, backend, on_step):
        """Verifies ExecutionResult has correct fields."""
        events = [{"type": "text", "content": "Done"}]
        with patch("asyncio.create_subprocess_exec", new_callable=AsyncMock) as mock_exec, \
             patch.object(backend, "_git_diff_name_only", return_value=["a.py"]):
            mock_exec.return_value = _make_process(stdout_lines=events, returncode=0)
            result = await backend.execute("do stuff", "/tmp", "", on_step)

            assert isinstance(result, ExecutionResult)
            assert result.success is True
            assert result.error == ""
            assert len(result.steps) == 1
            assert result.files_changed == ["a.py"]

    @pytest.mark.asyncio
    async def test_handles_subprocess_error(self, backend, on_step):
        """Verifies ExecutionResult(success=False) on subprocess error."""
        with patch("asyncio.create_subprocess_exec", new_callable=AsyncMock) as mock_exec, \
             patch.object(backend, "_git_diff_name_only", return_value=[]):
            mock_exec.return_value = _make_process(
                stderr=b"cline: task execution failed", returncode=1
            )
            result = await backend.execute("do stuff", "/tmp", "", on_step)

            assert result.success is False
            assert "task execution failed" in result.error

    @pytest.mark.asyncio
    async def test_handles_process_not_found(self, backend, on_step):
        """Verifies graceful handling when cline is not installed."""
        with patch("asyncio.create_subprocess_exec", new_callable=AsyncMock) as mock_exec:
            mock_exec.side_effect = FileNotFoundError("cline not found")
            result = await backend.execute("do stuff", "/tmp", "", on_step)

            assert result.success is False
            assert "cline" in result.error

    @pytest.mark.asyncio
    async def test_handles_invalid_json_lines(self, backend, on_step):
        """Verifies non-JSON lines are silently ignored."""
        mixed_lines = [
            "not json at all",
            {"type": "text", "content": "valid event"},
            "another bad line",
        ]
        with patch("asyncio.create_subprocess_exec", new_callable=AsyncMock) as mock_exec, \
             patch.object(backend, "_git_diff_name_only", return_value=[]):
            proc = AsyncMock()
            proc.returncode = 0
            encoded = []
            for item in mixed_lines:
                if isinstance(item, dict):
                    encoded.append(json.dumps(item).encode() + b"\n")
                else:
                    encoded.append(item.encode() + b"\n")

            async def _iter():
                for line in encoded:
                    yield line

            proc.stdout = _iter()
            proc.stderr = AsyncMock()
            proc.stderr.read = AsyncMock(return_value=b"")
            proc.wait = AsyncMock(return_value=0)
            mock_exec.return_value = proc

            result = await backend.execute("do stuff", "/tmp", "", on_step)

            assert len(result.steps) == 1
            assert result.steps[0].type == "text"
            assert result.success is True

    @pytest.mark.asyncio
    async def test_passes_timeout_flag(self, backend, on_step):
        """Verifies --timeout is passed when timeout is set."""
        backend_with_timeout = ClineBackend(timeout=300)
        with patch("asyncio.create_subprocess_exec", new_callable=AsyncMock) as mock_exec, \
             patch.object(backend_with_timeout, "_git_diff_name_only", return_value=[]):
            mock_exec.return_value = _make_process(returncode=0)
            await backend_with_timeout.execute("do stuff", "/tmp/cwd", "", on_step)

            args = mock_exec.call_args[0]
            assert "--timeout" in args
            idx = args.index("--timeout")
            assert args[idx + 1] == "300"

    @pytest.mark.asyncio
    async def test_no_timeout_flag_by_default(self, backend, on_step):
        """Verifies --timeout is NOT passed when timeout is 0 (default)."""
        with patch("asyncio.create_subprocess_exec", new_callable=AsyncMock) as mock_exec, \
             patch.object(backend, "_git_diff_name_only", return_value=[]):
            mock_exec.return_value = _make_process(returncode=0)
            await backend.execute("do stuff", "/tmp/cwd", "", on_step)

            args = mock_exec.call_args[0]
            assert "--timeout" not in args

    @pytest.mark.asyncio
    async def test_no_model_flag_when_empty(self, backend, on_step):
        """Verifies -m is NOT passed when model is empty string."""
        with patch("asyncio.create_subprocess_exec", new_callable=AsyncMock) as mock_exec, \
             patch.object(backend, "_git_diff_name_only", return_value=[]):
            mock_exec.return_value = _make_process(returncode=0)
            await backend.execute("do stuff", "/tmp/cwd", "", on_step)

            args = mock_exec.call_args[0]
            assert "-m" not in args
