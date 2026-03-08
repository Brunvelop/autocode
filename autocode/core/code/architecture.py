"""
architecture.py
Motor de análisis de arquitectura de código y endpoint registrado.

Proporciona:
- Snapshot de arquitectura: jerarquía de directorios/archivos con métricas de calidad
- Propagación bottom-up de MI/CC desde archivos a directorios (ponderada por LOC)
- Resolución de dependencias a nivel de archivo (imports internos del proyecto)
- Detección de dependencias circulares entre archivos (Python AST + JS regex)
- Endpoint registrado para el frontend (treemap + grafo de dependencias)
"""

import ast
import logging
import posixpath
import re
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Set

from autocode.interfaces.registry import register_function
from autocode.core.code.models import (
    ArchitectureNode,
    ArchitectureSnapshot,
    ArchitectureSnapshotOutput,
    FileDependency,
)
from autocode.core.vcs.git import git, get_tracked_files
from autocode.core.code.analyzer import analyze_file_metrics

from autocode.core.code.coupling import JS_IMPORT_RE

logger = logging.getLogger(__name__)

JS_EXTENSIONS = frozenset({".js", ".mjs", ".jsx"})
_ALL_EXTENSIONS = (".py", ".js", ".mjs", ".jsx")


# ==============================================================================
# REGISTERED ENDPOINTS
# ==============================================================================


@register_function(http_methods=["GET"], interfaces=["api"])
def get_architecture_snapshot(path: str = ".") -> ArchitectureSnapshotOutput:
    """
    Obtiene un snapshot de la arquitectura del proyecto con métricas por nodo.

    Analiza todos los archivos Python y JavaScript trackeados por git, construye
    una jerarquía de directorios/archivos, calcula métricas de calidad (MI, CC,
    LOC) por archivo y las propaga hacia arriba a los directorios padres como
    promedios ponderados por líneas de código fuente (SLOC).

    Args:
        path: Path relativo al directorio a analizar (default: directorio actual)
    """
    try:
        # Git metadata
        commit_hash = git("rev-parse", "HEAD")
        commit_short = git("rev-parse", "--short", "HEAD")
        branch = git("rev-parse", "--abbrev-ref", "HEAD")

        # Get tracked files (Python + JavaScript)
        all_files = get_tracked_files(*_ALL_EXTENSIONS)

        # Build hierarchy with per-file metrics
        nodes = _build_architecture_nodes(all_files)

        # Propagate metrics bottom-up
        root_id = "."
        _propagate_metrics(nodes, root_id)

        # Compute global aggregates from file nodes
        file_nodes = [n for n in nodes if n.type == "file"]
        total_files = len(file_nodes)
        total_sloc = sum(n.sloc for n in file_nodes)
        total_functions = sum(n.functions_count for n in file_nodes)
        total_classes = sum(n.classes_count for n in file_nodes)

        if total_sloc > 0:
            avg_mi = sum(n.mi * n.sloc for n in file_nodes) / total_sloc
            avg_complexity = sum(n.avg_complexity * n.sloc for n in file_nodes) / total_sloc
        elif file_nodes:
            avg_mi = sum(n.mi for n in file_nodes) / len(file_nodes)
            avg_complexity = sum(n.avg_complexity for n in file_nodes) / len(file_nodes)
        else:
            avg_mi = 0.0
            avg_complexity = 0.0

        # Resolve file-level dependencies (Python AST + JS regex)
        dependencies, circular_dependencies = _resolve_file_dependencies(all_files)

        snapshot = ArchitectureSnapshot(
            root_id=root_id,
            nodes=nodes,
            commit_hash=commit_hash,
            commit_short=commit_short,
            branch=branch,
            timestamp=datetime.now().isoformat(),
            total_files=total_files,
            total_sloc=total_sloc,
            total_functions=total_functions,
            total_classes=total_classes,
            avg_mi=round(avg_mi, 1),
            avg_complexity=round(avg_complexity, 2),
            dependencies=dependencies,
            circular_dependencies=circular_dependencies,
        )

        return ArchitectureSnapshotOutput(
            success=True,
            result=snapshot,
            message=f"Arquitectura: {total_files} archivos, {total_sloc} SLOC, "
                    f"MI={avg_mi:.1f}, CC={avg_complexity:.2f}",
        )

    except Exception as e:
        logger.error(f"Error generando snapshot de arquitectura: {e}")
        return ArchitectureSnapshotOutput(success=False, message=str(e))


# ==============================================================================
# HIERARCHY BUILDING
# ==============================================================================


def _build_architecture_nodes(py_files: List[str]) -> List[ArchitectureNode]:
    """Build a flat list of ArchitectureNode from a list of .py file paths.

    Creates the root node, intermediate directory nodes, and file nodes
    with metrics from _analyze_content.

    Args:
        py_files: List of relative paths to Python files (from git ls-files)

    Returns:
        List of ArchitectureNode in adjacency-list format
    """
    root_id = "."
    root = ArchitectureNode(
        id=root_id, parent_id=None, name="root", type="directory", path=root_id,
    )
    nodes: List[ArchitectureNode] = [root]
    created_dirs: Dict[str, ArchitectureNode] = {root_id: root}

    for fpath in py_files:
        # Create intermediate directories
        parts = fpath.replace("\\", "/").split("/")
        current_parent = root_id

        for i, part in enumerate(parts[:-1]):
            # Build directory path
            if current_parent == root_id:
                dir_path = part
            else:
                dir_path = f"{current_parent}/{part}"

            if dir_path not in created_dirs:
                dir_node = ArchitectureNode(
                    id=dir_path,
                    parent_id=current_parent,
                    name=part,
                    type="directory",
                    path=dir_path,
                )
                nodes.append(dir_node)
                created_dirs[dir_path] = dir_node

            current_parent = dir_path

        # Create file node with metrics
        file_name = parts[-1]
        try:
            content = Path(fpath).read_text(encoding="utf-8")
            fm = analyze_file_metrics(fpath, content)
            file_node = ArchitectureNode(
                id=fpath,
                parent_id=current_parent,
                name=file_name,
                type="file",
                path=fpath,
                loc=fm.total_loc,
                sloc=fm.sloc,
                mi=fm.maintainability_index,
                avg_complexity=fm.avg_complexity,
                max_complexity=fm.max_complexity,
                functions_count=fm.functions_count,
                classes_count=fm.classes_count,
            )
        except Exception as e:
            logger.debug(f"Skip {fpath}: {e}")
            file_node = ArchitectureNode(
                id=fpath,
                parent_id=current_parent,
                name=file_name,
                type="file",
                path=fpath,
            )

        nodes.append(file_node)

    return nodes


# ==============================================================================
# METRIC PROPAGATION
# ==============================================================================


def _propagate_metrics(nodes: List[ArchitectureNode], root_id: str) -> None:
    """Propagate metrics bottom-up from files to parent directories.

    Each directory receives:
    - sloc/loc: sum of direct children
    - mi: LOC-weighted average of direct children
    - avg_complexity: LOC-weighted average of direct children
    - max_complexity: max of direct children
    - functions_count/classes_count: sum of direct children
    - children_count: number of direct children

    Processing order: bottom-up (leaves first) using topological sort by depth.

    Args:
        nodes: List of ArchitectureNode (modified in-place)
        root_id: ID of the root node
    """
    node_map: Dict[str, ArchitectureNode] = {n.id: n for n in nodes}

    # Build children map
    children_map: Dict[str, List[str]] = defaultdict(list)
    for n in nodes:
        if n.parent_id is not None:
            children_map[n.parent_id].append(n.id)

    # Calculate depth for each node (for bottom-up ordering)
    depths: Dict[str, int] = {}
    _compute_depths(root_id, children_map, depths, 0)

    # Process directories bottom-up (deepest first)
    dir_nodes = [n for n in nodes if n.type == "directory"]
    dir_nodes.sort(key=lambda n: depths.get(n.id, 0), reverse=True)

    for dir_node in dir_nodes:
        child_ids = children_map.get(dir_node.id, [])
        if not child_ids:
            continue

        children = [node_map[cid] for cid in child_ids if cid in node_map]
        dir_node.children_count = len(children)

        # Aggregate metrics
        total_sloc = sum(c.sloc for c in children)
        total_loc = sum(c.loc for c in children)
        total_funcs = sum(c.functions_count for c in children)
        total_classes = sum(c.classes_count for c in children)
        max_cc = max((c.max_complexity for c in children), default=0)

        dir_node.sloc = total_sloc
        dir_node.loc = total_loc
        dir_node.functions_count = total_funcs
        dir_node.classes_count = total_classes
        dir_node.max_complexity = max_cc

        # LOC-weighted averages for MI and CC
        if total_sloc > 0:
            dir_node.mi = round(
                sum(c.mi * c.sloc for c in children) / total_sloc, 2
            )
            dir_node.avg_complexity = round(
                sum(c.avg_complexity * c.sloc for c in children) / total_sloc, 2
            )
        elif children:
            # If no SLOC, use simple average
            dir_node.mi = round(
                sum(c.mi for c in children) / len(children), 2
            )
            dir_node.avg_complexity = round(
                sum(c.avg_complexity for c in children) / len(children), 2
            )


def _compute_depths(
    node_id: str,
    children_map: Dict[str, List[str]],
    depths: Dict[str, int],
    current_depth: int,
) -> None:
    """Recursively compute depth of each node from root."""
    depths[node_id] = current_depth
    for child_id in children_map.get(node_id, []):
        _compute_depths(child_id, children_map, depths, current_depth + 1)


# ==============================================================================
# FILE-LEVEL DEPENDENCY RESOLUTION
# ==============================================================================


def _resolve_file_dependencies(
    all_files: List[str],
) -> Tuple[List[FileDependency], List[List[str]]]:
    """Resolve file-level import dependencies between Python and JS files.

    For Python: parses AST, extracts import/from-import statements, filters
    to internal project imports, resolves module paths to file paths.
    For JS: uses regex, extracts relative imports (./  ../), resolves to
    file paths in the tracked file set.

    Multiple imports from the same source→target pair are merged into a single
    FileDependency with aggregated import_names.

    Args:
        all_files: List of relative file paths (.py, .js, .mjs, .jsx)

    Returns:
        Tuple of (dependencies, circular_dependencies) where:
        - dependencies: List[FileDependency] with resolved source→target pairs
        - circular_dependencies: List[List[str]] with [source, target] circular pairs
    """
    if not all_files:
        return [], []

    # Separate by language
    py_files = [f for f in all_files if f.endswith(".py")]
    js_files = [f for f in all_files if Path(f).suffix in JS_EXTENSIONS]

    # Build lookup structures
    file_set: Set[str] = set(all_files)
    top_packages = _get_top_level_packages(all_files)
    module_to_file = _build_module_to_file_map(py_files)

    # Collect raw edges: (source_file, target_file) → set of import_names
    edges: Dict[Tuple[str, str], Set[str]] = defaultdict(set)

    # --- Python files (AST) ---
    _collect_python_file_deps(py_files, top_packages, module_to_file, file_set, edges)

    # --- JS files (regex) ---
    _collect_js_file_deps(js_files, file_set, edges)

    # Build FileDependency list
    dependencies: List[FileDependency] = []
    for (source, target), names in sorted(edges.items()):
        dependencies.append(
            FileDependency(
                source=source,
                target=target,
                import_names=sorted(names),
            )
        )

    # Detect circular dependencies (A→B and B→A)
    circular_dependencies: List[List[str]] = []
    seen_pairs: Set[Tuple[str, str]] = set()
    edge_keys = set(edges.keys())

    for source, target in edge_keys:
        if (target, source) in edge_keys:
            pair = tuple(sorted([source, target]))
            if pair not in seen_pairs:
                seen_pairs.add(pair)
                circular_dependencies.append(list(pair))

    return dependencies, circular_dependencies


def _collect_python_file_deps(
    py_files: List[str],
    top_packages: Set[str],
    module_to_file: Dict[str, str],
    file_set: Set[str],
    edges: Dict[Tuple[str, str], Set[str]],
) -> None:
    """Collect file-level dependencies from Python files using AST."""
    for fpath in py_files:
        try:
            content = Path(fpath).read_text(encoding="utf-8")
            tree = ast.parse(content, filename=fpath)
        except Exception:
            logger.debug(f"Skipping {fpath} for dependency analysis (parse error)")
            continue

        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module:
                if not _is_internal_module(node.module, top_packages):
                    continue
                target_file = _resolve_module_to_file(node.module, module_to_file)
                if target_file and target_file != fpath and target_file in file_set:
                    names = [
                        alias.name
                        for alias in (node.names or [])
                        if alias.name != "*"
                    ]
                    edges[(fpath, target_file)].update(names)

            elif isinstance(node, ast.Import):
                for alias in node.names:
                    if not _is_internal_module(alias.name, top_packages):
                        continue
                    target_file = _resolve_module_to_file(
                        alias.name, module_to_file
                    )
                    if target_file and target_file != fpath and target_file in file_set:
                        edges[(fpath, target_file)].add(alias.name)


def _collect_js_file_deps(
    js_files: List[str],
    file_set: Set[str],
    edges: Dict[Tuple[str, str], Set[str]],
) -> None:
    """Collect file-level dependencies from JS files using regex.

    Only relative imports (starting with './' or '../') are processed.
    Bare specifiers like 'lit' or 'd3' are external and skipped.
    """
    for fpath in js_files:
        try:
            content = Path(fpath).read_text(encoding="utf-8")
        except Exception:
            logger.debug(f"Skipping {fpath} for JS dependency analysis")
            continue

        file_dir = posixpath.dirname(fpath.replace("\\", "/"))

        for match in JS_IMPORT_RE.finditer(content):
            module = match.group("module")
            if not module.startswith("."):
                continue

            # Resolve relative path to a project file path
            target_file = _resolve_js_import(file_dir, module, file_set)
            if target_file and target_file != fpath:
                edges[(fpath, target_file)].add(module)


def _resolve_js_import(
    file_dir: str, module: str, file_set: Set[str]
) -> Optional[str]:
    """Resolve a relative JS import specifier to a tracked file path.

    Tries the following resolution strategies:
    1. Direct path: './component.js' → {dir}/component.js
    2. Extension variants: './component' → {dir}/component.js, .mjs, .jsx
    3. Index file: './utils' → {dir}/utils/index.js

    Args:
        file_dir: Directory of the importing file (posix-normalized)
        module: The import specifier (e.g., './component.js', '../utils')
        file_set: Set of all tracked file paths

    Returns:
        Resolved file path if found in file_set, None otherwise
    """
    resolved = posixpath.normpath(posixpath.join(file_dir, module))

    # 1. Direct match (already has extension)
    if resolved in file_set:
        return resolved

    # 2. Try adding common JS extensions
    for ext in (".js", ".mjs", ".jsx"):
        candidate = resolved + ext
        if candidate in file_set:
            return candidate

    # 3. Try as directory with index file
    for ext in (".js", ".mjs", ".jsx"):
        candidate = resolved + "/index" + ext
        if candidate in file_set:
            return candidate

    return None


def _get_top_level_packages(py_files: List[str]) -> Set[str]:
    """Get top-level package names from file paths.

    Args:
        py_files: List of relative Python file paths

    Returns:
        Set of top-level directory/package names
    """
    pkgs: Set[str] = set()
    for f in py_files:
        parts = f.replace("\\", "/").split("/")
        if parts:
            pkgs.add(parts[0])
    return pkgs


def _is_internal_module(module_name: str, top_packages: Set[str]) -> bool:
    """Check if a module name belongs to the project (not stdlib/third-party).

    Args:
        module_name: Dotted module name (e.g., 'autocode.core.code.models')
        top_packages: Set of known top-level project package names

    Returns:
        True if the module is internal to the project
    """
    top = module_name.split(".")[0]
    return top in top_packages


def _build_module_to_file_map(py_files: List[str]) -> Dict[str, str]:
    """Build a mapping from dotted module names to file paths.

    For each file path like 'autocode/core/code/models.py', creates entries:
    - 'autocode.core.code.models' → 'autocode/core/code/models.py'

    For __init__.py files like 'autocode/core/__init__.py', creates:
    - 'autocode.core' → 'autocode/core/__init__.py'

    Args:
        py_files: List of relative Python file paths

    Returns:
        Dict mapping dotted module names to file paths
    """
    module_map: Dict[str, str] = {}
    for fpath in py_files:
        normalized = fpath.replace("\\", "/")
        if normalized.endswith("/__init__.py"):
            # Package: autocode/core/__init__.py → autocode.core
            module_name = normalized[: -len("/__init__.py")].replace("/", ".")
        elif normalized.endswith(".py"):
            # Module: autocode/core/code/models.py → autocode.core.code.models
            module_name = normalized[:-3].replace("/", ".")
        else:
            continue
        module_map[module_name] = fpath
    return module_map


def _resolve_module_to_file(
    module_name: str, module_to_file: Dict[str, str]
) -> Optional[str]:
    """Resolve a dotted module name to its file path.

    Tries multiple resolution strategies:
    1. Direct match: 'autocode.core.code.models' → known file
    2. Package __init__: if module is a package directory

    For 'from autocode.core import code', the module is 'autocode.core'
    which resolves to 'autocode/core/__init__.py'.

    Args:
        module_name: Dotted module name to resolve
        module_to_file: Pre-built module→file mapping

    Returns:
        File path if resolved, None otherwise
    """
    # Direct module match
    if module_name in module_to_file:
        return module_to_file[module_name]

    return None
