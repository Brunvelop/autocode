"""
Tests for SubprocessBackend.

Uses a StubSubprocessBackend concrete implementation to test the shared
logic in SubprocessBackend without requiring any real CLI tool.
"""

import asyncio
import json
import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from autocode.core.planning.backends.subprocess_base import SubprocessBackend
from autocode.core.planning.backends.base import ExecutorBackend, ExecutionResult
from autocode.core.planning.models import ExecutionStep


# ---------------------------------------------------------------------------
# Stub concrete implementation for testing the base class
# ---------------------------------------------------------------------------


class StubSubprocessBackend(SubprocessBackend):
    """Stub concreto para testear la lógica de SubprocessBackend."""

    name = "stub"

    def __init__(self):
        self._parse_results = []   # list of ExecutionStep or None to return in order
        self._final_events = set()  # event types that trigger loop break

    def build_command(self, instruction: str, cwd: str, model: str) -> list:
        cmd = ["echo", "stub"]
        if model:
            cmd.extend(["-m", model])
        cmd.append(instruction)
        return cmd

    def parse_event(self, event: dict):
        # Simulate side-effect accumulation
        if "sessionID" in event:
            self._session_id = event["sessionID"]
        if event.get("tokens"):
            self._tokens += event["tokens"]
        if event.get("cost"):
            self._cost += event["cost"]
        # Return pre-configured results in order
        if self._parse_results:
            return self._parse_results.pop(0)
        return None

    def is_final_event(self, event: dict) -> bool:
        return event.get("type") in self._final_events

    async def fetch_post_metadata(self, session_id: str, cwd: str) -> tuple:
        return (0, 0.0)  # Default: no post-execution metadata


# ---------------------------------------------------------------------------
# Process mock helper
# ---------------------------------------------------------------------------


def _make_process(stdout_lines=None, stderr=b"", returncode=0):
    """Create a mock async subprocess with configurable events."""
    proc = AsyncMock()
    proc.returncode = returncode

    lines = stdout_lines or []
    encoded = []
    for item in lines:
        if isinstance(item, dict):
            encoded.append(json.dumps(item).encode() + b"\n")
        elif isinstance(item, str):
            encoded.append(item.encode() + b"\n")
        else:
            encoded.append(item)

    async def _iter():
        for line in encoded:
            yield line

    proc.stdout = _iter()
    proc.stderr = AsyncMock()
    proc.stderr.read = AsyncMock(return_value=stderr)
    proc.wait = AsyncMock(return_value=returncode)
    return proc


def _make_step(content="step content", step_type="text") -> ExecutionStep:
    return ExecutionStep(timestamp="2026-01-01T00:00:00+00:00", type=step_type, content=content)


# ===========================================================================
# TestSubprocessBackendContract — ABCness and structure
# ===========================================================================


class TestSubprocessBackendContract:
    """Tests that SubprocessBackend is a proper ABC."""

    def test_is_abstract_cannot_instantiate(self):
        """SubprocessBackend cannot be instantiated directly (abstract methods)."""
        with pytest.raises(TypeError):
            SubprocessBackend()

    def test_inherits_from_executor_backend(self):
        """SubprocessBackend is a subclass of ExecutorBackend."""
        assert issubclass(SubprocessBackend, ExecutorBackend)

    def test_has_required_abstract_methods(self):
        """build_command, parse_event, fetch_post_metadata are abstract."""
        abstract = SubprocessBackend.__abstractmethods__
        assert "build_command" in abstract
        assert "parse_event" in abstract
        assert "fetch_post_metadata" in abstract

    def test_stub_is_instantiable(self):
        """A concrete subclass with all methods implemented can be instantiated."""
        backend = StubSubprocessBackend()
        assert backend is not None

    def test_stub_is_instance_of_executor_backend(self):
        """Concrete subclass is an instance of ExecutorBackend."""
        assert isinstance(StubSubprocessBackend(), ExecutorBackend)

    def test_stub_is_instance_of_subprocess_backend(self):
        """Concrete subclass is an instance of SubprocessBackend."""
        assert isinstance(StubSubprocessBackend(), SubprocessBackend)

    def test_is_final_event_default_returns_false(self):
        """Default is_final_event() returns False (reads until EOF)."""
        backend = StubSubprocessBackend()
        assert backend.is_final_event({}) is False
        assert backend.is_final_event({"type": "anything"}) is False

    def test_abort_default_is_noop_when_no_process(self):
        """Default abort() (from ExecutorBackend) is a no-op when no process."""
        backend = StubSubprocessBackend()
        backend.abort()  # Should not raise


# ===========================================================================
# TestSubprocessBackendSpawn — subprocess creation
# ===========================================================================


class TestSubprocessBackendSpawn:
    """Tests for subprocess spawning logic in execute()."""

    @pytest.mark.asyncio
    async def test_returns_error_on_file_not_found(self):
        """Returns ExecutionResult(success=False) when binary is not found."""
        backend = StubSubprocessBackend()
        with patch("asyncio.create_subprocess_exec", new_callable=AsyncMock) as mock_exec:
            mock_exec.side_effect = FileNotFoundError("echo: not found")
            result = await backend.execute("test", "/tmp", "", AsyncMock())

        assert result.success is False
        assert result.error != ""

    @pytest.mark.asyncio
    async def test_returns_error_on_os_error(self):
        """Returns ExecutionResult(success=False) on OSError (e.g. permission denied)."""
        backend = StubSubprocessBackend()
        with patch("asyncio.create_subprocess_exec", new_callable=AsyncMock) as mock_exec:
            mock_exec.side_effect = OSError("permission denied")
            result = await backend.execute("test", "/tmp", "", AsyncMock())

        assert result.success is False
        assert result.error != ""

    @pytest.mark.asyncio
    async def test_spawns_with_build_command_args(self):
        """execute() passes the args returned by build_command to create_subprocess_exec."""
        backend = StubSubprocessBackend()
        with patch("asyncio.create_subprocess_exec", new_callable=AsyncMock) as mock_exec:
            mock_exec.return_value = _make_process(returncode=0)
            await backend.execute("my instruction", "/tmp", "gpt-4", AsyncMock())

            args = mock_exec.call_args[0]
            # StubSubprocessBackend.build_command returns ["echo", "stub", "-m", model, instruction]
            assert "echo" in args
            assert "stub" in args
            assert "-m" in args
            idx = list(args).index("-m")
            assert args[idx + 1] == "gpt-4"
            assert "my instruction" in args

    @pytest.mark.asyncio
    async def test_passes_cwd_to_subprocess(self):
        """execute() passes cwd= to create_subprocess_exec."""
        backend = StubSubprocessBackend()
        with patch("asyncio.create_subprocess_exec", new_callable=AsyncMock) as mock_exec:
            mock_exec.return_value = _make_process(returncode=0)
            await backend.execute("test", "/my/project", "", AsyncMock())

            kwargs = mock_exec.call_args[1]
            assert kwargs["cwd"] == "/my/project"

    @pytest.mark.asyncio
    async def test_error_includes_command_name(self):
        """Error message includes the command name (cmd[0])."""
        backend = StubSubprocessBackend()
        with patch("asyncio.create_subprocess_exec", new_callable=AsyncMock) as mock_exec:
            mock_exec.side_effect = FileNotFoundError("not found")
            result = await backend.execute("test", "/tmp", "", AsyncMock())

        # build_command returns ["echo", ...], so cmd[0] == "echo"
        assert "echo" in result.error


# ===========================================================================
# TestSubprocessBackendNdjsonLoop — NDJSON parsing loop
# ===========================================================================


class TestSubprocessBackendNdjsonLoop:
    """Tests for the NDJSON reading and parsing loop in execute()."""

    @pytest.mark.asyncio
    async def test_skips_empty_lines(self):
        """Empty lines in stdout are silently skipped (parse_event not called)."""
        backend = StubSubprocessBackend()
        with patch("asyncio.create_subprocess_exec", new_callable=AsyncMock) as mock_exec, \
             patch.object(backend, "parse_event", wraps=backend.parse_event) as mock_parse:
            mock_exec.return_value = _make_process(
                stdout_lines=["", "   ", "\t", ""],
                returncode=0,
            )
            await backend.execute("test", "/tmp", "", AsyncMock())

        mock_parse.assert_not_called()

    @pytest.mark.asyncio
    async def test_skips_invalid_json(self):
        """Non-JSON lines are silently skipped (parse_event not called)."""
        backend = StubSubprocessBackend()
        with patch("asyncio.create_subprocess_exec", new_callable=AsyncMock) as mock_exec, \
             patch.object(backend, "parse_event", wraps=backend.parse_event) as mock_parse:
            mock_exec.return_value = _make_process(
                stdout_lines=["not json", "also not json", "{broken"],
                returncode=0,
            )
            await backend.execute("test", "/tmp", "", AsyncMock())

        mock_parse.assert_not_called()

    @pytest.mark.asyncio
    async def test_calls_parse_event_for_each_valid_json(self):
        """parse_event is called once per valid JSON line."""
        backend = StubSubprocessBackend()
        events = [
            {"type": "a"},
            {"type": "b"},
            {"type": "c"},
        ]
        with patch("asyncio.create_subprocess_exec", new_callable=AsyncMock) as mock_exec, \
             patch.object(backend, "parse_event", wraps=backend.parse_event) as mock_parse:
            mock_exec.return_value = _make_process(stdout_lines=events, returncode=0)
            await backend.execute("test", "/tmp", "", AsyncMock())

        assert mock_parse.call_count == 3

    @pytest.mark.asyncio
    async def test_mixed_valid_and_invalid_lines(self):
        """Valid JSON events are parsed; invalid/empty lines are skipped."""
        backend = StubSubprocessBackend()
        backend._parse_results = [_make_step("ok")]
        lines = [
            "not json",
            {"type": "valid"},  # → step returned from _parse_results
            "",
            "also broken",
        ]
        on_step = AsyncMock()
        with patch("asyncio.create_subprocess_exec", new_callable=AsyncMock) as mock_exec:
            mock_exec.return_value = _make_process(stdout_lines=lines, returncode=0)
            result = await backend.execute("test", "/tmp", "", on_step)

        assert len(result.steps) == 1
        assert on_step.call_count == 1

    @pytest.mark.asyncio
    async def test_breaks_on_is_final_event(self):
        """Loop stops after is_final_event() returns True; later events are not parsed."""
        backend = StubSubprocessBackend()
        backend._final_events = {"final"}
        # 3 events: normal, final, after_final
        events = [
            {"type": "normal"},
            {"type": "final"},
            {"type": "after_final"},
        ]
        with patch("asyncio.create_subprocess_exec", new_callable=AsyncMock) as mock_exec, \
             patch.object(backend, "parse_event", wraps=backend.parse_event) as mock_parse:
            mock_exec.return_value = _make_process(stdout_lines=events, returncode=0)
            await backend.execute("test", "/tmp", "", AsyncMock())

        # parse_event called for "normal" and "final" but NOT for "after_final"
        assert mock_parse.call_count == 2

    @pytest.mark.asyncio
    async def test_reads_until_eof_by_default(self):
        """Without is_final_event override, all lines are consumed."""
        backend = StubSubprocessBackend()
        events = [{"type": f"event_{i}"} for i in range(5)]
        with patch("asyncio.create_subprocess_exec", new_callable=AsyncMock) as mock_exec, \
             patch.object(backend, "parse_event", wraps=backend.parse_event) as mock_parse:
            mock_exec.return_value = _make_process(stdout_lines=events, returncode=0)
            await backend.execute("test", "/tmp", "", AsyncMock())

        assert mock_parse.call_count == 5

    @pytest.mark.asyncio
    async def test_on_step_called_for_non_none_steps(self):
        """on_step is called only when parse_event returns a non-None ExecutionStep."""
        backend = StubSubprocessBackend()
        # 3 events; parse_event returns: step, None, step
        backend._parse_results = [_make_step("first"), None, _make_step("third")]
        events = [{"type": "a"}, {"type": "b"}, {"type": "c"}]
        on_step = AsyncMock()
        with patch("asyncio.create_subprocess_exec", new_callable=AsyncMock) as mock_exec:
            mock_exec.return_value = _make_process(stdout_lines=events, returncode=0)
            result = await backend.execute("test", "/tmp", "", on_step)

        assert on_step.call_count == 2
        assert len(result.steps) == 2

    @pytest.mark.asyncio
    async def test_final_event_step_emitted_before_break(self):
        """parse_event result for a final event IS emitted to on_step before breaking."""
        backend = StubSubprocessBackend()
        backend._final_events = {"final"}
        # parse_event will return a step for the final event
        backend._parse_results = [_make_step("final step")]
        events = [{"type": "final"}]
        on_step = AsyncMock()
        with patch("asyncio.create_subprocess_exec", new_callable=AsyncMock) as mock_exec:
            mock_exec.return_value = _make_process(stdout_lines=events, returncode=0)
            result = await backend.execute("test", "/tmp", "", on_step)

        # Step is emitted THEN break happens
        assert on_step.call_count == 1
        assert len(result.steps) == 1
        assert result.steps[0].content == "final step"


# ===========================================================================
# TestSubprocessBackendProcessManagement — process reference and timeout
# ===========================================================================


class TestSubprocessBackendProcessManagement:
    """Tests for process reference storage, abort, and timeout handling."""

    @pytest.mark.asyncio
    async def test_stores_process_reference(self):
        """execute() stores the spawned subprocess in self._process."""
        backend = StubSubprocessBackend()
        with patch("asyncio.create_subprocess_exec", new_callable=AsyncMock) as mock_exec:
            mock_proc = _make_process(returncode=0)
            mock_exec.return_value = mock_proc
            await backend.execute("test", "/tmp", "", AsyncMock())

        assert backend._process is mock_proc

    def test_abort_kills_running_process(self):
        """abort() calls kill() when the process is still running."""
        backend = StubSubprocessBackend()
        mock_proc = MagicMock()
        mock_proc.returncode = None  # still running
        backend._process = mock_proc

        backend.abort()

        mock_proc.kill.assert_called_once()

    def test_abort_noop_when_no_process(self):
        """abort() is a no-op when no process has been started."""
        backend = StubSubprocessBackend()
        assert backend._process is None
        backend.abort()  # must not raise

    def test_abort_noop_when_done(self):
        """abort() does NOT kill a process that has already terminated."""
        backend = StubSubprocessBackend()
        mock_proc = MagicMock()
        mock_proc.returncode = 0  # already finished
        backend._process = mock_proc

        backend.abort()

        mock_proc.kill.assert_not_called()

    def test_abort_noop_when_process_failed(self):
        """abort() does NOT kill a process that terminated with an error code."""
        backend = StubSubprocessBackend()
        mock_proc = MagicMock()
        mock_proc.returncode = 1  # finished with error
        backend._process = mock_proc

        backend.abort()

        mock_proc.kill.assert_not_called()

    @pytest.mark.asyncio
    async def test_timeout_terminates_then_kills(self):
        """When process does not terminate in time, terminate() then kill() are called."""
        backend = StubSubprocessBackend()
        mock_proc = _make_process(stdout_lines=[], returncode=0)
        mock_proc.terminate = MagicMock()
        mock_proc.kill = MagicMock()

        with patch("asyncio.create_subprocess_exec", new_callable=AsyncMock) as mock_exec, \
             patch("asyncio.wait_for", side_effect=asyncio.TimeoutError):
            mock_exec.return_value = mock_proc
            await backend.execute("test", "/tmp", "", AsyncMock())

        mock_proc.terminate.assert_called_once()
        mock_proc.kill.assert_called_once()

    @pytest.mark.asyncio
    async def test_abort_after_execute_kills_process(self):
        """After execute() stores _process, abort() can kill it."""
        backend = StubSubprocessBackend()
        mock_proc = _make_process(returncode=0)
        mock_proc.kill = MagicMock()

        with patch("asyncio.create_subprocess_exec", new_callable=AsyncMock) as mock_exec:
            mock_exec.return_value = mock_proc
            await backend.execute("test", "/tmp", "", AsyncMock())

        # Simulate process still running when abort is called
        mock_proc.returncode = None
        backend.abort()

        mock_proc.kill.assert_called_once()

    @pytest.mark.asyncio
    async def test_resets_state_on_each_execute(self):
        """State (_session_id, _tokens, _cost) is reset at the start of each execute()."""
        backend = StubSubprocessBackend()

        # First execute: accumulate some state via parse_event side-effects
        first_events = [{"type": "a", "sessionID": "ses_first", "tokens": 100, "cost": 0.1}]
        with patch("asyncio.create_subprocess_exec", new_callable=AsyncMock) as mock_exec:
            mock_exec.return_value = _make_process(stdout_lines=first_events, returncode=0)
            await backend.execute("test", "/tmp", "", AsyncMock())

        assert backend._session_id == "ses_first"
        assert backend._tokens == 100

        # Second execute: state should be reset, then accumulate new values
        second_events = [{"type": "b", "sessionID": "ses_second", "tokens": 50, "cost": 0.05}]
        with patch("asyncio.create_subprocess_exec", new_callable=AsyncMock) as mock_exec:
            mock_exec.return_value = _make_process(stdout_lines=second_events, returncode=0)
            result = await backend.execute("test", "/tmp", "", AsyncMock())

        assert backend._session_id == "ses_second"
        assert backend._tokens == 50
        assert result.session_id == "ses_second"


# ===========================================================================
# TestSubprocessBackendMetadata — token/cost consolidation
# ===========================================================================


class TestSubprocessBackendMetadata:
    """Tests for the metadata consolidation logic (stream vs post-execution)."""

    @pytest.mark.asyncio
    async def test_uses_stream_accumulated_when_metadata_empty(self):
        """When fetch_post_metadata returns (0, 0.0), stream values are used."""
        backend = StubSubprocessBackend()
        # parse_event accumulates 200 tokens / 0.02 cost via side-effects
        events = [
            {"type": "a", "tokens": 100, "cost": 0.01},
            {"type": "b", "tokens": 100, "cost": 0.01},
        ]
        # Default stub fetch_post_metadata returns (0, 0.0)
        with patch("asyncio.create_subprocess_exec", new_callable=AsyncMock) as mock_exec:
            mock_exec.return_value = _make_process(stdout_lines=events, returncode=0)
            result = await backend.execute("test", "/tmp", "", AsyncMock())

        assert result.total_tokens == 200
        assert result.total_cost == pytest.approx(0.02)

    @pytest.mark.asyncio
    async def test_uses_metadata_when_available(self):
        """When fetch_post_metadata returns non-zero values, they override stream data."""
        backend = StubSubprocessBackend()
        events = [{"type": "a", "tokens": 100, "cost": 0.01}]

        with patch("asyncio.create_subprocess_exec", new_callable=AsyncMock) as mock_exec, \
             patch.object(backend, "fetch_post_metadata", return_value=(5000, 0.50)):
            mock_exec.return_value = _make_process(stdout_lines=events, returncode=0)
            result = await backend.execute("test", "/tmp", "", AsyncMock())

        assert result.total_tokens == 5000
        assert result.total_cost == pytest.approx(0.50)

    @pytest.mark.asyncio
    async def test_calls_fetch_post_metadata_with_session_id(self):
        """execute() passes the accumulated session_id to fetch_post_metadata."""
        backend = StubSubprocessBackend()
        events = [{"type": "a", "sessionID": "ses_xyz"}]

        with patch("asyncio.create_subprocess_exec", new_callable=AsyncMock) as mock_exec, \
             patch.object(
                 backend, "fetch_post_metadata", new_callable=AsyncMock, return_value=(0, 0.0)
             ) as mock_meta:
            mock_exec.return_value = _make_process(stdout_lines=events, returncode=0)
            await backend.execute("test", "/my/cwd", "", AsyncMock())

        mock_meta.assert_called_once_with("ses_xyz", "/my/cwd")

    @pytest.mark.asyncio
    async def test_partial_metadata_tokens_zero_uses_stream_tokens(self):
        """If meta_tokens == 0 but meta_cost > 0, stream tokens are preserved."""
        backend = StubSubprocessBackend()
        events = [{"type": "a", "tokens": 300, "cost": 0.03}]

        with patch("asyncio.create_subprocess_exec", new_callable=AsyncMock) as mock_exec, \
             patch.object(backend, "fetch_post_metadata", return_value=(0, 0.99)):
            mock_exec.return_value = _make_process(stdout_lines=events, returncode=0)
            result = await backend.execute("test", "/tmp", "", AsyncMock())

        # meta_tokens=0 → falsy → use stream; meta_cost=0.99 → truthy → use meta
        assert result.total_tokens == 300
        assert result.total_cost == pytest.approx(0.99)

    @pytest.mark.asyncio
    async def test_partial_metadata_cost_zero_uses_stream_cost(self):
        """If meta_cost == 0.0 but meta_tokens > 0, stream cost is preserved."""
        backend = StubSubprocessBackend()
        events = [{"type": "a", "tokens": 300, "cost": 0.03}]

        with patch("asyncio.create_subprocess_exec", new_callable=AsyncMock) as mock_exec, \
             patch.object(backend, "fetch_post_metadata", return_value=(9999, 0.0)):
            mock_exec.return_value = _make_process(stdout_lines=events, returncode=0)
            result = await backend.execute("test", "/tmp", "", AsyncMock())

        # meta_tokens=9999 → truthy → use meta; meta_cost=0.0 → falsy → use stream
        assert result.total_tokens == 9999
        assert result.total_cost == pytest.approx(0.03)

    @pytest.mark.asyncio
    async def test_session_id_in_result(self):
        """result.session_id matches the session_id accumulated by parse_event."""
        backend = StubSubprocessBackend()
        events = [{"type": "a", "sessionID": "ses_abc"}]

        with patch("asyncio.create_subprocess_exec", new_callable=AsyncMock) as mock_exec:
            mock_exec.return_value = _make_process(stdout_lines=events, returncode=0)
            result = await backend.execute("test", "/tmp", "", AsyncMock())

        assert result.session_id == "ses_abc"

    @pytest.mark.asyncio
    async def test_success_true_on_zero_returncode(self):
        """ExecutionResult.success is True when process exits with code 0."""
        backend = StubSubprocessBackend()
        with patch("asyncio.create_subprocess_exec", new_callable=AsyncMock) as mock_exec:
            mock_exec.return_value = _make_process(returncode=0)
            result = await backend.execute("test", "/tmp", "", AsyncMock())

        assert result.success is True
        assert result.error == ""

    @pytest.mark.asyncio
    async def test_success_false_on_nonzero_returncode(self):
        """ExecutionResult.success is False when process exits with non-zero code."""
        backend = StubSubprocessBackend()
        with patch("asyncio.create_subprocess_exec", new_callable=AsyncMock) as mock_exec:
            mock_exec.return_value = _make_process(
                stderr=b"something went wrong", returncode=1
            )
            result = await backend.execute("test", "/tmp", "", AsyncMock())

        assert result.success is False
        assert "something went wrong" in result.error

    @pytest.mark.asyncio
    async def test_files_changed_is_always_empty(self):
        """SubprocessBackend never populates files_changed (that's the executor's job)."""
        backend = StubSubprocessBackend()
        with patch("asyncio.create_subprocess_exec", new_callable=AsyncMock) as mock_exec:
            mock_exec.return_value = _make_process(returncode=0)
            result = await backend.execute("test", "/tmp", "", AsyncMock())

        assert result.files_changed == []


# ===========================================================================
# TestEpochMsToIso — static helper
# ===========================================================================


class TestEpochMsToIso:
    """Tests for SubprocessBackend._epoch_ms_to_iso static helper."""

    def test_valid_epoch(self):
        """Converts a valid epoch_ms to an ISO 8601 string with year and timezone."""
        result = SubprocessBackend._epoch_ms_to_iso(1773780143463)
        assert "2026" in result
        assert "T" in result
        assert "+00:00" in result

    def test_invalid_returns_empty(self):
        """Returns empty string for None (TypeError)."""
        result = SubprocessBackend._epoch_ms_to_iso(None)
        assert result == ""

    def test_zero_epoch(self):
        """Epoch 0 ms is a valid date (1970-01-01T00:00:00+00:00)."""
        result = SubprocessBackend._epoch_ms_to_iso(0)
        assert "1970" in result
        assert "T" in result

    def test_very_large_value_returns_empty(self):
        """Extremely large epoch_ms that causes OSError returns empty string."""
        result = SubprocessBackend._epoch_ms_to_iso(99999999999999999)
        assert result == ""

    def test_callable_on_instance(self):
        """_epoch_ms_to_iso can be called via self on an instance."""
        backend = StubSubprocessBackend()
        result = backend._epoch_ms_to_iso(1773780143463)
        assert "2026" in result
