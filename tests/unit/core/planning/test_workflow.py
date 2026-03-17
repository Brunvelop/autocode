"""
Tests for workflow.py — approve/revert/review_metrics operations.

These operations are extracted from planner.py into a dedicated workflow module
that handles git-related operations (approve, revert) and review metrics retrieval.

RED phase: autocode.core.planning.workflow does NOT exist yet.
These tests will fail with ImportError until the module is created.
"""
import json
from unittest.mock import patch

import pytest

from autocode.core.planning.workflow import (
    approve_plan,
    revert_plan,
    get_plan_review_metrics,
)
from autocode.core.planning.models import (
    CommitPlan,
    PlanExecutionState,
    TaskExecutionResult,
    ReviewResult,
    ReviewFileMetrics,
)


# ==============================================================================
# TESTS: approve_plan (workflow)
# ==============================================================================


class TestApprovePlanWorkflow:
    """Tests for approve_plan imported from workflow module.

    Verifies that a plan in pending_review can be approved,
    which triggers git add + commit and transitions to completed.
    """

    def _create_pending_review_plan(self, tmp_path, plan_id="20260501-120000",
                                     title="feat: add feature",
                                     files_changed=None,
                                     parent_commit="abc123"):
        """Helper: creates a plan JSON in tmp_path with status=pending_review."""
        if files_changed is None:
            files_changed = ["src/main.py", "src/utils.py"]
        plan_data = {
            "id": plan_id,
            "title": title,
            "status": "pending_review",
            "parent_commit": parent_commit,
            "branch": "main",
            "tasks": [
                {"type": "modify", "path": "src/main.py", "description": "Add feature"},
            ],
            "created_at": "2026-05-01T12:00:00",
            "updated_at": "2026-05-01T12:00:00",
            "execution": {
                "started_at": "2026-05-01T12:00:01",
                "completed_at": "2026-05-01T12:05:00",
                "model_used": "openrouter/z-ai/glm-5",
                "task_results": [
                    {
                        "task_index": 0,
                        "status": "completed",
                        "started_at": "2026-05-01T12:00:01",
                        "completed_at": "2026-05-01T12:05:00",
                        "files_changed": files_changed,
                        "llm_summary": "Added feature",
                    }
                ],
                "files_changed": files_changed,
                "commit_hash": "",
                "total_tokens": 1000,
                "total_cost": 0.005,
                "review": {
                    "mode": "human",
                    "verdict": "needs_changes",
                    "summary": "Awaiting human review",
                    "reviewed_by": "",
                },
            },
        }
        (tmp_path / f"{plan_id}.json").write_text(json.dumps(plan_data))
        return plan_id

    def test_approve_commits_and_completes(self, tmp_path):
        """Plan en pending_review → approve → git add+commit → completed."""
        plan_id = self._create_pending_review_plan(tmp_path)

        with patch("autocode.core.planning.planner.PLANS_DIR", str(tmp_path)), \
             patch("autocode.core.planning.workflow.git_checked") as mock_git:
            mock_git.return_value = "new_commit_hash_abc"

            result = approve_plan(plan_id=plan_id)

        assert result.success is True
        assert result.result.status == "completed"
        # Verify git was called for add + commit
        git_calls = [str(c) for c in mock_git.call_args_list]
        assert any("add" in c for c in git_calls)
        assert any("commit" in c for c in git_calls)

    def test_approve_rejects_wrong_status(self, tmp_path):
        """Plan en draft → approve → error."""
        plan_data = {
            "id": "20260501-130000",
            "title": "Draft Plan",
            "status": "draft",
            "tasks": [],
            "created_at": "2026-05-01T13:00:00",
        }
        (tmp_path / "20260501-130000.json").write_text(json.dumps(plan_data))

        with patch("autocode.core.planning.planner.PLANS_DIR", str(tmp_path)):
            result = approve_plan(plan_id="20260501-130000")

        assert result.success is False
        assert "status" in result.message.lower() or "pending_review" in result.message.lower()

    def test_approve_stores_commit_hash(self, tmp_path):
        """Tras approve, execution.commit_hash se rellena con el hash del commit."""
        plan_id = self._create_pending_review_plan(tmp_path)

        with patch("autocode.core.planning.planner.PLANS_DIR", str(tmp_path)), \
             patch("autocode.core.planning.workflow.git_checked") as mock_git:
            mock_git.return_value = "def456789"

            result = approve_plan(plan_id=plan_id)

        assert result.success is True
        assert result.result.execution.commit_hash == "def456789"

    def test_approve_with_custom_message(self, tmp_path):
        """approve con commit_message usa ese mensaje en vez del plan title."""
        plan_id = self._create_pending_review_plan(tmp_path, title="original title")

        with patch("autocode.core.planning.planner.PLANS_DIR", str(tmp_path)), \
             patch("autocode.core.planning.workflow.git_checked") as mock_git:
            mock_git.return_value = "abc123"

            result = approve_plan(plan_id=plan_id, commit_message="custom: my message")

        assert result.success is True
        # Verify the commit call used the custom message
        commit_calls = [c for c in mock_git.call_args_list
                        if "commit" in str(c)]
        assert len(commit_calls) >= 1
        assert "custom: my message" in str(commit_calls[0])

    def test_approve_nonexistent_plan(self, tmp_path):
        """approve_plan con plan inexistente → error."""
        with patch("autocode.core.planning.planner.PLANS_DIR", str(tmp_path)):
            result = approve_plan(plan_id="nonexistent")

        assert result.success is False
        assert "no encontrado" in result.message.lower() or "not found" in result.message.lower()


# ==============================================================================
# TESTS: revert_plan (workflow)
# ==============================================================================


class TestRevertPlanWorkflow:
    """Tests for revert_plan imported from workflow module.

    Verifies that a plan in pending_review can be reverted,
    which triggers git checkout to restore files and transitions to reverted.
    """

    def _create_pending_review_plan(self, tmp_path, plan_id="20260501-140000",
                                     files_changed=None,
                                     parent_commit="abc123"):
        """Helper: creates a plan JSON in tmp_path with status=pending_review."""
        if files_changed is None:
            files_changed = ["src/main.py", "src/utils.py"]
        plan_data = {
            "id": plan_id,
            "title": "feat: add feature",
            "status": "pending_review",
            "parent_commit": parent_commit,
            "branch": "main",
            "tasks": [
                {"type": "modify", "path": "src/main.py", "description": "Add feature"},
            ],
            "created_at": "2026-05-01T14:00:00",
            "updated_at": "2026-05-01T14:00:00",
            "execution": {
                "started_at": "2026-05-01T14:00:01",
                "completed_at": "2026-05-01T14:05:00",
                "model_used": "openrouter/z-ai/glm-5",
                "task_results": [
                    {
                        "task_index": 0,
                        "status": "completed",
                        "started_at": "2026-05-01T14:00:01",
                        "completed_at": "2026-05-01T14:05:00",
                        "files_changed": files_changed,
                        "llm_summary": "Added feature",
                    }
                ],
                "files_changed": files_changed,
                "commit_hash": "",
                "total_tokens": 1000,
                "total_cost": 0.005,
                "review": {
                    "mode": "human",
                    "verdict": "needs_changes",
                    "summary": "Awaiting human review",
                    "reviewed_by": "",
                },
            },
        }
        (tmp_path / f"{plan_id}.json").write_text(json.dumps(plan_data))
        return plan_id

    def test_revert_restores_files(self, tmp_path):
        """Plan en pending_review → revert → git checkout para cada archivo → reverted."""
        plan_id = self._create_pending_review_plan(
            tmp_path, files_changed=["src/main.py", "src/utils.py"]
        )

        with patch("autocode.core.planning.planner.PLANS_DIR", str(tmp_path)), \
             patch("autocode.core.planning.workflow.git_checked") as mock_git:
            result = revert_plan(plan_id=plan_id)

        assert result.success is True
        assert result.result.status == "reverted"
        # Verify git checkout was called with the files
        git_calls = [str(c) for c in mock_git.call_args_list]
        assert any("checkout" in c for c in git_calls)
        assert any("src/main.py" in c for c in git_calls)
        assert any("src/utils.py" in c for c in git_calls)

    def test_revert_rejects_wrong_status(self, tmp_path):
        """Plan en draft → revert → error."""
        plan_data = {
            "id": "20260501-150000",
            "title": "Draft Plan",
            "status": "draft",
            "tasks": [],
            "created_at": "2026-05-01T15:00:00",
        }
        (tmp_path / "20260501-150000.json").write_text(json.dumps(plan_data))

        with patch("autocode.core.planning.planner.PLANS_DIR", str(tmp_path)):
            result = revert_plan(plan_id="20260501-150000")

        assert result.success is False
        assert "status" in result.message.lower() or "pending_review" in result.message.lower()

    def test_revert_marks_as_reverted(self, tmp_path):
        """Tras revert, el status es 'reverted'."""
        plan_id = self._create_pending_review_plan(tmp_path)

        with patch("autocode.core.planning.planner.PLANS_DIR", str(tmp_path)), \
             patch("autocode.core.planning.workflow.git_checked"):
            result = revert_plan(plan_id=plan_id)

        assert result.success is True
        assert result.result.status == "reverted"

    def test_revert_uses_parent_commit(self, tmp_path):
        """Revert usa parent_commit del plan como referencia para checkout."""
        plan_id = self._create_pending_review_plan(
            tmp_path, parent_commit="deadbeef123"
        )

        with patch("autocode.core.planning.planner.PLANS_DIR", str(tmp_path)), \
             patch("autocode.core.planning.workflow.git_checked") as mock_git:
            result = revert_plan(plan_id=plan_id)

        assert result.success is True
        git_calls_str = str(mock_git.call_args_list)
        assert "deadbeef123" in git_calls_str

    def test_revert_empty_files_returns_error(self, tmp_path):
        """revert con files_changed vacío → success=False."""
        plan_id = self._create_pending_review_plan(
            tmp_path, files_changed=[]
        )

        with patch("autocode.core.planning.planner.PLANS_DIR", str(tmp_path)):
            result = revert_plan(plan_id=plan_id)

        assert result.success is False
        assert "no files" in result.message.lower() or "empty" in result.message.lower()

    def test_revert_nonexistent_plan(self, tmp_path):
        """revert_plan con plan inexistente → error."""
        with patch("autocode.core.planning.planner.PLANS_DIR", str(tmp_path)):
            result = revert_plan(plan_id="nonexistent")

        assert result.success is False
        assert "no encontrado" in result.message.lower() or "not found" in result.message.lower()


# ==============================================================================
# TESTS: get_plan_review_metrics (workflow)
# ==============================================================================


class TestGetPlanReviewMetricsWorkflow:
    """Tests for get_plan_review_metrics imported from workflow module.

    Verifies extraction of review metrics (file_metrics, summary, quality_gates)
    from a plan's execution.review data.
    """

    def _create_plan_with_review(self, tmp_path, plan_id="20260501-160000",
                                  has_review=True):
        """Helper: creates a plan with execution.review populated."""
        review_data = None
        if has_review:
            review_data = {
                "mode": "auto",
                "verdict": "approved",
                "summary": "All checks passed",
                "issues": ["Minor style issue"],
                "suggestions": ["Consider adding docstrings"],
                "file_metrics": [
                    {
                        "path": "src/main.py",
                        "before": {"sloc": 100, "avg_complexity": 3.0},
                        "after": {"sloc": 120, "avg_complexity": 3.5},
                        "deltas": {"delta_sloc": 20, "delta_complexity": 0.5},
                    },
                    {
                        "path": "src/utils.py",
                        "before": {"sloc": 50, "avg_complexity": 2.0},
                        "after": {"sloc": 55, "avg_complexity": 2.1},
                        "deltas": {"delta_sloc": 5, "delta_complexity": 0.1},
                    },
                ],
                "quality_gates": {
                    "complexity_ok": True,
                    "no_regressions": True,
                },
                "reviewed_at": "2026-05-01T16:10:00",
                "reviewed_by": "auto",
            }

        execution_data = {
            "started_at": "2026-05-01T16:00:01",
            "completed_at": "2026-05-01T16:05:00",
            "model_used": "openrouter/z-ai/glm-5",
            "task_results": [],
            "files_changed": ["src/main.py", "src/utils.py"],
            "commit_hash": "",
            "total_tokens": 1000,
            "total_cost": 0.005,
        }
        if review_data is not None:
            execution_data["review"] = review_data

        plan_data = {
            "id": plan_id,
            "title": "feat: reviewed feature",
            "status": "pending_review",
            "parent_commit": "abc123",
            "branch": "main",
            "tasks": [],
            "created_at": "2026-05-01T16:00:00",
            "updated_at": "2026-05-01T16:00:00",
            "execution": execution_data,
        }
        (tmp_path / f"{plan_id}.json").write_text(json.dumps(plan_data))
        return plan_id

    def test_returns_review_metrics(self, tmp_path):
        """Plan con review → returns file_metrics, summary, quality_gates."""
        plan_id = self._create_plan_with_review(tmp_path, has_review=True)

        with patch("autocode.core.planning.planner.PLANS_DIR", str(tmp_path)):
            result = get_plan_review_metrics(plan_id=plan_id)

        assert result.success is True
        data = result.result

        # Verify files
        assert len(data["files"]) == 2
        assert data["files"][0]["path"] == "src/main.py"
        assert data["files"][0]["delta_sloc"] == 20
        assert data["files"][1]["path"] == "src/utils.py"

        # Verify summary
        assert data["summary"]["verdict"] == "approved"
        assert data["summary"]["summary"] == "All checks passed"
        assert data["summary"]["mode"] == "auto"
        assert "Minor style issue" in data["summary"]["issues"]
        assert "Consider adding docstrings" in data["summary"]["suggestions"]

        # Verify quality_gates
        assert data["quality_gates"]["complexity_ok"] is True
        assert data["quality_gates"]["no_regressions"] is True

    def test_returns_empty_when_no_review(self, tmp_path):
        """Plan sin review → returns empty files/summary/quality_gates."""
        plan_id = self._create_plan_with_review(tmp_path, has_review=False)

        with patch("autocode.core.planning.planner.PLANS_DIR", str(tmp_path)):
            result = get_plan_review_metrics(plan_id=plan_id)

        assert result.success is True
        data = result.result
        assert data["files"] == []
        assert data["summary"] == {}
        assert data["quality_gates"] == {}

    def test_nonexistent_plan_returns_error(self, tmp_path):
        """Plan inexistente → success=False."""
        with patch("autocode.core.planning.planner.PLANS_DIR", str(tmp_path)):
            result = get_plan_review_metrics(plan_id="nonexistent")

        assert result.success is False
