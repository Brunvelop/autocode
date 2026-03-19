"""
Tests for DspyReactBackend.

Tests cover:
- extract_files_changed: trajectory parsing for modified files (migrated from test_executor_helpers)
- extract_cost_from_history: LM history cost extraction (migrated from test_executor_helpers)
- DspyReactBackend.execute: full execution flow with mocked DSPy components

All DSPy/LM interactions are mocked — no real API calls.
"""

import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from autocode.core.planning.backends.dspy_react import (
    DspyReactBackend,
    extract_files_changed,
    extract_cost_from_history,
    WRITE_TOOLS,
    EXECUTOR_TOOLS,
)
from autocode.core.planning.backends.base import ExecutionResult
from autocode.core.planning.models import ExecutionStep


# ============================================================================
# FIXTURES
# ============================================================================


@pytest.fixture
def backend():
    return DspyReactBackend()


@pytest.fixture
def on_step():
    return AsyncMock()


# ============================================================================
# TEST: extract_files_changed (migrated from test_executor_helpers)
# ============================================================================


class TestExtractFilesChanged:
    """Extract file paths from DSPy ReAct trajectory."""

    def test_extracts_write_file_paths(self):
        """Extracts paths from write_file_content actions."""
        trajectory = {
            "Action_0": "read_file_content",
            "Action_0_args": {"path": "src/api.py"},
            "Action_1": "write_file_content",
            "Action_1_args": {"path": "src/api.py", "content": "..."},
        }
        files = extract_files_changed(trajectory)
        assert files == ["src/api.py"]

    def test_extracts_replace_in_file_paths(self):
        """Extracts paths from replace_in_file actions."""
        trajectory = {
            "Action_0": "replace_in_file",
            "Action_0_args": {"path": "src/models.py", "old": "x", "new": "y"},
        }
        files = extract_files_changed(trajectory)
        assert files == ["src/models.py"]

    def test_extracts_delete_file_paths(self):
        """Extracts paths from delete_file actions."""
        trajectory = {
            "Action_0": "delete_file",
            "Action_0_args": {"path": "old_file.py"},
        }
        files = extract_files_changed(trajectory)
        assert files == ["old_file.py"]

    def test_ignores_read_only_actions(self):
        """Read actions do not count as files changed."""
        trajectory = {
            "Action_0": "read_file_content",
            "Action_0_args": {"path": "src/api.py"},
            "Action_1": "get_code_summary",
            "Action_1_args": {"path": "src/"},
        }
        files = extract_files_changed(trajectory)
        assert files == []

    def test_deduplicates_paths(self):
        """Same file written multiple times appears once."""
        trajectory = {
            "Action_0": "write_file_content",
            "Action_0_args": {"path": "src/api.py", "content": "v1"},
            "Action_1": "write_file_content",
            "Action_1_args": {"path": "src/api.py", "content": "v2"},
        }
        files = extract_files_changed(trajectory)
        assert files == ["src/api.py"]

    def test_multiple_files_changed(self):
        """Multiple different files are all returned."""
        trajectory = {
            "Action_0": "write_file_content",
            "Action_0_args": {"path": "a.py", "content": "..."},
            "Action_1": "replace_in_file",
            "Action_1_args": {"path": "b.py", "old": "x", "new": "y"},
            "Action_2": "delete_file",
            "Action_2_args": {"path": "c.py"},
        }
        files = extract_files_changed(trajectory)
        assert files == ["a.py", "b.py", "c.py"]

    def test_empty_trajectory_returns_empty(self):
        """Empty dict returns empty list."""
        assert extract_files_changed({}) == []

    def test_none_trajectory_returns_empty(self):
        """None returns empty list."""
        assert extract_files_changed(None) == []

    def test_non_dict_trajectory_returns_empty(self):
        """Non-dict (e.g. list) returns empty list."""
        assert extract_files_changed([1, 2, 3]) == []

    def test_args_without_path_are_skipped(self):
        """Write action args without 'path' key are ignored."""
        trajectory = {
            "Action_0": "write_file_content",
            "Action_0_args": {"content": "..."},  # no path key
        }
        files = extract_files_changed(trajectory)
        assert files == []

    def test_args_not_dict_are_skipped(self):
        """Non-dict args values are ignored."""
        trajectory = {
            "Action_0": "write_file_content",
            "Action_0_args": "not a dict",
        }
        files = extract_files_changed(trajectory)
        assert files == []


# ============================================================================
# TEST: extract_cost_from_history (migrated from test_executor_helpers)
# ============================================================================


class TestExtractCostFromHistory:
    """Extract token counts and cost from LM call history."""

    def test_extracts_usage_from_standard_format(self):
        """Standard DSPy/LiteLLM usage dict format."""
        lm = SimpleNamespace(history=[
            {
                "usage": {
                    "prompt_tokens": 100,
                    "completion_tokens": 50,
                },
                "cost": 0.002,
            }
        ])
        result = extract_cost_from_history(lm)
        assert result["prompt_tokens"] == 100
        assert result["completion_tokens"] == 50
        assert result["total_tokens"] == 150
        assert result["total_cost"] == 0.002

    def test_extracts_usage_from_input_output_format(self):
        """Alternative format with input_tokens/output_tokens."""
        lm = SimpleNamespace(history=[
            {
                "usage": {
                    "input_tokens": 200,
                    "output_tokens": 100,
                },
                "cost": 0.005,
            }
        ])
        result = extract_cost_from_history(lm)
        assert result["prompt_tokens"] == 200
        assert result["completion_tokens"] == 100
        assert result["total_tokens"] == 300
        assert result["total_cost"] == 0.005

    def test_sums_across_multiple_calls(self):
        """Multiple calls in history are summed."""
        lm = SimpleNamespace(history=[
            {"usage": {"prompt_tokens": 100, "completion_tokens": 50}, "cost": 0.001},
            {"usage": {"prompt_tokens": 200, "completion_tokens": 100}, "cost": 0.003},
        ])
        result = extract_cost_from_history(lm)
        assert result["prompt_tokens"] == 300
        assert result["completion_tokens"] == 150
        assert result["total_tokens"] == 450
        assert result["total_cost"] == 0.004

    def test_extracts_cost_from_response_cost(self):
        """Fallback: response_cost key."""
        lm = SimpleNamespace(history=[
            {"usage": {}, "response_cost": 0.01}
        ])
        result = extract_cost_from_history(lm)
        assert result["total_cost"] == 0.01

    def test_extracts_cost_from_hidden_params(self):
        """Fallback: _hidden_params.response_cost."""
        lm = SimpleNamespace(history=[
            {"usage": {}, "_hidden_params": {"response_cost": 0.007}}
        ])
        result = extract_cost_from_history(lm)
        assert result["total_cost"] == 0.007

    def test_extracts_cost_from_response_hidden_params(self):
        """Fallback: response._hidden_params.response_cost."""
        lm = SimpleNamespace(history=[
            {
                "usage": {},
                "response": {"_hidden_params": {"response_cost": 0.015}},
            }
        ])
        result = extract_cost_from_history(lm)
        assert result["total_cost"] == 0.015

    def test_no_history_returns_zeros(self):
        """LM with no history returns all zeros."""
        lm = SimpleNamespace(history=[])
        result = extract_cost_from_history(lm)
        assert result == {
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "total_tokens": 0,
            "total_cost": 0.0,
        }

    def test_no_history_attr_returns_zeros(self):
        """LM without history attribute returns all zeros."""
        lm = SimpleNamespace()
        result = extract_cost_from_history(lm)
        assert result == {
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "total_tokens": 0,
            "total_cost": 0.0,
        }

    def test_non_dict_entries_are_skipped(self):
        """Non-dict entries in history are ignored."""
        lm = SimpleNamespace(history=[
            "not a dict",
            {"usage": {"prompt_tokens": 50, "completion_tokens": 25}, "cost": 0.001},
        ])
        result = extract_cost_from_history(lm)
        assert result["prompt_tokens"] == 50
        assert result["completion_tokens"] == 25
        assert result["total_tokens"] == 75
        assert result["total_cost"] == 0.001

    def test_none_cost_is_treated_as_zero(self):
        """None cost values are treated as 0."""
        lm = SimpleNamespace(history=[
            {"usage": {"prompt_tokens": 10, "completion_tokens": 5}, "cost": None}
        ])
        result = extract_cost_from_history(lm)
        assert result["total_tokens"] == 15
        assert result["total_cost"] == 0.0


# ============================================================================
# TEST: DspyReactBackend
# ============================================================================


class TestDspyReactBackendName:
    """Backend name is 'dspy'."""

    def test_name(self, backend):
        assert backend.name == "dspy"


class TestDspyReactBackendConstants:
    """Verify constants are correctly defined."""

    def test_write_tools_contains_expected(self):
        assert "write_file_content" in WRITE_TOOLS
        assert "replace_in_file" in WRITE_TOOLS
        assert "delete_file" in WRITE_TOOLS

    def test_executor_tools_contains_expected(self):
        assert "read_file_content" in EXECUTOR_TOOLS
        assert "write_file_content" in EXECUTOR_TOOLS
        assert "get_code_summary" in EXECUTOR_TOOLS


class TestDspyReactBackendExecute:
    """Tests for DspyReactBackend.execute with mocked DSPy."""

    def _make_status_message(self, message):
        """Create a mock StatusMessage."""
        msg = MagicMock()
        msg.message = message
        # Make isinstance check work
        msg.__class__ = type("StatusMessage", (), {})
        return msg

    def _make_prediction(self, summary="All done", trajectory=None):
        """Create a mock Prediction."""
        pred = MagicMock()
        pred.completion_summary = summary
        pred.trajectory = trajectory or {}
        return pred

    @pytest.mark.asyncio
    async def test_returns_execution_result_on_success(self, backend, on_step):
        """Successful execution returns ExecutionResult(success=True)."""
        mock_prediction = self._make_prediction(
            summary="Created validation module",
            trajectory={
                "Action_0": "write_file_content",
                "Action_0_args": {"path": "src/api.py", "content": "..."},
            },
        )

        # Mock the async stream to yield a prediction
        async def mock_stream(*args, **kwargs):
            yield mock_prediction

        mock_lm = MagicMock()
        mock_lm.history = [
            {"usage": {"prompt_tokens": 500, "completion_tokens": 200}, "cost": 0.003}
        ]

        with (
            patch("autocode.core.planning.backends.dspy_react.get_dspy_lm", return_value=mock_lm),
            patch("autocode.core.planning.backends.dspy_react.prepare_chat_tools", return_value=[]),
            patch("autocode.core.planning.backends.dspy_react.dspy") as mock_dspy,
        ):
            # Configure dspy mocks
            mock_dspy.ReAct.return_value = MagicMock()
            mock_dspy.streaming.StreamListener = MagicMock
            mock_dspy.streamify.return_value = mock_stream
            mock_dspy.context.return_value.__enter__ = MagicMock()
            mock_dspy.context.return_value.__exit__ = MagicMock()
            mock_dspy.Prediction = type(mock_prediction)
            # StatusMessage isinstance check
            mock_dspy.streaming.StatusMessage = type("FakeStatusMessage", (), {})

            result = await backend.execute("do stuff", "/tmp", "openrouter/openai/gpt-4o", on_step)

        assert isinstance(result, ExecutionResult)
        assert result.success is True
        assert result.files_changed == []
        assert result.total_tokens == 700
        assert result.total_cost == 0.003

    @pytest.mark.asyncio
    async def test_returns_failure_when_no_prediction(self, backend, on_step):
        """No prediction from DSPy returns ExecutionResult(success=False)."""
        # Stream yields nothing (no prediction)
        async def mock_stream(*args, **kwargs):
            return
            yield  # make it an async generator

        mock_lm = MagicMock()
        mock_lm.history = []

        with (
            patch("autocode.core.planning.backends.dspy_react.get_dspy_lm", return_value=mock_lm),
            patch("autocode.core.planning.backends.dspy_react.prepare_chat_tools", return_value=[]),
            patch("autocode.core.planning.backends.dspy_react.dspy") as mock_dspy,
        ):
            mock_dspy.ReAct.return_value = MagicMock()
            mock_dspy.streaming.StreamListener = MagicMock
            mock_dspy.streamify.return_value = mock_stream
            mock_dspy.context.return_value.__enter__ = MagicMock()
            mock_dspy.context.return_value.__exit__ = MagicMock()
            mock_dspy.Prediction = type("FakePrediction", (), {})
            mock_dspy.streaming.StatusMessage = type("FakeStatusMessage", (), {})

            result = await backend.execute("do stuff", "/tmp", "", on_step)

        assert result.success is False
        assert "No prediction" in result.error

    @pytest.mark.asyncio
    async def test_calls_on_step_for_status_messages(self, backend, on_step):
        """on_step is called for each StatusMessage from the stream."""
        # Create real-ish StatusMessage objects
        class FakeStatusMessage:
            def __init__(self, message):
                self.message = message

        class FakePrediction:
            completion_summary = "Done"
            trajectory = {}

        async def mock_stream(*args, **kwargs):
            yield FakeStatusMessage("🛠️ read_file(path='src/api.py')")
            yield FakeStatusMessage("✅ Herramienta completada")
            yield FakePrediction()

        mock_lm = MagicMock()
        mock_lm.history = []

        with (
            patch("autocode.core.planning.backends.dspy_react.get_dspy_lm", return_value=mock_lm),
            patch("autocode.core.planning.backends.dspy_react.prepare_chat_tools", return_value=[]),
            # Patch StatusMessage at module level (imported via from dspy.streaming import StatusMessage)
            patch("autocode.core.planning.backends.dspy_react.StatusMessage", FakeStatusMessage),
            patch("autocode.core.planning.backends.dspy_react.dspy") as mock_dspy,
        ):
            mock_dspy.ReAct.return_value = MagicMock()
            mock_dspy.streaming.StreamListener = MagicMock
            mock_dspy.streamify.return_value = mock_stream
            mock_dspy.context.return_value.__enter__ = MagicMock()
            mock_dspy.context.return_value.__exit__ = MagicMock()
            mock_dspy.Prediction = FakePrediction

            result = await backend.execute("do stuff", "/tmp", "", on_step)

        # 2 status messages + 1 final summary step = 3 on_step calls
        assert on_step.call_count == 3
        # First two are status messages
        step_0 = on_step.call_args_list[0][0][0]
        assert step_0.type == "status"
        assert "read_file" in step_0.content
        step_1 = on_step.call_args_list[1][0][0]
        assert step_1.type == "status"
        assert "completada" in step_1.content
        # Third is the final summary
        step_2 = on_step.call_args_list[2][0][0]
        assert step_2.type == "text"
        assert step_2.content == "Done"

    @pytest.mark.asyncio
    async def test_handles_exception_gracefully(self, backend, on_step):
        """Exception during execution returns ExecutionResult(success=False)."""
        with (
            patch(
                "autocode.core.planning.backends.dspy_react.get_dspy_lm",
                side_effect=ValueError("API key not configured"),
            ),
        ):
            result = await backend.execute("do stuff", "/tmp", "", on_step)

        assert result.success is False
        assert "API key" in result.error

    @pytest.mark.asyncio
    async def test_clears_lm_history_after_execution(self, backend, on_step):
        """LM history is cleared after execution to prevent accumulation."""
        mock_prediction = MagicMock()
        mock_prediction.completion_summary = "Done"
        mock_prediction.trajectory = {}

        async def mock_stream(*args, **kwargs):
            yield mock_prediction

        mock_lm = MagicMock()
        history_list = [{"usage": {}, "cost": 0.001}]
        mock_lm.history = history_list

        with (
            patch("autocode.core.planning.backends.dspy_react.get_dspy_lm", return_value=mock_lm),
            patch("autocode.core.planning.backends.dspy_react.prepare_chat_tools", return_value=[]),
            patch("autocode.core.planning.backends.dspy_react.dspy") as mock_dspy,
        ):
            mock_dspy.ReAct.return_value = MagicMock()
            mock_dspy.streaming.StreamListener = MagicMock
            mock_dspy.streamify.return_value = mock_stream
            mock_dspy.context.return_value.__enter__ = MagicMock()
            mock_dspy.context.return_value.__exit__ = MagicMock()
            mock_dspy.Prediction = type(mock_prediction)
            mock_dspy.streaming.StatusMessage = type("FakeStatusMessage", (), {})

            await backend.execute("do stuff", "/tmp", "", on_step)

        # history.clear() was called — list should be empty now
        assert history_list == []

    @pytest.mark.asyncio
    async def test_uses_default_model_when_empty(self, backend, on_step):
        """Empty model string falls back to default openrouter model."""
        async def mock_stream(*args, **kwargs):
            return
            yield

        mock_lm = MagicMock()
        mock_lm.history = []

        with (
            patch("autocode.core.planning.backends.dspy_react.get_dspy_lm", return_value=mock_lm) as mock_get_lm,
            patch("autocode.core.planning.backends.dspy_react.prepare_chat_tools", return_value=[]),
            patch("autocode.core.planning.backends.dspy_react.dspy") as mock_dspy,
        ):
            mock_dspy.ReAct.return_value = MagicMock()
            mock_dspy.streaming.StreamListener = MagicMock
            mock_dspy.streamify.return_value = mock_stream
            mock_dspy.context.return_value.__enter__ = MagicMock()
            mock_dspy.context.return_value.__exit__ = MagicMock()
            mock_dspy.Prediction = type("FakePrediction", (), {})
            mock_dspy.streaming.StatusMessage = type("FakeStatusMessage", (), {})

            await backend.execute("do stuff", "/tmp", "", on_step)

        mock_get_lm.assert_called_once_with("openrouter/openai/gpt-4o")

    @pytest.mark.asyncio
    async def test_passes_model_to_get_dspy_lm(self, backend, on_step):
        """Explicit model is passed to get_dspy_lm."""
        async def mock_stream(*args, **kwargs):
            return
            yield

        mock_lm = MagicMock()
        mock_lm.history = []

        with (
            patch("autocode.core.planning.backends.dspy_react.get_dspy_lm", return_value=mock_lm) as mock_get_lm,
            patch("autocode.core.planning.backends.dspy_react.prepare_chat_tools", return_value=[]),
            patch("autocode.core.planning.backends.dspy_react.dspy") as mock_dspy,
        ):
            mock_dspy.ReAct.return_value = MagicMock()
            mock_dspy.streaming.StreamListener = MagicMock
            mock_dspy.streamify.return_value = mock_stream
            mock_dspy.context.return_value.__enter__ = MagicMock()
            mock_dspy.context.return_value.__exit__ = MagicMock()
            mock_dspy.Prediction = type("FakePrediction", (), {})
            mock_dspy.streaming.StatusMessage = type("FakeStatusMessage", (), {})

            await backend.execute("do stuff", "/tmp", "anthropic/claude-3.5-sonnet", on_step)

        mock_get_lm.assert_called_once_with("anthropic/claude-3.5-sonnet")

    @pytest.mark.asyncio
    async def test_empty_summary_does_not_emit_final_step(self, backend, on_step):
        """If prediction has empty completion_summary, no final text step is emitted."""
        mock_prediction = MagicMock()
        mock_prediction.completion_summary = ""
        mock_prediction.trajectory = {}

        async def mock_stream(*args, **kwargs):
            yield mock_prediction

        mock_lm = MagicMock()
        mock_lm.history = []

        with (
            patch("autocode.core.planning.backends.dspy_react.get_dspy_lm", return_value=mock_lm),
            patch("autocode.core.planning.backends.dspy_react.prepare_chat_tools", return_value=[]),
            patch("autocode.core.planning.backends.dspy_react.dspy") as mock_dspy,
        ):
            mock_dspy.ReAct.return_value = MagicMock()
            mock_dspy.streaming.StreamListener = MagicMock
            mock_dspy.streamify.return_value = mock_stream
            mock_dspy.context.return_value.__enter__ = MagicMock()
            mock_dspy.context.return_value.__exit__ = MagicMock()
            mock_dspy.Prediction = type(mock_prediction)
            mock_dspy.streaming.StatusMessage = type("FakeStatusMessage", (), {})

            result = await backend.execute("do stuff", "/tmp", "", on_step)

        assert result.success is True
        assert on_step.call_count == 0  # No status messages, no summary
        assert len(result.steps) == 0
