"""
models.py
Modelos de datos para planificación de commits.

Permite diseñar commits futuros desde la UI, almacenarlos como planes
estructurados en .autocode/plans/ y visualizarlos como ghost nodes en git-graph.
"""

from typing import List, Optional, Literal
from pydantic import BaseModel, Field

from autocode.interfaces.models import GenericOutput


# Tipos de tarea soportados
TaskType = Literal["create", "modify", "delete", "rename"]

# Estados de un plan
PlanStatus = Literal["draft", "ready", "abandoned"]


class PlanTask(BaseModel):
    """
    Tarea individual dentro de un plan de commit.
    
    Representa una operación atómica sobre un archivo:
    crear, modificar, eliminar o renombrar.
    """
    type: TaskType = Field(..., description="Tipo de operación: create, modify, delete, rename")
    path: str = Field(..., description="Archivo objetivo de la operación")
    description: str = Field(..., description="Qué hacer (1 línea)")
    details: str = Field("", description="Instrucciones detalladas de implementación")
    acceptance_criteria: List[str] = Field(default_factory=list, description="Criterios de validación")


class PlanContext(BaseModel):
    """
    Contexto de referencia para un plan de commit.
    
    Archivos relevantes, DCCs y notas arquitectónicas que
    ayudan a entender y ejecutar el plan.
    """
    relevant_files: List[str] = Field(default_factory=list, description="Archivos a leer para contexto")
    relevant_dccs: List[str] = Field(default_factory=list, description="DCCs de referencia")
    architectural_notes: str = Field("", description="Notas de diseño y arquitectura")


class CommitPlan(BaseModel):
    """
    Plan completo para un commit futuro.
    
    Contiene toda la información necesaria para entender, revisar
    y eventualmente ejecutar un commit planificado.
    """
    id: str = Field(..., description="ID único del plan (formato: YYYYMMDD-HHMMSS)")
    title: str = Field(..., description="Futuro mensaje de commit")
    description: str = Field("", description="Por qué este commit es necesario")
    parent_commit: str = Field("", description="Hash de HEAD cuando se creó el plan")
    branch: str = Field("", description="Branch donde se planificó")
    status: PlanStatus = Field("draft", description="Estado del plan: draft, ready, abandoned")
    tasks: List[PlanTask] = Field(default_factory=list, description="Tareas del plan")
    context: PlanContext = Field(default_factory=PlanContext, description="Contexto de referencia")
    created_at: str = Field("", description="Fecha de creación ISO")
    updated_at: str = Field("", description="Fecha de última actualización ISO")
    tags: List[str] = Field(default_factory=list, description="Etiquetas de clasificación")
    conversation_log: List[dict] = Field(default_factory=list, description="Historial del chat usado para planificar")


class CommitPlanSummary(BaseModel):
    """
    Versión ligera de CommitPlan para listados.
    
    Solo contiene la información mínima para renderizar
    ghost nodes en el git-graph.
    """
    id: str = Field(..., description="ID único del plan")
    title: str = Field(..., description="Futuro mensaje de commit")
    status: PlanStatus = Field("draft", description="Estado del plan")
    tasks_count: int = Field(0, description="Número de tareas")
    created_at: str = Field("", description="Fecha de creación ISO")
    branch: str = Field("", description="Branch donde se planificó")


# ==============================================================================
# OUTPUT MODELS (GenericOutput wrappers)
# ==============================================================================


class CommitPlanOutput(GenericOutput):
    """Output de create/get/update commit plan."""
    result: Optional[CommitPlan] = None


class CommitPlanListOutput(GenericOutput):
    """Output de list_commit_plans."""
    result: Optional[List[CommitPlanSummary]] = None
