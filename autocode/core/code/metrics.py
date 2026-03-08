"""
metrics.py
Motor de métricas de código y endpoints registrados.

Proporciona:
- Snapshots persistentes en .autocode/metrics/
- Comparación entre snapshots
- Métricas per-commit (before/after via git show)
- Historial temporal de métricas

El análisis por archivo (CC, MI, nesting, line counts) lo delega a analyzer.py.
El acoplamiento lo delega a coupling.py.
La persistencia de snapshots la delega a snapshots.py.
"""
import logging
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Optional

from autocode.interfaces.registry import register_function
from autocode.core.vcs.git import git, git_show, get_tracked_files
from autocode.core.code.analyzer import analyze_file_metrics
from autocode.core.code.coupling import analyze_coupling
from autocode.core.code.snapshots import (
    save_snapshot,
    load_snapshot_by_hash,
    load_previous_snapshot,
    load_history_points,
    list_snapshots,
)
from autocode.core.code.models import (
    MetricsSnapshot,
    MetricsComparison,
    MetricsSnapshotOutput,
    MetricsSnapshotListOutput,
    CommitMetrics,
    CommitFileMetrics,
    CommitMetricsOutput,
    MetricsHistory,
    MetricsHistoryOutput,
)

logger = logging.getLogger(__name__)

JS_EXTENSIONS = frozenset({".js", ".mjs", ".jsx"})
_ALL_EXTENSIONS = (".py", ".js", ".mjs", ".jsx")


# ==============================================================================
# REGISTERED ENDPOINTS
# ==============================================================================


@register_function(http_methods=["GET"], interfaces=["api", "mcp"])
def generate_code_metrics() -> MetricsSnapshotOutput:
    """
    Genera un snapshot completo de métricas del proyecto y lo compara con el anterior.

    Analiza todos los archivos Python y JavaScript trackeados por git calculando
    complejidad ciclomática, índice de mantenibilidad, acoplamiento y más.
    Guarda el snapshot en .autocode/metrics/ para seguimiento histórico.

    Si ya existe un snapshot para el commit actual, lo reutiliza sin
    recalcular (cache por commit hash).
    """
    try:
        # Check cache: si ya existe snapshot para el commit actual, reutilizar
        current_hash = git("rev-parse", "HEAD")
        cached = load_snapshot_by_hash(current_hash)

        if cached is not None:
            logger.debug(f"Snapshot en cache para {current_hash[:7]}, reutilizando")
            snapshot = cached
        else:
            snapshot = _build_current_snapshot()
            save_snapshot(snapshot)

        previous = load_previous_snapshot(snapshot.commit_hash)
        comparison = _compare_snapshots(previous, snapshot)

        source = "cache" if cached is not None else "generado"
        return MetricsSnapshotOutput(
            success=True,
            result=comparison,
            message=f"Snapshot ({source}): {snapshot.total_files} archivos, "
                    f"avg CC={snapshot.avg_complexity:.2f}, avg MI={snapshot.avg_mi:.1f}",
        )
    except Exception as e:
        logger.error(f"Error generando métricas: {e}")
        return MetricsSnapshotOutput(success=False, message=str(e))


@register_function(http_methods=["GET"], interfaces=["api", "mcp"])
def get_metrics_snapshots() -> MetricsSnapshotListOutput:
    """
    Lista todos los snapshots de métricas guardados.

    Retorna una lista con fecha, commit y resumen de cada snapshot
    guardado en .autocode/metrics/.
    """
    try:
        snapshots = list_snapshots()
        return MetricsSnapshotListOutput(
            success=True,
            result=snapshots,
            message=f"{len(snapshots)} snapshots encontrados",
        )
    except Exception as e:
        logger.error(f"Error listando snapshots: {e}")
        return MetricsSnapshotListOutput(success=False, message=str(e))


@register_function(http_methods=["GET"], interfaces=["api", "mcp"])
def get_commit_metrics(commit_hash: str) -> CommitMetricsOutput:
    """
    Calcula métricas before/after de los archivos cambiados en un commit.

    Para cada archivo Python o JavaScript modificado, analiza el código antes y
    después del commit usando git show, calculando deltas de SLOC, complejidad y MI.

    Args:
        commit_hash: Hash del commit (completo o abreviado)
    """
    try:
        metrics = _analyze_commit(commit_hash)
        return CommitMetricsOutput(
            success=True,
            result=metrics,
            message=f"Commit {metrics.commit_short}: {len(metrics.files)} archivos analizados",
        )
    except Exception as e:
        logger.error(f"Error analizando commit {commit_hash}: {e}")
        return CommitMetricsOutput(success=False, message=str(e))


@register_function(http_methods=["GET"], interfaces=["api", "mcp"])
def get_metrics_history(max_count: int = 100) -> MetricsHistoryOutput:
    """
    Obtiene la serie temporal de métricas agregadas para graficar.

    Carga todos los snapshots guardados en .autocode/metrics/ y extrae
    solo los valores agregados (sin datos per-file) para renderizar
    gráficas de evolución de métricas a lo largo de los commits.

    Args:
        max_count: Número máximo de puntos a retornar (default 100)
    """
    try:
        points = load_history_points(max_count)

        # Metadata de métricas disponibles para el frontend
        available_metrics = [
            {"key": "total_sloc", "label": "SLOC", "group": "volume", "description": "Líneas de código fuente"},
            {"key": "total_files", "label": "Archivos", "group": "volume", "description": "Archivos Python"},
            {"key": "total_functions", "label": "Funciones", "group": "volume", "description": "Funciones y métodos"},
            {"key": "total_classes", "label": "Clases", "group": "volume", "description": "Clases definidas"},
            {"key": "total_comments", "label": "Comentarios", "group": "volume", "description": "Líneas de comentario"},
            {"key": "total_blanks", "label": "Blanks", "group": "volume", "description": "Líneas en blanco"},
            {"key": "avg_complexity", "label": "CC Media", "group": "quality", "description": "Complejidad ciclomática media"},
            {"key": "avg_mi", "label": "MI Media", "group": "quality", "description": "Índice de mantenibilidad medio (0-100)"},
            {"key": "rank_a", "label": "Rank A", "group": "distribution", "description": "Funciones con CC ≤ 5"},
            {"key": "rank_b", "label": "Rank B", "group": "distribution", "description": "Funciones con CC 6-10"},
            {"key": "rank_c", "label": "Rank C", "group": "distribution", "description": "Funciones con CC 11-15"},
            {"key": "rank_d", "label": "Rank D", "group": "distribution", "description": "Funciones con CC 16-20"},
            {"key": "rank_e", "label": "Rank E", "group": "distribution", "description": "Funciones con CC 21-25"},
            {"key": "rank_f", "label": "Rank F", "group": "distribution", "description": "Funciones con CC > 25"},
            {"key": "circular_deps_count", "label": "Deps Circulares", "group": "coupling", "description": "Dependencias circulares detectadas"},
        ]

        history = MetricsHistory(points=points, available_metrics=available_metrics)

        return MetricsHistoryOutput(
            success=True,
            result=history,
            message=f"{len(points)} snapshots en historial",
        )
    except Exception as e:
        logger.error(f"Error obteniendo historial de métricas: {e}")
        return MetricsHistoryOutput(success=False, message=str(e))


# ==============================================================================
# SNAPSHOT BUILDING
# ==============================================================================


def _build_current_snapshot() -> MetricsSnapshot:
    """Build a full metrics snapshot of the current project state."""
    all_files = get_tracked_files(*_ALL_EXTENSIONS)
    file_metrics = []
    for fpath in all_files:
        try:
            content = Path(fpath).read_text(encoding="utf-8")
            fm = analyze_file_metrics(fpath, content)
            file_metrics.append(fm)
        except Exception as e:
            logger.debug(f"Skip {fpath}: {e}")

    # Aggregates
    all_funcs = [f for fm in file_metrics for f in fm.functions]
    total_sloc = sum(fm.sloc for fm in file_metrics)
    total_comments = sum(fm.comments for fm in file_metrics)
    total_blanks = sum(fm.blanks for fm in file_metrics)
    total_functions = sum(fm.functions_count for fm in file_metrics)
    total_classes = sum(fm.classes_count for fm in file_metrics)
    avg_cc = sum(f.complexity for f in all_funcs) / len(all_funcs) if all_funcs else 0
    avg_mi = sum(fm.maintainability_index for fm in file_metrics) / len(file_metrics) if file_metrics else 0

    # Complexity distribution
    dist: dict[str, int] = defaultdict(int)
    for f in all_funcs:
        dist[f.rank] += 1

    # Coupling (Python-only until commit 6 adds JS import analysis)
    py_files = [f for f in all_files if f.endswith(".py")]
    coupling, circulars = analyze_coupling(py_files)

    return MetricsSnapshot(
        commit_hash=git("rev-parse", "HEAD"),
        commit_short=git("rev-parse", "--short", "HEAD"),
        branch=git("rev-parse", "--abbrev-ref", "HEAD"),
        timestamp=datetime.now().isoformat(),
        files=file_metrics,
        total_files=len(file_metrics),
        total_sloc=total_sloc,
        total_comments=total_comments,
        total_blanks=total_blanks,
        total_functions=total_functions,
        total_classes=total_classes,
        avg_complexity=round(avg_cc, 2),
        avg_mi=round(avg_mi, 1),
        complexity_distribution=dict(dist),
        coupling=coupling,
        circular_deps=circulars,
    )


# ==============================================================================
# COMPARISON
# ==============================================================================


def _compare_snapshots(before: Optional[MetricsSnapshot], after: MetricsSnapshot) -> MetricsComparison:
    """Compare two snapshots and compute deltas."""
    if before is None:
        return MetricsComparison(before=None, after=after)

    # File-level comparison
    before_map = {f.path: f for f in before.files}
    after_map = {f.path: f for f in after.files}
    improved, degraded = [], []

    for path, af in after_map.items():
        bf = before_map.get(path)
        if bf and af.avg_complexity < bf.avg_complexity:
            improved.append({"path": path, "before": bf.avg_complexity, "after": af.avg_complexity})
        elif bf and af.avg_complexity > bf.avg_complexity:
            degraded.append({"path": path, "before": bf.avg_complexity, "after": af.avg_complexity})

    return MetricsComparison(
        before=before,
        after=after,
        delta_sloc=after.total_sloc - before.total_sloc,
        delta_functions=after.total_functions - before.total_functions,
        delta_classes=after.total_classes - before.total_classes,
        delta_avg_complexity=round(after.avg_complexity - before.avg_complexity, 2),
        delta_avg_mi=round(after.avg_mi - before.avg_mi, 1),
        files_improved=improved,
        files_degraded=degraded,
    )


# ==============================================================================
# PER-COMMIT ANALYSIS
# ==============================================================================


def _analyze_commit(commit_hash: str) -> CommitMetrics:
    """Analyze the impact of a specific commit on code metrics."""
    # Resolve short hash
    full_hash = git("rev-parse", commit_hash)
    short_hash = git("rev-parse", "--short", commit_hash)

    # Get parent
    parents_str = git("log", "-1", "--format=%P", full_hash)
    parents = parents_str.split() if parents_str else []

    # Get changed .py files
    if parents:
        diff_output = git("diff-tree", "--no-commit-id", "-r", "--name-status", parents[0], full_hash)
    else:
        diff_output = git("diff-tree", "--no-commit-id", "-r", "--name-status", full_hash)

    file_metrics: list[CommitFileMetrics] = []
    total_delta_sloc = 0
    total_delta_cc = 0.0
    count_cc = 0

    for line in diff_output.strip().split("\n"):
        if not line or "\t" not in line:
            continue
        parts = line.split("\t")
        if len(parts) < 2:
            continue
        status_letter = parts[0].strip()[0]
        fpath = parts[-1].strip()

        ext = Path(fpath).suffix
        if ext != ".py" and ext not in JS_EXTENSIONS:
            continue

        status = {"A": "added", "M": "modified", "D": "deleted"}.get(status_letter, "modified")

        before_fm = None
        after_fm = None

        # Get "before" content (from parent)
        if status != "added" and parents:
            before_content = git_show(f"{parents[0]}:{fpath}")
            if before_content:
                before_fm = analyze_file_metrics(fpath, before_content)

        # Get "after" content (from this commit)
        if status != "deleted":
            after_content = git_show(f"{full_hash}:{fpath}")
            if after_content:
                after_fm = analyze_file_metrics(fpath, after_content)

        d_sloc = (after_fm.sloc if after_fm else 0) - (before_fm.sloc if before_fm else 0)
        d_cc = (after_fm.avg_complexity if after_fm else 0) - (before_fm.avg_complexity if before_fm else 0)
        d_mi = (after_fm.maintainability_index if after_fm else 0) - (before_fm.maintainability_index if before_fm else 0)

        file_metrics.append(CommitFileMetrics(
            path=fpath, status=status,
            before=before_fm, after=after_fm,
            delta_sloc=d_sloc,
            delta_complexity=round(d_cc, 2),
            delta_mi=round(d_mi, 1),
        ))
        total_delta_sloc += d_sloc
        total_delta_cc += d_cc
        count_cc += 1

    avg_delta_cc = round(total_delta_cc / count_cc, 2) if count_cc else 0

    return CommitMetrics(
        commit_hash=full_hash,
        commit_short=short_hash,
        files=file_metrics,
        summary={
            "delta_sloc": total_delta_sloc,
            "delta_avg_complexity": avg_delta_cc,
            "files_analyzed": len(file_metrics),
        },
    )


