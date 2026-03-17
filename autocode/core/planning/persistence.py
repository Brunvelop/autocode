"""
persistence.py

Capa de persistencia para planes de commit.

Responsabilidad única: guardar, cargar y listar planes en .autocode/plans/.
Extraído de planner.py para separación de responsabilidades.
"""
import json
import logging
from pathlib import Path
from typing import Optional

from autocode.core.planning.models import CommitPlan, CommitPlanSummary

logger = logging.getLogger(__name__)

# Directorio de planes (relativo al CWD del proyecto host)
PLANS_DIR = ".autocode/plans"


def save_plan(plan: CommitPlan, plans_dir: Optional[str] = None) -> None:
    """Save plan as JSON in .autocode/plans/."""
    dir_path = Path(plans_dir if plans_dir is not None else PLANS_DIR)
    dir_path.mkdir(parents=True, exist_ok=True)
    path = dir_path / f"{plan.id}.json"
    path.write_text(plan.model_dump_json(indent=2), encoding="utf-8")
    logger.debug(f"Plan saved: {path}")


def load_plan(plan_id: str, plans_dir: Optional[str] = None) -> Optional[CommitPlan]:
    """Load a plan by ID. Returns None if not found."""
    dir_path = Path(plans_dir if plans_dir is not None else PLANS_DIR)
    plan_file = dir_path / f"{plan_id}.json"
    if not plan_file.exists():
        return None
    try:
        data = json.loads(plan_file.read_text(encoding="utf-8"))
        return CommitPlan(**data)
    except Exception as e:
        logger.error(f"Error loading plan {plan_id}: {e}")
        return None


def list_plan_summaries(status_filter: str = "", plans_dir: Optional[str] = None) -> list[CommitPlanSummary]:
    """List all plans as summaries, optionally filtered by status."""
    dir_path = Path(plans_dir if plans_dir is not None else PLANS_DIR)
    if not dir_path.exists():
        return []

    summaries = []
    for f in sorted(dir_path.glob("*.json"), reverse=True):
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
            plan_status = data.get("status", "draft")
            if status_filter and plan_status != status_filter:
                continue
            summaries.append(CommitPlanSummary(
                id=data.get("id", f.stem),
                title=data.get("title", ""),
                status=plan_status,
                tasks_count=len(data.get("tasks", [])),
                created_at=data.get("created_at", ""),
                branch=data.get("branch", ""),
            ))
        except Exception as e:
            logger.debug(f"Skip plan {f.name}: {e}")
            continue

    return summaries
