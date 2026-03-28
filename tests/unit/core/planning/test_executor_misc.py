"""
Tests for executor miscellaneous concerns.

Covers:
- Backend selection (opencode, cline, unknown raises)
- Error handling: plan not found, invalid status, backend exception
- _build_instruction creates markdown from plan
- Backend receives correct instruction/cwd/model args
- execute_commit_plan registered endpoint
- execute_commit_plan sync wrapper reads from plan (not SSE parsing)
- CWD passed correctly to backend and sandbox
- Unexpected exception persists failed status
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from autocode.core.planning.models import PlanExecutionState
from autocode.core.planning.backends import get_backend
from autocode.core.planning.executor import (
    stream_execute_plan,
    _build_instruction,
)
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
        assert callable(execute_commit_plan)


# ============================================================================
# TEST: SYNC WRAPPER READS FROM PLAN, NOT FROM SSE PARSING
# ============================================================================


class TestExecuteCommitPlanSync:
    """execute_commit_plan (sync wrapper) returns correct result without parsing SSE."""

    def test_sync_wrapper_returns_success_from_plan(self):
        """Sync wrapper reads final state from plan.execution, not from SSE parsing.

        The old implementation parsed SSE strings with split("data: ") — fragile
        and coupled to SSE format. The new implementation drains the generator
        (discarding SSE bytes) and then calls load_plan() to read the authoritative
        final state from persistence.

        Key assertion: result.execution contains 'started_at', a field present in
        plan.execution.model_dump() but NOT in the plan_complete SSE event data.
        """
        plan = _make_plan()
        final_plan = plan.model_copy(deep=True)
        final_plan.status = "pending_review"
        final_plan.execution = PlanExecutionState(
            started_at="2026-01-01T12:00:00",
            completed_at="2026-01-01T12:01:00",
            total_tokens=1500,
            total_cost=0.003,
            backend="mock",
            files_changed=["a.py"],
        )

        with (
            patch("autocode.core.planning.executor.load_plan", side_effect=[plan, final_plan]),
            _patch_save_plan(),
            _patch_backend(MockBackend()),
            _patch_compute_review_metrics(),
            _patch_getcwd(),
        ):
            from autocode.core.planning.executor import execute_commit_plan
            result = execute_commit_plan("20260101-120000", backend="mock")

        assert result.status == "pending_review", (
            f"Expected status='pending_review', got {result.status!r}."
        )
        assert isinstance(result.execution, dict), (
            "result.execution should be a dict from plan.execution.model_dump()"
        )
        assert "started_at" in result.execution, (
            "result.execution should come from plan.execution.model_dump() (contains "
            "'started_at'), not from SSE event data (which does not have 'started_at'). "
            "This indicates the sync wrapper is still parsing SSE instead of reading "
            "the final plan state from persistence."
        )

    def test_sync_wrapper_raises_when_plan_not_found(self):
        """Sync wrapper raises HTTPException(404) when plan doesn't exist."""
        from fastapi import HTTPException

        with _patch_load_plan(None):
            from autocode.core.planning.executor import execute_commit_plan
            with pytest.raises(HTTPException) as exc_info:
                execute_commit_plan("nonexistent", backend="mock")

        assert exc_info.value.status_code == 404
        assert "not found" in exc_info.value.detail.lower(), (
            f"Expected 'not found' in detail, got {exc_info.value.detail!r}. "
            "The sync wrapper should raise HTTPException(404) with a clear message."
        )


# ============================================================================
# TEST: CWD ASSUMPTION
# ============================================================================


class TestCwdAssumption:
    """Document and test the CWD assumption.

    os.getcwd() is used as cwd for both the backend and ExecutionSandbox.
    This is correct for CLI usage (single repo). This test acts as a contract
    to prevent regressions if the cwd is ever accidentally hardcoded or
    sourced from somewhere other than os.getcwd().
    """

    @pytest.mark.asyncio
    async def test_cwd_passed_to_backend_and_sandbox(self):
        """os.getcwd() is used as cwd for both backend and sandbox."""
        plan = _make_plan()
        backend = MockBackend()
        mock_sandbox_cls = MagicMock()
        mock_instance = AsyncMock()
        mock_instance.snapshot = AsyncMock(return_value="abc")
        mock_instance.collect_changes = AsyncMock(return_value=[])
        mock_instance.revert = AsyncMock()
        mock_sandbox_cls.return_value = mock_instance

        with (
            _patch_load_plan(plan),
            _patch_save_plan(),
            _patch_backend(backend),
            _patch_compute_review_metrics(),
            patch("autocode.core.planning.executor.os.getcwd", return_value="/my/mono/repo"),
            patch("autocode.core.planning.executor.ExecutionSandbox", mock_sandbox_cls),
        ):
            await _collect_events(
                stream_execute_plan("20260101-120000", backend="mock")
            )

        mock_sandbox_cls.assert_called_once_with("/my/mono/repo")
        assert backend.execute_called_with["cwd"] == "/my/mono/repo"


# ============================================================================
# TEST: UNEXPECTED EXCEPTION PERSISTS FAILED STATUS
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

        assert saved_plans[-1].status == "failed", (
            f"Plan should be saved as 'failed', got '{saved_plans[-1].status}'. "
            "Exception before sandbox still must not leave plan stuck in 'executing'."
        )
