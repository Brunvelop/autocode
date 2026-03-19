"""
Tests for executor SSE event emission.

Covers:
- plan_start event (plan_id, title, backend, model)
- step events forwarded from backend
- real-time streaming (not batch)
- plan_complete with success / failure
- review_start includes files_changed
- event ordering
"""

import asyncio
import time
from typing import List
from unittest.mock import patch

import pytest

from autocode.core.planning.models import ExecutionStep
from autocode.core.planning.executor import stream_execute_plan
from tests.unit.core.planning.conftest import (
    _make_plan,
    _make_execution_result,
    _collect_events,
    _find_event,
    _find_events,
    MockBackend,
    _patch_load_plan,
    _patch_save_plan,
    _patch_backend,
    _patch_compute_review_metrics,
    _patch_getcwd,
    _patch_sandbox,
    _parse_sse,
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
                except (Exception,):
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
        gap = event_arrival_times[1] - event_arrival_times[0]
        assert gap >= step_delay * 0.5, (
            f"Steps should arrive incrementally (gap={gap*1000:.1f}ms), "
            f"not in batch (expected ≥{step_delay * 0.5 * 1000:.0f}ms). "
            f"This indicates steps are being batched instead of streamed in real-time."
        )

    @pytest.mark.asyncio
    async def test_step_sse_emitted_before_backend_returns(self):
        """Step SSE events are available to consumers before execute() returns."""
        plan = _make_plan()
        backend_completed = asyncio.Event()
        step1_received_before_backend_done = False

        step1 = ExecutionStep(type="thinking", content="Early step")
        result = _make_execution_result(steps=[step1])

        class SlowMockBackend:
            name = "mock"

            async def execute(self, instruction, cwd, model, on_step):
                await on_step(step1)
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
                        if not backend_completed.is_set():
                            step1_received_before_backend_done = True
                except (Exception,):
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
        assert event_types[0] == "plan_start"
        assert event_types[-1] == "plan_complete"
        if "review_start" in event_types:
            assert event_types.index("review_start") < event_types.index("review_complete")
        step_indices = [i for i, t in enumerate(event_types) if t == "step"]
        if step_indices and "review_start" in event_types:
            assert max(step_indices) < event_types.index("review_start")
