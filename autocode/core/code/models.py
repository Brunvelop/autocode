"""
models.py
Modelos de datos para estructura de código normalizada.

Usa estructura plana (adjacency list) para evitar recursión en OpenAPI schema.
Similar a GitNodeEntry/GitTreeGraph en autocode/core/vcs/models.py.
"""

from typing import List, Optional, Literal
from pydantic import BaseModel, Field

from autocode.interfaces.models import GenericOutput


# Tipos de nodos soportados
NodeType = Literal["directory", "file", "class", "function", "method", "import", "variable"]

# Lenguajes soportados
Language = Literal["python", "javascript"]


class CodeNode(BaseModel):
    """
    Nodo normalizado de estructura de código (no-recursivo / adjacency list).
    
    Representa directorios, archivos, clases, funciones, etc.
    La relación padre-hijo se establece via parent_id, no con children anidados.
    """
    id: str = Field(..., description="ID único del nodo (path::name para código interno)")
    parent_id: Optional[str] = Field(None, description="ID del nodo padre; None solo para root")
    name: str = Field(..., description="Nombre display del nodo")
    type: NodeType = Field(..., description="Tipo de nodo")
    language: Optional[Language] = Field(None, description="Lenguaje del código (null para directorios)")
    path: str = Field(..., description="Path relativo al root")
    line_start: Optional[int] = Field(None, description="Línea de inicio (solo para código)")
    line_end: Optional[int] = Field(None, description="Línea de fin (solo para código)")
    loc: int = Field(0, description="Lines of code")
    
    # Metadata adicional según tipo
    decorators: Optional[List[str]] = Field(None, description="Decoradores (funciones/clases Python)")
    params: Optional[List[str]] = Field(None, description="Parámetros (funciones)")
    bases: Optional[List[str]] = Field(None, description="Clases base (herencia)")
    exports: Optional[bool] = Field(None, description="Es exportado (JS)")
    is_async: Optional[bool] = Field(None, description="Es async (funciones)")


class CodeGraph(BaseModel):
    """
    Representación no-recursiva del árbol de código como grafo.
    
    El frontend puede reconstruir el árbol usando parent_id de cada nodo.
    """
    root_id: str = Field(..., description="ID del nodo raíz")
    nodes: List[CodeNode] = Field(default_factory=list, description="Todos los nodos del árbol")


class CodeStructureResult(BaseModel):
    """
    Resultado de análisis de estructura de código.
    """
    graph: CodeGraph = Field(..., description="Grafo de nodos (no recursivo)")
    languages: List[str] = Field(default_factory=list, description="Lenguajes detectados")
    total_files: int = Field(0, description="Total de archivos")
    total_loc: int = Field(0, description="Total de líneas de código")
    total_functions: int = Field(0, description="Total de funciones")
    total_classes: int = Field(0, description="Total de clases")


class CodeStructureOutput(GenericOutput):
    """
    Output de get_code_structure().
    Extiende GenericOutput con tipado específico para result.
    """
    result: Optional[CodeStructureResult] = None


# ==============================================================================
# CODE METRICS MODELS
# ==============================================================================


class FunctionMetrics(BaseModel):
    """Métricas de complejidad de una función/método individual."""

    name: str = Field(..., description="Nombre de la función/método")
    file: str = Field(..., description="Path del archivo")
    line: int = Field(0, description="Línea de inicio")
    complexity: int = Field(0, description="Complejidad ciclomática")
    rank: str = Field("A", description="Grado de complejidad (A-F)")
    nesting_depth: int = Field(0, description="Profundidad máxima de anidamiento")
    sloc: int = Field(0, description="Líneas de código fuente")
    is_method: bool = Field(False, description="Si es método de clase")
    class_name: Optional[str] = Field(None, description="Clase contenedora si es método")


class FileMetrics(BaseModel):
    """Métricas agregadas de un archivo individual."""

    path: str = Field(..., description="Path relativo del archivo")
    language: Optional[Language] = Field(None, description="Lenguaje detectado")
    sloc: int = Field(0, description="Líneas de código fuente (sin blanks ni comments)")
    comments: int = Field(0, description="Líneas de comentario")
    blanks: int = Field(0, description="Líneas en blanco")
    total_loc: int = Field(0, description="Total de líneas")
    functions: List[FunctionMetrics] = Field(default_factory=list, description="Métricas por función")
    classes_count: int = Field(0, description="Número de clases")
    functions_count: int = Field(0, description="Número de funciones/métodos")
    avg_complexity: float = Field(0.0, description="Complejidad ciclomática media")
    max_complexity: int = Field(0, description="Complejidad ciclomática máxima")
    max_nesting: int = Field(0, description="Profundidad máxima de anidamiento")
    maintainability_index: float = Field(100.0, description="Índice de mantenibilidad (0-100)")


class PackageCoupling(BaseModel):
    """Métricas de acoplamiento de un subpaquete."""

    name: str = Field(..., description="Nombre del paquete (ej: autocode.core)")
    ce: int = Field(0, description="Acoplamiento eferente (imports salientes)")
    ca: int = Field(0, description="Acoplamiento aferente (imports entrantes)")
    instability: float = Field(0.0, description="Inestabilidad: Ce/(Ce+Ca). 0=estable, 1=inestable")
    imports_to: List[str] = Field(default_factory=list, description="Paquetes de los que depende")
    imported_by: List[str] = Field(default_factory=list, description="Paquetes que dependen de este")


class MetricsSnapshot(BaseModel):
    """Snapshot completo de métricas de código en un momento dado."""

    commit_hash: str = Field(..., description="Hash completo del commit")
    commit_short: str = Field("", description="Hash abreviado")
    branch: str = Field("", description="Rama activa")
    timestamp: str = Field("", description="Fecha ISO del snapshot")
    # Per-file metrics
    files: List[FileMetrics] = Field(default_factory=list, description="Métricas por archivo")
    # Aggregates
    total_files: int = Field(0)
    total_sloc: int = Field(0)
    total_comments: int = Field(0)
    total_blanks: int = Field(0)
    total_functions: int = Field(0)
    total_classes: int = Field(0)
    avg_complexity: float = Field(0.0)
    avg_mi: float = Field(0.0)
    complexity_distribution: dict = Field(default_factory=dict, description="Distribución {A:n, B:n, ...}")
    # Coupling
    coupling: List[PackageCoupling] = Field(default_factory=list)
    circular_deps: List[List[str]] = Field(default_factory=list)


class MetricsComparison(BaseModel):
    """Comparación entre dos snapshots de métricas."""

    before: Optional[MetricsSnapshot] = Field(None, description="Snapshot anterior (None si es el primero)")
    after: MetricsSnapshot = Field(..., description="Snapshot actual")
    delta_sloc: int = Field(0)
    delta_functions: int = Field(0)
    delta_classes: int = Field(0)
    delta_avg_complexity: float = Field(0.0)
    delta_avg_mi: float = Field(0.0)
    files_improved: List[dict] = Field(default_factory=list, description="Archivos donde CC bajó")
    files_degraded: List[dict] = Field(default_factory=list, description="Archivos donde CC subió")


class CommitFileMetrics(BaseModel):
    """Métricas before/after de un archivo en un commit."""

    path: str = Field(..., description="Path del archivo")
    status: str = Field("modified", description="added/modified/deleted")
    before: Optional[FileMetrics] = Field(None, description="Métricas antes del commit")
    after: Optional[FileMetrics] = Field(None, description="Métricas después del commit")
    delta_sloc: int = Field(0)
    delta_complexity: float = Field(0.0)
    delta_mi: float = Field(0.0)


class CommitMetrics(BaseModel):
    """Métricas de impacto de un commit específico."""

    commit_hash: str = Field(...)
    commit_short: str = Field("")
    files: List[CommitFileMetrics] = Field(default_factory=list)
    summary: dict = Field(default_factory=dict, description="Resumen: delta_sloc, delta_cc, etc.")


# ==============================================================================
# METRICS OUTPUT MODELS (GenericOutput wrappers)
# ==============================================================================


class MetricsSnapshotOutput(GenericOutput):
    """Output de generate_code_metrics() y get_metrics_snapshot()."""
    result: Optional[MetricsComparison] = None


class MetricsSnapshotListOutput(GenericOutput):
    """Output de get_metrics_snapshots()."""
    result: Optional[List[dict]] = None


class CommitMetricsOutput(GenericOutput):
    """Output de get_commit_metrics()."""
    result: Optional[CommitMetrics] = None


# ==============================================================================
# METRICS HISTORY MODELS (for charting over commits)
# ==============================================================================


class MetricsHistoryPoint(BaseModel):
    """Punto de datos ligero para la gráfica temporal de métricas por commit."""

    commit_hash: str = Field(..., description="Hash completo del commit")
    commit_short: str = Field("", description="Hash abreviado")
    branch: str = Field("", description="Rama activa en el momento del snapshot")
    timestamp: str = Field("", description="Fecha ISO del snapshot")
    # Aggregate metrics (all plottable)
    total_sloc: int = Field(0, description="Total líneas de código fuente")
    total_files: int = Field(0, description="Total archivos Python")
    total_functions: int = Field(0, description="Total funciones/métodos")
    total_classes: int = Field(0, description="Total clases")
    total_comments: int = Field(0, description="Total líneas de comentario")
    total_blanks: int = Field(0, description="Total líneas en blanco")
    avg_complexity: float = Field(0.0, description="Complejidad ciclomática media")
    avg_mi: float = Field(0.0, description="Índice de mantenibilidad medio")
    # Complexity distribution
    rank_a: int = Field(0, description="Funciones con rank A (CC ≤ 5)")
    rank_b: int = Field(0, description="Funciones con rank B (CC 6-10)")
    rank_c: int = Field(0, description="Funciones con rank C (CC 11-15)")
    rank_d: int = Field(0, description="Funciones con rank D (CC 16-20)")
    rank_e: int = Field(0, description="Funciones con rank E (CC 21-25)")
    rank_f: int = Field(0, description="Funciones con rank F (CC > 25)")
    # Coupling
    circular_deps_count: int = Field(0, description="Número de dependencias circulares")


class MetricsHistory(BaseModel):
    """Serie temporal de métricas a lo largo de commits."""

    points: List[MetricsHistoryPoint] = Field(
        default_factory=list, description="Puntos ordenados cronológicamente (más antiguo primero)"
    )
    available_metrics: List[dict] = Field(
        default_factory=list,
        description="Métricas disponibles con metadata: [{key, label, group, description}]",
    )


class MetricsHistoryOutput(GenericOutput):
    """Output de get_metrics_history()."""
    result: Optional[MetricsHistory] = None
