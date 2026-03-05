"""
reviewer.py
Motor de revisión post-ejecución para planes de commit.

Computa métricas before/after de archivos .py cambiados,
reutilizando _analyze_content() de autocode.core.code.metrics.

Flujo:
1. Recibe lista de archivos cambiados + referencia al commit padre
2. Para cada .py: obtiene contenido "before" (git show) y "after" (disco)
3. Analiza ambos con _analyze_content()
4. Calcula deltas y retorna List[ReviewFileMetrics]
"""

import logging
import subprocess
from pathlib import Path
from typing import List, Optional

from autocode.core.code.metrics import _analyze_content
from autocode.core.code.models import FileMetrics
from autocode.core.planning.models import ReviewFileMetrics

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
    content = _git_show(f"{parent_commit}:{fpath}", repo_path)
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


def _git_show(ref: str, repo_path: str = ".") -> Optional[str]:
    """Get file content at a specific git ref. Returns None on error."""
    result = subprocess.run(
        ["git", "show", ref],
        capture_output=True, text=True, check=False,
        cwd=repo_path,
    )
    if result.returncode != 0:
        return None
    return result.stdout
