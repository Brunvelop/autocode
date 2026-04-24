"""
planner.py
CRUD de planes de commit.

Persistencia en .autocode/plans/{id}.json.
Sigue el patrón de autocode/core/code/metrics.py para
persistencia, helpers git y endpoints registrados.

Los planes se crean vía chat (el agente usa create_commit_plan
con toda la información recopilada durante la conversación).
"""
import logging
from datetime import datetime

from fastapi import HTTPException

from autocode.core.planning.persistence import save_plan, load_plan, list_plan_summaries, delete_plan
from autocode.core.planning.transitions import validate_transition, InvalidTransitionError
from refract import register_function
from autocode.core.vcs.git import git, git_checked
from autocode.core.planning.models import (
    CommitPlan,
    CommitPlanSummary,
    CommitPlanList,
    DeleteResult,
)

logger = logging.getLogger(__name__)


# ==============================================================================
# REGISTERED ENDPOINTS — CRUD
# ==============================================================================


@register_function(http_methods=["POST"], interfaces=["api"])
def create_commit_plan(
    title: str,
    description: str = "",
) -> CommitPlan:
    """
    Crea un nuevo plan de commit.

    Auto-rellena parent_commit (HEAD actual), branch, timestamps e ID.

    Args:
        title: Mensaje de commit futuro
        description: Instrucciones freeform del commit (markdown)
    """
    try:
        now = datetime.now()
        plan_id = now.strftime("%Y%m%d-%H%M%S")

        plan = CommitPlan(
            id=plan_id,
            title=title,
            description=description,
            parent_commit=git("rev-parse", "HEAD"),
            branch=git("rev-parse", "--abbrev-ref", "HEAD"),
            status="draft",
            created_at=now.isoformat(),
            updated_at=now.isoformat(),
        )

        save_plan(plan)
        return plan
    except Exception as e:
        logger.error(f"Error creando plan: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@register_function(http_methods=["GET"], interfaces=["api", "cli"])
def list_commit_plans(status: str = "") -> CommitPlanList:
    """
    Lista todos los planes de commit guardados.

    Retorna versiones ligeras (CommitPlanSummary) para listados.
    Filtro opcional por status (draft, ready, abandoned).

    Args:
        status: Filtrar por estado (vacío = todos)
    """
    try:
        summaries = list_plan_summaries(status)
        return CommitPlanList(plans=summaries)
    except Exception as e:
        logger.error(f"Error listando planes: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@register_function(http_methods=["GET"], interfaces=["api"])
def get_commit_plan(plan_id: str) -> CommitPlan:
    """
    Obtiene el detalle completo de un plan de commit.

    Args:
        plan_id: ID del plan (formato YYYYMMDD-HHMMSS)
    """
    try:
        plan = load_plan(plan_id)
        if plan is None:
            raise HTTPException(status_code=404, detail=f"Plan '{plan_id}' no encontrado")
        return plan
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error obteniendo plan {plan_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@register_function(http_methods=["PUT"], interfaces=["api"])
def update_commit_plan(
    plan_id: str,
    title: str = "",
    description: str = "",
    status: str = "",
) -> CommitPlan:
    """
    Actualiza parcialmente un plan de commit.

    Solo los campos proporcionados (no vacíos) se sobreescriben.

    Args:
        plan_id: ID del plan a actualizar
        title: Nuevo título (vacío = no cambiar)
        description: Nueva descripción (vacío = no cambiar)
        status: Nuevo estado: draft, ready, abandoned (vacío = no cambiar)
    """
    # Statuses that can be set manually via update endpoint
    MANUALLY_SETTABLE = {"draft", "ready", "abandoned"}

    try:
        plan = load_plan(plan_id)
        if plan is None:
            raise HTTPException(status_code=404, detail=f"Plan '{plan_id}' no encontrado")

        # Handle status change
        if status:
            # Recovery: plan stuck in "executing" without completed_at → allow reset to draft
            if _try_recover_stuck_plan(plan, status):
                save_plan(plan)
                return plan

            # Only allow manually settable statuses through this endpoint
            if status not in MANUALLY_SETTABLE:
                raise HTTPException(
                    status_code=400,
                    detail=f"Status '{status}' is managed by the executor and cannot be set manually",
                )

            # Validate the transition is allowed by the state machine
            try:
                validate_transition(plan.status, status)
            except InvalidTransitionError as e:
                raise HTTPException(status_code=400, detail=str(e))

            plan.status = status

        # Partial update of other fields
        if title:
            plan.title = title
        if description:
            plan.description = description

        plan.updated_at = datetime.now().isoformat()
        save_plan(plan)
        return plan
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error actualizando plan {plan_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@register_function(http_methods=["DELETE"], interfaces=["api"])
def delete_commit_plan(plan_id: str) -> DeleteResult:
    """
    Elimina un plan de commit.

    Args:
        plan_id: ID del plan a eliminar
    """
    try:
        deleted = delete_plan(plan_id)
        if not deleted:
            raise HTTPException(status_code=404, detail=f"Plan '{plan_id}' no encontrado")
        return DeleteResult(deleted=plan_id)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error eliminando plan {plan_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==============================================================================
# PRIVATE HELPERS
# ==============================================================================


def _try_recover_stuck_plan(plan: CommitPlan, target_status: str) -> bool:
    """Try to recover a plan stuck in 'executing' state.

    A plan gets stuck when execution dies (crash, timeout, browser refresh).
    If the plan is in 'executing' with no completed_at, allow reset to draft.

    Returns True if recovery was performed, False otherwise.
    """
    if (
        target_status == "draft"
        and plan.status == "executing"
        and (plan.execution is None or not plan.execution.completed_at)
    ):
        plan.status = "draft"
        plan.execution = None
        plan.updated_at = datetime.now().isoformat()
        logger.info(f"Plan '{plan.id}' recovered from stuck executing → draft")
        return True
    return False
