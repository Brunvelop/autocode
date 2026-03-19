"""
Tests for executor cancel/abort support.

Covers:
- Closing generator mid-execution calls backend.abort()
- abort() NOT called when execution completes normally
- sandbox.revert() called on cancel (git reset --hard)
- Plan saved as 'failed' on cancel
- completed_at timestamp set on cancel
"""

import asyncio
from unittest.mock import AsyncMock, patch

import pytest

from autocode.core.planning.models import ExecutionStep
from autocode.core.planning.executor import stream_execute_plan
from tests.unit.core.planning.conftest import (
    _make_plan,
    _make_execution_result,
    _collect_events,
    MockBackend,
    _patch_load_plan,
    _patch_save_plan,
    _patch_backend,
    _patch_compute_review_metrics,
    _patch_getcwd,
    _parse_sse,
)


# ============================================================================
# CANCEL HELPERS
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
            except (Exception,):
                pass
        await gen.aclose()


# ============================================================================
# TEST: CANCEL / ABORT SUPPORT
# ============================================================================


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
                except (Exception,):
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
                except (Exception,):
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
                except (Exception,):
                    pass
            await gen.aclose()

        last_saved = saved_plans[-1]
        assert last_saved.execution is not None
        assert last_saved.execution.completed_at is not None, (
            "completed_at should be set when plan is cancelled"
        )
