"""
Tests for persistence.py — save/load/list plans.
RED phase: autocode.core.planning.persistence does not exist yet.
Tests define the public API that will be extracted from planner.py.
"""

import json
from pathlib import Path
from unittest.mock import patch

import pytest

from autocode.core.planning.persistence import (
    save_plan,
    load_plan,
    list_plan_summaries,
    delete_plan,
)
from autocode.core.planning.models import CommitPlan, CommitPlanSummary


class TestSavePlan:
    """Tests for save_plan() — persist plan as JSON."""

    def test_save_creates_json_file(self, tmp_path):
        """save_plan crea el archivo JSON en .autocode/plans/{id}.json."""
        plan = CommitPlan(id="20260101-000000", title="Test Plan")
        with patch("autocode.core.planning.persistence.PLANS_DIR", str(tmp_path)):
            save_plan(plan)
        plan_file = tmp_path / "20260101-000000.json"
        assert plan_file.exists()

    def test_save_creates_directory_if_missing(self, tmp_path):
        """save_plan crea el directorio si no existe."""
        plan = CommitPlan(id="20260101-000001", title="Dir Test")
        subdir = tmp_path / "subdir"
        with patch("autocode.core.planning.persistence.PLANS_DIR", str(subdir)):
            save_plan(plan)
        assert (subdir / "20260101-000001.json").exists()

    def test_save_writes_valid_json(self, tmp_path):
        """El archivo guardado contiene JSON válido del plan."""
        plan = CommitPlan(id="20260101-000002", title="JSON Test", description="desc")
        with patch("autocode.core.planning.persistence.PLANS_DIR", str(tmp_path)):
            save_plan(plan)
        data = json.loads((tmp_path / "20260101-000002.json").read_text())
        assert data["id"] == "20260101-000002"
        assert data["title"] == "JSON Test"
        assert data["description"] == "desc"

    def test_save_overwrites_existing(self, tmp_path):
        """save_plan sobreescribe el archivo si ya existe."""
        plan = CommitPlan(id="20260101-000003", title="Original")
        with patch("autocode.core.planning.persistence.PLANS_DIR", str(tmp_path)):
            save_plan(plan)
            plan.title = "Updated"
            save_plan(plan)
        data = json.loads((tmp_path / "20260101-000003.json").read_text())
        assert data["title"] == "Updated"


class TestLoadPlan:
    """Tests for load_plan() — load plan by ID."""

    def test_load_returns_commit_plan(self, tmp_path):
        """load_plan retorna un CommitPlan si el archivo existe."""
        plan = CommitPlan(id="20260101-000010", title="Load Test")
        (tmp_path / "20260101-000010.json").write_text(
            plan.model_dump_json(), encoding="utf-8"
        )
        with patch("autocode.core.planning.persistence.PLANS_DIR", str(tmp_path)):
            result = load_plan("20260101-000010")
        assert isinstance(result, CommitPlan)
        assert result.id == "20260101-000010"
        assert result.title == "Load Test"

    def test_load_returns_none_if_not_found(self, tmp_path):
        """load_plan retorna None si el plan no existe."""
        with patch("autocode.core.planning.persistence.PLANS_DIR", str(tmp_path)):
            result = load_plan("nonexistent-plan")
        assert result is None

    def test_load_preserves_all_fields(self, tmp_path):
        """load_plan preserva todos los campos del plan."""
        from autocode.core.planning.models import PlanTask, PlanContext

        plan = CommitPlan(
            id="20260101-000011",
            title="Full Plan",
            description="Test description",
            status="ready",
            tasks=[PlanTask(type="modify", path="src/main.py", description="Fix")],
            context=PlanContext(architectural_notes="Use async"),
            tags=["refactor", "test"],
        )
        (tmp_path / "20260101-000011.json").write_text(
            plan.model_dump_json(), encoding="utf-8"
        )
        with patch("autocode.core.planning.persistence.PLANS_DIR", str(tmp_path)):
            result = load_plan("20260101-000011")
        assert result.description == "Test description"
        assert result.status == "ready"
        assert len(result.tasks) == 1
        assert result.tags == ["refactor", "test"]
        assert result.context.architectural_notes == "Use async"


class TestListPlanSummaries:
    """Tests for list_plan_summaries() — list plans as summaries."""

    def test_returns_empty_list_if_no_plans(self, tmp_path):
        """Sin planes → lista vacía."""
        with patch("autocode.core.planning.persistence.PLANS_DIR", str(tmp_path)):
            result = list_plan_summaries()
        assert result == []

    def test_returns_empty_if_dir_missing(self, tmp_path):
        """Si el directorio no existe → lista vacía."""
        missing = tmp_path / "missing"
        with patch("autocode.core.planning.persistence.PLANS_DIR", str(missing)):
            result = list_plan_summaries()
        assert result == []

    def test_returns_all_plans_as_summaries(self, tmp_path):
        """Retorna CommitPlanSummary para cada plan guardado."""
        for i in range(3):
            plan = CommitPlan(id=f"20260101-00002{i}", title=f"Plan {i}")
            (tmp_path / f"20260101-00002{i}.json").write_text(
                plan.model_dump_json(), encoding="utf-8"
            )
        with patch("autocode.core.planning.persistence.PLANS_DIR", str(tmp_path)):
            result = list_plan_summaries()
        assert len(result) == 3
        assert all(isinstance(s, CommitPlanSummary) for s in result)

    def test_filters_by_status(self, tmp_path):
        """status_filter filtra correctamente por estado."""
        draft_plan = CommitPlan(id="20260101-000030", title="Draft", status="draft")
        ready_plan = CommitPlan(id="20260101-000031", title="Ready", status="ready")
        (tmp_path / "20260101-000030.json").write_text(
            draft_plan.model_dump_json(), encoding="utf-8"
        )
        (tmp_path / "20260101-000031.json").write_text(
            ready_plan.model_dump_json(), encoding="utf-8"
        )
        with patch("autocode.core.planning.persistence.PLANS_DIR", str(tmp_path)):
            drafts = list_plan_summaries(status_filter="draft")
            readies = list_plan_summaries(status_filter="ready")
            all_plans = list_plan_summaries()
        assert len(drafts) == 1
        assert drafts[0].status == "draft"
        assert len(readies) == 1
        assert readies[0].status == "ready"
        assert len(all_plans) == 2

    def test_summary_contains_correct_fields(self, tmp_path):
        """CommitPlanSummary contiene id, title, status, tasks_count, created_at, branch."""
        from autocode.core.planning.models import PlanTask

        plan = CommitPlan(
            id="20260101-000040",
            title="Full Summary Test",
            status="draft",
            branch="main",
            created_at="2026-01-01T00:00:00",
            tasks=[
                PlanTask(type="modify", path="a.py", description="A"),
                PlanTask(type="create", path="b.py", description="B"),
            ],
        )
        (tmp_path / "20260101-000040.json").write_text(
            plan.model_dump_json(), encoding="utf-8"
        )
        with patch("autocode.core.planning.persistence.PLANS_DIR", str(tmp_path)):
            result = list_plan_summaries()
        s = result[0]
        assert s.id == "20260101-000040"
        assert s.title == "Full Summary Test"
        assert s.status == "draft"
        assert s.tasks_count == 2
        assert s.branch == "main"
        assert s.created_at == "2026-01-01T00:00:00"

    def test_returns_plans_sorted_newest_first(self, tmp_path):
        """Los planes se retornan ordenados de más reciente a más antiguo (por nombre de archivo)."""
        for plan_id in ["20260101-000050", "20260102-000050", "20260103-000050"]:
            plan = CommitPlan(id=plan_id, title=f"Plan {plan_id}")
            (tmp_path / f"{plan_id}.json").write_text(
                plan.model_dump_json(), encoding="utf-8"
            )
        with patch("autocode.core.planning.persistence.PLANS_DIR", str(tmp_path)):
            result = list_plan_summaries()
        # Newest first
        assert result[0].id == "20260103-000050"
        assert result[-1].id == "20260101-000050"


class TestDeletePlan:
    """Tests for delete_plan() — delete plan by ID."""

    def test_delete_existing_plan_returns_true(self, tmp_path):
        """delete_plan retorna True cuando el plan existe y se elimina."""
        plan = CommitPlan(id="20260101-000060", title="To Delete")
        (tmp_path / "20260101-000060.json").write_text(
            plan.model_dump_json(), encoding="utf-8"
        )
        with patch("autocode.core.planning.persistence.PLANS_DIR", str(tmp_path)):
            result = delete_plan("20260101-000060")
        assert result is True

    def test_delete_nonexistent_plan_returns_false(self, tmp_path):
        """delete_plan retorna False cuando el plan no existe."""
        with patch("autocode.core.planning.persistence.PLANS_DIR", str(tmp_path)):
            result = delete_plan("nonexistent-plan")
        assert result is False

    def test_delete_removes_file_from_disk(self, tmp_path):
        """delete_plan elimina el archivo del disco."""
        plan = CommitPlan(id="20260101-000061", title="Remove Me")
        plan_file = tmp_path / "20260101-000061.json"
        plan_file.write_text(plan.model_dump_json(), encoding="utf-8")
        assert plan_file.exists()
        with patch("autocode.core.planning.persistence.PLANS_DIR", str(tmp_path)):
            delete_plan("20260101-000061")
        assert not plan_file.exists()
