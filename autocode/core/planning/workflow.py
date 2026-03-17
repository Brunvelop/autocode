"""
workflow.py
Git-related workflow operations for commit plans.

Extracted from planner.py — handles approve, revert, and review metrics
retrieval. These operations interact with git (add, commit, checkout)
and transition plans to terminal states (completed, reverted).
"""
import logging
from datetime import datetime

from autocode.core.vcs.git import git_checked
from autocode.core.planning.persistence import load_plan, save_plan
from autocode.core.planning.transitions import REVIEWABLE_STATUSES
from autocode.core.registry import register_function
from autocode.core.models import GenericOutput
from autocode.core.planning.models import CommitPlanOutput

logger = logging.getLogger(__name__)


# ==============================================================================
# REGISTERED ENDPOINTS — APPROVE / REVERT
# ==============================================================================


@register_function(http_methods=["POST"], interfaces=["api", "mcp"])
def approve_plan(plan_id: str, commit_message: str = "") -> CommitPlanOutput:
    """Aprueba un plan en pending_review: git add + commit → completed.

    Ejecuta git add para cada archivo cambiado, luego git commit
    con el título del plan (o un mensaje personalizado).
    Almacena el commit hash resultante en execution.commit_hash.

    Args:
        plan_id: ID del plan a aprobar
        commit_message: Mensaje de commit personalizado (vacío = usar plan.title)
    """
    try:
        plan = load_plan(plan_id)
        if plan is None:
            return CommitPlanOutput(
                success=False,
                message=f"Plan '{plan_id}' no encontrado",
            )

        if plan.status not in REVIEWABLE_STATUSES:
            return CommitPlanOutput(
                success=False,
                message=(
                    f"Cannot approve plan in status '{plan.status}'. "
                    f"Must be in: {', '.join(sorted(REVIEWABLE_STATUSES))}"
                ),
            )

        # Get files to commit from execution state
        files = (
            plan.execution.files_changed
            if plan.execution and plan.execution.files_changed
            else []
        )

        # git add + commit (use _git_checked to detect failures)
        message = commit_message or plan.title
        for f in files:
            git_checked("add", f)
        git_checked("commit", "-m", message)
        commit_hash = git_checked("rev-parse", "HEAD")

        # Update plan state
        if plan.execution:
            plan.execution.commit_hash = commit_hash
        plan.status = "completed"
        plan.updated_at = datetime.now().isoformat()
        save_plan(plan)

        logger.info(f"Plan '{plan_id}' approved and committed: {commit_hash}")
        return CommitPlanOutput(
            success=True,
            result=plan,
            message=f"Plan '{plan_id}' approved. Commit: {commit_hash}",
        )
    except Exception as e:
        logger.error(f"Error approving plan {plan_id}: {e}")
        return CommitPlanOutput(success=False, message=str(e))


@register_function(http_methods=["POST"], interfaces=["api", "mcp"])
def revert_plan(plan_id: str) -> CommitPlanOutput:
    """Revierte cambios de un plan: git checkout -- files → reverted.

    Restaura cada archivo modificado al estado del parent_commit
    del plan usando git checkout. Marca el plan como 'reverted'.

    Args:
        plan_id: ID del plan a revertir
    """
    try:
        plan = load_plan(plan_id)
        if plan is None:
            return CommitPlanOutput(
                success=False,
                message=f"Plan '{plan_id}' no encontrado",
            )

        if plan.status not in REVIEWABLE_STATUSES:
            return CommitPlanOutput(
                success=False,
                message=(
                    f"Cannot revert plan in status '{plan.status}'. "
                    f"Must be in: {', '.join(sorted(REVIEWABLE_STATUSES))}"
                ),
            )

        # Get files to revert from execution state
        files = (
            plan.execution.files_changed
            if plan.execution and plan.execution.files_changed
            else []
        )

        if not files:
            return CommitPlanOutput(
                success=False,
                message=f"Plan '{plan_id}' has no files to revert (files_changed is empty)",
            )

        # git checkout {parent_commit} -- file1 file2 ... (use _git_checked to detect failures)
        ref = plan.parent_commit or "HEAD"
        for f in files:
            git_checked("checkout", ref, "--", f)

        # Update plan state
        plan.status = "reverted"
        plan.updated_at = datetime.now().isoformat()
        save_plan(plan)

        logger.info(
            f"Plan '{plan_id}' reverted: {len(files)} files restored to {ref}"
        )
        return CommitPlanOutput(
            success=True,
            result=plan,
            message=f"Plan '{plan_id}' reverted. {len(files)} files restored.",
        )
    except Exception as e:
        logger.error(f"Error reverting plan {plan_id}: {e}")
        return CommitPlanOutput(success=False, message=str(e))


# ==============================================================================
# REGISTERED ENDPOINTS — REVIEW METRICS
# ==============================================================================


@register_function(http_methods=["GET"], interfaces=["api"])
def get_plan_review_metrics(plan_id: str) -> GenericOutput:
    """Retorna métricas de review de un plan para la UI.

    Extrae file_metrics, quality_gates y summary del ReviewResult
    almacenado en plan.execution.review. Formato compatible con
    la tabla combinada de commit-detail.js.

    Args:
        plan_id: ID del plan
    """
    try:
        plan = load_plan(plan_id)
        if plan is None:
            return GenericOutput(
                success=False, result=None,
                message=f"Plan '{plan_id}' no encontrado",
            )

        review = plan.execution.review if plan.execution else None
        if review is None:
            return GenericOutput(
                success=True,
                result={"files": [], "summary": {}, "quality_gates": {}},
                message="No review data available",
            )

        # Transform file_metrics to flat format compatible with commit-detail table
        files = []
        for fm in review.file_metrics:
            files.append({
                "path": fm.path,
                "before": fm.before,
                "after": fm.after,
                **fm.deltas,
            })

        return GenericOutput(
            success=True,
            result={
                "files": files,
                "summary": {
                    "verdict": review.verdict,
                    "summary": review.summary,
                    "mode": review.mode,
                    "reviewed_at": review.reviewed_at,
                    "reviewed_by": review.reviewed_by,
                    "issues": review.issues,
                    "suggestions": review.suggestions,
                },
                "quality_gates": review.quality_gates,
            },
            message=f"Review metrics for plan '{plan_id}'",
        )
    except Exception as e:
        logger.error(f"Error getting review metrics for {plan_id}: {e}")
        return GenericOutput(success=False, result=None, message=str(e))
