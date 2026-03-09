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
from typing import Optional

import lizard

from autocode.core.code.models import ClassInfo, FileMetrics, FunctionMetrics

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
    lz_analyzer = lizard.FileAnalyzer(lizard.get_extensions(["nd"]))
    lizard_analysis = lz_analyzer.analyze_source_code(path, content)

    if language == "python":
        # Python: use AST to detect class membership accurately.
        # Lizard names nested functions as "outer.inner" (dot notation) but does NOT
        # prefix class methods with the class name.  We use AST line ranges to know
        # which method belongs to which class, and skip pure inner functions.
        class_ranges = _get_python_class_ranges(content, path)
        func_metrics = [
            _to_function_metrics(f, path, _find_class_for_line(f.start_line, class_ranges))
            for f in lizard_analysis.function_list
            if "." not in f.name   # skip nested functions (outer.inner noise)
        ]
        classes_info = _build_classes_info(class_ranges, content)
    else:
        func_metrics = [
            _to_function_metrics(f, path, _find_js_class_for_func(f))
            for f in lizard_analysis.function_list
        ]
        classes_info = []  # JS: no AST, no class info

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
        classes=classes_info,
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


def _get_python_class_ranges(content: str, path: str) -> list:
    """Return list of (start_line, end_line, class_name) for each class in a Python file.

    Uses AST for accurate class boundary detection.  End line is the last line
    of the class body (inclusive), so a method at line L belongs to class C when
    C.start_line < L <= C.end_line.

    Args:
        content: Python source code
        path: File path (for AST error reporting)

    Returns:
        List of (start_line, end_line, class_name) tuples
    """
    try:
        tree = ast.parse(content, filename=path)
        return [
            (node.lineno, node.end_lineno, node.name)
            for node in ast.walk(tree)
            if isinstance(node, ast.ClassDef)
        ]
    except SyntaxError:
        return []


def _find_class_for_line(line: int, class_ranges: list) -> Optional[str]:
    """Return the class name that contains the given line number, or None.

    A function at ``line`` is considered a method of a class when:
        class_start_line < line <= class_end_line

    Args:
        line: Line number of the function (from lizard's start_line)
        class_ranges: List of (start_line, end_line, class_name) from
                      _get_python_class_ranges()

    Returns:
        Class name string, or None if the line is outside any class.
    """
    for start, end, cname in class_ranges:
        if start < line <= end:
            return cname
    return None


def _find_js_class_for_func(func) -> Optional[str]:
    """Detect JS/C++ class membership from lizard's naming convention.

    Lizard names JS/C++ class methods as ``ClassName.method`` or
    ``ClassName::method``.  We only treat the prefix as a class name when it
    starts with an uppercase letter (CamelCase convention) to avoid false
    positives from nested functions like ``outerFn.innerFn``.

    Args:
        func: lizard.FunctionInfo object

    Returns:
        Class name string, or None if the function is not a class method.
    """
    parts = func.name.split(".")
    if len(parts) > 1 and parts[0][0].isupper():
        return parts[0]
    if "::" in func.name:
        parts = func.name.split("::")
        return parts[0] if len(parts) > 1 else None
    return None


def _to_function_metrics(func, path: str, class_name: Optional[str] = None) -> FunctionMetrics:
    """Convert a lizard FunctionInfo to our FunctionMetrics model.

    Pure converter: accepts pre-detected ``class_name`` from the appropriate
    language-specific helper (_find_class_for_line for Python,
    _find_js_class_for_func for JS/others) and builds the FunctionMetrics
    dataclass.  Contains no language-detection logic itself.

    Args:
        func: lizard.FunctionInfo object
        path: File path for the FunctionMetrics.file field
        class_name: Optional class name (pre-detected by a language helper)

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
        is_method=class_name is not None,
        class_name=class_name,
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


def _build_classes_info(class_ranges: list, content: str) -> list:
    """Build ClassInfo list from AST class ranges, computing SLOC per class.

    For each class range (start_line, end_line, name) extracted by
    _get_python_class_ranges(), counts the source lines of code within
    the class body (excluding blank lines and comment-only lines).

    Args:
        class_ranges: List of (start_line, end_line, class_name) tuples (1-indexed)
        content: Full file content as string

    Returns:
        List of ClassInfo objects with name, line_start, line_end, sloc
    """
    lines = content.split("\n")
    result = []
    for start, end, name in class_ranges:
        class_lines = lines[start - 1 : end]  # 1-indexed → 0-indexed
        sloc = sum(
            1 for l in class_lines
            if l.strip() and not l.strip().startswith("#")
        )
        result.append(ClassInfo(name=name, line_start=start, line_end=end, sloc=sloc))
    return result


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
