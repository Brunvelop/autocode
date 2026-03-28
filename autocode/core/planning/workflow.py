"""
workflow.py
Git-related workflow operations for commit plans.

Extracted from planner.py — handles approve, revert, and review metrics
retrieval. These operations interact with git (add, commit, checkout)
and transition plans to terminal states (completed, reverted).
"""
import logging
from datetime import datetime

from fastapi import HTTPException

from autocode.core.vcs.git import git_checked
from autocode.core.planning.persistence import load_plan, save_plan
from autocode.core.planning.transitions import REVIEWABLE_STATUSES
from refract import register_function
from autocode.core.planning.models import CommitPlan, PlanReviewMetrics

logger = logging.getLogger(__name__)


# ==============================================================================
# REGISTERED ENDPOINTS — APPROVE / REVERT
# ==============================================================================


@register_function(http_methods=["POST"], interfaces=["api", "mcp"])
def approve_plan(plan_id: str, commit_message: str = "") -> CommitPlan:
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
            raise HTTPException(status_code=404, detail=f"Plan '{plan_id}' no encontrado")

        if plan.status not in REVIEWABLE_STATUSES:
            raise HTTPException(
                status_code=400,
                detail=(
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

        # git add + commit (use git_checked to detect failures)
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
        return plan
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error approving plan {plan_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@register_function(http_methods=["POST"], interfaces=["api", "mcp"])
def revert_plan(plan_id: str) -> CommitPlan:
    """Revierte cambios de un plan: git checkout -- files → reverted.

    Restaura cada archivo modificado al estado del parent_commit
    del plan usando git checkout. Marca el plan como 'reverted'.

    Args:
        plan_id: ID del plan a revertir
    """
    try:
        plan = load_plan(plan_id)
        if plan is None:
            raise HTTPException(status_code=404, detail=f"Plan '{plan_id}' no encontrado")

        if plan.status not in REVIEWABLE_STATUSES:
            raise HTTPException(
                status_code=400,
                detail=(
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

        if not files and plan.parent_commit:
            # Fallback: recompute from parent_commit diff
            logger.info(
                f"Plan '{plan_id}' has empty files_changed, "
                f"recomputing from parent_commit via git diff"
            )
            diff_output = git_checked("diff", "--name-only", plan.parent_commit)
            files = [f for f in diff_output.split("\n") if f]

        if not files:
            raise HTTPException(
                status_code=400,
                detail=f"Plan '{plan_id}' has no files to revert (files_changed is empty)",
            )

        # git checkout {parent_commit} -- file1 file2 ... (use git_checked to detect failures)
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
        return plan
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error reverting plan {plan_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==============================================================================
# REGISTERED ENDPOINTS — REVIEW METRICS
# ==============================================================================


@register_function(http_methods=["GET"], interfaces=["api"])
def get_plan_review_metrics(plan_id: str) -> PlanReviewMetrics:
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
            raise HTTPException(status_code=404, detail=f"Plan '{plan_id}' no encontrado")

        review = plan.execution.review if plan.execution else None
        if review is None:
            return PlanReviewMetrics(files=[], summary={}, quality_gates={})

        # Transform file_metrics to flat format compatible with commit-detail table
        files = []
        for fm in review.file_metrics:
            files.append({
                "path": fm.path,
                "before": fm.before,
                "after": fm.after,
                **fm.deltas,
            })

        return PlanReviewMetrics(
            files=files,
            summary={
                "verdict": review.verdict,
                "summary": review.summary,
                "mode": review.mode,
                "reviewed_at": review.reviewed_at,
                "reviewed_by": review.reviewed_by,
                "issues": review.issues,
                "suggestions": review.suggestions,
            },
            quality_gates=review.quality_gates,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting review metrics for {plan_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
