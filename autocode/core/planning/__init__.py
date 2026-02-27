"""
autocode/core/planning
Módulo de planificación de commits.

Permite diseñar commits futuros desde la UI, almacenarlos como planes
estructurados en .autocode/plans/ y visualizarlos como ghost nodes en git-graph.
"""

from .models import (
    PlanTask,
    PlanContext,
    CommitPlan,
    CommitPlanSummary,
    CommitPlanOutput,
    CommitPlanListOutput,
)
from .planner import (
    create_commit_plan,
    list_commit_plans,
    get_commit_plan,
    update_commit_plan,
    delete_commit_plan,
)

__all__ = [
    # Models
    "PlanTask",
    "PlanContext",
    "CommitPlan",
    "CommitPlanSummary",
    "CommitPlanOutput",
    "CommitPlanListOutput",
    # Functions
    "create_commit_plan",
    "list_commit_plans",
    "get_commit_plan",
    "update_commit_plan",
    "delete_commit_plan",
]
