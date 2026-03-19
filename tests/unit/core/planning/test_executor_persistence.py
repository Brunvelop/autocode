"""
Tests for executor execution state persistence and sandbox file detection.

Covers:
- Steps from backend stored in plan.execution.steps
- files_changed stored in plan.execution.files_changed
- Backend name and session_id persisted
- Total cost and tokens persisted
- files_changed comes from sandbox.collect_changes(), not backend result
- Agent commit safety net: collect_changes() and snapshot() called correctly
"""

from unittest.mock import AsyncMock, patch

import pytest

from autocode.core.planning.models import ExecutionStep
from autocode.core.planning.executor import stream_execute_plan
from tests.unit.core.planning.conftest import (
    _make_plan,
    _make_execution_result,
    _collect_events,
    _find_event,
    MockBackend,
    _patch_load_plan,
    _patch_save_plan,
    _patch_backend,
    _patch_compute_review_metrics,
    _patch_getcwd,
)


# ============================================================================
# TEST: EXECUTION STATE PERSISTENCE
# ============================================================================


class TestStoresExecutionStepsInPlan:
    """Steps from the backend are stored in plan.execution.steps."""

    @pytest.mark.asyncio
    async def test_stores_execution_steps_in_plan(self):
        plan = _make_plan()
        steps = [
            ExecutionStep(type="thinking", content="Step 1"),
            ExecutionStep(type="tool_use", tool="write_file", path="a.py", content="Step 2"),
        ]
        result = _make_execution_result(steps=steps)
        backend = MockBackend(result)
        saved_plans = []

        def capture_save(p):
            saved_plans.append(p.model_copy(deep=True))

        with (
            _patch_load_plan(plan),
            patch("autocode.core.planning.executor.save_plan", side_effect=capture_save),
            _patch_backend(backend),
            _patch_compute_review_metrics(),
            _patch_getcwd(),
            patch(
                "autocode.core.planning.executor.ExecutionSandbox",
                return_value=_make_mock_sandbox(),
            ),
        ):
            await _collect_events(
                stream_execute_plan("20260101-120000", backend="mock", review_mode="human")
            )

        final = saved_plans[-1]
        assert final.execution is not None
        assert len(final.execution.steps) == 2
        assert final.execution.steps[0].type == "thinking"
        assert final.execution.steps[1].tool == "write_file"


class TestStoresFilesChangedInPlan:
    """files_changed from the backend are stored in plan.execution.files_changed."""

    @pytest.mark.asyncio
    async def test_stores_files_changed_in_plan(self):
        plan = _make_plan()
        result = _make_execution_result(files_changed=["x.py", "y.py", "z.py"])
        backend = MockBackend(result)
        saved_plans = []

        def capture_save(p):
            saved_plans.append(p.model_copy(deep=True))

        with (
            _patch_load_plan(plan),
            patch("autocode.core.planning.executor.save_plan", side_effect=capture_save),
            _patch_backend(backend),
            _patch_compute_review_metrics(),
            _patch_getcwd(),
            patch(
                "autocode.core.planning.executor.ExecutionSandbox",
                return_value=_make_mock_sandbox(files=["x.py", "y.py", "z.py"]),
            ),
        ):
            await _collect_events(
                stream_execute_plan("20260101-120000", backend="mock", review_mode="human")
            )

        final = saved_plans[-1]
        assert final.execution.files_changed == ["x.py", "y.py", "z.py"]


class TestStoresBackendAndSessionId:
    """Backend name and session_id are persisted in execution state."""

    @pytest.mark.asyncio
    async def test_stores_backend_and_session_id(self):
        plan = _make_plan()
        result = _make_execution_result(session_id="sess-xyz")
        backend = MockBackend(result)
        saved_plans = []

        def capture_save(p):
            saved_plans.append(p.model_copy(deep=True))

        with (
            _patch_load_plan(plan),
            patch("autocode.core.planning.executor.save_plan", side_effect=capture_save),
            _patch_backend(backend),
            _patch_compute_review_metrics(),
            _patch_getcwd(),
        ):
            await _collect_events(
                stream_execute_plan("20260101-120000", backend="mock", review_mode="human")
            )

        final = saved_plans[-1]
        assert final.execution.backend == "mock"
        assert final.execution.session_id == "sess-xyz"


class TestStoresTotalCost:
    """Tokens and cost from the backend are persisted."""

    @pytest.mark.asyncio
    async def test_stores_total_cost_and_tokens(self):
        plan = _make_plan()
        result = _make_execution_result(total_tokens=5000, total_cost=0.01)
        backend = MockBackend(result)
        saved_plans = []

        def capture_save(p):
            saved_plans.append(p.model_copy(deep=True))

        with (
            _patch_load_plan(plan),
            patch("autocode.core.planning.executor.save_plan", side_effect=capture_save),
            _patch_backend(backend),
            _patch_compute_review_metrics(),
            _patch_getcwd(),
        ):
            await _collect_events(
                stream_execute_plan("20260101-120000", backend="mock", review_mode="human")
            )

        final = saved_plans[-1]
        assert final.execution.total_tokens == 5000
        assert final.execution.total_cost == 0.01


# ============================================================================
# TEST: AGENT COMMIT SAFETY NET
# ============================================================================


def _make_mock_sandbox(files=None, head="abc123"):
    """Create an AsyncMock sandbox with configurable files and head."""
    mock_sandbox = AsyncMock()
    mock_sandbox.snapshot = AsyncMock(return_value=head)
    mock_sandbox.collect_changes = AsyncMock(return_value=files or [])
    mock_sandbox.revert = AsyncMock()
    return mock_sandbox


class TestAgentCommitSafetyNet:
    """Safety net (undo agent commits) is handled inside sandbox.collect_changes().

    The executor delegates to ExecutionSandbox which encapsulates:
    - snapshot: record HEAD before execution
    - collect_changes: if agent committed (HEAD moved), reset --mixed first, then diff
    - revert: reset --hard back to pre-exec HEAD

    These tests verify that collect_changes() is always called after execution.
    The actual safety net logic is tested in test_execution.py.
    """

    @pytest.mark.asyncio
    async def test_collect_changes_called_after_execution(self):
        """sandbox.collect_changes() is always called after backend execution completes."""
        plan = _make_plan()
        backend = MockBackend()
        mock_sandbox = _make_mock_sandbox(files=["a.py"])

        with (
            _patch_load_plan(plan),
            _patch_save_plan(),
            _patch_backend(backend),
            _patch_compute_review_metrics(),
            _patch_getcwd("/fake/project"),
            patch(
                "autocode.core.planning.executor.ExecutionSandbox",
                return_value=mock_sandbox,
            ),
        ):
            await _collect_events(
                stream_execute_plan("20260101-120000", backend="mock", review_mode="human")
            )

        mock_sandbox.collect_changes.assert_called_once()

    @pytest.mark.asyncio
    async def test_snapshot_called_before_execution(self):
        """sandbox.snapshot() is called before the backend executes."""
        plan = _make_plan()
        call_order = []

        class OrderTrackingBackend:
            name = "mock"

            def abort(self):
                pass

            async def execute(self, instruction, cwd, model, on_step):
                call_order.append("execute")
                return _make_execution_result()

        mock_sandbox = AsyncMock()

        async def _snapshot():
            call_order.append("snapshot")
            return "abc123"

        mock_sandbox.snapshot = _snapshot
        mock_sandbox.collect_changes = AsyncMock(return_value=[])
        mock_sandbox.revert = AsyncMock()

        with (
            _patch_load_plan(plan),
            _patch_save_plan(),
            _patch_backend(OrderTrackingBackend()),
            _patch_compute_review_metrics(),
            _patch_getcwd("/fake/project"),
            patch(
                "autocode.core.planning.executor.ExecutionSandbox",
                return_value=mock_sandbox,
            ),
        ):
            await _collect_events(
                stream_execute_plan("20260101-120000", backend="mock", review_mode="human")
            )

        assert call_order.index("snapshot") < call_order.index("execute"), (
            "snapshot() must be called before backend.execute()"
        )

    @pytest.mark.asyncio
    async def test_graceful_when_git_unavailable(self):
        """Executor continues normally when git is unavailable (sandbox returns empty)."""
        plan = _make_plan()
        backend = MockBackend()
        mock_sandbox = AsyncMock()
        mock_sandbox.snapshot = AsyncMock(return_value="")  # git unavailable
        mock_sandbox.collect_changes = AsyncMock(return_value=[])
        mock_sandbox.revert = AsyncMock()

        with (
            _patch_load_plan(plan),
            _patch_save_plan(),
            _patch_backend(backend),
            _patch_compute_review_metrics(),
            _patch_getcwd("/fake/project"),
            patch(
                "autocode.core.planning.executor.ExecutionSandbox",
                return_value=mock_sandbox,
            ),
        ):
            events = await _collect_events(
                stream_execute_plan("20260101-120000", backend="mock", review_mode="human")
            )

        complete = _find_event(events, "plan_complete")
        assert complete is not None
        assert complete["data"]["success"] is True
        assert complete["data"]["files_changed"] == []


# ============================================================================
# TEST: FILES CHANGED COMPUTED BY EXECUTOR
# ============================================================================


class TestFilesChangedComputedByExecutor:
    """files_changed comes from sandbox.collect_changes(), not from the backend result.

    This decouples the executor from backend-specific file detection logic.
    Backends always return files_changed=[] (see Commit 4); the executor
    computes the actual list via git diff through ExecutionSandbox.
    """

    @pytest.mark.asyncio
    async def test_files_changed_from_sandbox_ignores_backend_value(self):
        """Executor uses sandbox.collect_changes() for files_changed, ignoring backend's value."""
        plan = _make_plan()
        result = _make_execution_result(files_changed=["backend_file.py"])
        backend = MockBackend(result)
        sandbox_files = ["sandbox_file_a.py", "sandbox_file_b.py"]
        mock_sandbox = _make_mock_sandbox(files=sandbox_files)

        with (
            _patch_load_plan(plan),
            _patch_save_plan(),
            _patch_backend(backend),
            _patch_compute_review_metrics(),
            _patch_getcwd("/fake/project"),
            patch(
                "autocode.core.planning.executor.ExecutionSandbox",
                return_value=mock_sandbox,
            ),
        ):
            events = await _collect_events(
                stream_execute_plan("20260101-120000", backend="mock", review_mode="human")
            )

        complete = _find_event(events, "plan_complete")
        assert complete["data"]["files_changed"] == sandbox_files
        assert "backend_file.py" not in complete["data"]["files_changed"]

    @pytest.mark.asyncio
    async def test_files_changed_from_sandbox_stored_in_plan(self):
        """files_changed from sandbox is stored in plan.execution.files_changed."""
        plan = _make_plan()
        sandbox_files = ["src/module.py", "tests/test_module.py"]
        mock_sandbox = _make_mock_sandbox(files=sandbox_files)
        saved_plans = []

        def capture_save(p):
            saved_plans.append(p.model_copy(deep=True))

        with (
            _patch_load_plan(plan),
            patch("autocode.core.planning.executor.save_plan", side_effect=capture_save),
            _patch_backend(MockBackend()),
            _patch_compute_review_metrics(),
            _patch_getcwd("/fake/project"),
            patch(
                "autocode.core.planning.executor.ExecutionSandbox",
                return_value=mock_sandbox,
            ),
        ):
            await _collect_events(
                stream_execute_plan("20260101-120000", backend="mock", review_mode="human")
            )

        final = saved_plans[-1]
        assert final.execution.files_changed == sandbox_files

    @pytest.mark.asyncio
    async def test_files_changed_from_sandbox_passed_to_review_flow(self):
        """files_changed from sandbox is passed to the review flow (review_start event)."""
        plan = _make_plan()
        sandbox_files = ["changed_by_agent.py"]
        mock_sandbox = _make_mock_sandbox(files=sandbox_files)

        with (
            _patch_load_plan(plan),
            _patch_save_plan(),
            _patch_backend(MockBackend()),
            _patch_compute_review_metrics(),
            _patch_getcwd("/fake/project"),
            patch(
                "autocode.core.planning.executor.ExecutionSandbox",
                return_value=mock_sandbox,
            ),
        ):
            events = await _collect_events(
                stream_execute_plan("20260101-120000", backend="mock", review_mode="human")
            )

        review_start = _find_event(events, "review_start")
        assert review_start is not None
        assert review_start["data"]["files_changed"] == sandbox_files
