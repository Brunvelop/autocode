"""
models.py
Modelos de datos para planificación de commits.

Permite diseñar commits futuros desde la UI, almacenarlos como planes
estructurados en .autocode/plans/ y visualizarlos como ghost nodes en git-graph.
"""

from typing import List, Optional, Literal
from pydantic import BaseModel, Field

from autocode.interfaces.models import GenericOutput


# Tipos de tarea soportados (no restrictivo — str libre con ejemplos sugeridos)
# Los iconos de la UI están en commit-plan-detail.js TASK_ICONS

# Estados de un plan
PlanStatus = Literal["draft", "ready", "executing", "completed", "failed", "abandoned"]

# Estados de ejecución de una tarea individual
TaskStatus = Literal["pending", "running", "completed", "failed", "skipped"]


class TaskExecutionResult(BaseModel):
    """
    Resultado de ejecución de una tarea individual.
    
    Registra el estado, tiempos, resumen del LLM y archivos
    modificados durante la ejecución de una task.
    """
    task_index: int = Field(..., description="Índice de la tarea en el plan")
    status: TaskStatus = Field("pending", description="Estado de ejecución")
    started_at: str = Field("", description="Inicio de ejecución ISO")
    completed_at: str = Field("", description="Fin de ejecución ISO")
    error: str = Field("", description="Mensaje de error si falló")
    llm_summary: str = Field("", description="Resumen generado por el LLM de los cambios realizados")
    files_changed: List[str] = Field(default_factory=list, description="Archivos creados/modificados/eliminados")
    prompt_tokens: int = Field(0, description="Tokens de prompt consumidos")
    completion_tokens: int = Field(0, description="Tokens de completion generados")
    total_tokens: int = Field(0, description="Total tokens consumidos")
    total_cost: float = Field(0.0, description="Coste total en USD")


class PlanExecutionState(BaseModel):
    """
    Estado completo de ejecución de un plan.
    
    Contiene metadata de la ejecución (modelo, tiempos) y
    los resultados individuales de cada tarea.
    """
    started_at: str = Field("", description="Inicio de ejecución ISO")
    completed_at: str = Field("", description="Fin de ejecución ISO")
    model_used: str = Field("", description="Modelo de inferencia utilizado")
    task_results: List[TaskExecutionResult] = Field(default_factory=list, description="Resultados por tarea")
    commit_hash: str = Field("", description="Hash del commit generado (si auto_commit)")
    total_tokens: int = Field(0, description="Total tokens de todas las tareas")
    total_cost: float = Field(0.0, description="Coste total en USD de toda la ejecución")


class PlanTask(BaseModel):
    """
    Tarea individual dentro de un plan de commit.
    
    Representa una operación atómica sobre un archivo:
    crear, modificar, eliminar o renombrar.
    """
    type: str = Field(..., description="Tipo de operación (ej: create, modify, delete, rename, refactor, fix, enhance, test)")
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
    execution: Optional[PlanExecutionState] = Field(None, description="Estado de ejecución (gestionado por el executor)")


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
