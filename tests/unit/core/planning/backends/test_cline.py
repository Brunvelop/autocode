"""
Tests for ClineBackend.

All tests mock subprocess to avoid requiring the cline CLI.
Tests use the real JSON event format emitted by `cline task --json`.
"""

import asyncio
import json
import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from autocode.core.planning.backends.cline import (
    ClineBackend,
    _epoch_ms_to_iso,
    _parse_tool_text,
    _TOOL_NAME_MAP,
)
from autocode.core.planning.backends.base import ExecutionResult
from autocode.core.planning.models import ExecutionStep


# ---------------------------------------------------------------------------
# Fixtures con formato REAL de Cline
# ---------------------------------------------------------------------------

TASK_ID = "1773780171429"


def _cl_task_started(task_id=TASK_ID):
    """Evento task_started real de Cline."""
    return {"type": "task_started", "taskId": task_id}


def _cl_say_task(text, ts=1773780171439):
    """Evento say:task — echo del prompt inicial."""
    return {
        "ts": ts,
        "type": "say",
        "say": "task",
        "text": text,
        "modelInfo": {"providerId": "anthropic", "modelId": "claude-opus-4-6", "mode": "act"},
        "conversationHistoryIndex": -1,
    }


def _cl_say_api_req(ts=1773780172034):
    """Evento say:api_req_started — request interno al LLM."""
    return {
        "ts": ts,
        "type": "say",
        "say": "api_req_started",
        "text": '{"request": "..."}',
        "modelInfo": {"providerId": "anthropic", "modelId": "claude-opus-4-6", "mode": "act"},
        "conversationHistoryIndex": -1,
    }


def _cl_say_reasoning(text, ts=1773780174146, idx=0):
    """Evento say:reasoning — pensamiento del modelo."""
    return {
        "ts": ts,
        "type": "say",
        "say": "reasoning",
        "text": text,
        "partial": False,
        "modelInfo": {"providerId": "anthropic", "modelId": "claude-opus-4-6", "mode": "act"},
        "conversationHistoryIndex": idx,
    }


def _cl_say_tool(tool, path="", content="", ts=1773780175028, idx=0):
    """Evento say:tool — uso de herramienta (text es JSON embebido)."""
    tool_data = {"tool": tool, "path": path, "content": content, "operationIsLocatedInWorkspace": True}
    return {
        "ts": ts,
        "type": "say",
        "say": "tool",
        "text": json.dumps(tool_data),
        "partial": False,
        "modelInfo": {"providerId": "anthropic", "modelId": "claude-opus-4-6", "mode": "act"},
        "conversationHistoryIndex": idx,
    }


def _cl_say_task_progress(text, ts=1773780177205, idx=1):
    """Evento say:task_progress — progreso de tarea."""
    return {
        "ts": ts,
        "type": "say",
        "say": "task_progress",
        "text": text,
        "modelInfo": {"providerId": "anthropic", "modelId": "claude-opus-4-6", "mode": "act"},
        "conversationHistoryIndex": idx,
    }


def _cl_say_completion(text, ts=1773780189208, idx=5):
    """Evento say:completion_result — resultado final."""
    return {
        "ts": ts,
        "type": "say",
        "say": "completion_result",
        "text": text,
        "modelInfo": {"providerId": "anthropic", "modelId": "claude-opus-4-6", "mode": "act"},
        "conversationHistoryIndex": idx,
    }


def _cl_say_error(text, ts=1773780190000, idx=6):
    """Evento say:error — error durante ejecución."""
    return {
        "ts": ts,
        "type": "say",
        "say": "error",
        "text": text,
        "modelInfo": {"providerId": "anthropic", "modelId": "claude-opus-4-6", "mode": "act"},
        "conversationHistoryIndex": idx,
    }


def _cl_say_text(text, ts=1773780188000, idx=4):
    """Evento say:text — texto genérico."""
    return {
        "ts": ts,
        "type": "say",
        "say": "text",
        "text": text,
        "modelInfo": {"providerId": "anthropic", "modelId": "claude-opus-4-6", "mode": "act"},
        "conversationHistoryIndex": idx,
    }


# ---------------------------------------------------------------------------
# Process mock helper
# ---------------------------------------------------------------------------

@pytest.fixture
def backend():
    return ClineBackend()


@pytest.fixture
def on_step():
    return AsyncMock()


def _make_process(stdout_lines=None, stderr=b"", returncode=0):
    """Create a mock async subprocess with real-format events."""
    proc = AsyncMock()
    proc.returncode = returncode

    lines = stdout_lines or []
    encoded = []
    for item in lines:
        if isinstance(item, dict):
            encoded.append(json.dumps(item).encode() + b"\n")
        else:
            encoded.append(item.encode() + b"\n")

    async def _iter():
        for line in encoded:
            yield line

    proc.stdout = _iter()
    proc.stderr = AsyncMock()
    proc.stderr.read = AsyncMock(return_value=stderr)
    proc.wait = AsyncMock(return_value=returncode)
    return proc


# ===========================================================================
# Unit tests para helpers de parseo
# ===========================================================================


class TestParseToolText:
    """Tests for _parse_tool_text helper."""

    def test_parses_valid_json(self):
        text = '{"tool": "readFile", "path": "README.md", "content": "/tmp/README.md"}'
        result = _parse_tool_text(text)
        assert result["tool"] == "readFile"
        assert result["path"] == "README.md"

    def test_returns_empty_on_invalid_json(self):
        result = _parse_tool_text("not json")
        assert result == {}

    def test_returns_empty_on_none(self):
        result = _parse_tool_text(None)
        assert result == {}

    def test_returns_empty_on_empty_string(self):
        result = _parse_tool_text("")
        assert result == {}

    def test_parses_newFileCreated(self):
        text = json.dumps({
            "tool": "newFileCreated",
            "path": "hello.txt",
            "content": "Hello World",
            "operationIsLocatedInWorkspace": True,
            "startLineNumbers": [],
        })
        result = _parse_tool_text(text)
        assert result["tool"] == "newFileCreated"
        assert result["path"] == "hello.txt"


class TestClineToolNameMap:
    """Tests for the Cline tool name mapping."""

    def test_readFile_maps_to_read_file(self):
        assert _TOOL_NAME_MAP["readFile"] == "read_file"

    def test_writeToFile_maps_to_write_file(self):
        assert _TOOL_NAME_MAP["writeToFile"] == "write_file"

    def test_newFileCreated_maps_to_write_file(self):
        assert _TOOL_NAME_MAP["newFileCreated"] == "write_file"

    def test_editedExistingFile_maps_to_edit_file(self):
        assert _TOOL_NAME_MAP["editedExistingFile"] == "edit_file"

    def test_executeCommand_maps_to_execute_command(self):
        assert _TOOL_NAME_MAP["executeCommand"] == "execute_command"

    def test_listFiles_maps_to_list_files(self):
        assert _TOOL_NAME_MAP["listFiles"] == "list_files"

    def test_searchFiles_maps_to_search_files(self):
        assert _TOOL_NAME_MAP["searchFiles"] == "search_files"

    def test_attemptCompletion_maps_to_completion(self):
        assert _TOOL_NAME_MAP["attemptCompletion"] == "completion"

    def test_snake_case_variants_also_mapped(self):
        assert _TOOL_NAME_MAP["read_file"] == "read_file"
        assert _TOOL_NAME_MAP["write_to_file"] == "write_file"
        assert _TOOL_NAME_MAP["replace_in_file"] == "edit_file"


class TestClineEpochMsToIso:
    """Tests for _epoch_ms_to_iso (shared helper)."""

    def test_converts_valid_cline_timestamp(self):
        result = _epoch_ms_to_iso(1773780171439)
        assert "2026" in result
        assert "T" in result


# ===========================================================================
# Unit tests para _parse_event
# ===========================================================================


class TestParseEvent:
    """Tests for ClineBackend._parse_event with real formats."""

    def setup_method(self):
        self.backend = ClineBackend()

    def test_task_started_returns_none(self):
        """task_started es metadata, no genera step."""
        event = _cl_task_started()
        step = self.backend._parse_event(event)
        assert step is None

    def test_say_task_returns_none(self):
        """say:task es echo del prompt, no genera step."""
        event = _cl_say_task("Do something")
        step = self.backend._parse_event(event)
        assert step is None

    def test_say_api_req_returns_none(self):
        """say:api_req_started es metadata interna, no genera step."""
        event = _cl_say_api_req()
        step = self.backend._parse_event(event)
        assert step is None

    def test_say_task_progress_returns_none(self):
        """say:task_progress es metadata interna, no genera step."""
        event = _cl_say_task_progress("- [x] Step 1\n- [ ] Step 2")
        step = self.backend._parse_event(event)
        assert step is None

    def test_reasoning_parsed_as_thinking(self):
        event = _cl_say_reasoning("Let me analyze the code...")
        step = self.backend._parse_event(event)
        assert step is not None
        assert step.type == "thinking"
        assert step.content == "Let me analyze the code..."
        assert step.timestamp != ""

    def test_tool_readFile_parsed(self):
        event = _cl_say_tool(tool="readFile", path="README.md", content="/tmp/README.md")
        step = self.backend._parse_event(event)
        assert step is not None
        assert step.type == "tool_use"
        assert step.tool == "read_file"
        assert step.path == "README.md"

    def test_tool_newFileCreated_parsed(self):
        event = _cl_say_tool(tool="newFileCreated", path="hello.txt", content="Hello World")
        step = self.backend._parse_event(event)
        assert step is not None
        assert step.type == "tool_use"
        assert step.tool == "write_file"
        assert step.path == "hello.txt"
        assert step.content == "Hello World"

    def test_tool_executeCommand_parsed(self):
        event = _cl_say_tool(tool="executeCommand", path="", content="npm test")
        step = self.backend._parse_event(event)
        assert step is not None
        assert step.tool == "execute_command"

    def test_tool_unknown_passes_through(self):
        event = _cl_say_tool(tool="someNewTool", path="x.py")
        step = self.backend._parse_event(event)
        assert step is not None
        assert step.tool == "someNewTool"

    def test_completion_result_parsed(self):
        event = _cl_say_completion("I completed the task successfully.")
        step = self.backend._parse_event(event)
        assert step is not None
        assert step.type == "completion"
        assert "completed" in step.content

    def test_say_text_parsed(self):
        event = _cl_say_text("Some informational text")
        step = self.backend._parse_event(event)
        assert step is not None
        assert step.type == "text"
        assert step.content == "Some informational text"

    def test_say_error_parsed(self):
        event = _cl_say_error("Something went wrong")
        step = self.backend._parse_event(event)
        assert step is not None
        assert step.type == "error"
        assert "went wrong" in step.content

    def test_unknown_say_type_returns_none(self):
        event = {
            "ts": 1773780190000,
            "type": "say",
            "say": "some_future_type",
            "text": "...",
        }
        step = self.backend._parse_event(event)
        assert step is None

    def test_timestamp_converted_to_iso(self):
        event = _cl_say_reasoning("thinking...", ts=1773780174146)
        step = self.backend._parse_event(event)
        assert "2026" in step.timestamp
        assert "T" in step.timestamp

    def test_tool_with_malformed_text_json(self):
        """If tool text is not valid JSON, tool/path are empty."""
        event = {
            "ts": 1773780175028,
            "type": "say",
            "say": "tool",
            "text": "not valid json",
            "partial": False,
        }
        step = self.backend._parse_event(event)
        assert step is not None
        assert step.type == "tool_use"
        assert step.tool == ""
        assert step.path == ""


# ===========================================================================
# Integration tests: full execute() flow
# ===========================================================================


class TestClineBackend:
    """Integration tests for ClineBackend.execute() with real event format."""

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
    async def test_parses_real_json_events_to_steps(self, backend, on_step):
        """Verifies real Cline JSON events are parsed to ExecutionStep."""
        events = [
            _cl_task_started(),
            _cl_say_task("Read README.md and create hello.txt"),
            _cl_say_api_req(),
            _cl_say_reasoning("Let me read the README.md file first."),
            _cl_say_tool(tool="readFile", path="README.md", content="/tmp/README.md"),
            _cl_say_task_progress("- [x] Read README.md\n- [ ] Create hello.txt"),
            _cl_say_api_req(ts=1773780177231),
            _cl_say_reasoning("Now I'll create hello.txt.", ts=1773780179451, idx=2),
            _cl_say_tool(tool="newFileCreated", path="hello.txt", content="Hello World", ts=1773780180838, idx=2),
            _cl_say_task_progress("- [x] Read README.md\n- [x] Create hello.txt", ts=1773780184935, idx=3),
            _cl_say_api_req(ts=1773780184964),
            _cl_say_reasoning("Both tasks are complete.", ts=1773780187535, idx=4),
            _cl_say_completion("I read README.md and created hello.txt."),
        ]
        with patch("asyncio.create_subprocess_exec", new_callable=AsyncMock) as mock_exec, \
             patch.object(backend, "_git_diff_name_only", return_value=[]):
            mock_exec.return_value = _make_process(stdout_lines=events, returncode=0)
            result = await backend.execute("do stuff", "/tmp", "", on_step)

            # Visible steps: 3x reasoning + 2x tool + 1x completion = 6
            assert len(result.steps) == 6
            assert result.steps[0].type == "thinking"
            assert result.steps[0].content == "Let me read the README.md file first."
            assert result.steps[1].type == "tool_use"
            assert result.steps[1].tool == "read_file"
            assert result.steps[1].path == "README.md"
            assert result.steps[2].type == "thinking"
            assert result.steps[3].type == "tool_use"
            assert result.steps[3].tool == "write_file"
            assert result.steps[3].path == "hello.txt"
            assert result.steps[4].type == "thinking"
            assert result.steps[5].type == "completion"

    @pytest.mark.asyncio
    async def test_calls_on_step_only_for_visible_events(self, backend, on_step):
        """Verifies on_step is NOT called for internal events."""
        events = [
            _cl_task_started(),
            _cl_say_task("Do something"),
            _cl_say_api_req(),
            _cl_say_reasoning("Thinking..."),
            _cl_say_tool(tool="readFile", path="x.py", content="..."),
            _cl_say_task_progress("- [x] Done"),
            _cl_say_completion("All done."),
        ]
        with patch("asyncio.create_subprocess_exec", new_callable=AsyncMock) as mock_exec, \
             patch.object(backend, "_git_diff_name_only", return_value=[]):
            mock_exec.return_value = _make_process(stdout_lines=events, returncode=0)
            await backend.execute("do stuff", "/tmp", "", on_step)

            # reasoning + tool + completion = 3
            assert on_step.call_count == 3

    @pytest.mark.asyncio
    async def test_extracts_session_id_from_task_started(self, backend, on_step):
        """Verifies session_id comes from task_started.taskId."""
        events = [
            _cl_task_started(task_id="12345"),
            _cl_say_reasoning("Hello"),
        ]
        with patch("asyncio.create_subprocess_exec", new_callable=AsyncMock) as mock_exec, \
             patch.object(backend, "_git_diff_name_only", return_value=[]):
            mock_exec.return_value = _make_process(stdout_lines=events, returncode=0)
            result = await backend.execute("do stuff", "/tmp", "", on_step)

            assert result.session_id == "12345"

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
        events = [
            _cl_task_started(),
            _cl_say_reasoning("Done"),
            _cl_say_completion("Task complete."),
        ]
        with patch("asyncio.create_subprocess_exec", new_callable=AsyncMock) as mock_exec, \
             patch.object(backend, "_git_diff_name_only", return_value=["a.py"]):
            mock_exec.return_value = _make_process(stdout_lines=events, returncode=0)
            result = await backend.execute("do stuff", "/tmp", "", on_step)

            assert isinstance(result, ExecutionResult)
            assert result.success is True
            assert result.error == ""
            assert len(result.steps) == 2  # reasoning + completion
            assert result.files_changed == ["a.py"]
            assert result.session_id == TASK_ID

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
            _cl_say_reasoning("valid event"),
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
            assert result.steps[0].type == "thinking"
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

    @pytest.mark.asyncio
    async def test_tool_names_are_normalized(self, backend, on_step):
        """Verifies Cline tool names are mapped to normalized names."""
        events = [
            _cl_say_tool(tool="readFile", path="a.py"),
            _cl_say_tool(tool="newFileCreated", path="b.py"),
            _cl_say_tool(tool="editedExistingFile", path="c.py"),
            _cl_say_tool(tool="executeCommand", content="npm test"),
            _cl_say_tool(tool="listFiles", path="src/"),
            _cl_say_tool(tool="searchFiles", path="*.py"),
        ]
        with patch("asyncio.create_subprocess_exec", new_callable=AsyncMock) as mock_exec, \
             patch.object(backend, "_git_diff_name_only", return_value=[]):
            mock_exec.return_value = _make_process(stdout_lines=events, returncode=0)
            result = await backend.execute("do stuff", "/tmp", "", on_step)

            tools = [s.tool for s in result.steps]
            assert tools == [
                "read_file", "write_file", "edit_file",
                "execute_command", "list_files", "search_files",
            ]

    @pytest.mark.asyncio
    async def test_empty_session_produces_empty_result(self, backend, on_step):
        """Verifies an empty stdout produces a valid empty result."""
        with patch("asyncio.create_subprocess_exec", new_callable=AsyncMock) as mock_exec, \
             patch.object(backend, "_git_diff_name_only", return_value=[]):
            mock_exec.return_value = _make_process(stdout_lines=[], returncode=0)
            result = await backend.execute("do stuff", "/tmp", "", on_step)

            assert result.success is True
            assert result.steps == []
            assert result.session_id == ""

    @pytest.mark.asyncio
    async def test_error_events_are_captured(self, backend, on_step):
        """Verifies say:error events become error steps."""
        events = [
            _cl_task_started(),
            _cl_say_error("API rate limit exceeded"),
        ]
        with patch("asyncio.create_subprocess_exec", new_callable=AsyncMock) as mock_exec, \
             patch.object(backend, "_git_diff_name_only", return_value=[]):
            mock_exec.return_value = _make_process(stdout_lines=events, returncode=0)
            result = await backend.execute("do stuff", "/tmp", "", on_step)

            assert len(result.steps) == 1
            assert result.steps[0].type == "error"
            assert "rate limit" in result.steps[0].content
