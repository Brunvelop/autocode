"""
coupling.py
Análisis de acoplamiento entre paquetes del proyecto.

Extrae imports internos de archivos Python (AST) y JavaScript (regex),
calcula métricas de acoplamiento eferente (Ce) y aferente (Ca), instabilidad,
y detecta dependencias circulares entre paquetes de 2 niveles (ej: autocode.core).

Extraído de metrics.py (Commit 2) para SRP — un módulo, una responsabilidad.
JS import extraction added in Commit 6.
"""

import ast
import logging
import posixpath
import re
from collections import defaultdict
from pathlib import Path

from autocode.core.code.models import PackageCoupling

logger = logging.getLogger(__name__)

JS_EXTENSIONS = frozenset({".js", ".mjs", ".jsx"})

# Matches: import ... from '...' and export ... from '...'
# Captures the module specifier in the named group "module"
JS_IMPORT_RE = re.compile(
    r"""(?:import|export)\s+"""       # import or export keyword
    r"""(?:.*?\s+from\s+)?"""          # optional: default/named/namespace + from
    r"""['"](?P<module>[^'"]+)['"]""",  # quoted module specifier
    re.MULTILINE,
)


def analyze_coupling(
    files: list[str],
) -> tuple[list[PackageCoupling], list[list[str]]]:
    """Analyze inter-package imports and detect circular dependencies.

    Orchestrates the full coupling analysis pipeline:
    1. Determine top-level packages from file paths
    2. Extract internal imports from each file (AST)
    3. Compute Ce/Ca/Instability per 2-level package
    4. Detect circular dependencies

    Args:
        files: List of relative file paths (from git ls-files)

    Returns:
        Tuple of (coupling_list, circular_deps) where:
        - coupling_list: PackageCoupling per package with Ce/Ca/Instability
        - circular_deps: List of [pkg_a, pkg_b] circular pairs
    """
    if not files:
        return [], []

    top_pkgs = _top_level_packages(files)
    imports_by_pkg: dict[str, set[str]] = defaultdict(set)

    for fpath in files:
        try:
            content = Path(fpath).read_text(encoding="utf-8")
        except Exception:
            continue

        ext = Path(fpath).suffix
        if ext == ".py":
            pairs = _extract_python_imports(fpath, content, top_pkgs)
        elif ext in JS_EXTENSIONS:
            pairs = _extract_js_imports(fpath, content, top_pkgs)
        else:
            continue

        for src_pkg, tgt_pkg in pairs:
            if src_pkg != tgt_pkg:
                imports_by_pkg[src_pkg].add(tgt_pkg)

    return _compute_coupling_metrics(imports_by_pkg)


def _top_level_packages(files: list[str]) -> set[str]:
    """Get top-level package names from file paths.

    Extracts the first directory component of each path.
    For root-level files (no directory), uses the filename itself.

    Args:
        files: List of relative file paths

    Returns:
        Set of top-level directory/package names
    """
    pkgs: set[str] = set()
    for f in files:
        parts = f.replace("\\", "/").split("/")
        if parts:
            pkgs.add(parts[0])
    return pkgs


def _extract_python_imports(
    fpath: str, content: str, top_pkgs: set[str]
) -> list[tuple[str, str]]:
    """Extract internal import pairs (src_pkg, tgt_pkg) from a Python file.

    Parses the file content with AST, finds import/from-import statements,
    filters to only internal project imports (matching top_pkgs), and
    returns (source_package, target_package) pairs at the 2-level depth
    (e.g., "autocode.core", "autocode.interfaces").

    Args:
        fpath: Relative file path (used to determine source package)
        content: File content string
        top_pkgs: Set of known top-level project package names

    Returns:
        List of (src_pkg, tgt_pkg) tuples. May include same-package pairs;
        the caller is responsible for filtering those out.
    """
    try:
        tree = ast.parse(content, filename=fpath)
    except SyntaxError:
        return []

    module = fpath.replace("/", ".").replace("\\", ".").replace(".py", "")
    src_parts = module.split(".")
    src_pkg = ".".join(src_parts[:2]) if len(src_parts) >= 2 else src_parts[0]

    pairs: list[tuple[str, str]] = []

    for node in ast.walk(tree):
        target = None
        if isinstance(node, ast.ImportFrom) and node.module:
            if any(node.module.startswith(p) for p in top_pkgs):
                target = node.module
        elif isinstance(node, ast.Import):
            for alias in node.names:
                if any(alias.name.startswith(p) for p in top_pkgs):
                    tgt_parts = alias.name.split(".")
                    tgt_pkg = (
                        ".".join(tgt_parts[:2])
                        if len(tgt_parts) >= 2
                        else tgt_parts[0]
                    )
                    pairs.append((src_pkg, tgt_pkg))

        if target:
            tgt_parts = target.split(".")
            tgt_pkg = (
                ".".join(tgt_parts[:2]) if len(tgt_parts) >= 2 else tgt_parts[0]
            )
            pairs.append((src_pkg, tgt_pkg))

    return pairs


def _extract_js_imports(
    fpath: str, content: str, top_pkgs: set[str]
) -> list[tuple[str, str]]:
    """Extract internal import pairs (src_pkg, tgt_pkg) from a JavaScript file.

    Uses regex to find import/export-from statements. Only relative imports
    (starting with './' or '../') are considered internal; bare specifiers
    (e.g., 'lit', 'd3', 'lodash/get') are treated as external and skipped.

    Relative paths are resolved against the file's directory to produce an
    absolute project path, then mapped to a 2-level dotted package name.

    Args:
        fpath: Relative file path (e.g., "web/elements/graph/index.js")
        content: File content string
        top_pkgs: Set of known top-level project package names (unused for JS,
                  kept for API symmetry with Python variant)

    Returns:
        List of (src_pkg, tgt_pkg) tuples. May include same-package pairs;
        the caller is responsible for filtering those out.
    """
    src_pkg = _file_to_package(fpath)
    file_dir = posixpath.dirname(fpath.replace("\\", "/"))

    pairs: list[tuple[str, str]] = []

    for match in JS_IMPORT_RE.finditer(content):
        module = match.group("module")
        # Only process relative imports (internal)
        if not module.startswith("."):
            continue

        # Resolve relative path against file's directory
        resolved = posixpath.normpath(posixpath.join(file_dir, module))
        tgt_pkg = _file_to_package(resolved)

        pairs.append((src_pkg, tgt_pkg))

    return pairs


def _file_to_package(fpath: str) -> str:
    """Convert a file path to a 2-level dotted package name.

    Examples:
        "web/elements/graph/index.js" → "web.elements"
        "autocode/core/code/metrics.py" → "autocode.core"
        "setup.py" → "setup.py"

    Args:
        fpath: Relative file path

    Returns:
        Dotted 2-level package name
    """
    parts = fpath.replace("\\", "/").split("/")
    if len(parts) >= 2:
        return f"{parts[0]}.{parts[1]}"
    return parts[0] if parts else fpath


def _compute_coupling_metrics(
    imports_by_pkg: dict[str, set[str]],
) -> tuple[list[PackageCoupling], list[list[str]]]:
    """Compute Ce/Ca/Instability and detect circular dependencies.

    Args:
        imports_by_pkg: Dict mapping package name → set of packages it imports

    Returns:
        Tuple of (coupling_list, circular_deps)
    """
    # Gather all known packages
    all_pkgs: set[str] = set()
    for src, targets in imports_by_pkg.items():
        all_pkgs.add(src)
        all_pkgs.update(targets)

    if not all_pkgs:
        return [], []

    # Ce (efferent coupling) = number of packages this one depends on
    ce = {pkg: len(imports_by_pkg.get(pkg, set())) for pkg in all_pkgs}

    # Ca (afferent coupling) = number of packages that depend on this one
    ca: dict[str, int] = defaultdict(int)
    imported_by: dict[str, list[str]] = defaultdict(list)
    for src, targets in imports_by_pkg.items():
        for tgt in targets:
            ca[tgt] += 1
            imported_by[tgt].append(src)

    # Build PackageCoupling list
    coupling: list[PackageCoupling] = []
    for pkg in sorted(all_pkgs):
        c_e = ce.get(pkg, 0)
        c_a = ca.get(pkg, 0)
        inst = c_e / (c_e + c_a) if (c_e + c_a) > 0 else 0
        coupling.append(
            PackageCoupling(
                name=pkg,
                ce=c_e,
                ca=c_a,
                instability=round(inst, 2),
                imports_to=sorted(imports_by_pkg.get(pkg, set())),
                imported_by=sorted(imported_by.get(pkg, [])),
            )
        )

    # Detect circular dependencies (A→B and B→A)
    circulars: list[list[str]] = []
    seen: set[tuple[str, str]] = set()
    for a in imports_by_pkg:
        for b in imports_by_pkg[a]:
            if a in imports_by_pkg.get(b, set()):
                pair = tuple(sorted([a, b]))
                if pair not in seen:
                    seen.add(pair)
                    circulars.append(list(pair))

    return coupling, circulars
