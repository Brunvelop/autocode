"""
Tests for planner.py — CRUD operations and status transitions.

Covers:
- Status transition validation in update_commit_plan
- Recovery of zombie plans (stuck in executing)
- New executor-managed statuses blocked from manual setting
"""
import json
from unittest.mock import patch

from autocode.core.planning.planner import (
    create_commit_plan,
    update_commit_plan,
    list_commit_plans,
)


class TestStatusTransitionValidation:
    """Tests for status transition validation in update_commit_plan."""

    def test_reject_executing_status_via_update(self, tmp_path):
        """update_commit_plan rechaza status='executing' (solo executor puede setearlo)."""
        with patch("autocode.core.planning.persistence.PLANS_DIR", str(tmp_path)), \
             patch("autocode.core.planning.planner.git", return_value="abc123"):
            create_result = create_commit_plan(title="Test Plan")
            plan_id = create_result.result.id

            result = update_commit_plan(plan_id=plan_id, status="executing")
            assert result.success is False
            assert "executor" in result.message.lower() or "managed" in result.message.lower()

    def test_reject_completed_status_via_update(self, tmp_path):
        """update_commit_plan rechaza status='completed'."""
        with patch("autocode.core.planning.persistence.PLANS_DIR", str(tmp_path)), \
             patch("autocode.core.planning.planner.git", return_value="abc123"):
            create_result = create_commit_plan(title="Test Plan")
            plan_id = create_result.result.id

            result = update_commit_plan(plan_id=plan_id, status="completed")
            assert result.success is False

    def test_reject_failed_status_via_update(self, tmp_path):
        """update_commit_plan rechaza status='failed'."""
        with patch("autocode.core.planning.persistence.PLANS_DIR", str(tmp_path)), \
             patch("autocode.core.planning.planner.git", return_value="abc123"):
            create_result = create_commit_plan(title="Test Plan")
            plan_id = create_result.result.id

            result = update_commit_plan(plan_id=plan_id, status="failed")
            assert result.success is False

    def test_allow_manual_statuses(self, tmp_path):
        """update_commit_plan permite draft, ready, abandoned via valid transitions."""
        with patch("autocode.core.planning.persistence.PLANS_DIR", str(tmp_path)), \
             patch("autocode.core.planning.planner.git", return_value="abc123"):
            create_result = create_commit_plan(title="Test Plan")
            plan_id = create_result.result.id

            # Plan starts as "draft" — test valid transition sequences
            # draft → ready (valid)
            result = update_commit_plan(plan_id=plan_id, status="ready")
            assert result.success is True, "Status 'ready' should be allowed from draft"
            # ready → draft (valid)
            result = update_commit_plan(plan_id=plan_id, status="draft")
            assert result.success is True, "Status 'draft' should be allowed from ready"
            # draft → abandoned (valid)
            result = update_commit_plan(plan_id=plan_id, status="abandoned")
            assert result.success is True, "Status 'abandoned' should be allowed from draft"

    def test_list_plans_includes_new_statuses(self, tmp_path):
        """list_commit_plans filtra correctamente los nuevos estados."""
        with patch("autocode.core.planning.persistence.PLANS_DIR", str(tmp_path)), \
             patch("autocode.core.planning.planner.git", return_value="abc123"):
            create_commit_plan(title="Plan 1")

            # Manualmente crear un plan con status "completed" para test
            plan_data = {
                "id": "20260101-000001",
                "title": "Completed Plan",
                "status": "completed",
                "tasks": [],
                "created_at": "2026-01-01",
            }
            (tmp_path / "20260101-000001.json").write_text(json.dumps(plan_data))

            result = list_commit_plans(status="completed")
            assert result.success is True
            assert len(result.result) == 1
            assert result.result[0].status == "completed"


class TestRecoveryFromStuckExecuting:
    """Tests for recovery of plans stuck in 'executing' state (zombie plans).

    A plan gets stuck in 'executing' when the execution dies (crash, timeout,
    browser refresh). These tests verify that such plans can be recovered
    back to 'draft' via update_commit_plan.
    """

    def _create_executing_plan(self, tmp_path, completed_at=""):
        """Helper: creates a plan in 'executing' state with optional completed_at."""
        plan_data = {
            "id": "20260101-120000",
            "title": "Stuck Plan",
            "status": "executing",
            "tasks": [{"type": "modify", "path": "src/main.py", "description": "Fix bug"}],
            "created_at": "2026-01-01T12:00:00",
            "updated_at": "2026-01-01T12:00:00",
            "execution": {
                "started_at": "2026-01-01T12:00:01",
                "completed_at": completed_at,
                "model_used": "openrouter/z-ai/glm-5",
                "task_results": [],
                "commit_hash": "",
                "total_tokens": 0,
                "total_cost": 0.0,
            },
        }
        (tmp_path / "20260101-120000.json").write_text(json.dumps(plan_data))
        return "20260101-120000"

    def test_recovery_executing_to_draft_with_empty_completed_at(self, tmp_path):
        """Plan en executing con completed_at vacío puede transicionar a draft."""
        with patch("autocode.core.planning.persistence.PLANS_DIR", str(tmp_path)):
            plan_id = self._create_executing_plan(tmp_path, completed_at="")

            result = update_commit_plan(plan_id=plan_id, status="draft")
            assert result.success is True
            assert result.result.status == "draft"

    def test_recovery_executing_to_draft_clears_execution(self, tmp_path):
        """Al resetear a draft, execution se limpia a None."""
        with patch("autocode.core.planning.persistence.PLANS_DIR", str(tmp_path)):
            plan_id = self._create_executing_plan(tmp_path, completed_at="")

            result = update_commit_plan(plan_id=plan_id, status="draft")
            assert result.success is True
            assert result.result.execution is None

    def test_recovery_executing_without_execution_object(self, tmp_path):
        """Plan en executing sin execution object (edge case) puede ir a draft."""
        plan_data = {
            "id": "20260101-130000",
            "title": "No Execution Plan",
            "status": "executing",
            "tasks": [],
            "created_at": "2026-01-01T13:00:00",
        }
        (tmp_path / "20260101-130000.json").write_text(json.dumps(plan_data))

        with patch("autocode.core.planning.persistence.PLANS_DIR", str(tmp_path)):
            result = update_commit_plan(plan_id="20260101-130000", status="draft")
            assert result.success is True
            assert result.result.status == "draft"
            assert result.result.execution is None

    def test_recovery_blocked_if_completed_at_set(self, tmp_path):
        """Plan en executing con completed_at (terminó normalmente) rechaza reset manual.

        Recovery path is NOT taken (completed_at is set), and the state machine
        rejects executing→draft since it's not a valid transition.
        """
        with patch("autocode.core.planning.persistence.PLANS_DIR", str(tmp_path)):
            plan_id = self._create_executing_plan(
                tmp_path, completed_at="2026-01-01T12:05:00"
            )

            result = update_commit_plan(plan_id=plan_id, status="draft")
            # Recovery not triggered (completed_at is set), and
            # executing→draft is not a valid state machine transition
            assert result.success is False
            assert "invalid transition" in result.message.lower()

    def test_executing_cannot_be_set_manually_from_draft(self, tmp_path):
        """No se puede setear 'executing' manualmente desde draft."""
        with patch("autocode.core.planning.persistence.PLANS_DIR", str(tmp_path)), \
             patch("autocode.core.planning.planner.git", return_value="abc123"):
            create_result = create_commit_plan(title="Test Plan")
            plan_id = create_result.result.id

            result = update_commit_plan(plan_id=plan_id, status="executing")
            assert result.success is False

    def test_recovery_message_indicates_recovery(self, tmp_path):
        """El mensaje de respuesta indica que fue una recovery."""
        with patch("autocode.core.planning.persistence.PLANS_DIR", str(tmp_path)):
            plan_id = self._create_executing_plan(tmp_path, completed_at="")

            result = update_commit_plan(plan_id=plan_id, status="draft")
            assert result.success is True
            assert "recover" in result.message.lower()


# ==============================================================================
# TESTS: Status transitions — new executor-managed statuses
# ==============================================================================


class TestStatusTransitionsUpdated:
    """Tests that pending_review, pending_commit, and reverted
    cannot be set manually via update_commit_plan.

    These states are managed by the executor (pending_review, pending_commit)
    and approve/revert endpoints (reverted).
    """

    def test_pending_review_not_manually_settable(self, tmp_path):
        """update_commit_plan rechaza status='pending_review'."""
        with patch("autocode.core.planning.persistence.PLANS_DIR", str(tmp_path)), \
             patch("autocode.core.planning.planner.git", return_value="abc123"):
            create_result = create_commit_plan(title="Test Plan")
            plan_id = create_result.result.id

            result = update_commit_plan(plan_id=plan_id, status="pending_review")
            assert result.success is False
            assert "managed" in result.message.lower() or "executor" in result.message.lower()

    def test_pending_commit_not_manually_settable(self, tmp_path):
        """update_commit_plan rechaza status='pending_commit'."""
        with patch("autocode.core.planning.persistence.PLANS_DIR", str(tmp_path)), \
             patch("autocode.core.planning.planner.git", return_value="abc123"):
            create_result = create_commit_plan(title="Test Plan")
            plan_id = create_result.result.id

            result = update_commit_plan(plan_id=plan_id, status="pending_commit")
            assert result.success is False

    def test_reverted_not_manually_settable(self, tmp_path):
        """update_commit_plan rechaza status='reverted'."""
        with patch("autocode.core.planning.persistence.PLANS_DIR", str(tmp_path)), \
             patch("autocode.core.planning.planner.git", return_value="abc123"):
            create_result = create_commit_plan(title="Test Plan")
            plan_id = create_result.result.id

            result = update_commit_plan(plan_id=plan_id, status="reverted")
            assert result.success is False
