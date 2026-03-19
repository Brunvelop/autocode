"""
models.py
Modelos de datos para planificación de commits.

Permite diseñar commits futuros desde la UI, almacenarlos como planes
estructurados en .autocode/plans/ y visualizarlos como ghost nodes en git-dashboard.
"""

from typing import List, Optional, Literal
from pydantic import BaseModel, Field

from autocode.core.models import GenericOutput


# Estados de un plan
PlanStatus = Literal[
    "draft", "ready", "executing",
    "pending_review",                    # review flow
    "completed", "failed",
    "reverted", "abandoned",             # reverted = post-review revert
]


class ReviewFileMetrics(BaseModel):
    """
    Métricas before/after de un archivo individual durante review.
    
    Permite comparar el estado del archivo antes y después de la
    ejecución del plan para evaluar quality gates.
    """
    path: str = Field(..., description="Ruta del archivo analizado")
    before: dict = Field(default_factory=dict, description="Métricas pre-cambio {sloc, avg_complexity, max_complexity, mi, ...}")
    after: dict = Field(default_factory=dict, description="Métricas post-cambio")
    deltas: dict = Field(default_factory=dict, description="Diferencias calculadas {delta_sloc, delta_complexity, ...}")


class ReviewResult(BaseModel):
    """
    Resultado de la revisión post-ejecución de un plan.
    
    Contiene el veredicto (approved/rejected/needs_changes),
    métricas por archivo y estado de quality gates.
    """
    mode: Literal["auto", "human"] = Field(..., description="Modo de review: auto o human")
    verdict: Literal["approved", "rejected", "needs_changes"] = Field(..., description="Veredicto de la revisión")
    summary: str = Field("", description="Resumen de la revisión")
    issues: List[str] = Field(default_factory=list, description="Problemas encontrados")
    suggestions: List[str] = Field(default_factory=list, description="Sugerencias de mejora")
    file_metrics: List[ReviewFileMetrics] = Field(default_factory=list, description="Métricas before/after por archivo")
    quality_gates: dict = Field(default_factory=dict, description="Estado de quality gates {gate_name: passed}")
    reviewed_at: str = Field("", description="Fecha de revisión ISO")
    reviewed_by: str = Field("", description="Quién revisó: 'auto' o nombre del usuario")


class ExecutionStep(BaseModel):
    """
    Paso individual de ejecución registrado por un backend.

    Cada step representa una acción atómica: pensamiento del LLM,
    uso de herramienta, texto generado o error.
    """
    timestamp: str = Field("", description="Timestamp ISO del paso")
    type: str = Field("", description="Tipo de paso: tool_use, thinking, text, error, etc.")
    content: str = Field("", description="Contenido del paso")
    tool: str = Field("", description="Herramienta usada (read_file, write_file, etc.)")
    path: str = Field("", description="Archivo afectado")


class PlanExecutionState(BaseModel):
    """
    Estado completo de ejecución de un plan.

    Contiene metadata de la ejecución (modelo, tiempos, backend)
    y los pasos registrados durante la ejecución.
    """
    started_at: str = Field("", description="Inicio de ejecución ISO")
    completed_at: str = Field("", description="Fin de ejecución ISO")
    model_used: str = Field("", description="Modelo de inferencia utilizado")
    steps: List[ExecutionStep] = Field(default_factory=list, description="Pasos de ejecución registrados")
    backend: str = Field("", description="Backend usado para la ejecución (opencode, cline, dspy)")
    session_id: str = Field("", description="ID de sesión del backend")
    commit_hash: str = Field("", description="Hash del commit generado (si auto_commit)")
    total_tokens: int = Field(0, description="Total tokens consumidos")
    total_cost: float = Field(0.0, description="Coste total en USD de toda la ejecución")
    files_changed: List[str] = Field(default_factory=list, description="Archivos modificados durante ejecución (para revert)")
    error: str = Field("", description="Mensaje de error si la ejecución falló inesperadamente")
    review: Optional[ReviewResult] = Field(None, description="Resultado de la revisión post-ejecución")


class CommitPlan(BaseModel):
    """
    Plan completo para un commit futuro.
    
    Contiene toda la información necesaria para entender, revisar
    y eventualmente ejecutar un commit planificado.
    """
    id: str = Field(..., description="ID único del plan (formato: YYYYMMDD-HHMMSS)")
    title: str = Field(..., description="Futuro mensaje de commit")
    description: str = Field("", description="Instrucciones freeform del commit (markdown)")
    parent_commit: str = Field("", description="Hash de HEAD cuando se creó el plan")
    branch: str = Field("", description="Branch donde se planificó")
    status: PlanStatus = Field("draft", description="Estado del plan: draft, ready, abandoned")
    created_at: str = Field("", description="Fecha de creación ISO")
    updated_at: str = Field("", description="Fecha de última actualización ISO")
    execution: Optional[PlanExecutionState] = Field(None, description="Estado de ejecución (gestionado por el executor)")


class CommitPlanSummary(BaseModel):
    """
    Versión ligera de CommitPlan para listados.
    
    Solo contiene la información mínima para renderizar
    ghost nodes en el git-dashboard.
    """
    id: str = Field(..., description="ID único del plan")
    title: str = Field(..., description="Futuro mensaje de commit")
    status: PlanStatus = Field("draft", description="Estado del plan")
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
