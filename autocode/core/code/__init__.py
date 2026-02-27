"""
autocode/core/code
Módulo de análisis e introspección de código.
Proporciona estructura normalizada de código Python y JavaScript,
y métricas de complejidad, mantenibilidad y acoplamiento.
"""

from .models import (
    CodeNode,
    CodeGraph,
    CodeStructureOutput,
    CodeStructureResult,
    CodeSummaryOutput,
    # Metrics models
    FunctionMetrics,
    FileMetrics,
    PackageCoupling,
    MetricsSnapshot,
    MetricsComparison,
    MetricsSnapshotOutput,
    MetricsSnapshotListOutput,
    CommitMetrics,
    CommitFileMetrics,
    CommitMetricsOutput,
    # Metrics history models
    MetricsHistoryPoint,
    MetricsHistory,
    MetricsHistoryOutput,
)
from .structure import get_code_structure, get_code_summary
from .metrics import generate_code_metrics, get_metrics_snapshots, get_commit_metrics, get_metrics_history

__all__ = [
    # Structure
    'CodeNode',
    'CodeGraph',
    'CodeStructureOutput',
    'CodeStructureResult',
    'CodeSummaryOutput',
    'get_code_structure',
    'get_code_summary',
    # Metrics models
    'FunctionMetrics',
    'FileMetrics',
    'PackageCoupling',
    'MetricsSnapshot',
    'MetricsComparison',
    'MetricsSnapshotOutput',
    'MetricsSnapshotListOutput',
    'CommitMetrics',
    'CommitFileMetrics',
    'CommitMetricsOutput',
    # Metrics history models
    'MetricsHistoryPoint',
    'MetricsHistory',
    'MetricsHistoryOutput',
    # Metrics functions
    'generate_code_metrics',
    'get_metrics_snapshots',
    'get_commit_metrics',
    'get_metrics_history',
]
