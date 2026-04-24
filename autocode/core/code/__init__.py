"""
autocode/core/code
Módulo de análisis e introspección de código.
Proporciona estructura normalizada de código Python y JavaScript,
y métricas de complejidad, mantenibilidad y acoplamiento.
"""

from .models import (
    CodeNode,
    CodeGraph,
    CodeStructureResult,
    CodeSummaryResult,
    # Metrics models
    FunctionMetrics,
    FileMetrics,
    PackageCoupling,
    MetricsSnapshot,
    MetricsComparison,
    MetricsSnapshotList,
    CommitMetrics,
    CommitFileMetrics,
    # Metrics history models
    MetricsHistoryPoint,
    MetricsHistory,
    # Architecture models
    FileDependency,
    ArchitectureNode,
    ArchitectureSnapshot,
    DependencyCycle,
    DependencyCyclesResult,
    # Health check models
    HealthViolation,
    HealthCheckResult,
)
from .structure import get_code_structure, get_code_summary
from .metrics import generate_code_metrics, get_metrics_snapshots, get_commit_metrics, get_metrics_history
from .architecture import get_architecture_snapshot, get_dependency_cycles
from .health import get_health_check

__all__ = [
    # Structure models
    'CodeNode',
    'CodeGraph',
    'CodeStructureResult',
    'CodeSummaryResult',
    'get_code_structure',
    'get_code_summary',
    # Metrics models
    'FunctionMetrics',
    'FileMetrics',
    'PackageCoupling',
    'MetricsSnapshot',
    'MetricsComparison',
    'MetricsSnapshotList',
    'CommitMetrics',
    'CommitFileMetrics',
    # Metrics history models
    'MetricsHistoryPoint',
    'MetricsHistory',
    # Metrics functions
    'generate_code_metrics',
    'get_metrics_snapshots',
    'get_commit_metrics',
    'get_metrics_history',
    # Architecture models
    'FileDependency',
    'ArchitectureNode',
    'ArchitectureSnapshot',
    'DependencyCycle',
    'DependencyCyclesResult',
    # Architecture functions
    'get_architecture_snapshot',
    'get_dependency_cycles',
    # Health check models
    'HealthViolation',
    'HealthCheckResult',
    # Health check function
    'get_health_check',
]
