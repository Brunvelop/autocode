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
)
from .structure import get_code_structure
from .metrics import generate_code_metrics, get_metrics_snapshots, get_commit_metrics

__all__ = [
    # Structure
    'CodeNode',
    'CodeGraph',
    'CodeStructureOutput',
    'CodeStructureResult',
    'get_code_structure',
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
    # Metrics functions
    'generate_code_metrics',
    'get_metrics_snapshots',
    'get_commit_metrics',
]
