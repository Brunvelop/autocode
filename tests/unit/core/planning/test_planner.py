"""
Tests for status transition validation in update_commit_plan.

Verifica que los estados gestionados por el executor (executing, completed, failed)
no pueden ser seteados manualmente via update_commit_plan().
"""
import json
from unittest.mock import patch

import pytest

from autocode.core.planning.planner import (
    create_commit_plan,
    update_commit_plan,
    list_commit_plans,
)


class TestStatusTransitionValidation:
    """Tests for status transition validation in update_commit_plan."""

    def test_reject_executing_status_via_update(self, tmp_path):
        """update_commit_plan rechaza status='executing' (solo executor puede setearlo)."""
        with patch("autocode.core.planning.planner.PLANS_DIR", str(tmp_path)), \
             patch("autocode.core.planning.planner._git", return_value="abc123"):
            create_result = create_commit_plan(title="Test Plan")
            plan_id = create_result.result.id

            result = update_commit_plan(plan_id=plan_id, status="executing")
            assert result.success is False
            assert "executor" in result.message.lower() or "managed" in result.message.lower()

    def test_reject_completed_status_via_update(self, tmp_path):
        """update_commit_plan rechaza status='completed'."""
        with patch("autocode.core.planning.planner.PLANS_DIR", str(tmp_path)), \
             patch("autocode.core.planning.planner._git", return_value="abc123"):
            create_result = create_commit_plan(title="Test Plan")
            plan_id = create_result.result.id

            result = update_commit_plan(plan_id=plan_id, status="completed")
            assert result.success is False

    def test_reject_failed_status_via_update(self, tmp_path):
        """update_commit_plan rechaza status='failed'."""
        with patch("autocode.core.planning.planner.PLANS_DIR", str(tmp_path)), \
             patch("autocode.core.planning.planner._git", return_value="abc123"):
            create_result = create_commit_plan(title="Test Plan")
            plan_id = create_result.result.id

            result = update_commit_plan(plan_id=plan_id, status="failed")
            assert result.success is False

    def test_allow_manual_statuses(self, tmp_path):
        """update_commit_plan permite draft, ready, abandoned."""
        with patch("autocode.core.planning.planner.PLANS_DIR", str(tmp_path)), \
             patch("autocode.core.planning.planner._git", return_value="abc123"):
            create_result = create_commit_plan(title="Test Plan")
            plan_id = create_result.result.id

            for status in ("draft", "ready", "abandoned"):
                result = update_commit_plan(plan_id=plan_id, status=status)
                assert result.success is True, f"Status '{status}' should be allowed"

    def test_list_plans_includes_new_statuses(self, tmp_path):
        """list_commit_plans filtra correctamente los nuevos estados."""
        with patch("autocode.core.planning.planner.PLANS_DIR", str(tmp_path)), \
             patch("autocode.core.planning.planner._git", return_value="abc123"):
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
