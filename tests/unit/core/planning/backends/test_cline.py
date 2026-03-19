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
        with patch("asyncio.create_subprocess_exec", new_callable=AsyncMock) as mock_exec:
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
        with patch("asyncio.create_subprocess_exec", new_callable=AsyncMock) as mock_exec:
            mock_exec.return_value = _make_process(returncode=0)
            await backend.execute("do stuff", "/tmp/cwd", "anthropic/claude-3.5-sonnet", on_step)

            args = mock_exec.call_args[0]
            assert "-m" in args
            idx = args.index("-m")
            assert args[idx + 1] == "anthropic/claude-3.5-sonnet"

    @pytest.mark.asyncio
    async def test_passes_cwd(self, backend, on_step):
        """Verifies --cwd is passed."""
        with patch("asyncio.create_subprocess_exec", new_callable=AsyncMock) as mock_exec:
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
        with patch("asyncio.create_subprocess_exec", new_callable=AsyncMock) as mock_exec:
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
        with patch("asyncio.create_subprocess_exec", new_callable=AsyncMock) as mock_exec:
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
        with patch("asyncio.create_subprocess_exec", new_callable=AsyncMock) as mock_exec:
            mock_exec.return_value = _make_process(stdout_lines=events, returncode=0)
            result = await backend.execute("do stuff", "/tmp", "", on_step)

            assert result.session_id == "12345"

    @pytest.mark.asyncio
    async def test_files_changed_always_empty(self, backend, on_step):
        """Verifies backend does NOT detect files — files_changed is always []."""
        with patch("asyncio.create_subprocess_exec", new_callable=AsyncMock) as mock_exec:
            mock_exec.return_value = _make_process(returncode=0)
            result = await backend.execute("do stuff", "/tmp", "", on_step)

            assert result.files_changed == []

    @pytest.mark.asyncio
    async def test_returns_execution_result(self, backend, on_step):
        """Verifies ExecutionResult has correct fields."""
        events = [
            _cl_task_started(),
            _cl_say_reasoning("Done"),
            _cl_say_completion("Task complete."),
        ]
        with patch("asyncio.create_subprocess_exec", new_callable=AsyncMock) as mock_exec:
            mock_exec.return_value = _make_process(stdout_lines=events, returncode=0)
            result = await backend.execute("do stuff", "/tmp", "", on_step)

            assert isinstance(result, ExecutionResult)
            assert result.success is True
            assert result.error == ""
            assert len(result.steps) == 2  # reasoning + completion
            assert result.files_changed == []
            assert result.session_id == TASK_ID

    @pytest.mark.asyncio
    async def test_handles_subprocess_error(self, backend, on_step):
        """Verifies ExecutionResult(success=False) on subprocess error."""
        with patch("asyncio.create_subprocess_exec", new_callable=AsyncMock) as mock_exec:
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
        with patch("asyncio.create_subprocess_exec", new_callable=AsyncMock) as mock_exec:
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
        with patch("asyncio.create_subprocess_exec", new_callable=AsyncMock) as mock_exec:
            mock_exec.return_value = _make_process(returncode=0)
            await backend_with_timeout.execute("do stuff", "/tmp/cwd", "", on_step)

            args = mock_exec.call_args[0]
            assert "--timeout" in args
            idx = args.index("--timeout")
            assert args[idx + 1] == "300"

    @pytest.mark.asyncio
    async def test_no_timeout_flag_by_default(self, backend, on_step):
        """Verifies --timeout is NOT passed when timeout is 0 (default)."""
        with patch("asyncio.create_subprocess_exec", new_callable=AsyncMock) as mock_exec:
            mock_exec.return_value = _make_process(returncode=0)
            await backend.execute("do stuff", "/tmp/cwd", "", on_step)

            args = mock_exec.call_args[0]
            assert "--timeout" not in args

    @pytest.mark.asyncio
    async def test_no_model_flag_when_empty(self, backend, on_step):
        """Verifies -m is NOT passed when model is empty string."""
        with patch("asyncio.create_subprocess_exec", new_callable=AsyncMock) as mock_exec:
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
        with patch("asyncio.create_subprocess_exec", new_callable=AsyncMock) as mock_exec:
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
        with patch("asyncio.create_subprocess_exec", new_callable=AsyncMock) as mock_exec:
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
        with patch("asyncio.create_subprocess_exec", new_callable=AsyncMock) as mock_exec:
            mock_exec.return_value = _make_process(stdout_lines=events, returncode=0)
            result = await backend.execute("do stuff", "/tmp", "", on_step)

            assert len(result.steps) == 1
            assert result.steps[0].type == "error"
            assert "rate limit" in result.steps[0].content


# ===========================================================================
# Tests for _accumulate_api_cost (stream-based token/cost accumulation)
# ===========================================================================


class TestAccumulateApiCost:
    """Tests for ClineBackend._accumulate_api_cost."""

    def setup_method(self):
        self.backend = ClineBackend()

    def test_extracts_tokens_in_and_out(self):
        """Accumulates tokensIn + tokensOut into tokens key."""
        event = {
            "ts": 1773780174146,
            "type": "say",
            "say": "api_req_finished",
            "text": json.dumps({"tokensIn": 1000, "tokensOut": 200, "cost": 0.025}),
        }
        accum = {"tokens": 0, "cost": 0.0}
        self.backend._accumulate_api_cost(event, accum)

        assert accum["tokens"] == 1200
        assert accum["cost"] == pytest.approx(0.025)

    def test_accumulates_across_multiple_calls(self):
        """Multiple api_req_finished events are summed correctly."""
        accum = {"tokens": 0, "cost": 0.0}
        for _ in range(3):
            event = {
                "ts": 1000,
                "type": "say",
                "say": "api_req_finished",
                "text": json.dumps({"tokensIn": 500, "tokensOut": 100, "cost": 0.01}),
            }
            self.backend._accumulate_api_cost(event, accum)

        assert accum["tokens"] == 1800
        assert accum["cost"] == pytest.approx(0.03)

    def test_handles_missing_tokensIn(self):
        """Missing tokensIn defaults to 0."""
        event = {
            "ts": 1000,
            "type": "say",
            "say": "api_req_finished",
            "text": json.dumps({"tokensOut": 300, "cost": 0.005}),
        }
        accum = {"tokens": 0, "cost": 0.0}
        self.backend._accumulate_api_cost(event, accum)

        assert accum["tokens"] == 300
        assert accum["cost"] == pytest.approx(0.005)

    def test_handles_missing_cost(self):
        """Missing cost defaults to 0.0."""
        event = {
            "ts": 1000,
            "type": "say",
            "say": "api_req_finished",
            "text": json.dumps({"tokensIn": 400, "tokensOut": 100}),
        }
        accum = {"tokens": 0, "cost": 0.0}
        self.backend._accumulate_api_cost(event, accum)

        assert accum["tokens"] == 500
        assert accum["cost"] == 0.0

    def test_handles_all_fields_missing(self):
        """Empty JSON dict doesn't change the accumulator."""
        event = {
            "ts": 1000,
            "type": "say",
            "say": "api_req_finished",
            "text": json.dumps({}),
        }
        accum = {"tokens": 0, "cost": 0.0}
        self.backend._accumulate_api_cost(event, accum)

        assert accum["tokens"] == 0
        assert accum["cost"] == 0.0

    def test_handles_invalid_json_text(self):
        """Non-JSON text doesn't crash; accumulator stays unchanged."""
        event = {
            "ts": 1000,
            "type": "say",
            "say": "api_req_finished",
            "text": "not valid json at all",
        }
        accum = {"tokens": 100, "cost": 0.01}
        self.backend._accumulate_api_cost(event, accum)

        assert accum["tokens"] == 100
        assert accum["cost"] == pytest.approx(0.01)

    def test_handles_missing_text_field(self):
        """Event without 'text' field doesn't crash."""
        event = {"ts": 1000, "type": "say", "say": "api_req_finished"}
        accum = {"tokens": 0, "cost": 0.0}
        self.backend._accumulate_api_cost(event, accum)

        assert accum["tokens"] == 0

    @pytest.mark.asyncio
    async def test_execute_accumulates_from_api_req_finished_events(self, backend, on_step):
        """execute() sums tokens/cost from api_req_finished stream events."""
        events = [
            _cl_task_started(),
            _cl_say_reasoning("Thinking...", ts=1773780174000),
            {
                "ts": 1773780175000,
                "type": "say",
                "say": "api_req_finished",
                "text": json.dumps({"tokensIn": 800, "tokensOut": 150, "cost": 0.018}),
            },
            _cl_say_tool(tool="readFile", path="x.py", content="code"),
            {
                "ts": 1773780180000,
                "type": "say",
                "say": "api_req_finished",
                "text": json.dumps({"tokensIn": 900, "tokensOut": 200, "cost": 0.022}),
            },
            _cl_say_completion("Done."),
        ]
        with patch("asyncio.create_subprocess_exec", new_callable=AsyncMock) as mock_exec, \
             patch.object(backend, "_fetch_task_history", return_value={}):
            mock_exec.return_value = _make_process(stdout_lines=events, returncode=0)
            result = await backend.execute("do stuff", "/tmp", "", on_step)

            # 800+150 + 900+200 = 2050 tokens, 0.018 + 0.022 = 0.04 cost
            assert result.total_tokens == 2050
            assert result.total_cost == pytest.approx(0.04)

    @pytest.mark.asyncio
    async def test_api_req_finished_not_emitted_as_step(self, backend, on_step):
        """api_req_finished events are NOT forwarded to on_step."""
        events = [
            _cl_task_started(),
            {
                "ts": 1773780175000,
                "type": "say",
                "say": "api_req_finished",
                "text": json.dumps({"tokensIn": 500, "tokensOut": 100, "cost": 0.01}),
            },
            _cl_say_completion("Done."),
        ]
        with patch("asyncio.create_subprocess_exec", new_callable=AsyncMock) as mock_exec, \
             patch.object(backend, "_fetch_task_history", return_value={}):
            mock_exec.return_value = _make_process(stdout_lines=events, returncode=0)
            await backend.execute("do stuff", "/tmp", "", on_step)

            # Only completion → 1 step, not the api_req_finished
            assert on_step.call_count == 1


# ===========================================================================
# Tests for post-execution metadata extraction via `cline history`
# ===========================================================================


class TestFetchTaskHistory:
    """Tests for ClineBackend._fetch_task_history."""

    @pytest.mark.asyncio
    async def test_calls_cline_history(self, backend):
        """Verifies `cline history` is called."""
        history = [{"id": "12345", "totalTokensUsed": 5000, "totalCost": 0.05}]
        mock_proc = AsyncMock()
        mock_proc.returncode = 0
        mock_proc.communicate = AsyncMock(return_value=(json.dumps(history).encode(), b""))

        with patch("asyncio.create_subprocess_exec", new_callable=AsyncMock) as mock_exec:
            mock_exec.return_value = mock_proc
            await backend._fetch_task_history("12345", "/tmp/cwd")

            args = mock_exec.call_args[0]
            assert args[0] == "cline"
            assert "history" in args

    @pytest.mark.asyncio
    async def test_returns_matching_task_entry(self, backend):
        """Returns the history entry whose 'id' matches task_id."""
        history = [
            {"id": "11111", "totalTokensUsed": 100, "totalCost": 0.01},
            {"id": "12345", "totalTokensUsed": 5000, "totalCost": 0.05},
            {"id": "99999", "totalTokensUsed": 200, "totalCost": 0.02},
        ]
        mock_proc = AsyncMock()
        mock_proc.returncode = 0
        mock_proc.communicate = AsyncMock(return_value=(json.dumps(history).encode(), b""))

        with patch("asyncio.create_subprocess_exec", new_callable=AsyncMock) as mock_exec:
            mock_exec.return_value = mock_proc
            result = await backend._fetch_task_history("12345", "/tmp")

            assert result["id"] == "12345"
            assert result["totalTokensUsed"] == 5000
            assert result["totalCost"] == pytest.approx(0.05)

    @pytest.mark.asyncio
    async def test_returns_empty_dict_when_task_not_found(self, backend):
        """Returns empty dict when no history entry matches task_id."""
        history = [{"id": "11111", "totalTokensUsed": 100, "totalCost": 0.01}]
        mock_proc = AsyncMock()
        mock_proc.returncode = 0
        mock_proc.communicate = AsyncMock(return_value=(json.dumps(history).encode(), b""))

        with patch("asyncio.create_subprocess_exec", new_callable=AsyncMock) as mock_exec:
            mock_exec.return_value = mock_proc
            result = await backend._fetch_task_history("99999", "/tmp")

            assert result == {}

    @pytest.mark.asyncio
    async def test_matches_task_id_as_string(self, backend):
        """Matches task_id even when history stores id as an integer."""
        history = [{"id": 12345, "totalTokensUsed": 3000, "totalCost": 0.03}]
        mock_proc = AsyncMock()
        mock_proc.returncode = 0
        mock_proc.communicate = AsyncMock(return_value=(json.dumps(history).encode(), b""))

        with patch("asyncio.create_subprocess_exec", new_callable=AsyncMock) as mock_exec:
            mock_exec.return_value = mock_proc
            result = await backend._fetch_task_history("12345", "/tmp")

            assert result["totalTokensUsed"] == 3000

    @pytest.mark.asyncio
    async def test_returns_empty_dict_when_task_id_empty(self, backend):
        """No subprocess is launched when task_id is an empty string."""
        with patch("asyncio.create_subprocess_exec", new_callable=AsyncMock) as mock_exec:
            result = await backend._fetch_task_history("", "/tmp")

            assert result == {}
            mock_exec.assert_not_called()

    @pytest.mark.asyncio
    async def test_returns_empty_dict_on_nonzero_returncode(self, backend):
        """Returns empty dict when cline history exits with non-zero code."""
        mock_proc = AsyncMock()
        mock_proc.returncode = 1
        mock_proc.communicate = AsyncMock(return_value=(b"", b"error"))

        with patch("asyncio.create_subprocess_exec", new_callable=AsyncMock) as mock_exec:
            mock_exec.return_value = mock_proc
            result = await backend._fetch_task_history("12345", "/tmp")

            assert result == {}

    @pytest.mark.asyncio
    async def test_returns_empty_dict_on_process_not_found(self, backend):
        """Returns empty dict when the cline binary is not installed."""
        with patch("asyncio.create_subprocess_exec", new_callable=AsyncMock) as mock_exec:
            mock_exec.side_effect = FileNotFoundError("cline not found")
            result = await backend._fetch_task_history("12345", "/tmp")

            assert result == {}

    @pytest.mark.asyncio
    async def test_returns_empty_dict_on_os_error(self, backend):
        """Returns empty dict on any OSError."""
        with patch("asyncio.create_subprocess_exec", new_callable=AsyncMock) as mock_exec:
            mock_exec.side_effect = OSError("permission denied")
            result = await backend._fetch_task_history("12345", "/tmp")

            assert result == {}

    @pytest.mark.asyncio
    async def test_returns_empty_dict_on_invalid_json(self, backend):
        """Returns empty dict when cline history output is not valid JSON."""
        mock_proc = AsyncMock()
        mock_proc.returncode = 0
        mock_proc.communicate = AsyncMock(return_value=(b"not valid json", b""))

        with patch("asyncio.create_subprocess_exec", new_callable=AsyncMock) as mock_exec:
            mock_exec.return_value = mock_proc
            result = await backend._fetch_task_history("12345", "/tmp")

            assert result == {}

    @pytest.mark.asyncio
    async def test_returns_empty_dict_when_history_not_a_list(self, backend):
        """Returns empty dict when history JSON is not a list."""
        mock_proc = AsyncMock()
        mock_proc.returncode = 0
        mock_proc.communicate = AsyncMock(return_value=(b'{"error": "not a list"}', b""))

        with patch("asyncio.create_subprocess_exec", new_callable=AsyncMock) as mock_exec:
            mock_exec.return_value = mock_proc
            result = await backend._fetch_task_history("12345", "/tmp")

            assert result == {}

    @pytest.mark.asyncio
    async def test_execute_enriches_tokens_from_history(self, backend, on_step):
        """execute() uses history totalTokensUsed to override streamed accumulation."""
        events = [
            _cl_task_started(task_id="12345"),
            _cl_say_reasoning("Thinking"),
        ]
        history_data = {"id": "12345", "totalTokensUsed": 8000, "totalCost": 0.08}

        with patch("asyncio.create_subprocess_exec", new_callable=AsyncMock) as mock_exec, \
             patch.object(backend, "_fetch_task_history", return_value=history_data):
            mock_exec.return_value = _make_process(stdout_lines=events, returncode=0)
            result = await backend.execute("do stuff", "/tmp", "", on_step)

            assert result.total_tokens == 8000
            assert result.total_cost == pytest.approx(0.08)

    @pytest.mark.asyncio
    async def test_execute_falls_back_to_stream_when_history_empty(self, backend, on_step):
        """execute() keeps streamed values when _fetch_task_history returns empty."""
        events = [
            _cl_task_started(task_id="12345"),
            {
                "ts": 1773780175000,
                "type": "say",
                "say": "api_req_finished",
                "text": json.dumps({"tokensIn": 1000, "tokensOut": 200, "cost": 0.025}),
            },
            _cl_say_reasoning("Thinking"),
        ]
        with patch("asyncio.create_subprocess_exec", new_callable=AsyncMock) as mock_exec, \
             patch.object(backend, "_fetch_task_history", return_value={}):
            mock_exec.return_value = _make_process(stdout_lines=events, returncode=0)
            result = await backend.execute("do stuff", "/tmp", "", on_step)

            assert result.total_tokens == 1200  # 1000 + 200 from api_req_finished
            assert result.total_cost == pytest.approx(0.025)

    @pytest.mark.asyncio
    async def test_execute_calls_fetch_history_with_session_id_and_cwd(self, backend, on_step):
        """execute() passes the extracted session_id and cwd to _fetch_task_history."""
        events = [_cl_task_started(task_id="42000")]

        with patch("asyncio.create_subprocess_exec", new_callable=AsyncMock) as mock_exec, \
             patch.object(backend, "_fetch_task_history", return_value={}) as mock_history:
            mock_exec.return_value = _make_process(stdout_lines=events, returncode=0)
            await backend.execute("do stuff", "/my/project", "", on_step)

            mock_history.assert_called_once_with("42000", "/my/project")


# ===========================================================================
# Tests for completion detection and process management (Bug 2 fix)
# ===========================================================================


class TestCompletionDetection:
    """Tests for completion detection, process timeout, and process reference storage."""

    @pytest.mark.asyncio
    async def test_breaks_on_completion_result(self, backend, on_step):
        """Events after completion_result are NOT processed — loop breaks early."""
        events = [
            _cl_task_started(),
            _cl_say_reasoning("Thinking..."),
            _cl_say_completion("Done!"),
            _cl_say_reasoning("This should NOT appear"),  # after completion → skipped
        ]
        with patch("asyncio.create_subprocess_exec", new_callable=AsyncMock) as mock_exec, \
             patch.object(backend, "_fetch_task_history", return_value={}):
            mock_exec.return_value = _make_process(stdout_lines=events, returncode=0)
            result = await backend.execute("do stuff", "/tmp", "", on_step)

        # Only: thinking + completion = 2 steps; reasoning after completion is skipped
        assert len(result.steps) == 2
        assert result.steps[0].type == "thinking"
        assert result.steps[1].type == "completion"

    @pytest.mark.asyncio
    async def test_breaks_on_error_event(self, backend, on_step):
        """Events after an error say event are NOT processed — loop breaks early."""
        events = [
            _cl_task_started(),
            _cl_say_reasoning("Thinking..."),
            _cl_say_error("Something went wrong"),
            _cl_say_reasoning("This should NOT appear"),  # after error → skipped
        ]
        with patch("asyncio.create_subprocess_exec", new_callable=AsyncMock) as mock_exec, \
             patch.object(backend, "_fetch_task_history", return_value={}):
            mock_exec.return_value = _make_process(stdout_lines=events, returncode=0)
            result = await backend.execute("do stuff", "/tmp", "", on_step)

        # Only: thinking + error = 2 steps; reasoning after error is skipped
        assert len(result.steps) == 2
        assert result.steps[0].type == "thinking"
        assert result.steps[1].type == "error"

    @pytest.mark.asyncio
    async def test_kills_process_on_timeout(self, backend, on_step):
        """When process does not terminate in time, terminate() then kill() are called."""
        events = [_cl_say_completion("Done")]
        mock_proc = _make_process(stdout_lines=events, returncode=0)
        mock_proc.terminate = MagicMock()
        mock_proc.kill = MagicMock()

        with patch("asyncio.create_subprocess_exec", new_callable=AsyncMock) as mock_exec, \
             patch.object(backend, "_fetch_task_history", return_value={}), \
             patch("asyncio.wait_for", side_effect=asyncio.TimeoutError):
            mock_exec.return_value = mock_proc
            await backend.execute("do stuff", "/tmp", "", on_step)

        mock_proc.terminate.assert_called_once()
        mock_proc.kill.assert_called_once()

    @pytest.mark.asyncio
    async def test_stores_process_reference(self, backend, on_step):
        """execute() stores the subprocess handle in self._process."""
        with patch("asyncio.create_subprocess_exec", new_callable=AsyncMock) as mock_exec, \
             patch.object(backend, "_fetch_task_history", return_value={}):
            mock_proc = _make_process(returncode=0)
            mock_exec.return_value = mock_proc
            await backend.execute("do stuff", "/tmp", "", on_step)

        assert backend._process is mock_proc


# ===========================================================================
# Tests for abort() — cancel support (C3)
# ===========================================================================


class TestAbort:
    """Tests for ClineBackend.abort()."""

    def test_abort_kills_process_when_running(self, backend):
        """abort() calls kill() on the subprocess when it is still running."""
        mock_proc = MagicMock()
        mock_proc.returncode = None  # Process still running
        backend._process = mock_proc

        backend.abort()

        mock_proc.kill.assert_called_once()

    def test_abort_noop_when_no_process(self, backend):
        """abort() does not crash when no process has been started yet."""
        assert backend._process is None

        backend.abort()  # Should not raise

    def test_abort_noop_when_process_already_done(self, backend):
        """abort() does not kill a process that has already terminated (returncode set)."""
        mock_proc = MagicMock()
        mock_proc.returncode = 0  # Process already finished
        backend._process = mock_proc

        backend.abort()

        mock_proc.kill.assert_not_called()

    def test_abort_noop_when_process_failed(self, backend):
        """abort() does not kill a process that has terminated with an error code."""
        mock_proc = MagicMock()
        mock_proc.returncode = 1  # Process finished with error
        backend._process = mock_proc

        backend.abort()

        mock_proc.kill.assert_not_called()

    @pytest.mark.asyncio
    async def test_abort_after_execute_kills_process(self, backend, on_step):
        """After execute() starts a subprocess, abort() can kill it."""
        mock_proc = _make_process(returncode=0)
        mock_proc.kill = MagicMock()
        mock_proc.returncode = None  # Simulate still running at abort time

        with patch("asyncio.create_subprocess_exec", new_callable=AsyncMock) as mock_exec, \
             patch.object(backend, "_fetch_task_history", return_value={}):
            mock_exec.return_value = mock_proc
            # Start execute but we only care that _process is set
            await backend.execute("do stuff", "/tmp", "", on_step)

        # Simulate the process still running when abort is called
        mock_proc.returncode = None
        backend.abort()

        mock_proc.kill.assert_called_once()
