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
