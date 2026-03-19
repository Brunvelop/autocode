"""
Tests for executor FSM transitions and review modes.

Covers:
- FSM: draft → executing → pending_review / completed / failed
- Review mode human → pending_review
- Review mode auto approved → completed + commit
- Review mode auto rejected → pending_review
- _run_review_flow yields only SSE strings (no mixed types)
"""

from unittest.mock import patch

import pytest

from autocode.core.planning.models import PlanExecutionState
from autocode.core.planning.executor import stream_execute_plan
from tests.unit.core.planning.conftest import (
    _make_plan,
    _collect_events,
    _find_event,
    MockBackend,
    _patch_load_plan,
    _patch_save_plan,
    _patch_backend,
    _patch_auto_review,
    _patch_compute_review_metrics,
    _patch_git_add_and_commit,
    _patch_getcwd,
    _patch_sandbox,
)


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
        from tests.unit.core.planning.conftest import _make_execution_result
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
# TEST: REVIEW FLOW YIELDS ONLY STRINGS — NO MIXED TYPES
# ============================================================================


class TestReviewFlowNoMixedTypes:
    """_run_review_flow should only yield SSE strings, not dicts."""

    @pytest.mark.asyncio
    async def test_review_flow_only_yields_strings(self):
        """Every item yielded by _run_review_flow must be a string (SSE event)."""
        from autocode.core.planning.executor import _run_review_flow

        plan = _make_plan()
        plan.execution = PlanExecutionState(started_at="2026-01-01T12:00:00")

        with (
            _patch_compute_review_metrics(),
            _patch_auto_review(verdict="approved"),
            _patch_git_add_and_commit("abc"),
            _patch_save_plan(),
        ):
            items = []
            async for item in _run_review_flow(plan, "auto", ["a.py"]):
                items.append(item)

        for item in items:
            assert isinstance(item, str), (
                f"_run_review_flow should only yield strings (SSE events), "
                f"got {type(item)}: {item!r}"
            )

    @pytest.mark.asyncio
    async def test_commit_hash_read_from_plan_after_review(self):
        """After review flow, commit_hash is available via plan.execution.commit_hash."""
        plan = _make_plan()
        backend = MockBackend()

        with (
            _patch_load_plan(plan),
            _patch_save_plan(),
            _patch_backend(backend),
            _patch_auto_review(verdict="approved"),
            _patch_git_add_and_commit("commit-from-plan"),
            _patch_getcwd(),
            _patch_sandbox(["src/api.py"]),
        ):
            events = await _collect_events(
                stream_execute_plan("20260101-120000", backend="mock", review_mode="auto")
            )

        complete = _find_event(events, "plan_complete")
        assert complete is not None
        assert complete["data"]["commit_hash"] == "commit-from-plan"
