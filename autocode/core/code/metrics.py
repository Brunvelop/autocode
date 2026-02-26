"""
metrics.py
Motor de análisis de métricas de código y endpoints registrados.

Proporciona:
- Análisis de complejidad ciclomática, mantenibilidad, anidamiento
- Análisis de acoplamiento entre paquetes
- Snapshots persistentes en .autocode/metrics/
- Comparación entre snapshots
- Métricas per-commit (before/after via git show)
"""
import ast
import json
import logging
import math
import os
import subprocess
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Optional

from autocode.interfaces.registry import register_function
from autocode.core.code.models import (
    FileMetrics,
    FunctionMetrics,
    PackageCoupling,
    MetricsSnapshot,
    MetricsComparison,
    MetricsSnapshotOutput,
    MetricsSnapshotListOutput,
    CommitMetrics,
    CommitFileMetrics,
    CommitMetricsOutput,
)

logger = logging.getLogger(__name__)

# Directorio de snapshots (relativo al CWD del proyecto host)
METRICS_DIR = ".autocode/metrics"


# ==============================================================================
# REGISTERED ENDPOINTS
# ==============================================================================


@register_function(http_methods=["GET"], interfaces=["api", "mcp"])
def generate_code_metrics() -> MetricsSnapshotOutput:
    """
    Genera un snapshot completo de métricas del proyecto y lo compara con el anterior.

    Analiza todos los archivos .py trackeados por git calculando complejidad
    ciclomática, índice de mantenibilidad, acoplamiento y más.
    Guarda el snapshot en .autocode/metrics/ para seguimiento histórico.
    """
    try:
        snapshot = _build_current_snapshot()
        _save_snapshot(snapshot)
        previous = _load_previous_snapshot(snapshot.commit_hash)
        comparison = _compare_snapshots(previous, snapshot)
        return MetricsSnapshotOutput(
            success=True,
            result=comparison,
            message=f"Snapshot generado: {snapshot.total_files} archivos, "
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
        snapshots = _list_snapshots()
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
    Calcula métricas before/after de los archivos .py cambiados en un commit.

    Para cada archivo Python modificado, analiza el código antes y después
    del commit usando git show, calculando deltas de SLOC, complejidad y MI.

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


# ==============================================================================
# SNAPSHOT BUILDING
# ==============================================================================


def _build_current_snapshot() -> MetricsSnapshot:
    """Build a full metrics snapshot of the current project state."""
    py_files = _get_tracked_py_files()
    file_metrics = []
    for fpath in py_files:
        try:
            content = Path(fpath).read_text(encoding="utf-8")
            fm = _analyze_content(content, fpath)
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

    # Coupling
    coupling, circulars = _analyze_coupling(py_files)

    return MetricsSnapshot(
        commit_hash=_git("rev-parse", "HEAD"),
        commit_short=_git("rev-parse", "--short", "HEAD"),
        branch=_git("rev-parse", "--abbrev-ref", "HEAD"),
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
# FILE ANALYSIS (pure functions — work on content string)
# ==============================================================================


def _analyze_content(content: str, path: str) -> FileMetrics:
    """Analyze a Python file's content and return FileMetrics."""
    lines = content.split("\n")
    line_info = _count_line_types(lines)
    sloc, comments, blanks = line_info["sloc"], line_info["comments"], line_info["blanks"]
    total_loc = len(lines)

    try:
        tree = ast.parse(content, filename=path)
    except SyntaxError:
        return FileMetrics(
            path=path, language="python",
            sloc=sloc, comments=comments, blanks=blanks, total_loc=total_loc,
        )

    func_metrics = _extract_function_metrics(tree, content, path)
    classes_count = sum(1 for n in ast.walk(tree) if isinstance(n, ast.ClassDef))
    complexities = [f.complexity for f in func_metrics]
    nestings = [f.nesting_depth for f in func_metrics]

    avg_cc = sum(complexities) / len(complexities) if complexities else 0
    max_cc = max(complexities) if complexities else 0
    max_nest = max(nestings) if nestings else 0
    mi = _maintainability_index(sloc, avg_cc, total_loc)

    return FileMetrics(
        path=path,
        language="python",
        sloc=sloc,
        comments=comments,
        blanks=blanks,
        total_loc=total_loc,
        functions=func_metrics,
        classes_count=classes_count,
        functions_count=len(func_metrics),
        avg_complexity=round(avg_cc, 2),
        max_complexity=max_cc,
        max_nesting=max_nest,
        maintainability_index=round(mi, 1),
    )


def _count_line_types(lines: list[str]) -> dict:
    """Count SLOC, comment lines, blank lines."""
    sloc = comments = blanks = 0
    in_docstring = False
    docstring_char = None
    for line in lines:
        stripped = line.strip()
        if not stripped:
            blanks += 1
            continue
        # Track docstrings (triple quotes)
        if in_docstring:
            comments += 1
            if docstring_char in stripped:
                in_docstring = False
            continue
        if stripped.startswith('"""') or stripped.startswith("'''"):
            docstring_char = stripped[:3]
            comments += 1
            # Single-line docstring
            if stripped.count(docstring_char) >= 2:
                continue
            in_docstring = True
            continue
        if stripped.startswith("#"):
            comments += 1
        else:
            sloc += 1
    return {"sloc": sloc, "comments": comments, "blanks": blanks}


def _extract_function_metrics(tree: ast.Module, content: str, path: str) -> list[FunctionMetrics]:
    """Extract complexity metrics for every function/method in the AST."""
    results = []
    lines = content.split("\n")

    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue

        cc = _cyclomatic_complexity(node)
        nd = _nesting_depth(node)
        start = node.lineno
        end = getattr(node, "end_lineno", start)
        func_lines = lines[start - 1 : end]
        func_sloc = sum(1 for l in func_lines if l.strip() and not l.strip().startswith("#"))

        # Detect if method
        is_method = False
        class_name = None
        for cls in ast.walk(tree):
            if isinstance(cls, ast.ClassDef):
                for item in cls.body:
                    if item is node:
                        is_method = True
                        class_name = cls.name
                        break

        results.append(FunctionMetrics(
            name=node.name,
            file=path,
            line=start,
            complexity=cc,
            rank=_cc_rank(cc),
            nesting_depth=nd,
            sloc=func_sloc,
            is_method=is_method,
            class_name=class_name,
        ))

    return results


def _cyclomatic_complexity(node: ast.AST) -> int:
    """Calculate cyclomatic complexity of a function node.
    
    CC = 1 + number of decision points (if/elif/for/while/and/or/
    except/with/assert/ternary/comprehension-if).
    """
    cc = 1
    for child in ast.walk(node):
        if isinstance(child, (ast.If, ast.IfExp)):
            cc += 1
        elif isinstance(child, ast.For):
            cc += 1
        elif isinstance(child, ast.While):
            cc += 1
        elif isinstance(child, ast.ExceptHandler):
            cc += 1
        elif isinstance(child, ast.With):
            cc += 1
        elif isinstance(child, ast.Assert):
            cc += 1
        elif isinstance(child, ast.BoolOp):
            # and/or add len(values) - 1 decision points
            cc += len(child.values) - 1
        elif isinstance(child, ast.comprehension):
            cc += len(child.ifs) + 1  # the for + each if filter
    # Subtract 1 for the function node itself if it got counted
    return max(cc, 1)


def _nesting_depth(node: ast.AST, depth: int = 0) -> int:
    """Calculate max nesting depth of control flow in a function."""
    nesting_types = (ast.If, ast.For, ast.While, ast.With, ast.Try, ast.ExceptHandler)
    max_d = depth
    for child in ast.iter_child_nodes(node):
        if isinstance(child, nesting_types):
            max_d = max(max_d, _nesting_depth(child, depth + 1))
        else:
            max_d = max(max_d, _nesting_depth(child, depth))
    return max_d


def _cc_rank(cc: int) -> str:
    """Convert cyclomatic complexity to letter rank."""
    if cc <= 5:
        return "A"
    if cc <= 10:
        return "B"
    if cc <= 15:
        return "C"
    if cc <= 20:
        return "D"
    if cc <= 25:
        return "E"
    return "F"


def _maintainability_index(sloc: int, avg_cc: float, total_loc: int) -> float:
    """Calculate Maintainability Index (simplified SEI formula).
    
    MI = max(0, (171 - 5.2·ln(HV) - 0.23·CC - 16.2·ln(LOC)) * 100/171)
    We approximate Halstead Volume ≈ SLOC * log2(SLOC) for simplicity.
    """
    if sloc <= 0:
        return 100.0
    hv = sloc * max(math.log2(sloc), 1)
    ln_hv = math.log(max(hv, 1))
    ln_loc = math.log(max(sloc, 1))
    mi = (171 - 5.2 * ln_hv - 0.23 * avg_cc - 16.2 * ln_loc) * 100 / 171
    return max(0.0, min(100.0, mi))


# ==============================================================================
# COUPLING ANALYSIS
# ==============================================================================


def _analyze_coupling(py_files: list[str]) -> tuple[list[PackageCoupling], list[list[str]]]:
    """Analyze inter-package imports and detect circular dependencies."""
    imports: dict[str, set[str]] = defaultdict(set)

    for fpath in py_files:
        try:
            content = Path(fpath).read_text(encoding="utf-8")
            tree = ast.parse(content, filename=fpath)
        except Exception:
            continue

        module = fpath.replace("/", ".").replace("\\", ".").replace(".py", "")
        src_parts = module.split(".")
        src_pkg = ".".join(src_parts[:2]) if len(src_parts) >= 2 else src_parts[0]

        for node in ast.walk(tree):
            target = None
            if isinstance(node, ast.ImportFrom) and node.module:
                # Only track internal project imports
                if any(node.module.startswith(p) for p in _top_level_packages(py_files)):
                    target = node.module
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    if any(alias.name.startswith(p) for p in _top_level_packages(py_files)):
                        target = alias.name
            if target:
                tgt_parts = target.split(".")
                tgt_pkg = ".".join(tgt_parts[:2]) if len(tgt_parts) >= 2 else tgt_parts[0]
                if src_pkg != tgt_pkg:
                    imports[src_pkg].add(tgt_pkg)

    # All known packages
    all_pkgs: set[str] = set()
    for s, ts in imports.items():
        all_pkgs.add(s)
        all_pkgs.update(ts)

    # Ce/Ca/Instability
    ce = {m: len(imports.get(m, set())) for m in all_pkgs}
    ca: dict[str, int] = defaultdict(int)
    imported_by: dict[str, list[str]] = defaultdict(list)
    for s, ts in imports.items():
        for t in ts:
            ca[t] += 1
            imported_by[t].append(s)

    coupling = []
    for m in sorted(all_pkgs):
        c_e = ce.get(m, 0)
        c_a = ca.get(m, 0)
        inst = c_e / (c_e + c_a) if (c_e + c_a) > 0 else 0
        coupling.append(PackageCoupling(
            name=m, ce=c_e, ca=c_a, instability=round(inst, 2),
            imports_to=sorted(imports.get(m, set())),
            imported_by=sorted(imported_by.get(m, [])),
        ))

    # Circular deps
    circulars: list[list[str]] = []
    seen: set[tuple[str, str]] = set()
    for a in imports:
        for b in imports[a]:
            if a in imports.get(b, set()):
                pair = tuple(sorted([a, b]))
                if pair not in seen:
                    seen.add(pair)
                    circulars.append(list(pair))

    return coupling, circulars


_top_packages_cache: Optional[set] = None


def _top_level_packages(py_files: list[str]) -> set[str]:
    """Get top-level package names from file paths."""
    global _top_packages_cache
    if _top_packages_cache is not None:
        return _top_packages_cache
    pkgs = set()
    for f in py_files:
        parts = f.replace("\\", "/").split("/")
        if parts:
            pkgs.add(parts[0])
    _top_packages_cache = pkgs
    return pkgs


# ==============================================================================
# SNAPSHOT PERSISTENCE
# ==============================================================================


def _save_snapshot(snapshot: MetricsSnapshot) -> None:
    """Save snapshot as JSON in .autocode/metrics/."""
    metrics_dir = Path(METRICS_DIR)
    metrics_dir.mkdir(parents=True, exist_ok=True)
    fname = f"{snapshot.commit_short}.json"
    path = metrics_dir / fname
    path.write_text(snapshot.model_dump_json(indent=2), encoding="utf-8")
    logger.debug(f"Snapshot saved: {path}")


def _load_previous_snapshot(current_hash: str) -> Optional[MetricsSnapshot]:
    """Load the most recent snapshot that isn't the current commit."""
    metrics_dir = Path(METRICS_DIR)
    if not metrics_dir.exists():
        return None
    files = sorted(metrics_dir.glob("*.json"), reverse=True)
    for f in files:
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
            snap = MetricsSnapshot(**data)
            if snap.commit_hash != current_hash:
                return snap
        except Exception:
            continue
    return None


def _list_snapshots() -> list[dict]:
    """List all saved snapshots with summary info."""
    metrics_dir = Path(METRICS_DIR)
    if not metrics_dir.exists():
        return []
    result = []
    for f in sorted(metrics_dir.glob("*.json"), reverse=True):
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
            result.append({
                "filename": f.name,
                "commit_short": data.get("commit_short", ""),
                "branch": data.get("branch", ""),
                "timestamp": data.get("timestamp", ""),
                "total_files": data.get("total_files", 0),
                "total_sloc": data.get("total_sloc", 0),
                "avg_complexity": data.get("avg_complexity", 0),
                "avg_mi": data.get("avg_mi", 0),
            })
        except Exception:
            continue
    return result


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
    full_hash = _git("rev-parse", commit_hash)
    short_hash = _git("rev-parse", "--short", commit_hash)

    # Get parent
    parents_str = _git("log", "-1", "--format=%P", full_hash)
    parents = parents_str.split() if parents_str else []

    # Get changed .py files
    if parents:
        diff_output = _git("diff-tree", "--no-commit-id", "-r", "--name-status", parents[0], full_hash)
    else:
        diff_output = _git("diff-tree", "--no-commit-id", "-r", "--name-status", full_hash)

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

        if not fpath.endswith(".py"):
            continue

        status = {"A": "added", "M": "modified", "D": "deleted"}.get(status_letter, "modified")

        before_fm = None
        after_fm = None

        # Get "before" content (from parent)
        if status != "added" and parents:
            before_content = _git_show(f"{parents[0]}:{fpath}")
            if before_content:
                before_fm = _analyze_content(before_content, fpath)

        # Get "after" content (from this commit)
        if status != "deleted":
            after_content = _git_show(f"{full_hash}:{fpath}")
            if after_content:
                after_fm = _analyze_content(after_content, fpath)

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


# ==============================================================================
# GIT HELPERS
# ==============================================================================


def _git(*args: str) -> str:
    """Run a git command and return stripped stdout."""
    result = subprocess.run(
        ["git"] + list(args),
        capture_output=True, text=True, check=False,
    )
    return result.stdout.strip()


def _git_show(ref: str) -> Optional[str]:
    """Get file content at a specific git ref. Returns None on error."""
    result = subprocess.run(
        ["git", "show", ref],
        capture_output=True, text=True, check=False,
    )
    if result.returncode != 0:
        return None
    return result.stdout


def _get_tracked_py_files() -> list[str]:
    """Get all .py files tracked by git."""
    output = _git("ls-files", "--cached", "*.py")
    if not output:
        return []
    return [f for f in output.split("\n") if f.endswith(".py")]
