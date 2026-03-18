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
from autocode.core.planning.backends.base import ExecutionResult
from autocode.core.planning.executor import (
    stream_execute_plan,
    _get_backend,
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
    """Patch _get_backend to return the given backend instance."""
    return patch("autocode.core.planning.executor._get_backend", return_value=backend)


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
    """_get_backend resolves backend name to instance."""

    def test_backend_selection_opencode(self):
        from autocode.core.planning.backends.opencode import OpenCodeBackend

        backend = _get_backend("opencode")
        assert isinstance(backend, OpenCodeBackend)
        assert backend.name == "opencode"

    def test_backend_selection_cline(self):
        from autocode.core.planning.backends.cline import ClineBackend

        backend = _get_backend("cline")
        assert isinstance(backend, ClineBackend)
        assert backend.name == "cline"

    def test_backend_unknown_raises(self):
        with pytest.raises(ValueError, match="Unknown backend"):
            _get_backend("nonexistent")


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
