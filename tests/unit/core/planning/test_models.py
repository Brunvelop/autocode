"""
Tests for extended planning models with execution state.

RED phase: These tests define the expected behavior for:
- Extended PlanStatus with executing/completed/failed states
- TaskExecutionResult model
- PlanExecutionState model
- CommitPlan.execution field
"""

import pytest
from pydantic import ValidationError

from autocode.core.planning.models import (
    CommitPlan,
    CommitPlanSummary,
    TaskExecutionResult,
    PlanExecutionState,
    ReviewFileMetrics,
    ReviewResult,
)


class TestPlanStatusExtended:
    """Tests for extended PlanStatus with execution states."""

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


class TestTaskExecutionResult:
    """Tests for TaskExecutionResult model."""

    def test_default_values(self):
        """TaskExecutionResult tiene defaults razonables."""
        result = TaskExecutionResult(task_index=0)
        assert result.task_index == 0
        assert result.status == "pending"
        assert result.error == ""
        assert result.llm_summary == ""
        assert result.files_changed == []
        assert result.prompt_tokens == 0
        assert result.completion_tokens == 0
        assert result.total_tokens == 0
        assert result.total_cost == 0.0

    def test_all_fields(self):
        """TaskExecutionResult acepta todos los campos."""
        result = TaskExecutionResult(
            task_index=2,
            status="completed",
            started_at="2026-01-01T00:00:00",
            completed_at="2026-01-01T00:01:00",
            llm_summary="Added new function",
            files_changed=["src/main.py", "src/utils.py"],
        )
        assert result.status == "completed"
        assert len(result.files_changed) == 2

    def test_status_literals(self):
        """TaskExecutionResult.status solo acepta pending/running/completed/failed/skipped."""
        for valid in ("pending", "running", "completed", "failed", "skipped"):
            r = TaskExecutionResult(task_index=0, status=valid)
            assert r.status == valid

        with pytest.raises(ValidationError):
            TaskExecutionResult(task_index=0, status="unknown")


class TestPlanExecutionState:
    """Tests for PlanExecutionState model."""

    def test_default_values(self):
        """PlanExecutionState tiene defaults vacíos."""
        state = PlanExecutionState()
        assert state.started_at == ""
        assert state.completed_at == ""
        assert state.model_used == ""
        assert state.task_results == []
        assert state.commit_hash == ""
        assert state.total_tokens == 0
        assert state.total_cost == 0.0

    def test_with_task_results(self):
        """PlanExecutionState contiene TaskExecutionResult list."""
        state = PlanExecutionState(
            started_at="2026-01-01T00:00:00",
            model_used="openrouter/openai/gpt-4o",
            task_results=[
                TaskExecutionResult(task_index=0, status="completed"),
                TaskExecutionResult(task_index=1, status="failed", error="Syntax error"),
            ],
        )
        assert len(state.task_results) == 2
        assert state.task_results[1].error == "Syntax error"


class TestCommitPlanExecution:
    """Tests for CommitPlan.execution field."""

    def test_execution_default_none(self):
        """CommitPlan.execution es None por defecto."""
        plan = CommitPlan(id="test", title="test")
        assert plan.execution is None

    def test_execution_roundtrip_json(self):
        """CommitPlan con execution serializa/deserializa correctamente."""
        plan = CommitPlan(
            id="test",
            title="test",
            status="completed",
            execution=PlanExecutionState(
                started_at="2026-01-01T00:00:00",
                model_used="gpt-4o",
                task_results=[TaskExecutionResult(task_index=0, status="completed")],
                commit_hash="abc123",
            ),
        )
        json_str = plan.model_dump_json()
        restored = CommitPlan.model_validate_json(json_str)
        assert restored.execution is not None
        assert restored.execution.commit_hash == "abc123"
        assert restored.execution.task_results[0].status == "completed"

    def test_plan_summary_new_statuses(self):
        """CommitPlanSummary acepta los nuevos estados."""
        for status in ("executing", "completed", "failed"):
            s = CommitPlanSummary(id="t", title="t", status=status)
            assert s.status == status


class TestReviewModels:
    """Tests for review-related models: ReviewFileMetrics, ReviewResult, and new PlanStatus states."""

    def test_plan_status_includes_pending_review(self):
        """PlanStatus acepta 'pending_review'."""
        plan = CommitPlan(id="test", title="test", status="pending_review")
        assert plan.status == "pending_review"

    def test_plan_status_includes_pending_commit(self):
        """PlanStatus acepta 'pending_commit'."""
        plan = CommitPlan(id="test", title="test", status="pending_commit")
        assert plan.status == "pending_commit"

    def test_plan_status_includes_reverted(self):
        """PlanStatus acepta 'reverted'."""
        plan = CommitPlan(id="test", title="test", status="reverted")
        assert plan.status == "reverted"

    def test_plan_summary_accepts_review_states(self):
        """CommitPlanSummary acepta los nuevos estados de review."""
        for status in ("pending_review", "pending_commit", "reverted"):
            s = CommitPlanSummary(id="t", title="t", status=status)
            assert s.status == status

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
        # Archivo nuevo: no tiene before
        new_file = ReviewFileMetrics(
            path="src/new.py",
            before={},
            after={"sloc": 50, "avg_complexity": 2.0},
            deltas={"delta_sloc": 50},
        )
        assert new_file.before == {}
        assert new_file.after["sloc"] == 50

        # Archivo eliminado: no tiene after
        deleted = ReviewFileMetrics(
            path="src/old.py",
            before={"sloc": 30},
            after={},
            deltas={"delta_sloc": -30},
        )
        assert deleted.after == {}

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
        """ReviewResult acepta verdict='approved'."""
        r = ReviewResult(mode="auto", verdict="approved")
        assert r.verdict == "approved"

    def test_review_result_verdict_rejected(self):
        """ReviewResult acepta verdict='rejected'."""
        r = ReviewResult(mode="auto", verdict="rejected")
        assert r.verdict == "rejected"

    def test_review_result_verdict_needs_changes(self):
        """ReviewResult acepta verdict='needs_changes'."""
        r = ReviewResult(mode="human", verdict="needs_changes")
        assert r.verdict == "needs_changes"

    def test_review_result_verdict_rejects_invalid(self):
        """ReviewResult rechaza verdicts inválidos."""
        with pytest.raises(ValidationError):
            ReviewResult(mode="auto", verdict="maybe")

    def test_review_result_mode_rejects_invalid(self):
        """ReviewResult rechaza modes inválidos."""
        with pytest.raises(ValidationError):
            ReviewResult(mode="invalid_mode", verdict="approved")

    def test_plan_execution_state_has_review(self):
        """PlanExecutionState.review es Optional[ReviewResult], default None."""
        state = PlanExecutionState()
        assert state.review is None

    def test_plan_execution_state_with_review(self):
        """PlanExecutionState acepta un ReviewResult."""
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
