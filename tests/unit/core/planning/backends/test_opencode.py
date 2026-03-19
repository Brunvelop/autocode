"""
Tests for OpenCodeBackend.

All tests mock subprocess to avoid requiring the opencode CLI.
Tests use the real JSON event format emitted by `opencode run --format json`.
"""

import asyncio
import json
import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from autocode.core.planning.backends.opencode import (
    OpenCodeBackend,
    _epoch_ms_to_iso,
    _extract_tool_path,
    _TOOL_NAME_MAP,
)
from autocode.core.planning.backends.base import ExecutionResult
from autocode.core.planning.models import ExecutionStep


# ---------------------------------------------------------------------------
# Fixtures con formato REAL de OpenCode
# ---------------------------------------------------------------------------

SESSION_ID = "ses_30276fdaeffeQ09eUEJU7zKvdD"
MSG_ID = "msg_cfd890297001JtqE759PsJArGT"


def _oc_step_start(ts=1773780143463, snapshot="abc123"):
    """Evento step_start real de OpenCode."""
    return {
        "type": "step_start",
        "timestamp": ts,
        "sessionID": SESSION_ID,
        "part": {
            "id": "prt_001",
            "sessionID": SESSION_ID,
            "messageID": MSG_ID,
            "type": "step-start",
            "snapshot": snapshot,
        },
    }


def _oc_text(text, ts=1773780143500):
    """Evento text real de OpenCode."""
    return {
        "type": "text",
        "timestamp": ts,
        "sessionID": SESSION_ID,
        "part": {
            "id": "prt_002",
            "sessionID": SESSION_ID,
            "messageID": MSG_ID,
            "type": "text",
            "text": text,
            "time": {"start": ts, "end": ts},
        },
    }


def _oc_tool_use(tool, file_path="", output="", title="", ts=1773780153760):
    """Evento tool_use real de OpenCode."""
    input_data = {}
    if file_path:
        input_data["filePath"] = file_path
    return {
        "type": "tool_use",
        "timestamp": ts,
        "sessionID": SESSION_ID,
        "part": {
            "id": "prt_003",
            "sessionID": SESSION_ID,
            "messageID": MSG_ID,
            "type": "tool",
            "callID": "toolu_018NhYGaGuMwzgCjA68by7B2",
            "tool": tool,
            "state": {
                "status": "completed",
                "input": input_data,
                "output": output,
                "title": title or file_path.rsplit("/", 1)[-1] if file_path else title,
                "metadata": {},
                "time": {"start": ts, "end": ts + 7},
            },
        },
    }


def _oc_step_finish(cost=0.07, total_tokens=11902, ts=1773780143488, reason="stop"):
    """Evento step_finish real de OpenCode."""
    return {
        "type": "step_finish",
        "timestamp": ts,
        "sessionID": SESSION_ID,
        "part": {
            "id": "prt_004",
            "sessionID": SESSION_ID,
            "messageID": MSG_ID,
            "type": "step-finish",
            "reason": reason,
            "snapshot": "abc123",
            "cost": cost,
            "tokens": {
                "total": total_tokens,
                "input": 2,
                "output": 5,
                "reasoning": 0,
                "cache": {"read": 0, "write": total_tokens - 7},
            },
        },
    }


# ---------------------------------------------------------------------------
# Process mock helper
# ---------------------------------------------------------------------------

@pytest.fixture
def backend():
    return OpenCodeBackend()


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


class TestEpochMsToIso:
    """Tests for _epoch_ms_to_iso helper."""

    def test_converts_valid_epoch(self):
        result = _epoch_ms_to_iso(1773780143463)
        assert "2026" in result
        assert "T" in result
        assert "+00:00" in result

    def test_returns_empty_on_zero(self):
        result = _epoch_ms_to_iso(0)
        assert "1970" in result  # epoch 0 is valid, just 1970

    def test_returns_empty_on_invalid(self):
        result = _epoch_ms_to_iso(None)
        assert result == ""

    def test_returns_empty_on_negative_overflow(self):
        # Extremely large value that would cause OSError
        result = _epoch_ms_to_iso(99999999999999999)
        assert result == ""


class TestExtractToolPath:
    """Tests for _extract_tool_path helper."""

    def test_extracts_filePath(self):
        state = {"input": {"filePath": "/tmp/test/README.md"}, "title": "README.md"}
        assert _extract_tool_path(state) == "/tmp/test/README.md"

    def test_fallback_to_pattern(self):
        state = {"input": {"pattern": "*.py"}, "title": "glob"}
        assert _extract_tool_path(state) == "*.py"

    def test_fallback_to_command(self):
        state = {"input": {"command": "ls -la"}, "title": "bash"}
        assert _extract_tool_path(state) == "ls -la"

    def test_fallback_to_title(self):
        state = {"input": {}, "title": "some-title"}
        assert _extract_tool_path(state) == "some-title"

    def test_empty_state(self):
        assert _extract_tool_path({}) == ""

    def test_priority_filePath_over_pattern(self):
        state = {"input": {"filePath": "/a/b.py", "pattern": "*.py"}}
        assert _extract_tool_path(state) == "/a/b.py"


class TestToolNameMap:
    """Tests for the tool name mapping."""

    def test_read_maps_to_read_file(self):
        assert _TOOL_NAME_MAP["read"] == "read_file"

    def test_write_maps_to_write_file(self):
        assert _TOOL_NAME_MAP["write"] == "write_file"

    def test_bash_maps_to_execute_command(self):
        assert _TOOL_NAME_MAP["bash"] == "execute_command"

    def test_edit_maps_to_edit_file(self):
        assert _TOOL_NAME_MAP["edit"] == "edit_file"

    def test_glob_maps_to_list_files(self):
        assert _TOOL_NAME_MAP["glob"] == "list_files"

    def test_grep_maps_to_search_files(self):
        assert _TOOL_NAME_MAP["grep"] == "search_files"


# ===========================================================================
# Unit tests para _parse_event
# ===========================================================================


class TestParseEvent:
    """Tests for OpenCodeBackend._parse_event with real formats."""

    def setup_method(self):
        self.backend = OpenCodeBackend()

    def test_text_event_parsed(self):
        event = _oc_text("HELLO")
        step = self.backend._parse_event(event)
        assert step is not None
        assert step.type == "text"
        assert step.content == "HELLO"
        assert step.timestamp != ""

    def test_tool_use_read_event_parsed(self):
        event = _oc_tool_use(
            tool="read",
            file_path="/tmp/test/README.md",
            output="1: # test\n",
            title="README.md",
        )
        step = self.backend._parse_event(event)
        assert step is not None
        assert step.type == "tool_use"
        assert step.tool == "read_file"
        assert step.path == "/tmp/test/README.md"
        assert "# test" in step.content

    def test_tool_use_write_event_parsed(self):
        event = _oc_tool_use(
            tool="write",
            file_path="/tmp/test/hello.txt",
            output="Wrote file successfully.",
            title="hello.txt",
        )
        step = self.backend._parse_event(event)
        assert step is not None
        assert step.type == "tool_use"
        assert step.tool == "write_file"
        assert step.path == "/tmp/test/hello.txt"
        assert "successfully" in step.content

    def test_tool_use_bash_event_parsed(self):
        event = _oc_tool_use(tool="bash", title="bash")
        event["part"]["state"]["input"] = {"command": "ls -la"}
        event["part"]["state"]["output"] = "total 8\n..."
        step = self.backend._parse_event(event)
        assert step is not None
        assert step.tool == "execute_command"
        assert step.path == "ls -la"

    def test_tool_use_unknown_tool_passes_through(self):
        event = _oc_tool_use(tool="some_new_tool", title="new")
        step = self.backend._parse_event(event)
        assert step is not None
        assert step.tool == "some_new_tool"

    def test_step_start_returns_none(self):
        event = _oc_step_start()
        step = self.backend._parse_event(event)
        assert step is None

    def test_step_finish_returns_none(self):
        event = _oc_step_finish()
        step = self.backend._parse_event(event)
        assert step is None

    def test_unknown_event_type_returns_none(self):
        event = {"type": "unknown_thing", "timestamp": 1234567890000}
        step = self.backend._parse_event(event)
        assert step is None

    def test_timestamp_converted_to_iso(self):
        event = _oc_text("hi", ts=1773780143463)
        step = self.backend._parse_event(event)
        assert "2026" in step.timestamp
        assert "T" in step.timestamp

    def test_tool_use_pending_status_uses_title(self):
        """When tool status is not 'completed', uses title as content."""
        event = _oc_tool_use(tool="read", file_path="/tmp/x.py", title="x.py")
        event["part"]["state"]["status"] = "pending"
        event["part"]["state"]["output"] = ""
        step = self.backend._parse_event(event)
        assert step.content == "x.py"


# ===========================================================================
# Integration tests: full execute() flow
# ===========================================================================


class TestOpenCodeBackend:
    """Integration tests for OpenCodeBackend.execute() with real event format."""

    def test_name(self, backend):
        assert backend.name == "opencode"

    @pytest.mark.asyncio
    async def test_builds_correct_command(self, backend, on_step):
        """Verifies that opencode run --format json is called."""
        with patch("asyncio.create_subprocess_exec", new_callable=AsyncMock) as mock_exec:
            mock_exec.return_value = _make_process(returncode=0)
            await backend.execute("do stuff", "/tmp/cwd", "", on_step)

            args = mock_exec.call_args[0]
            assert args[0] == "opencode"
            assert "run" in args
            assert "--format" in args
            assert "json" in args
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
        """Verifies --dir cwd is passed."""
        with patch("asyncio.create_subprocess_exec", new_callable=AsyncMock) as mock_exec:
            mock_exec.return_value = _make_process(returncode=0)
            await backend.execute("do stuff", "/my/project", "", on_step)

            args = mock_exec.call_args[0]
            assert "--dir" in args
            idx = args.index("--dir")
            assert args[idx + 1] == "/my/project"

    @pytest.mark.asyncio
    async def test_parses_real_json_events_to_steps(self, backend, on_step):
        """Verifies real OpenCode JSON events are parsed to ExecutionStep."""
        events = [
            _oc_step_start(),
            _oc_tool_use(
                tool="read",
                file_path="/tmp/test/README.md",
                output="1: # test\n",
                title="README.md",
            ),
            _oc_step_finish(cost=0.01, total_tokens=11966, reason="tool-calls"),
            _oc_step_start(ts=1773780156396),
            _oc_text("The README.md contains a simple heading.", ts=1773780157273),
            _oc_tool_use(
                tool="write",
                file_path="/tmp/test/hello.txt",
                output="Wrote file successfully.",
                title="hello.txt",
                ts=1773780157635,
            ),
            _oc_step_finish(cost=0.009, total_tokens=12133, reason="tool-calls"),
            _oc_step_start(ts=1773780159486),
            _oc_text("Done. I've read README.md and created hello.txt.", ts=1773780160472),
            _oc_step_finish(cost=0.008, total_tokens=12193, reason="stop"),
        ]
        with patch("asyncio.create_subprocess_exec", new_callable=AsyncMock) as mock_exec:
            mock_exec.return_value = _make_process(stdout_lines=events, returncode=0)
            result = await backend.execute("do stuff", "/tmp", "", on_step)

            # Solo text y tool_use generan steps (no step_start/step_finish)
            # 1x tool_use(read) + 1x text + 1x tool_use(write) + 1x text = 4
            assert len(result.steps) == 4
            assert result.steps[0].type == "tool_use"
            assert result.steps[0].tool == "read_file"
            assert result.steps[0].path == "/tmp/test/README.md"
            assert result.steps[1].type == "text"
            assert "README.md" in result.steps[1].content
            assert result.steps[2].type == "tool_use"
            assert result.steps[2].tool == "write_file"
            assert result.steps[3].type == "text"
            assert "Done" in result.steps[3].content

    @pytest.mark.asyncio
    async def test_calls_on_step_only_for_visible_events(self, backend, on_step):
        """Verifies on_step is NOT called for step_start/step_finish."""
        events = [
            _oc_step_start(),
            _oc_text("Step 1"),
            _oc_tool_use(tool="read", file_path="/tmp/x.py", output="content", title="x.py"),
            _oc_step_finish(cost=0.01, total_tokens=100),
        ]
        with patch("asyncio.create_subprocess_exec", new_callable=AsyncMock) as mock_exec:
            mock_exec.return_value = _make_process(stdout_lines=events, returncode=0)
            await backend.execute("do stuff", "/tmp", "", on_step)

            # Only text + tool_use = 2 calls
            assert on_step.call_count == 2

    @pytest.mark.asyncio
    async def test_accumulates_tokens_from_step_finish(self, backend, on_step):
        """Verifies total_tokens is summed from all step_finish events."""
        events = [
            _oc_step_start(),
            _oc_text("Hello"),
            _oc_step_finish(cost=0.01, total_tokens=1000),
            _oc_step_start(),
            _oc_text("World"),
            _oc_step_finish(cost=0.02, total_tokens=2000),
        ]
        with patch("asyncio.create_subprocess_exec", new_callable=AsyncMock) as mock_exec:
            mock_exec.return_value = _make_process(stdout_lines=events, returncode=0)
            result = await backend.execute("do stuff", "/tmp", "", on_step)

            assert result.total_tokens == 3000
            assert result.total_cost == pytest.approx(0.03, abs=1e-6)

    @pytest.mark.asyncio
    async def test_extracts_session_id(self, backend, on_step):
        """Verifies session_id is extracted from the first event's sessionID."""
        events = [
            _oc_step_start(),
            _oc_text("Hello"),
            _oc_step_finish(),
        ]
        with patch("asyncio.create_subprocess_exec", new_callable=AsyncMock) as mock_exec:
            mock_exec.return_value = _make_process(stdout_lines=events, returncode=0)
            result = await backend.execute("do stuff", "/tmp", "", on_step)

            assert result.session_id == SESSION_ID

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
            _oc_step_start(),
            _oc_text("Done"),
            _oc_step_finish(cost=0.05, total_tokens=500),
        ]
        with patch("asyncio.create_subprocess_exec", new_callable=AsyncMock) as mock_exec:
            mock_exec.return_value = _make_process(stdout_lines=events, returncode=0)
            result = await backend.execute("do stuff", "/tmp", "", on_step)

            assert isinstance(result, ExecutionResult)
            assert result.success is True
            assert result.error == ""
            assert len(result.steps) == 1
            assert result.files_changed == []
            assert result.total_tokens == 500
            assert result.total_cost == pytest.approx(0.05)
            assert result.session_id == SESSION_ID

    @pytest.mark.asyncio
    async def test_handles_subprocess_error(self, backend, on_step):
        """Verifies ExecutionResult(success=False) on subprocess error."""
        with patch("asyncio.create_subprocess_exec", new_callable=AsyncMock) as mock_exec:
            mock_exec.return_value = _make_process(
                stderr=b"opencode: command failed", returncode=1
            )
            result = await backend.execute("do stuff", "/tmp", "", on_step)

            assert result.success is False
            assert "command failed" in result.error

    @pytest.mark.asyncio
    async def test_handles_process_not_found(self, backend, on_step):
        """Verifies graceful handling when opencode is not installed."""
        with patch("asyncio.create_subprocess_exec", new_callable=AsyncMock) as mock_exec:
            mock_exec.side_effect = FileNotFoundError("opencode not found")
            result = await backend.execute("do stuff", "/tmp", "", on_step)

            assert result.success is False
            assert "opencode" in result.error

    @pytest.mark.asyncio
    async def test_handles_invalid_json_lines(self, backend, on_step):
        """Verifies non-JSON lines are silently ignored."""
        mixed_lines = [
            "not json at all",
            _oc_text("valid event"),
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
            assert result.steps[0].type == "text"
            assert result.success is True

    @pytest.mark.asyncio
    async def test_tool_names_are_normalized(self, backend, on_step):
        """Verifies OpenCode tool names are mapped to normalized names."""
        events = [
            _oc_tool_use(tool="read", file_path="/tmp/x.py", output="...", title="x.py"),
            _oc_tool_use(tool="write", file_path="/tmp/y.py", output="ok", title="y.py"),
            _oc_tool_use(tool="bash", title="bash"),
            _oc_tool_use(tool="glob", title="glob"),
            _oc_tool_use(tool="grep", title="grep"),
        ]
        # Set bash command input
        events[2]["part"]["state"]["input"] = {"command": "ls"}
        events[3]["part"]["state"]["input"] = {"pattern": "*.py"}
        events[4]["part"]["state"]["input"] = {"pattern": "TODO"}

        with patch("asyncio.create_subprocess_exec", new_callable=AsyncMock) as mock_exec:
            mock_exec.return_value = _make_process(stdout_lines=events, returncode=0)
            result = await backend.execute("do stuff", "/tmp", "", on_step)

            tools = [s.tool for s in result.steps]
            assert tools == ["read_file", "write_file", "execute_command", "list_files", "search_files"]

    @pytest.mark.asyncio
    async def test_empty_session_produces_empty_result(self, backend, on_step):
        """Verifies an empty stdout produces a valid empty result."""
        with patch("asyncio.create_subprocess_exec", new_callable=AsyncMock) as mock_exec, \
             patch.object(backend, "_fetch_session_export", return_value={}):
            mock_exec.return_value = _make_process(stdout_lines=[], returncode=0)
            result = await backend.execute("do stuff", "/tmp", "", on_step)

            assert result.success is True
            assert result.steps == []
            assert result.total_tokens == 0
            assert result.total_cost == 0.0
            assert result.session_id == ""


# ===========================================================================
# Tests for post-execution metadata extraction via `opencode export`
# ===========================================================================


class TestFetchSessionExport:
    """Tests for OpenCodeBackend._fetch_session_export."""

    @pytest.mark.asyncio
    async def test_calls_opencode_export_with_session_id(self, backend):
        """Verifies `opencode export {session_id}` is called with the correct args."""
        export_data = {"cost": 0.1, "tokens": {"total": 5000}}
        mock_proc = AsyncMock()
        mock_proc.returncode = 0
        mock_proc.communicate = AsyncMock(return_value=(json.dumps(export_data).encode(), b""))

        with patch("asyncio.create_subprocess_exec", new_callable=AsyncMock) as mock_exec:
            mock_exec.return_value = mock_proc
            await backend._fetch_session_export("ses_abc123", "/tmp/cwd")

            args = mock_exec.call_args[0]
            assert args[0] == "opencode"
            assert "export" in args
            assert "ses_abc123" in args

    @pytest.mark.asyncio
    async def test_returns_parsed_json_on_success(self, backend):
        """Verifies parsed JSON dict is returned when export succeeds."""
        export_data = {"cost": 0.1, "tokens": {"total": 5000, "input": 1000, "output": 200}}
        mock_proc = AsyncMock()
        mock_proc.returncode = 0
        mock_proc.communicate = AsyncMock(return_value=(json.dumps(export_data).encode(), b""))

        with patch("asyncio.create_subprocess_exec", new_callable=AsyncMock) as mock_exec:
            mock_exec.return_value = mock_proc
            result = await backend._fetch_session_export("ses_abc123", "/tmp")

            assert result["cost"] == pytest.approx(0.1)
            assert result["tokens"]["total"] == 5000

    @pytest.mark.asyncio
    async def test_returns_empty_dict_on_nonzero_returncode(self, backend):
        """Returns empty dict when opencode export exits with non-zero code."""
        mock_proc = AsyncMock()
        mock_proc.returncode = 1
        mock_proc.communicate = AsyncMock(return_value=(b"", b"session not found"))

        with patch("asyncio.create_subprocess_exec", new_callable=AsyncMock) as mock_exec:
            mock_exec.return_value = mock_proc
            result = await backend._fetch_session_export("ses_abc123", "/tmp")

            assert result == {}

    @pytest.mark.asyncio
    async def test_returns_empty_dict_when_session_id_empty(self, backend):
        """No subprocess is launched when session_id is an empty string."""
        with patch("asyncio.create_subprocess_exec", new_callable=AsyncMock) as mock_exec:
            result = await backend._fetch_session_export("", "/tmp")

            assert result == {}
            mock_exec.assert_not_called()

    @pytest.mark.asyncio
    async def test_returns_empty_dict_on_process_not_found(self, backend):
        """Returns empty dict when the opencode binary is not installed."""
        with patch("asyncio.create_subprocess_exec", new_callable=AsyncMock) as mock_exec:
            mock_exec.side_effect = FileNotFoundError("opencode not found")
            result = await backend._fetch_session_export("ses_abc123", "/tmp")

            assert result == {}

    @pytest.mark.asyncio
    async def test_returns_empty_dict_on_os_error(self, backend):
        """Returns empty dict on any OSError (e.g. permission denied)."""
        with patch("asyncio.create_subprocess_exec", new_callable=AsyncMock) as mock_exec:
            mock_exec.side_effect = OSError("permission denied")
            result = await backend._fetch_session_export("ses_abc123", "/tmp")

            assert result == {}

    @pytest.mark.asyncio
    async def test_returns_empty_dict_on_invalid_json(self, backend):
        """Returns empty dict when the export output is not valid JSON."""
        mock_proc = AsyncMock()
        mock_proc.returncode = 0
        mock_proc.communicate = AsyncMock(return_value=(b"not valid json output", b""))

        with patch("asyncio.create_subprocess_exec", new_callable=AsyncMock) as mock_exec:
            mock_exec.return_value = mock_proc
            result = await backend._fetch_session_export("ses_abc123", "/tmp")

            assert result == {}

    @pytest.mark.asyncio
    async def test_execute_enriches_cost_and_tokens_from_export(self, backend, on_step):
        """execute() uses export data to override streamed accumulation."""
        events = [
            _oc_step_start(),
            _oc_text("Hello"),
            _oc_step_finish(cost=0.01, total_tokens=100),  # streamed: 0.01 / 100
        ]
        export_data = {"cost": 0.05, "tokens": {"total": 500}}  # export: more accurate

        with patch("asyncio.create_subprocess_exec", new_callable=AsyncMock) as mock_exec, \
             patch.object(backend, "_fetch_session_export", return_value=export_data):
            mock_exec.return_value = _make_process(stdout_lines=events, returncode=0)
            result = await backend.execute("do stuff", "/tmp", "", on_step)

            assert result.total_cost == pytest.approx(0.05)
            assert result.total_tokens == 500

    @pytest.mark.asyncio
    async def test_execute_falls_back_to_stream_data_when_export_fails(self, backend, on_step):
        """execute() keeps streamed values when export returns empty dict."""
        events = [
            _oc_step_start(),
            _oc_text("Hello"),
            _oc_step_finish(cost=0.01, total_tokens=100),
        ]

        with patch("asyncio.create_subprocess_exec", new_callable=AsyncMock) as mock_exec, \
             patch.object(backend, "_fetch_session_export", return_value={}):
            mock_exec.return_value = _make_process(stdout_lines=events, returncode=0)
            result = await backend.execute("do stuff", "/tmp", "", on_step)

            assert result.total_cost == pytest.approx(0.01)
            assert result.total_tokens == 100

    @pytest.mark.asyncio
    async def test_execute_export_partial_data_preserves_stream_fallback(self, backend, on_step):
        """If export has no 'tokens' key, streamed token count is preserved."""
        events = [
            _oc_step_start(),
            _oc_text("Hello"),
            _oc_step_finish(cost=0.01, total_tokens=100),
        ]
        export_data = {"cost": 0.05}  # has cost but no tokens key

        with patch("asyncio.create_subprocess_exec", new_callable=AsyncMock) as mock_exec, \
             patch.object(backend, "_fetch_session_export", return_value=export_data):
            mock_exec.return_value = _make_process(stdout_lines=events, returncode=0)
            result = await backend.execute("do stuff", "/tmp", "", on_step)

            # cost overridden by export, tokens kept from stream (no tokens key in export)
            assert result.total_cost == pytest.approx(0.05)
            assert result.total_tokens == 100

    @pytest.mark.asyncio
    async def test_execute_calls_fetch_session_export_with_session_id(self, backend, on_step):
        """execute() passes the extracted session_id to _fetch_session_export."""
        events = [
            _oc_step_start(),
            _oc_step_finish(),
        ]

        with patch("asyncio.create_subprocess_exec", new_callable=AsyncMock) as mock_exec, \
             patch.object(backend, "_fetch_session_export", return_value={}) as mock_export:
            mock_exec.return_value = _make_process(stdout_lines=events, returncode=0)
            await backend.execute("do stuff", "/tmp/proj", "", on_step)

            mock_export.assert_called_once_with(SESSION_ID, "/tmp/proj")


# ===========================================================================
# Tests for process management (Bug 2 fix)
# ===========================================================================


class TestProcessManagement:
    """Tests for process reference storage and timeout handling in OpenCodeBackend."""

    @pytest.mark.asyncio
    async def test_stores_process_reference(self, backend, on_step):
        """execute() stores the subprocess handle in self._process."""
        with patch("asyncio.create_subprocess_exec", new_callable=AsyncMock) as mock_exec, \
             patch.object(backend, "_fetch_session_export", return_value={}):
            mock_proc = _make_process(returncode=0)
            mock_exec.return_value = mock_proc
            await backend.execute("do stuff", "/tmp", "", on_step)

        assert backend._process is mock_proc

    @pytest.mark.asyncio
    async def test_process_timeout_terminates(self, backend, on_step):
        """When process does not terminate in time, terminate() then kill() are called."""
        events = [_oc_text("Done")]
        mock_proc = _make_process(stdout_lines=events, returncode=0)
        mock_proc.terminate = MagicMock()
        mock_proc.kill = MagicMock()

        with patch("asyncio.create_subprocess_exec", new_callable=AsyncMock) as mock_exec, \
             patch.object(backend, "_fetch_session_export", return_value={}), \
             patch("asyncio.wait_for", side_effect=asyncio.TimeoutError):
            mock_exec.return_value = mock_proc
            await backend.execute("do stuff", "/tmp", "", on_step)

        mock_proc.terminate.assert_called_once()
        mock_proc.kill.assert_called_once()


# ===========================================================================
# Tests for abort() — cancel support (C3)
# ===========================================================================


class TestAbort:
    """Tests for OpenCodeBackend.abort()."""

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
             patch.object(backend, "_fetch_session_export", return_value={}):
            mock_exec.return_value = mock_proc
            # Start execute but we only care that _process is set
            await backend.execute("do stuff", "/tmp", "", on_step)

        # Simulate the process still running when abort is called
        mock_proc.returncode = None
        backend.abort()

        mock_proc.kill.assert_called_once()
