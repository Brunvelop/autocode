"""
Tests for plan executor — rewritten for pluggable backends (C10).

Tests cover the new backend-based executor that delegates to
ExecutorBackend implementations (opencode, cline, dspy).

All backend interactions are mocked — tests validate the orchestrator logic:
- SSE event emission (plan_start, step, plan_complete, error, heartbeat)
- FSM transitions (executing → pending_review / completed / failed)
- Review modes (human → pending_review, auto → quality gates)
- Backend selection and delegation
- Execution state persistence (steps, files_changed, cost)
"""

import asyncio
import json
import os
import time
from datetime import datetime
from typing import List
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from autocode.core.planning.models import (
    CommitPlan,
    ExecutionStep,
    PlanExecutionState,
    ReviewResult,
)
from autocode.core.planning.backends import get_backend
from autocode.core.planning.backends.base import ExecutionResult
from autocode.core.planning.executor import (
    stream_execute_plan,
    _build_instruction,
    _with_heartbeat,
)
from tests.unit.core.planning.conftest import _parse_sse


# ============================================================================
# HELPERS
# ============================================================================


def _make_plan(status="draft", **kwargs) -> CommitPlan:
    """Create a minimal CommitPlan for testing."""
    defaults = dict(
        id="20260101-120000",
        title="Add validation",
        description="Add input validation to the API endpoint.\n\n- Validate email format\n- Check required fields",
        parent_commit="abc123",
        branch="main",
        status=status,
        created_at="2026-01-01T12:00:00",
        updated_at="2026-01-01T12:00:00",
    )
    defaults.update(kwargs)
    return CommitPlan(**defaults)


def _make_execution_result(success=True, **kwargs) -> ExecutionResult:
    """Create an ExecutionResult for testing."""
    defaults = dict(
        success=success,
        files_changed=["src/api.py", "src/validators.py"],
        steps=[
            ExecutionStep(type="thinking", content="Analyzing requirements"),
            ExecutionStep(type="tool_use", tool="read_file", path="src/api.py", content="Reading file"),
            ExecutionStep(type="tool_use", tool="write_file", path="src/api.py", content="Writing changes"),
        ],
        total_tokens=1500,
        total_cost=0.003,
        session_id="sess-abc123",
        error="",
    )
    defaults.update(kwargs)
    return ExecutionResult(**defaults)


async def _collect_events(async_gen) -> List[dict]:
    """Collect all SSE events from an async generator, parsed."""
    events = []
    async for raw in async_gen:
        try:
            events.append(_parse_sse(raw))
        except (json.JSONDecodeError, IndexError):
            pass
    return events


def _find_event(events: List[dict], event_type: str) -> dict | None:
    """Find first event of a given type."""
    return next((e for e in events if e["event"] == event_type), None)


def _find_events(events: List[dict], event_type: str) -> List[dict]:
    """Find all events of a given type."""
    return [e for e in events if e["event"] == event_type]


# ============================================================================
# MOCK BACKEND
# ============================================================================


class MockBackend:
    """A fake backend that returns a preconfigured ExecutionResult."""

    name = "mock"

    def __init__(self, result: ExecutionResult | None = None):
        self._result = result or _make_execution_result()
        self.execute_called_with = None

    def abort(self) -> None:
        """No-op abort for tests."""
        pass

    async def execute(self, instruction, cwd, model, on_step):
        self.execute_called_with = {
            "instruction": instruction,
            "cwd": cwd,
            "model": model,
        }
        for step in self._result.steps:
            await on_step(step)
        return self._result


# ============================================================================
# PATCHES — shared across tests
# ============================================================================


def _patch_load_plan(plan):
    """Patch load_plan to return the given plan."""
    return patch("autocode.core.planning.executor.load_plan", return_value=plan)


def _patch_save_plan():
    """Patch save_plan to be a no-op."""
    return patch("autocode.core.planning.executor.save_plan")


def _patch_backend(backend):
    """Patch get_backend to return the given backend instance."""
    return patch("autocode.core.planning.executor.get_backend", return_value=backend)


def _patch_auto_review(verdict="approved", summary="All good"):
    """Patch auto_review to return a ReviewResult with given verdict."""
    result = ReviewResult(
        mode="auto",
        verdict=verdict,
        summary=summary,
        reviewed_by="auto",
    )
    return patch("autocode.core.planning.executor.auto_review", return_value=result)


def _patch_compute_review_metrics(metrics=None):
    """Patch compute_review_metrics."""
    return patch(
        "autocode.core.planning.executor.compute_review_metrics",
        return_value=metrics or [],
    )


def _patch_git_add_and_commit(commit_hash="def456"):
    """Patch git_add_and_commit."""
    return patch(
        "autocode.core.planning.executor.git_add_and_commit",
        return_value=commit_hash,
    )


def _patch_getcwd(cwd="/fake/project"):
    """Patch os.getcwd."""
    return patch("autocode.core.planning.executor.os.getcwd", return_value=cwd)


def _patch_sandbox(files=None, head="abc123"):
    """Patch ExecutionSandbox to return controlled files_changed and a no-op revert.

    Args:
        files: List of file paths collect_changes() should return. Defaults to [].
        head: SHA hash snapshot() should return.
    """
    if files is None:
        files = []
    mock_instance = AsyncMock()
    mock_instance.snapshot = AsyncMock(return_value=head)
    mock_instance.collect_changes = AsyncMock(return_value=files)
    mock_instance.revert = AsyncMock()
    mock_instance.pre_exec_head = head
    return patch(
        "autocode.core.planning.executor.ExecutionSandbox",
        return_value=mock_instance,
    )


# ============================================================================
# TEST: SSE EVENTS
# ============================================================================


class TestEmitsPlanStartEvent:
    """plan_start SSE event contains plan_id, title, backend, model."""

    @pytest.mark.asyncio
    async def test_emits_plan_start_event(self):
        plan = _make_plan()
        backend = MockBackend()

        with (
            _patch_load_plan(plan),
            _patch_save_plan(),
            _patch_backend(backend),
            _patch_compute_review_metrics(),
            _patch_getcwd(),
        ):
            events = await _collect_events(
                stream_execute_plan("20260101-120000", backend="mock", model="test-model")
            )

        start = _find_event(events, "plan_start")
        assert start is not None
        assert start["data"]["plan_id"] == "20260101-120000"
        assert start["data"]["title"] == "Add validation"
        assert start["data"]["backend"] == "mock"
        assert start["data"]["model"] == "test-model"


class TestStepEventsForwardedFromBackend:
    """Each step from the backend is forwarded as an SSE 'step' event."""

    @pytest.mark.asyncio
    async def test_step_events_forwarded_from_backend(self):
        plan = _make_plan()
        steps = [
            ExecutionStep(type="thinking", content="Planning changes"),
            ExecutionStep(type="tool_use", tool="read_file", path="src/api.py", content="Reading"),
            ExecutionStep(type="tool_use", tool="write_file", path="src/api.py", content="Writing"),
        ]
        result = _make_execution_result(steps=steps)
        backend = MockBackend(result)

        with (
            _patch_load_plan(plan),
            _patch_save_plan(),
            _patch_backend(backend),
            _patch_compute_review_metrics(),
            _patch_getcwd(),
        ):
            events = await _collect_events(
                stream_execute_plan("20260101-120000", backend="mock")
            )

        step_events = _find_events(events, "step")
        assert len(step_events) == 3
        assert step_events[0]["data"]["type"] == "thinking"
        assert step_events[0]["data"]["content"] == "Planning changes"
        assert step_events[1]["data"]["tool"] == "read_file"
        assert step_events[1]["data"]["path"] == "src/api.py"
        assert step_events[2]["data"]["tool"] == "write_file"


class TestStepEventsStreamedInRealTime:
    """Steps are emitted via SSE as they happen, not in batch after backend completes."""

    @pytest.mark.asyncio
    async def test_steps_arrive_incrementally_not_in_batch(self):
        """Each step SSE event should arrive before the next sleep completes.

        With Queue-based streaming: step1 SSE arrives immediately when on_step()
        is called, BEFORE the backend sleeps and calls on_step() for step2.
        With the old batch approach, both would arrive simultaneously at the end.
        """
        plan = _make_plan()
        step_delay = 0.1  # 100ms between steps

        step1 = ExecutionStep(type="thinking", content="Step 1")
        step2 = ExecutionStep(type="tool_use", tool="write_file", path="a.py", content="Step 2")
        result = _make_execution_result(steps=[step1, step2])

        class TimedMockBackend:
            name = "mock"

            async def execute(self, instruction, cwd, model, on_step):
                await on_step(step1)
                await asyncio.sleep(step_delay)
                await on_step(step2)
                return result

        event_arrival_times = []

        async def _collect_with_timing():
            async for raw in stream_execute_plan("20260101-120000", backend="mock"):
                try:
                    event = _parse_sse(raw)
                    if event["event"] == "step":
                        event_arrival_times.append(time.monotonic())
                except (json.JSONDecodeError, IndexError):
                    pass

        with (
            _patch_load_plan(plan),
            _patch_save_plan(),
            _patch_backend(TimedMockBackend()),
            _patch_compute_review_metrics(),
            _patch_getcwd(),
        ):
            await _collect_with_timing()

        assert len(event_arrival_times) == 2, (
            f"Expected 2 step events, got {len(event_arrival_times)}"
        )
        # With Queue-based streaming, the gap between step1 and step2 arrival
        # should reflect the sleep delay (≥ 50% of step_delay).
        # With the old batch approach, both arrive nearly simultaneously (gap ≈ 0ms).
        gap = event_arrival_times[1] - event_arrival_times[0]
        assert gap >= step_delay * 0.5, (
            f"Steps should arrive incrementally (gap={gap*1000:.1f}ms), "
            f"not in batch (expected ≥{step_delay * 0.5 * 1000:.0f}ms). "
            f"This indicates steps are being batched instead of streamed in real-time."
        )

    @pytest.mark.asyncio
    async def test_step_sse_emitted_before_backend_returns(self):
        """Step SSE events are available to consumers before execute() returns.

        Verifies that the Queue bridge allows consumers to receive steps
        WHILE the backend is still running (not after it completes).
        """
        plan = _make_plan()
        backend_completed = asyncio.Event()
        step1_received_before_backend_done = False

        step1 = ExecutionStep(type="thinking", content="Early step")
        result = _make_execution_result(steps=[step1])

        class SlowMockBackend:
            name = "mock"

            async def execute(self, instruction, cwd, model, on_step):
                await on_step(step1)
                # Simulate a long-running backend
                await asyncio.sleep(0.1)
                backend_completed.set()
                return result

        received_steps = []

        async def _collect_checking_timing():
            nonlocal step1_received_before_backend_done
            async for raw in stream_execute_plan("20260101-120000", backend="mock"):
                try:
                    event = _parse_sse(raw)
                    if event["event"] == "step":
                        received_steps.append(event)
                        # Check if we received this step before backend finished
                        if not backend_completed.is_set():
                            step1_received_before_backend_done = True
                except (json.JSONDecodeError, IndexError):
                    pass

        with (
            _patch_load_plan(plan),
            _patch_save_plan(),
            _patch_backend(SlowMockBackend()),
            _patch_compute_review_metrics(),
            _patch_getcwd(),
        ):
            await _collect_checking_timing()

        assert len(received_steps) == 1
        assert step1_received_before_backend_done, (
            "Step SSE event should be received by consumer BEFORE backend.execute() returns. "
            "This indicates real-time streaming is not working."
        )


class TestPlanCompleteWithSuccess:
    """plan_complete event reports success, files_changed, cost, status."""

    @pytest.mark.asyncio
    async def test_plan_complete_with_success(self):
        plan = _make_plan()
        result = _make_execution_result(
            success=True,
            files_changed=["a.py", "b.py"],
            total_tokens=2000,
            total_cost=0.005,
        )
        backend = MockBackend(result)

        with (
            _patch_load_plan(plan),
            _patch_save_plan(),
            _patch_backend(backend),
            _patch_compute_review_metrics(),
            _patch_getcwd(),
            _patch_sandbox(["a.py", "b.py"]),
        ):
            events = await _collect_events(
                stream_execute_plan("20260101-120000", backend="mock", review_mode="human")
            )

        complete = _find_event(events, "plan_complete")
        assert complete is not None
        assert complete["data"]["success"] is True
        assert complete["data"]["files_changed"] == ["a.py", "b.py"]
        assert complete["data"]["total_tokens"] == 2000
        assert complete["data"]["total_cost"] == 0.005
        assert complete["data"]["status"] == "pending_review"


class TestPlanCompleteWithFailure:
    """Backend failure → plan_complete with success=False, status=failed."""

    @pytest.mark.asyncio
    async def test_plan_complete_with_failure(self):
        plan = _make_plan()
        result = _make_execution_result(
            success=False,
            error="Command exited with code 1",
            files_changed=[],
            steps=[],
        )
        backend = MockBackend(result)

        with (
            _patch_load_plan(plan),
            _patch_save_plan(),
            _patch_backend(backend),
            _patch_getcwd(),
        ):
            events = await _collect_events(
                stream_execute_plan("20260101-120000", backend="mock")
            )

        complete = _find_event(events, "plan_complete")
        assert complete is not None
        assert complete["data"]["success"] is False
        assert complete["data"]["status"] == "failed"


# ============================================================================
# TEST: FSM TRANSITIONS
# ============================================================================


class TestFSMTransitions:
    """Verify status transitions: executing → pending_review / completed / failed."""

    @pytest.mark.asyncio
    async def test_draft_to_executing_to_pending_review(self):
        """draft → executing → pending_review (human review mode)."""
        plan = _make_plan(status="draft")
        backend = MockBackend()
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

        # First save: executing, last save: pending_review
        assert saved_plans[0].status == "executing"
        assert saved_plans[-1].status == "pending_review"

    @pytest.mark.asyncio
    async def test_failed_plan_can_be_re_executed(self):
        """failed → executing → pending_review."""
        plan = _make_plan(status="failed")
        backend = MockBackend()

        with (
            _patch_load_plan(plan),
            _patch_save_plan(),
            _patch_backend(backend),
            _patch_compute_review_metrics(),
            _patch_getcwd(),
        ):
            events = await _collect_events(
                stream_execute_plan("20260101-120000", backend="mock", review_mode="human")
            )

        complete = _find_event(events, "plan_complete")
        assert complete is not None
        assert complete["data"]["success"] is True

    @pytest.mark.asyncio
    async def test_backend_failure_sets_failed_status(self):
        """executing → failed when backend returns success=False."""
        plan = _make_plan()
        result = _make_execution_result(success=False, error="Crash")
        backend = MockBackend(result)
        saved_plans = []

        def capture_save(p):
            saved_plans.append(p.model_copy(deep=True))

        with (
            _patch_load_plan(plan),
            patch("autocode.core.planning.executor.save_plan", side_effect=capture_save),
            _patch_backend(backend),
            _patch_getcwd(),
        ):
            await _collect_events(
                stream_execute_plan("20260101-120000", backend="mock")
            )

        assert saved_plans[-1].status == "failed"

    @pytest.mark.asyncio
    async def test_auto_approved_sets_completed_status(self):
        """executing → completed when auto-review approves."""
        plan = _make_plan()
        backend = MockBackend()
        saved_plans = []

        def capture_save(p):
            saved_plans.append(p.model_copy(deep=True))

        with (
            _patch_load_plan(plan),
            patch("autocode.core.planning.executor.save_plan", side_effect=capture_save),
            _patch_backend(backend),
            _patch_auto_review(verdict="approved"),
            _patch_git_add_and_commit("abc999"),
            _patch_getcwd(),
        ):
            await _collect_events(
                stream_execute_plan("20260101-120000", backend="mock", review_mode="auto")
            )

        assert saved_plans[-1].status == "completed"


# ============================================================================
# TEST: REVIEW MODES
# ============================================================================


class TestReviewModeHuman:
    """Human review mode → pending_review, review_start/complete events."""

    @pytest.mark.asyncio
    async def test_review_mode_human_pending_review(self):
        plan = _make_plan()
        backend = MockBackend()

        with (
            _patch_load_plan(plan),
            _patch_save_plan(),
            _patch_backend(backend),
            _patch_compute_review_metrics(),
            _patch_getcwd(),
        ):
            events = await _collect_events(
                stream_execute_plan("20260101-120000", backend="mock", review_mode="human")
            )

        review_start = _find_event(events, "review_start")
        assert review_start is not None
        assert review_start["data"]["review_mode"] == "human"

        review_complete = _find_event(events, "review_complete")
        assert review_complete is not None
        assert review_complete["data"]["verdict"] == "needs_changes"
        assert review_complete["data"]["review_mode"] == "human"

        complete = _find_event(events, "plan_complete")
        assert complete["data"]["status"] == "pending_review"


class TestReviewModeAutoApproved:
    """Auto review approved → completed, commit created."""

    @pytest.mark.asyncio
    async def test_review_mode_auto_approved_commits(self):
        plan = _make_plan()
        backend = MockBackend()

        with (
            _patch_load_plan(plan),
            _patch_save_plan(),
            _patch_backend(backend),
            _patch_auto_review(verdict="approved", summary="All gates passed"),
            _patch_git_add_and_commit("commit-hash-123"),
            _patch_getcwd(),
            _patch_sandbox(["src/api.py"]),
        ):
            events = await _collect_events(
                stream_execute_plan("20260101-120000", backend="mock", review_mode="auto")
            )

        review_complete = _find_event(events, "review_complete")
        assert review_complete["data"]["verdict"] == "approved"

        complete = _find_event(events, "plan_complete")
        assert complete["data"]["status"] == "completed"
        assert complete["data"]["commit_hash"] == "commit-hash-123"


class TestReviewModeAutoRejected:
    """Auto review rejected → pending_review, no commit."""

    @pytest.mark.asyncio
    async def test_review_mode_auto_rejected_pending_review(self):
        plan = _make_plan()
        backend = MockBackend()

        with (
            _patch_load_plan(plan),
            _patch_save_plan(),
            _patch_backend(backend),
            _patch_auto_review(verdict="rejected", summary="Complexity too high"),
            _patch_getcwd(),
        ):
            events = await _collect_events(
                stream_execute_plan("20260101-120000", backend="mock", review_mode="auto")
            )

        review_complete = _find_event(events, "review_complete")
        assert review_complete["data"]["verdict"] == "rejected"

        complete = _find_event(events, "plan_complete")
        assert complete["data"]["status"] == "pending_review"
        assert complete["data"]["commit_hash"] == ""


# ============================================================================
# TEST: BACKEND SELECTION
# ============================================================================


class TestBackendSelection:
    """get_backend resolves backend name to instance."""

    def test_backend_selection_opencode(self):
        from autocode.core.planning.backends.opencode import OpenCodeBackend

        backend = get_backend("opencode")
        assert isinstance(backend, OpenCodeBackend)
        assert backend.name == "opencode"

    def test_backend_selection_cline(self):
        from autocode.core.planning.backends.cline import ClineBackend

        backend = get_backend("cline")
        assert isinstance(backend, ClineBackend)
        assert backend.name == "cline"

    def test_backend_unknown_raises(self):
        with pytest.raises(ValueError, match="Unknown backend"):
            get_backend("nonexistent")


# ============================================================================
# TEST: ERROR HANDLING
# ============================================================================


class TestPlanNotFound:
    """Plan not found → error SSE event."""

    @pytest.mark.asyncio
    async def test_plan_not_found_emits_error(self):
        with _patch_load_plan(None):
            events = await _collect_events(
                stream_execute_plan("nonexistent-id", backend="mock")
            )

        assert len(events) == 1
        assert events[0]["event"] == "error"
        assert "not found" in events[0]["data"]["message"]
        assert events[0]["data"]["success"] is False


class TestInvalidStatus:
    """Plan in non-executable status → error SSE event."""

    @pytest.mark.asyncio
    async def test_invalid_status_emits_error(self):
        plan = _make_plan(status="completed")
        with _patch_load_plan(plan):
            events = await _collect_events(
                stream_execute_plan("20260101-120000", backend="mock")
            )

        assert len(events) == 1
        assert events[0]["event"] == "error"
        assert "Cannot execute" in events[0]["data"]["message"]


class TestBackendException:
    """Unhandled exception in backend → error SSE event."""

    @pytest.mark.asyncio
    async def test_backend_exception_emits_error(self):
        plan = _make_plan()

        class CrashBackend:
            name = "crash"

            async def execute(self, instruction, cwd, model, on_step):
                raise RuntimeError("Backend exploded")

        with (
            _patch_load_plan(plan),
            _patch_save_plan(),
            _patch_backend(CrashBackend()),
            _patch_getcwd(),
        ):
            events = await _collect_events(
                stream_execute_plan("20260101-120000", backend="crash")
            )

        error = _find_event(events, "error")
        assert error is not None
        assert "Backend exploded" in error["data"]["message"]


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
            _patch_sandbox(),
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
            _patch_sandbox(["x.py", "y.py", "z.py"]),
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
# TEST: HEARTBEAT
# ============================================================================


class TestHeartbeat:
    """Heartbeat events are emitted during long-running execution."""

    @pytest.mark.asyncio
    async def test_heartbeat_emitted_during_execution(self):
        """Heartbeat wrapper emits heartbeat events interleaved with source."""
        emitted = []

        async def slow_source():
            yield "first"
            await asyncio.sleep(0.15)  # Trigger heartbeat
            yield "second"

        async for item in _with_heartbeat(slow_source(), interval=0.05):
            emitted.append(item)

        # Should have: "first", possibly heartbeat(s), "second"
        assert "first" in emitted
        assert "second" in emitted
        heartbeats = [e for e in emitted if isinstance(e, str) and "heartbeat" in e]
        assert len(heartbeats) >= 1

    @pytest.mark.asyncio
    async def test_heartbeat_contains_elapsed_s(self):
        """Heartbeat events contain elapsed_s field."""

        async def slow_source():
            await asyncio.sleep(0.15)
            yield "done"

        heartbeats = []
        async for item in _with_heartbeat(slow_source(), interval=0.05):
            if isinstance(item, str) and "heartbeat" in item:
                heartbeats.append(_parse_sse(item))

        assert len(heartbeats) >= 1
        assert "elapsed_s" in heartbeats[0]["data"]
        assert heartbeats[0]["data"]["elapsed_s"] >= 0


# ============================================================================
# TEST: BUILD INSTRUCTION
# ============================================================================


class TestBuildInstruction:
    """_build_instruction creates a markdown instruction from plan."""

    def test_builds_instruction_from_plan(self):
        plan = _make_plan(
            title="Fix auth bug",
            description="The login endpoint returns 500 when password is empty.",
        )
        instruction = _build_instruction(plan)
        assert "Fix auth bug" in instruction
        assert "login endpoint returns 500" in instruction

    def test_instruction_with_empty_description(self):
        plan = _make_plan(title="Quick fix", description="")
        instruction = _build_instruction(plan)
        assert "Quick fix" in instruction


# ============================================================================
# TEST: BACKEND RECEIVES CORRECT ARGS
# ============================================================================


class TestBackendReceivesCorrectArgs:
    """The executor passes correct instruction, cwd, model to backend."""

    @pytest.mark.asyncio
    async def test_backend_receives_instruction_cwd_model(self):
        plan = _make_plan(title="Fix bug", description="Fix the critical bug")
        backend = MockBackend()

        with (
            _patch_load_plan(plan),
            _patch_save_plan(),
            _patch_backend(backend),
            _patch_compute_review_metrics(),
            _patch_getcwd("/my/project"),
        ):
            await _collect_events(
                stream_execute_plan("20260101-120000", backend="mock", model="gpt-4")
            )

        assert backend.execute_called_with is not None
        assert "Fix bug" in backend.execute_called_with["instruction"]
        assert "Fix the critical bug" in backend.execute_called_with["instruction"]
        assert backend.execute_called_with["cwd"] == "/my/project"
        assert backend.execute_called_with["model"] == "gpt-4"


# ============================================================================
# TEST: REGISTERED ENDPOINT
# ============================================================================


class TestExecuteCommitPlanEndpoint:
    """execute_commit_plan is a sync wrapper around stream_execute_plan."""

    def test_execute_commit_plan_is_registered(self):
        """The function has the register_function decorator attributes."""
        from autocode.core.planning.executor import execute_commit_plan
        # The function should be callable (it's decorated but still a function)
        assert callable(execute_commit_plan)


# ============================================================================
# TEST: REVIEW EVENT INCLUDES FILES_CHANGED
# ============================================================================


class TestReviewStartIncludesFiles:
    """review_start event contains the list of files_changed."""

    @pytest.mark.asyncio
    async def test_review_start_includes_files_changed(self):
        plan = _make_plan()
        result = _make_execution_result(files_changed=["a.py", "b.py"])
        backend = MockBackend(result)

        with (
            _patch_load_plan(plan),
            _patch_save_plan(),
            _patch_backend(backend),
            _patch_compute_review_metrics(),
            _patch_getcwd(),
            _patch_sandbox(["a.py", "b.py"]),
        ):
            events = await _collect_events(
                stream_execute_plan("20260101-120000", backend="mock", review_mode="human")
            )

        review_start = _find_event(events, "review_start")
        assert review_start is not None
        assert review_start["data"]["files_changed"] == ["a.py", "b.py"]


# ============================================================================
# TEST: EVENT ORDER
# ============================================================================


class TestEventOrder:
    """SSE events are emitted in the correct order."""

    @pytest.mark.asyncio
    async def test_event_order_success_flow(self):
        """plan_start → step(s) → review_start → review_complete → plan_complete."""
        plan = _make_plan()
        backend = MockBackend()

        with (
            _patch_load_plan(plan),
            _patch_save_plan(),
            _patch_backend(backend),
            _patch_compute_review_metrics(),
            _patch_getcwd(),
        ):
            events = await _collect_events(
                stream_execute_plan("20260101-120000", backend="mock", review_mode="human")
            )

        event_types = [e["event"] for e in events]
        # plan_start should come first
        assert event_types[0] == "plan_start"
        # plan_complete should come last
        assert event_types[-1] == "plan_complete"
        # review_start before review_complete
        if "review_start" in event_types:
            assert event_types.index("review_start") < event_types.index("review_complete")
        # step events should come before review
        step_indices = [i for i, t in enumerate(event_types) if t == "step"]
        if step_indices and "review_start" in event_types:
            assert max(step_indices) < event_types.index("review_start")


# ============================================================================
# TEST: CANCEL / ABORT SUPPORT
# ============================================================================


def _make_slow_abortable_backend(abort_flag: list, sleep_seconds: float = 10.0):
    """Create a backend that emits one step then sleeps indefinitely.

    abort_flag is a mutable list so the closure can update it.
    """
    class SlowAbortableBackend:
        name = "mock"

        def abort(self):
            abort_flag.append(True)

        async def execute(self, instruction, cwd, model, on_step):
            step = ExecutionStep(type="thinking", content="Working...")
            await on_step(step)
            await asyncio.sleep(sleep_seconds)
            return _make_execution_result()

    return SlowAbortableBackend()


async def _consume_until_step_then_close(plan_id: str, backend_instance):
    """Helper: iterate stream_execute_plan until a step event, then close the generator.

    Returns after gen.aclose() completes, giving the cancel handler time to run.
    """
    with _patch_load_plan(_make_plan()), \
         patch("autocode.core.planning.executor.save_plan"), \
         _patch_backend(backend_instance), \
         _patch_getcwd("/fake/project"):
        gen = stream_execute_plan(plan_id, backend="mock")
        async for raw in gen:
            try:
                if _parse_sse(raw)["event"] == "step":
                    break
            except (json.JSONDecodeError, IndexError, KeyError):
                pass
        await gen.aclose()


class TestCancelKillsBackend:
    """When the SSE consumer disconnects (generator closed), abort() is called."""

    @pytest.mark.asyncio
    async def test_cancel_calls_abort_on_backend(self):
        """Closing the generator mid-execution calls backend.abort()."""
        abort_flag = []
        backend = _make_slow_abortable_backend(abort_flag)

        await _consume_until_step_then_close("20260101-120000", backend)

        assert abort_flag, "abort() must be called when the generator is closed mid-execution"

    @pytest.mark.asyncio
    async def test_abort_called_only_from_cancel_not_normal_flow(self):
        """abort() is NOT called when execution completes normally."""
        abort_flag = []
        backend = _make_slow_abortable_backend(abort_flag, sleep_seconds=0)
        # Override execute to complete immediately
        backend_result = _make_execution_result()

        class FastAbortableBackend:
            name = "mock"

            def abort(self):
                abort_flag.append(True)

            async def execute(self, instruction, cwd, model, on_step):
                step = ExecutionStep(type="thinking", content="Done")
                await on_step(step)
                return backend_result

        with (
            _patch_load_plan(_make_plan()),
            _patch_save_plan(),
            _patch_backend(FastAbortableBackend()),
            _patch_compute_review_metrics(),
            _patch_getcwd(),
        ):
            await _collect_events(
                stream_execute_plan("20260101-120000", backend="mock")
            )

        assert not abort_flag, "abort() should NOT be called when execution completes normally"


class TestCancelRevertsChanges:
    """When cancelled, sandbox.revert() is called to undo uncommitted work (git reset --hard)."""

    @pytest.mark.asyncio
    async def test_cancel_calls_sandbox_revert(self):
        """sandbox.revert() is called when the generator is closed mid-execution."""
        abort_flag = []
        backend = _make_slow_abortable_backend(abort_flag)

        mock_sandbox = AsyncMock()
        mock_sandbox.snapshot = AsyncMock(return_value="abc123")
        mock_sandbox.collect_changes = AsyncMock(return_value=[])
        mock_sandbox.revert = AsyncMock()

        with (
            _patch_load_plan(_make_plan()),
            patch("autocode.core.planning.executor.save_plan"),
            _patch_backend(backend),
            _patch_getcwd("/fake/project"),
            patch(
                "autocode.core.planning.executor.ExecutionSandbox",
                return_value=mock_sandbox,
            ),
        ):
            gen = stream_execute_plan("20260101-120000", backend="mock")
            async for raw in gen:
                try:
                    if _parse_sse(raw)["event"] == "step":
                        break
                except (json.JSONDecodeError, IndexError, KeyError):
                    pass
            await gen.aclose()

        mock_sandbox.revert.assert_called_once()


class TestCancelSetsPlanFailed:
    """When cancelled, the plan is saved with status='failed'."""

    @pytest.mark.asyncio
    async def test_cancel_sets_plan_status_failed(self):
        """Cancelling execution marks the plan as failed and persists it."""
        abort_flag = []
        backend = _make_slow_abortable_backend(abort_flag)
        saved_plans = []

        def capture_save(p):
            saved_plans.append(p.model_copy(deep=True))

        mock_sandbox = AsyncMock()
        mock_sandbox.snapshot = AsyncMock(return_value="abc123")
        mock_sandbox.collect_changes = AsyncMock(return_value=[])
        mock_sandbox.revert = AsyncMock()

        with (
            _patch_load_plan(_make_plan()),
            patch("autocode.core.planning.executor.save_plan", side_effect=capture_save),
            _patch_backend(backend),
            _patch_getcwd(),
            patch(
                "autocode.core.planning.executor.ExecutionSandbox",
                return_value=mock_sandbox,
            ),
        ):
            gen = stream_execute_plan("20260101-120000", backend="mock")
            async for raw in gen:
                try:
                    if _parse_sse(raw)["event"] == "step":
                        break
                except (json.JSONDecodeError, IndexError, KeyError):
                    pass
            await gen.aclose()

        assert len(saved_plans) >= 2, "Expected at least 'executing' + 'failed' saves"
        assert saved_plans[-1].status == "failed", (
            f"Expected plan.status='failed', got '{saved_plans[-1].status}'"
        )

    @pytest.mark.asyncio
    async def test_cancel_saves_completed_at_timestamp(self):
        """Cancelled plan has a completed_at timestamp set."""
        abort_flag = []
        backend = _make_slow_abortable_backend(abort_flag)
        saved_plans = []

        def capture_save(p):
            saved_plans.append(p.model_copy(deep=True))

        mock_sandbox = AsyncMock()
        mock_sandbox.snapshot = AsyncMock(return_value="abc123")
        mock_sandbox.collect_changes = AsyncMock(return_value=[])
        mock_sandbox.revert = AsyncMock()

        with (
            _patch_load_plan(_make_plan()),
            patch("autocode.core.planning.executor.save_plan", side_effect=capture_save),
            _patch_backend(backend),
            _patch_getcwd(),
            patch(
                "autocode.core.planning.executor.ExecutionSandbox",
                return_value=mock_sandbox,
            ),
        ):
            gen = stream_execute_plan("20260101-120000", backend="mock")
            async for raw in gen:
                try:
                    if _parse_sse(raw)["event"] == "step":
                        break
                except (json.JSONDecodeError, IndexError, KeyError):
                    pass
            await gen.aclose()

        last_saved = saved_plans[-1]
        assert last_saved.execution is not None
        assert last_saved.execution.completed_at is not None, (
            "completed_at should be set when plan is cancelled"
        )


# ============================================================================
# TEST: AGENT COMMIT SAFETY NET
# ============================================================================


class TestAgentCommitSafetyNet:
    """Safety net (undo agent commits) is now handled inside sandbox.collect_changes().

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

        mock_sandbox = AsyncMock()
        mock_sandbox.snapshot = AsyncMock(return_value="abc123")
        mock_sandbox.collect_changes = AsyncMock(return_value=["a.py"])
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

        # Sandbox degrades gracefully: no pre_exec_head → collect returns []
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
        # Backend reports one set of files...
        result = _make_execution_result(files_changed=["backend_file.py"])
        backend = MockBackend(result)
        # ...but sandbox reports a different set (the real git diff)
        sandbox_files = ["sandbox_file_a.py", "sandbox_file_b.py"]

        mock_sandbox = AsyncMock()
        mock_sandbox.snapshot = AsyncMock(return_value="abc123")
        mock_sandbox.collect_changes = AsyncMock(return_value=sandbox_files)
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
        assert complete["data"]["files_changed"] == sandbox_files
        # Sandbox files, NOT backend files
        assert "backend_file.py" not in complete["data"]["files_changed"]

    @pytest.mark.asyncio
    async def test_files_changed_from_sandbox_stored_in_plan(self):
        """files_changed from sandbox is stored in plan.execution.files_changed."""
        plan = _make_plan()
        sandbox_files = ["src/module.py", "tests/test_module.py"]

        mock_sandbox = AsyncMock()
        mock_sandbox.snapshot = AsyncMock(return_value="abc123")
        mock_sandbox.collect_changes = AsyncMock(return_value=sandbox_files)
        mock_sandbox.revert = AsyncMock()

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

        mock_sandbox = AsyncMock()
        mock_sandbox.snapshot = AsyncMock(return_value="abc123")
        mock_sandbox.collect_changes = AsyncMock(return_value=sandbox_files)
        mock_sandbox.revert = AsyncMock()

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


# ============================================================================
# TEST: UNEXPECTED EXCEPTION PERSISTS FAILED STATUS (Commit 1)
# ============================================================================


class TestUnexpectedExceptionPersistsFailedStatus:
    """When an unexpected exception occurs mid-execution, plan must be saved as 'failed'."""

    @pytest.mark.asyncio
    async def test_unexpected_exception_sets_plan_failed(self):
        """If an exception occurs after marking 'executing', plan is saved as 'failed'."""
        plan = _make_plan()
        saved_plans = []

        def capture_save(p):
            saved_plans.append(p.model_copy(deep=True))

        # Backend that raises an unexpected exception during execute()
        class ExplodingBackend:
            name = "exploding"

            def abort(self):
                pass

            async def execute(self, instruction, cwd, model, on_step):
                raise RuntimeError("Unexpected DB error")

        with (
            _patch_load_plan(plan),
            patch("autocode.core.planning.executor.save_plan", side_effect=capture_save),
            _patch_backend(ExplodingBackend()),
            _patch_getcwd(),
        ):
            events = await _collect_events(
                stream_execute_plan("20260101-120000", backend="exploding")
            )

        error = _find_event(events, "error")
        assert error is not None
        assert "Unexpected DB error" in error["data"]["message"]

        # THE KEY ASSERTION: plan must NOT stay stuck in 'executing'
        assert saved_plans[-1].status == "failed", (
            f"Plan should be saved as 'failed', got '{saved_plans[-1].status}'. "
            "A zombie plan stuck in 'executing' can never be re-executed."
        )
        assert saved_plans[-1].execution is not None
        assert saved_plans[-1].execution.completed_at != "", (
            "completed_at should be set when plan fails with unexpected exception"
        )
        assert saved_plans[-1].execution.error == "Unexpected DB error", (
            "The error message should be stored in plan.execution.error"
        )

    @pytest.mark.asyncio
    async def test_unexpected_exception_before_sandbox_still_fails_plan(self):
        """Exception before sandbox setup still marks plan as failed."""
        plan = _make_plan()
        saved_plans = []

        def capture_save(p):
            saved_plans.append(p.model_copy(deep=True))

        with (
            _patch_load_plan(plan),
            patch("autocode.core.planning.executor.save_plan", side_effect=capture_save),
            _patch_backend(MockBackend()),
            patch(
                "autocode.core.planning.executor.ExecutionSandbox",
                side_effect=RuntimeError("Git not found"),
            ),
            _patch_getcwd(),
        ):
            events = await _collect_events(
                stream_execute_plan("20260101-120000", backend="mock")
            )

        error = _find_event(events, "error")
        assert error is not None

        # Plan should be saved as failed, not left in 'executing'
        assert saved_plans[-1].status == "failed", (
            f"Plan should be saved as 'failed', got '{saved_plans[-1].status}'. "
            "Exception before sandbox still must not leave plan stuck in 'executing'."
        )
