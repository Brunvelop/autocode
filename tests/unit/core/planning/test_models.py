"""
Tests for simplified planning models.

Commit 1 (RED): These tests define the expected behavior for:
- ExecutionStep (NEW — replaces TaskExecutionResult)
- Simplified CommitPlan (no tasks, context, tags, conversation_log)
- PlanExecutionState with steps/backend/session_id (no task_results)
- CommitPlanSummary without tasks_count
- PlanStatus without pending_commit
"""

import pytest
from pydantic import ValidationError

from autocode.core.planning.models import (
    CommitPlan,
    CommitPlanSummary,
    ExecutionStep,
    PlanExecutionState,
    ReviewFileMetrics,
    ReviewResult,
)


# ── ExecutionStep (NEW) ─────────────────────────────────────────────────────


class TestExecutionStep:
    """Tests for the new ExecutionStep model that replaces TaskExecutionResult."""

    def test_default_values(self):
        """ExecutionStep has sensible empty defaults for all fields."""
        step = ExecutionStep()
        assert step.timestamp == ""
        assert step.type == ""
        assert step.content == ""
        assert step.tool == ""
        assert step.path == ""

    def test_all_fields(self):
        """ExecutionStep accepts all fields."""
        step = ExecutionStep(
            timestamp="2026-01-01T00:00:00",
            type="tool_use",
            content="Reading file contents",
            tool="read_file",
            path="src/main.py",
        )
        assert step.timestamp == "2026-01-01T00:00:00"
        assert step.type == "tool_use"
        assert step.content == "Reading file contents"
        assert step.tool == "read_file"
        assert step.path == "src/main.py"

    def test_type_accepts_any_string(self):
        """ExecutionStep.type is a free-form string — not a restricted Literal."""
        for step_type in ("tool_use", "thinking", "text", "error"):
            step = ExecutionStep(type=step_type)
            assert step.type == step_type

        # Also accepts arbitrary types (future-proof)
        step = ExecutionStep(type="custom_event")
        assert step.type == "custom_event"


# ── PlanStatus ───────────────────────────────────────────────────────────────


class TestPlanStatusExtended:
    """Tests for PlanStatus — executing, completed, failed are valid; pending_commit is NOT."""

    def test_plan_status_includes_executing(self):
        """PlanStatus Literal acepta 'executing'."""
        plan = CommitPlan(id="test", title="test", status="executing")
        assert plan.status == "executing"

    def test_plan_status_includes_completed(self):
        """PlanStatus Literal acepta 'completed'."""
        plan = CommitPlan(id="test", title="test", status="completed")
        assert plan.status == "completed"

    def test_plan_status_includes_failed(self):
        """PlanStatus Literal acepta 'failed'."""
        plan = CommitPlan(id="test", title="test", status="failed")
        assert plan.status == "failed"

    def test_plan_status_rejects_invalid(self):
        """PlanStatus rechaza valores inválidos (Pydantic ValidationError)."""
        with pytest.raises(ValidationError):
            CommitPlan(id="test", title="test", status="invalid_status")

    def test_plan_status_rejects_pending_commit(self):
        """'pending_commit' is removed from PlanStatus — must be rejected."""
        with pytest.raises(ValidationError):
            CommitPlan(id="test", title="test", status="pending_commit")


# ── PlanExecutionState ───────────────────────────────────────────────────────


class TestPlanExecutionState:
    """Tests for PlanExecutionState with steps, backend, and session_id."""

    def test_default_values(self):
        """PlanExecutionState has sensible empty defaults."""
        state = PlanExecutionState()
        assert state.started_at == ""
        assert state.completed_at == ""
        assert state.model_used == ""
        assert state.commit_hash == ""
        assert state.total_tokens == 0
        assert state.total_cost == 0.0
        assert state.files_changed == []
        assert state.review is None

    def test_has_steps_list(self):
        """PlanExecutionState has a 'steps' field (List[ExecutionStep])."""
        state = PlanExecutionState()
        assert state.steps == []

    def test_has_backend_field(self):
        """PlanExecutionState has a 'backend' string field."""
        state = PlanExecutionState()
        assert state.backend == ""

    def test_has_session_id(self):
        """PlanExecutionState has a 'session_id' string field."""
        state = PlanExecutionState()
        assert state.session_id == ""

    def test_with_steps(self):
        """PlanExecutionState with steps roundtrips correctly."""
        steps = [
            ExecutionStep(type="thinking", content="Analyzing..."),
            ExecutionStep(type="tool_use", tool="read_file", path="src/api.py"),
            ExecutionStep(type="tool_use", tool="write_file", path="src/api.py", content="Updated"),
        ]
        state = PlanExecutionState(
            started_at="2026-01-01T00:00:00",
            model_used="openrouter/openai/gpt-4o",
            backend="opencode",
            session_id="sess-123",
            steps=steps,
        )
        assert len(state.steps) == 3
        assert state.steps[0].type == "thinking"
        assert state.steps[1].tool == "read_file"
        assert state.steps[2].path == "src/api.py"
        assert state.backend == "opencode"
        assert state.session_id == "sess-123"


# ── CommitPlan (simplified) ──────────────────────────────────────────────────


class TestCommitPlanSimplified:
    """Tests verifying removed fields no longer exist on CommitPlan."""

    def test_no_tasks_field(self):
        """CommitPlan no longer has a 'tasks' attribute."""
        plan = CommitPlan(id="test", title="test")
        assert not hasattr(plan, "tasks")

    def test_no_context_field(self):
        """CommitPlan no longer has a 'context' attribute."""
        plan = CommitPlan(id="test", title="test")
        assert not hasattr(plan, "context")

    def test_no_tags_field(self):
        """CommitPlan no longer has a 'tags' attribute."""
        plan = CommitPlan(id="test", title="test")
        assert not hasattr(plan, "tags")

    def test_no_conversation_log_field(self):
        """CommitPlan no longer has a 'conversation_log' attribute."""
        plan = CommitPlan(id="test", title="test")
        assert not hasattr(plan, "conversation_log")

    def test_description_is_freeform(self):
        """description accepts long markdown content (freeform instructions)."""
        long_desc = """## Overview
This commit refactors the API layer to use the new backend protocol.

### Changes
- Replace direct subprocess calls with `ExecutorBackend.execute()`
- Add proper error handling for backend failures
- Update SSE events to use simplified step format

### Notes
The DSPy backend is preserved as a legacy option.
"""
        plan = CommitPlan(id="test", title="Refactor API", description=long_desc)
        assert "ExecutorBackend" in plan.description
        assert plan.description.startswith("## Overview")


# ── CommitPlanExecution ──────────────────────────────────────────────────────


class TestCommitPlanExecution:
    """Tests for CommitPlan.execution field with new step-based state."""

    def test_execution_default_none(self):
        """CommitPlan.execution es None por defecto."""
        plan = CommitPlan(id="test", title="test")
        assert plan.execution is None

    def test_execution_roundtrip_json(self):
        """CommitPlan with execution (steps + backend) serializes/deserializes."""
        plan = CommitPlan(
            id="test",
            title="test",
            status="completed",
            execution=PlanExecutionState(
                started_at="2026-01-01T00:00:00",
                model_used="gpt-4o",
                backend="opencode",
                session_id="sess-abc",
                steps=[
                    ExecutionStep(type="thinking", content="Planning changes"),
                    ExecutionStep(type="tool_use", tool="write_file", path="src/main.py"),
                ],
                commit_hash="abc123",
                total_tokens=1500,
                total_cost=0.05,
            ),
        )
        json_str = plan.model_dump_json()
        restored = CommitPlan.model_validate_json(json_str)
        assert restored.execution is not None
        assert restored.execution.commit_hash == "abc123"
        assert restored.execution.backend == "opencode"
        assert restored.execution.session_id == "sess-abc"
        assert len(restored.execution.steps) == 2
        assert restored.execution.steps[0].type == "thinking"
        assert restored.execution.steps[1].tool == "write_file"
        assert restored.execution.total_tokens == 1500
        assert restored.execution.total_cost == 0.05

    def test_plan_summary_new_statuses(self):
        """CommitPlanSummary acepta los nuevos estados."""
        for status in ("executing", "completed", "failed"):
            s = CommitPlanSummary(id="t", title="t", status=status)
            assert s.status == status


# ── CommitPlanSummary ────────────────────────────────────────────────────────


class TestCommitPlanSummary:
    """Tests for CommitPlanSummary — simplified without tasks_count."""

    def test_no_tasks_count_field(self):
        """CommitPlanSummary no longer has 'tasks_count'."""
        summary = CommitPlanSummary(id="t", title="t", status="draft")
        assert not hasattr(summary, "tasks_count")

    def test_summary_has_core_fields(self):
        """CommitPlanSummary still has id, title, status, created_at, branch."""
        summary = CommitPlanSummary(
            id="20260101-120000",
            title="Add feature X",
            status="ready",
            created_at="2026-01-01T12:00:00",
            branch="main",
        )
        assert summary.id == "20260101-120000"
        assert summary.title == "Add feature X"
        assert summary.status == "ready"
        assert summary.created_at == "2026-01-01T12:00:00"
        assert summary.branch == "main"


# ── Review Models (unchanged) ───────────────────────────────────────────────


class TestReviewModels:
    """Tests for review-related models — mostly unchanged from before."""

    def test_plan_status_includes_pending_review(self):
        """PlanStatus acepta 'pending_review'."""
        plan = CommitPlan(id="test", title="test", status="pending_review")
        assert plan.status == "pending_review"

    def test_plan_status_includes_reverted(self):
        """PlanStatus acepta 'reverted'."""
        plan = CommitPlan(id="test", title="test", status="reverted")
        assert plan.status == "reverted"

    def test_plan_summary_accepts_review_states(self):
        """CommitPlanSummary acepta review states (without pending_commit)."""
        for status in ("pending_review", "reverted"):
            s = CommitPlanSummary(id="t", title="t", status=status)
            assert s.status == status


class TestReviewFileMetrics:
    """Tests for ReviewFileMetrics — unchanged."""

    def test_review_file_metrics_creation(self):
        """ReviewFileMetrics se crea con path, before, after y deltas."""
        metrics = ReviewFileMetrics(
            path="src/main.py",
            before={"sloc": 100, "avg_complexity": 3.0, "max_complexity": 8, "mi": 72.5, "functions_count": 10},
            after={"sloc": 120, "avg_complexity": 3.5, "max_complexity": 9, "mi": 68.0, "functions_count": 12},
            deltas={"delta_sloc": 20, "delta_avg_complexity": 0.5, "delta_max_complexity": 1, "delta_mi": -4.5, "delta_functions_count": 2},
        )
        assert metrics.path == "src/main.py"
        assert metrics.before["sloc"] == 100
        assert metrics.after["sloc"] == 120
        assert metrics.deltas["delta_sloc"] == 20
        assert metrics.deltas["delta_mi"] == -4.5

    def test_review_file_metrics_empty_dicts(self):
        """ReviewFileMetrics acepta dicts vacíos (archivo nuevo o eliminado)."""
        new_file = ReviewFileMetrics(
            path="src/new.py",
            before={},
            after={"sloc": 50, "avg_complexity": 2.0},
            deltas={"delta_sloc": 50},
        )
        assert new_file.before == {}
        assert new_file.after["sloc"] == 50

        deleted = ReviewFileMetrics(
            path="src/old.py",
            before={"sloc": 30},
            after={},
            deltas={"delta_sloc": -30},
        )
        assert deleted.after == {}


class TestReviewResult:
    """Tests for ReviewResult — unchanged."""

    def test_review_result_creation(self):
        """ReviewResult se crea con todos los campos."""
        result = ReviewResult(
            mode="auto",
            verdict="approved",
            summary="All quality gates passed",
            issues=["Minor: function too long in utils.py"],
            suggestions=["Consider splitting into smaller functions"],
            file_metrics=[
                ReviewFileMetrics(
                    path="src/utils.py",
                    before={"sloc": 80},
                    after={"sloc": 95},
                    deltas={"delta_sloc": 15},
                ),
            ],
            quality_gates={"complexity_increase": True, "mi_minimum": True},
            reviewed_at="2026-01-01T12:00:00",
            reviewed_by="auto",
        )
        assert result.mode == "auto"
        assert result.verdict == "approved"
        assert result.summary == "All quality gates passed"
        assert len(result.issues) == 1
        assert len(result.suggestions) == 1
        assert len(result.file_metrics) == 1
        assert result.quality_gates["complexity_increase"] is True
        assert result.reviewed_by == "auto"

    def test_review_result_defaults(self):
        """ReviewResult tiene defaults razonables para campos opcionales."""
        result = ReviewResult(mode="human", verdict="approved")
        assert result.summary == ""
        assert result.issues == []
        assert result.suggestions == []
        assert result.file_metrics == []
        assert result.quality_gates == {}
        assert result.reviewed_at == ""
        assert result.reviewed_by == ""

    def test_review_result_verdict_approved(self):
        r = ReviewResult(mode="auto", verdict="approved")
        assert r.verdict == "approved"

    def test_review_result_verdict_rejected(self):
        r = ReviewResult(mode="auto", verdict="rejected")
        assert r.verdict == "rejected"

    def test_review_result_verdict_needs_changes(self):
        r = ReviewResult(mode="human", verdict="needs_changes")
        assert r.verdict == "needs_changes"

    def test_review_result_verdict_rejects_invalid(self):
        with pytest.raises(ValidationError):
            ReviewResult(mode="auto", verdict="maybe")

    def test_review_result_mode_rejects_invalid(self):
        with pytest.raises(ValidationError):
            ReviewResult(mode="invalid_mode", verdict="approved")

    def test_plan_execution_state_has_review(self):
        state = PlanExecutionState()
        assert state.review is None

    def test_plan_execution_state_with_review(self):
        review = ReviewResult(
            mode="auto",
            verdict="approved",
            summary="All good",
            quality_gates={"complexity_increase": True},
        )
        state = PlanExecutionState(review=review)
        assert state.review is not None
        assert state.review.verdict == "approved"
        assert state.review.quality_gates["complexity_increase"] is True

    def test_review_result_roundtrip_json(self):
        """ReviewResult serializa/deserializa correctamente via CommitPlan."""
        plan = CommitPlan(
            id="test-review",
            title="test review roundtrip",
            status="pending_review",
            execution=PlanExecutionState(
                started_at="2026-01-01T00:00:00",
                review=ReviewResult(
                    mode="auto",
                    verdict="rejected",
                    issues=["Complexity too high"],
                    file_metrics=[
                        ReviewFileMetrics(
                            path="src/main.py",
                            before={"sloc": 100},
                            after={"sloc": 150},
                            deltas={"delta_sloc": 50},
                        ),
                    ],
                    quality_gates={"complexity_increase": False},
                ),
            ),
        )
        json_str = plan.model_dump_json()
        restored = CommitPlan.model_validate_json(json_str)
        assert restored.status == "pending_review"
        assert restored.execution.review.verdict == "rejected"
        assert restored.execution.review.issues == ["Complexity too high"]
        assert len(restored.execution.review.file_metrics) == 1
        assert restored.execution.review.file_metrics[0].path == "src/main.py"
        assert restored.execution.review.quality_gates["complexity_increase"] is False
