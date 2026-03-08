"""
analyzer.py
Motor unificado de análisis de métricas por archivo (Python + JavaScript).

Usa lizard para CC, nesting depth y SLOC por función.
Mantiene fórmula propia de MI y conteo de líneas language-aware.

Extraído de metrics.py (Commit 4) para SRP — análisis de archivo como
responsabilidad independiente del snapshot/comparación/persistencia.
"""

import ast
import logging
import math
import re
from pathlib import Path

import lizard

from autocode.core.code.models import FileMetrics, FunctionMetrics

logger = logging.getLogger(__name__)

JS_EXTENSIONS = frozenset({".js", ".mjs", ".jsx"})

# Regex for counting JS classes (simple heuristic)
_JS_CLASS_RE = re.compile(r"^\s*(?:export\s+)?class\s+\w+", re.MULTILINE)


# ==============================================================================
# PUBLIC API
# ==============================================================================


def analyze_file_metrics(path: str, content: str) -> FileMetrics:
    """Analyze a single file and return FileMetrics.

    Unified engine for Python and JavaScript. Uses lizard for per-function
    CC, nesting depth, and SLOC. Uses our own line counting for
    SLOC/comments/blanks (language-aware). Computes MI with our formula.

    Args:
        path: Relative file path (used to detect language by extension)
        content: File content as string

    Returns:
        FileMetrics with all computed metrics
    """
    ext = Path(path).suffix
    language = "python" if ext == ".py" else "javascript"

    # Language-aware line counts
    line_info = count_lines(content, language)
    sloc = line_info["sloc"]
    comments = line_info["comments"]
    blanks = line_info["blanks"]
    total_loc = len(content.split("\n")) if content else 0

    if not content.strip():
        return FileMetrics(
            path=path,
            language=language,
            sloc=0,
            comments=0,
            blanks=blanks,
            total_loc=total_loc,
            maintainability_index=100.0,
        )

    # Lizard analysis for per-function metrics (nd = nesting depth extension)
    analyzer = lizard.FileAnalyzer(lizard.get_extensions(["nd"]))
    lizard_analysis = analyzer.analyze_source_code(path, content)
    func_metrics = [
        _to_function_metrics(f, path) for f in lizard_analysis.function_list
    ]

    # Class count
    classes_count = _count_classes(content, language, path)

    # Aggregates
    complexities = [f.complexity for f in func_metrics]
    avg_cc = sum(complexities) / len(complexities) if complexities else 0
    max_cc = max(complexities) if complexities else 0
    max_nest = max((f.nesting_depth for f in func_metrics), default=0)
    mi = maintainability_index(sloc, avg_cc, total_loc)

    return FileMetrics(
        path=path,
        language=language,
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


def count_lines(content: str, language: str) -> dict:
    """Count SLOC, comment lines, and blank lines (language-aware).

    Args:
        content: File content as string
        language: "python" or "javascript"

    Returns:
        Dict with keys "sloc", "comments", "blanks"
    """
    lines = content.split("\n")
    if language == "python":
        return _count_lines_python(lines)
    return _count_lines_js(lines)


def maintainability_index(sloc: int, avg_cc: float, total_loc: int) -> float:
    """Calculate Maintainability Index (simplified SEI formula).

    MI = max(0, (171 - 5.2·ln(HV) - 0.23·CC - 16.2·ln(LOC)) * 100/171)
    We approximate Halstead Volume ≈ SLOC * log2(SLOC) for simplicity.

    Args:
        sloc: Source lines of code
        avg_cc: Average cyclomatic complexity
        total_loc: Total lines of code

    Returns:
        MI value clamped to [0, 100]
    """
    if sloc <= 0:
        return 100.0
    hv = sloc * max(math.log2(sloc), 1)
    ln_hv = math.log(max(hv, 1))
    ln_loc = math.log(max(sloc, 1))
    mi = (171 - 5.2 * ln_hv - 0.23 * avg_cc - 16.2 * ln_loc) * 100 / 171
    return max(0.0, min(100.0, mi))


def cc_rank(cc: int) -> str:
    """Convert cyclomatic complexity to letter rank.

    A: ≤5, B: 6-10, C: 11-15, D: 16-20, E: 21-25, F: >25
    """
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


# ==============================================================================
# INTERNAL HELPERS
# ==============================================================================


def _to_function_metrics(func, path: str) -> FunctionMetrics:
    """Convert a lizard FunctionInfo to our FunctionMetrics model.

    Args:
        func: lizard.FunctionInfo object
        path: File path for the FunctionMetrics.file field

    Returns:
        FunctionMetrics with CC, nesting, SLOC from lizard
    """
    cc = func.cyclomatic_complexity
    # nd extension provides max_nesting_depth; fall back to top_nesting_level
    nesting = getattr(func, "max_nesting_depth", func.top_nesting_level)
    return FunctionMetrics(
        name=func.name,
        file=path,
        line=func.start_line,
        complexity=cc,
        rank=cc_rank(cc),
        nesting_depth=nesting,
        sloc=func.nloc,
        is_method="." in func.name or "::" in func.name,
        class_name=func.name.split(".")[0] if "." in func.name else None,
    )


def _count_classes(content: str, language: str, path: str) -> int:
    """Count classes in file content.

    Python: AST-based (accurate). JavaScript: regex-based (heuristic).

    Args:
        content: File content
        language: "python" or "javascript"
        path: File path (for AST error reporting)

    Returns:
        Number of class definitions found
    """
    if language == "python":
        try:
            tree = ast.parse(content, filename=path)
            return sum(1 for n in ast.walk(tree) if isinstance(n, ast.ClassDef))
        except SyntaxError:
            return 0
    else:
        return len(_JS_CLASS_RE.findall(content))


def _count_lines_python(lines: list[str]) -> dict:
    """Count SLOC, comment lines, blank lines for Python.

    Handles:
    - # comments
    - Triple-quoted docstrings (''' and \"\"\") as comments
    - Blank lines
    """
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


def _count_lines_js(lines: list[str]) -> dict:
    """Count SLOC, comment lines, blank lines for JavaScript.

    Handles:
    - // single-line comments
    - /* */ multi-line block comments
    - Blank lines
    """
    sloc = comments = blanks = 0
    in_block_comment = False

    for line in lines:
        stripped = line.strip()
        if not stripped:
            blanks += 1
            continue

        if in_block_comment:
            comments += 1
            if "*/" in stripped:
                in_block_comment = False
            continue

        if stripped.startswith("//"):
            comments += 1
            continue

        if stripped.startswith("/*"):
            comments += 1
            # Single-line block comment: /* ... */
            if "*/" in stripped:
                continue
            in_block_comment = True
            continue

        sloc += 1

    return {"sloc": sloc, "comments": comments, "blanks": blanks}
