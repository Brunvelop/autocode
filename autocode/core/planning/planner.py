"""
planner.py
CRUD de planes de commit.

Persistencia en .autocode/plans/{id}.json.
Sigue el patrón de autocode/core/code/metrics.py para
persistencia, helpers git y endpoints registrados.

Los planes se crean vía chat (el agente usa create_commit_plan
con toda la información recopilada durante la conversación).
"""
import json
import logging
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Optional

from autocode.interfaces.registry import register_function
from autocode.interfaces.models import GenericOutput
from autocode.core.planning.models import (
    PlanTask,
    PlanContext,
    CommitPlan,
    CommitPlanSummary,
    CommitPlanOutput,
    CommitPlanListOutput,
)

logger = logging.getLogger(__name__)

# Directorio de planes (relativo al CWD del proyecto host)
PLANS_DIR = ".autocode/plans"


# ==============================================================================
# REGISTERED ENDPOINTS — CRUD
# ==============================================================================


@register_function(http_methods=["POST"], interfaces=["api", "mcp"])
def create_commit_plan(
    title: str,
    description: str = "",
    tasks_json: str = "",
    context_json: str = "",
    tags: str = "",
) -> CommitPlanOutput:
    """
    Crea un nuevo plan de commit.

    Auto-rellena parent_commit (HEAD actual), branch, timestamps e ID.
    tasks_json y context_json son JSON strings opcionales.

    Args:
        title: Mensaje de commit futuro
        description: Por qué este commit es necesario
        tasks_json: JSON array de tareas [{type, path, description, details?, acceptance_criteria?}]
        context_json: JSON object de contexto {relevant_files?, relevant_dccs?, architectural_notes?}
        tags: Tags separados por coma
    """
    try:
        now = datetime.now()
        plan_id = now.strftime("%Y%m%d-%H%M%S")

        # Parse tasks
        tasks = []
        if tasks_json and tasks_json.strip():
            raw_tasks = json.loads(tasks_json)
            tasks = [PlanTask(**t) for t in raw_tasks]

        # Parse context
        context = PlanContext()
        if context_json and context_json.strip():
            raw_context = json.loads(context_json)
            context = PlanContext(**raw_context)

        # Parse tags
        tag_list = [t.strip() for t in tags.split(",") if t.strip()] if tags else []

        plan = CommitPlan(
            id=plan_id,
            title=title,
            description=description,
            parent_commit=_git("rev-parse", "HEAD"),
            branch=_git("rev-parse", "--abbrev-ref", "HEAD"),
            status="draft",
            tasks=tasks,
            context=context,
            created_at=now.isoformat(),
            updated_at=now.isoformat(),
            tags=tag_list,
        )

        _save_plan(plan)

        return CommitPlanOutput(
            success=True,
            result=plan,
            message=f"Plan '{plan_id}' creado: {title}",
        )
    except Exception as e:
        logger.error(f"Error creando plan: {e}")
        return CommitPlanOutput(success=False, message=str(e))


@register_function(http_methods=["GET"], interfaces=["api", "mcp"])
def list_commit_plans(status: str = "") -> CommitPlanListOutput:
    """
    Lista todos los planes de commit guardados.

    Retorna versiones ligeras (CommitPlanSummary) para listados.
    Filtro opcional por status (draft, ready, abandoned).

    Args:
        status: Filtrar por estado (vacío = todos)
    """
    try:
        summaries = _list_plan_summaries(status)
        return CommitPlanListOutput(
            success=True,
            result=summaries,
            message=f"{len(summaries)} planes encontrados",
        )
    except Exception as e:
        logger.error(f"Error listando planes: {e}")
        return CommitPlanListOutput(success=False, message=str(e))


@register_function(http_methods=["GET"], interfaces=["api", "mcp"])
def get_commit_plan(plan_id: str) -> CommitPlanOutput:
    """
    Obtiene el detalle completo de un plan de commit.

    Args:
        plan_id: ID del plan (formato YYYYMMDD-HHMMSS)
    """
    try:
        plan = _load_plan(plan_id)
        if plan is None:
            return CommitPlanOutput(success=False, message=f"Plan '{plan_id}' no encontrado")

        return CommitPlanOutput(
            success=True,
            result=plan,
            message=f"Plan '{plan_id}': {plan.title}",
        )
    except Exception as e:
        logger.error(f"Error obteniendo plan {plan_id}: {e}")
        return CommitPlanOutput(success=False, message=str(e))


@register_function(http_methods=["POST"], interfaces=["api", "mcp"])
def update_commit_plan(
    plan_id: str,
    title: str = "",
    description: str = "",
    status: str = "",
    tasks_json: str = "",
    context_json: str = "",
    tags: str = "",
) -> CommitPlanOutput:
    """
    Actualiza parcialmente un plan de commit.

    Solo los campos proporcionados (no vacíos) se sobreescriben.

    Args:
        plan_id: ID del plan a actualizar
        title: Nuevo título (vacío = no cambiar)
        description: Nueva descripción (vacío = no cambiar)
        status: Nuevo estado: draft, ready, abandoned (vacío = no cambiar)
        tasks_json: JSON array de tareas (vacío = no cambiar)
        context_json: JSON object de contexto (vacío = no cambiar)
        tags: Tags separados por coma (vacío = no cambiar)
    """
    try:
        plan = _load_plan(plan_id)
        if plan is None:
            return CommitPlanOutput(success=False, message=f"Plan '{plan_id}' no encontrado")

        # Actualización parcial
        if title:
            plan.title = title
        if description:
            plan.description = description
        if status and status in ("draft", "ready", "abandoned"):
            plan.status = status
        if tasks_json and tasks_json.strip():
            raw_tasks = json.loads(tasks_json)
            plan.tasks = [PlanTask(**t) for t in raw_tasks]
        if context_json and context_json.strip():
            raw_context = json.loads(context_json)
            plan.context = PlanContext(**raw_context)
        if tags:
            plan.tags = [t.strip() for t in tags.split(",") if t.strip()]

        plan.updated_at = datetime.now().isoformat()
        _save_plan(plan)

        return CommitPlanOutput(
            success=True,
            result=plan,
            message=f"Plan '{plan_id}' actualizado",
        )
    except Exception as e:
        logger.error(f"Error actualizando plan {plan_id}: {e}")
        return CommitPlanOutput(success=False, message=str(e))


@register_function(http_methods=["POST"], interfaces=["api", "mcp"])
def delete_commit_plan(plan_id: str) -> GenericOutput:
    """
    Elimina un plan de commit.

    Args:
        plan_id: ID del plan a eliminar
    """
    try:
        plans_dir = Path(PLANS_DIR)
        plan_file = plans_dir / f"{plan_id}.json"

        if not plan_file.exists():
            return GenericOutput(success=False, result=None, message=f"Plan '{plan_id}' no encontrado")

        plan_file.unlink()

        return GenericOutput(
            success=True,
            result={"deleted": plan_id},
            message=f"Plan '{plan_id}' eliminado",
        )
    except Exception as e:
        logger.error(f"Error eliminando plan {plan_id}: {e}")
        return GenericOutput(success=False, result=None, message=str(e))


# ==============================================================================
# PLAN PERSISTENCE
# ==============================================================================


def _save_plan(plan: CommitPlan) -> None:
    """Save plan as JSON in .autocode/plans/."""
    plans_dir = Path(PLANS_DIR)
    plans_dir.mkdir(parents=True, exist_ok=True)
    path = plans_dir / f"{plan.id}.json"
    path.write_text(plan.model_dump_json(indent=2), encoding="utf-8")
    logger.debug(f"Plan saved: {path}")


def _load_plan(plan_id: str) -> Optional[CommitPlan]:
    """Load a plan by ID."""
    plans_dir = Path(PLANS_DIR)
    plan_file = plans_dir / f"{plan_id}.json"
    if not plan_file.exists():
        return None
    try:
        data = json.loads(plan_file.read_text(encoding="utf-8"))
        return CommitPlan(**data)
    except Exception as e:
        logger.error(f"Error loading plan {plan_id}: {e}")
        return None


def _list_plan_summaries(status_filter: str = "") -> list[CommitPlanSummary]:
    """List all plans as summaries, optionally filtered by status."""
    plans_dir = Path(PLANS_DIR)
    if not plans_dir.exists():
        return []

    summaries = []
    for f in sorted(plans_dir.glob("*.json"), reverse=True):
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


# ==============================================================================
# GIT HELPERS
# ==============================================================================


def _git(*args: str) -> str:
    """Run a git command and return stripped stdout."""
    result = subprocess.run(
        ["git"] + list(args),
        capture_output=True, text=True, check=False,
    )
    return result.stdout.strip()
