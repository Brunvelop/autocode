"""
reviewer.py
Motor de revisión post-ejecución para planes de commit.

Computa métricas before/after de archivos .py cambiados,
reutilizando _analyze_content() de autocode.core.code.metrics.

Flujo de compute_review_metrics:
1. Recibe lista de archivos cambiados + referencia al commit padre
2. Para cada .py: obtiene contenido "before" (git show) y "after" (disco)
3. Analiza ambos con _analyze_content()
4. Calcula deltas y retorna List[ReviewFileMetrics]

Flujo de auto_review:
1. Computa métricas before/after via compute_review_metrics()
2. Evalúa quality gates configurables (complexity, MI, nesting, SLOC growth)
3. Determina verdict: rejected si algún gate falla, approved si todos pasan
4. Genera summary, issues y suggestions
"""

import logging
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Tuple

from autocode.core.vcs.git import git_show
from autocode.core.code.metrics import _analyze_content
from autocode.core.code.models import FileMetrics
from autocode.core.planning.models import ReviewFileMetrics, ReviewResult

logger = logging.getLogger(__name__)

# Métricas clave que se extraen de FileMetrics para el dict de review
_METRIC_KEYS = (
    "sloc",
    "avg_complexity",
    "max_complexity",
    "maintainability_index",
    "functions_count",
    "classes_count",
    "max_nesting",
)


# ==============================================================================
# PUBLIC API
# ==============================================================================


def compute_review_metrics(
    files_changed: List[str],
    parent_commit: str = "HEAD",
    repo_path: str = ".",
) -> List[ReviewFileMetrics]:
    """Computa métricas before/after para archivos .py cambiados.

    Args:
        files_changed: Lista de rutas relativas de archivos modificados.
        parent_commit: Referencia git para el estado "before" (default HEAD).
        repo_path: Ruta al repositorio git (default directorio actual).

    Returns:
        Lista de ReviewFileMetrics, una por cada archivo .py procesado.
        Archivos no-.py se ignoran silenciosamente.
    """
    py_files = [f for f in files_changed if f.endswith(".py")]
    if not py_files:
        return []

    results: List[ReviewFileMetrics] = []
    for fpath in py_files:
        try:
            before_dict = _get_before_metrics(fpath, parent_commit, repo_path)
            after_dict = _get_after_metrics(fpath, repo_path)
            deltas = _compute_deltas(before_dict, after_dict)

            results.append(ReviewFileMetrics(
                path=fpath,
                before=before_dict,
                after=after_dict,
                deltas=deltas,
            ))
        except Exception as e:
            logger.warning(f"Error computing review metrics for {fpath}: {e}")
            continue

    return results


# ==============================================================================
# INTERNAL HELPERS
# ==============================================================================


def _get_before_metrics(
    fpath: str, parent_commit: str, repo_path: str
) -> dict:
    """Obtiene métricas del archivo en el estado 'before' (git show).

    Returns dict vacío si el archivo no existía en parent_commit.
    """
    content = git_show(f"{parent_commit}:{fpath}", cwd=repo_path)
    if content is None:
        return {}
    fm = _analyze_content(content, fpath)
    return _file_metrics_to_dict(fm)


def _get_after_metrics(fpath: str, repo_path: str) -> dict:
    """Obtiene métricas del archivo en el estado 'after' (disco).

    Returns dict vacío si el archivo no existe en disco.
    """
    full_path = Path(repo_path) / fpath
    if not full_path.exists():
        return {}
    try:
        content = full_path.read_text(encoding="utf-8")
    except Exception:
        return {}
    fm = _analyze_content(content, fpath)
    return _file_metrics_to_dict(fm)


def _file_metrics_to_dict(fm: FileMetrics) -> dict:
    """Convierte FileMetrics a dict plano con las métricas clave."""
    return {key: getattr(fm, key) for key in _METRIC_KEYS}


def _compute_deltas(before: dict, after: dict) -> dict:
    """Calcula deltas entre métricas before y after.

    Para cada métrica clave, computa delta_{key} = after - before.
    Si una de las dos no tiene la métrica, se usa 0.
    """
    deltas = {}
    for key in _METRIC_KEYS:
        before_val = before.get(key, 0)
        after_val = after.get(key, 0)
        # Handle numeric subtraction (int or float)
        delta = after_val - before_val
        # Round floats for cleaner output
        if isinstance(delta, float):
            delta = round(delta, 2)
        deltas[f"delta_{key}"] = delta
    return deltas


# ==============================================================================
# QUALITY GATES CONFIGURATION
# ==============================================================================

# Each gate defines a threshold and evaluation type:
#   - "relative_increase": fails if (after - before) / before > threshold
#     (only evaluated when before has the metric, i.e. not new files)
#   - "absolute_minimum": fails if after value < threshold
#   - "absolute_maximum": fails if after value > threshold
QUALITY_GATES = {
    "complexity_increase": {
        "threshold": 0.3,
        "metric": "avg_complexity",
        "type": "relative_increase",
        "min_baseline": 2.0,  # Only evaluate if before avg_complexity >= 2
        "description": "Average complexity increased by more than 30%",
    },
    "mi_minimum": {
        "threshold": 40,
        "metric": "maintainability_index",
        "type": "absolute_minimum",
        "description": "Maintainability index dropped below 40",
    },
    "max_nesting": {
        "threshold": 6,
        "metric": "max_nesting",
        "type": "absolute_maximum",
        "description": "Maximum nesting depth exceeded 6 levels",
    },
    "sloc_growth": {
        "threshold": 0.5,
        "metric": "sloc",
        "type": "relative_increase",
        "min_baseline": 20,  # Only evaluate if before SLOC >= 20
        "description": "SLOC grew by more than 50%",
    },
}

# Threshold for generating suggestions (lower than gate failure)
_SUGGESTION_FACTOR = 0.5  # Suggest if metric is at 50% of the gate threshold


# ==============================================================================
# AUTO-REVIEW
# ==============================================================================


def auto_review(
    files_changed: List[str],
    parent_commit: str = "HEAD",
    repo_path: str = ".",
) -> ReviewResult:
    """Ejecuta auto-review de archivos cambiados con quality gates.

    1. Computa métricas before/after via compute_review_metrics()
    2. Evalúa quality gates via _evaluate_quality_gates()
    3. Determina verdict: rejected si algún gate falla, approved si todos pasan
    4. Genera summary con resumen de métricas

    Args:
        files_changed: Lista de rutas relativas de archivos modificados.
        parent_commit: Referencia git para el estado "before" (default HEAD).
        repo_path: Ruta al repositorio git (default directorio actual).

    Returns:
        ReviewResult con verdict, métricas, quality gates y summary.
    """
    file_metrics = compute_review_metrics(files_changed, parent_commit, repo_path)
    gates, issues, suggestions = _evaluate_quality_gates(file_metrics)

    all_passed = all(gates.values())
    verdict = "approved" if all_passed else "rejected"

    summary = _build_summary(file_metrics, gates, verdict)

    return ReviewResult(
        mode="auto",
        verdict=verdict,
        summary=summary,
        issues=issues,
        suggestions=suggestions,
        file_metrics=file_metrics,
        quality_gates=gates,
        reviewed_at=datetime.now().isoformat(),
        reviewed_by="auto",
    )


def _evaluate_quality_gates(
    file_metrics: List[ReviewFileMetrics],
) -> Tuple[dict, List[str], List[str]]:
    """Evalúa quality gates sobre métricas de archivos y retorna resultados.

    Evalúa cada gate usando el peor caso entre todos los archivos.

    Args:
        file_metrics: Lista de ReviewFileMetrics con before/after/deltas.

    Returns:
        Tuple de:
        - gates: dict {gate_name: bool} (True = passed)
        - issues: list de strings describiendo gates fallidos
        - suggestions: list de strings con sugerencias de mejora
    """
    gates: dict = {}
    issues: List[str] = []
    suggestions: List[str] = []

    for gate_name, gate_config in QUALITY_GATES.items():
        metric_key = gate_config["metric"]
        threshold = gate_config["threshold"]
        gate_type = gate_config["type"]
        description = gate_config["description"]

        passed = True  # Assume passed until proven otherwise

        min_baseline = gate_config.get("min_baseline", 0)

        for fm in file_metrics:
            gate_result = _evaluate_single_gate(
                fm, metric_key, threshold, gate_type, min_baseline
            )
            if gate_result is False:
                passed = False
                break

        gates[gate_name] = passed

        if not passed:
            issues.append(f"❌ {gate_name}: {description}")

        # Check for suggestions (approaching threshold but not yet failing)
        if passed and file_metrics:
            suggestion = _check_for_suggestion(
                file_metrics, metric_key, threshold, gate_type, gate_name
            )
            if suggestion:
                suggestions.append(suggestion)

    return gates, issues, suggestions


def _evaluate_single_gate(
    fm: ReviewFileMetrics,
    metric_key: str,
    threshold: float,
    gate_type: str,
    min_baseline: float = 0,
) -> bool:
    """Evalúa un single gate para un archivo. Returns True if passed."""
    before_val = fm.before.get(metric_key)
    after_val = fm.after.get(metric_key)

    if gate_type == "relative_increase":
        # Skip if no before (new file) or before is 0
        if not fm.before or before_val is None or before_val == 0:
            return True
        if after_val is None:
            return True
        # Skip relative check if before value is below minimum baseline
        # (avoids false positives on tiny files, e.g. 2 SLOC → 4 SLOC = 100%)
        if min_baseline > 0 and before_val < min_baseline:
            return True
        increase = (after_val - before_val) / before_val
        return increase <= threshold

    elif gate_type == "absolute_minimum":
        # Skip if no after metrics (deleted file)
        if not fm.after or after_val is None:
            return True
        return after_val >= threshold

    elif gate_type == "absolute_maximum":
        # Skip if no after metrics (deleted file)
        if not fm.after or after_val is None:
            return True
        return after_val <= threshold

    return True  # Unknown gate type → pass


def _check_for_suggestion(
    file_metrics: List[ReviewFileMetrics],
    metric_key: str,
    threshold: float,
    gate_type: str,
    gate_name: str,
) -> Optional[str]:
    """Check if metrics are approaching a gate threshold and generate suggestion."""
    for fm in file_metrics:
        before_val = fm.before.get(metric_key)
        after_val = fm.after.get(metric_key)

        if gate_type == "relative_increase":
            if not fm.before or before_val is None or before_val == 0:
                continue
            if after_val is None:
                continue
            increase = (after_val - before_val) / before_val
            warn_threshold = threshold * _SUGGESTION_FACTOR
            if increase > warn_threshold:
                pct = round(increase * 100)
                limit = round(threshold * 100)
                return (
                    f"⚠️ {gate_name}: {fm.path} — {metric_key} increased {pct}% "
                    f"(approaching {limit}% limit)"
                )

        elif gate_type == "absolute_minimum":
            if not fm.after or after_val is None:
                continue
            margin = after_val - threshold
            total_range = 100 - threshold  # Assume 0-100 scale for MI
            if total_range > 0 and margin / total_range < _SUGGESTION_FACTOR:
                return (
                    f"⚠️ {gate_name}: {fm.path} — {metric_key}={after_val:.1f} "
                    f"(minimum is {threshold})"
                )

        elif gate_type == "absolute_maximum":
            if not fm.after or after_val is None:
                continue
            if after_val > threshold * _SUGGESTION_FACTOR:
                return (
                    f"⚠️ {gate_name}: {fm.path} — {metric_key}={after_val} "
                    f"(maximum is {threshold})"
                )

    return None


def _build_summary(
    file_metrics: List[ReviewFileMetrics],
    gates: dict,
    verdict: str,
) -> str:
    """Genera un resumen textual del resultado de la review."""
    if not file_metrics:
        return f"Auto-review: {verdict}. No Python files to analyze."

    n_files = len(file_metrics)
    passed = sum(1 for v in gates.values() if v)
    total = len(gates)
    failed_gates = [name for name, v in gates.items() if not v]

    summary = f"Auto-review: {verdict}. {n_files} file(s) analyzed, {passed}/{total} quality gates passed."
    if failed_gates:
        summary += f" Failed: {', '.join(failed_gates)}."

    return summary
