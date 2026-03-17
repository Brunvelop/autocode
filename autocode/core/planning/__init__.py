"""
autocode/core/planning
Módulo de planificación de commits.

Permite diseñar commits futuros desde la UI, almacenarlos como planes
estructurados en .autocode/plans/ y visualizarlos como ghost nodes en git-dashboard.
"""

from .models import (
    ExecutionStep,
    CommitPlan,
    CommitPlanSummary,
    CommitPlanOutput,
    CommitPlanListOutput,
    PlanExecutionState,
)
from .planner import (
    create_commit_plan,
    list_commit_plans,
    get_commit_plan,
    update_commit_plan,
    delete_commit_plan,
)
from .workflow import (
    approve_plan,
    revert_plan,
    get_plan_review_metrics,
)
from .executor import (
    execute_commit_plan,
    stream_execute_plan,
)
from .persistence import (
    save_plan,
    load_plan,
    list_plan_summaries,
)
from .transitions import (
    validate_transition,
    can_execute,
    can_review,
    InvalidTransitionError,
)

__all__ = [
    # Models
    "ExecutionStep",
    "CommitPlan",
    "CommitPlanSummary",
    "CommitPlanOutput",
    "CommitPlanListOutput",
    "PlanExecutionState",
    # Functions — CRUD
    "create_commit_plan",
    "list_commit_plans",
    "get_commit_plan",
    "update_commit_plan",
    "delete_commit_plan",
    # Functions — Workflow (approve/revert/review)
    "approve_plan",
    "revert_plan",
    "get_plan_review_metrics",
    # Functions — Executor
    "execute_commit_plan",
    "stream_execute_plan",
    # Persistence
    "save_plan",
    "load_plan",
    "list_plan_summaries",
    # Transitions
    "validate_transition",
    "can_execute",
    "can_review",
    "InvalidTransitionError",
]
