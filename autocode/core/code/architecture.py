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

from fastapi import HTTPException
from refract import register_function
from autocode.core.code.models import (
    ArchitectureNode,
    ArchitectureHotspot,
    ArchitectureHotspotsResult,
    ArchitectureSnapshot,
    DependencyCycle,
    DependencyCycleLevel,
    DependencyCyclesResult,
    DependencyEdge,
    DependencySliceResult,
    FileDependency,
)
from autocode.core.vcs.git import git, git_show, get_tracked_files, get_tracked_files_at_commit
from autocode.core.code.analyzer import analyze_file_metrics, maintainability_index

from autocode.core.code.coupling import JS_IMPORT_RE

logger = logging.getLogger(__name__)

JS_EXTENSIONS = frozenset({".js", ".mjs", ".jsx"})
_ALL_EXTENSIONS = (".py", ".js", ".mjs", ".jsx")


# ==============================================================================
# REGISTERED ENDPOINTS
# ==============================================================================


@register_function(http_methods=["GET"], interfaces=["api"])
def get_architecture_snapshot(path: str = ".", commit_hash: str = "") -> ArchitectureSnapshot:
    """
    Obtiene un snapshot de la arquitectura del proyecto con métricas por nodo.

    Analiza todos los archivos Python y JavaScript trackeados por git, construye
    una jerarquía de directorios/archivos, calcula métricas de calidad (MI, CC,
    LOC) por archivo y las propaga hacia arriba a los directorios padres como
    promedios ponderados por líneas de código fuente (SLOC).

    Args:
        path: Path relativo al directorio a analizar (default: directorio actual)
        commit_hash: Hash del commit a analizar. Si está vacío, usa HEAD (default: "")
    """
    try:
        if commit_hash:
            # Historical mode: read files from git object store at the given commit
            commit_full = git("rev-parse", commit_hash)
            commit_short = git("rev-parse", "--short", commit_hash)
            branch = git("log", "-1", "--format=%D", commit_hash)
            all_files = get_tracked_files_at_commit(commit_hash, *_ALL_EXTENSIONS)
            content_reader = lambda fpath: git_show(f"{commit_hash}:{fpath}") or ""
        else:
            # Current mode (unchanged): read files from disk at HEAD
            commit_full = git("rev-parse", "HEAD")
            commit_short = git("rev-parse", "--short", "HEAD")
            branch = git("rev-parse", "--abbrev-ref", "HEAD")
            all_files = get_tracked_files(*_ALL_EXTENSIONS)
            content_reader = None  # default: Path.read_text

        # Build hierarchy with per-file metrics
        nodes = _build_architecture_nodes(all_files, content_reader=content_reader)

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
        dependencies, circular_dependencies = _resolve_file_dependencies(
            all_files, content_reader=content_reader
        )

        return ArchitectureSnapshot(
            root_id=root_id,
            nodes=nodes,
            commit_hash=commit_full,
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

    except Exception as e:
        logger.error(f"Error generando snapshot de arquitectura: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@register_function(http_methods=["GET"], interfaces=["mcp"])
def get_dependency_cycles(
    path: str = ".",
    max_cycles: int = 20,
    min_cycle_size: int = 2,
    granularity: str = "file",
    depth: Optional[int] = None,
    max_depth: Optional[int] = None,
) -> DependencyCyclesResult:
    """Return compact dependency cycles for agent-oriented analysis."""
    try:
        normalized_path = path.strip() or "."
        normalized_granularity = granularity.strip().lower()
        if max_cycles < 1:
            raise HTTPException(status_code=400, detail="max_cycles must be >= 1")
        if min_cycle_size < 2:
            raise HTTPException(status_code=400, detail="min_cycle_size must be >= 2")
        if normalized_granularity not in {"file", "grouped", "all"}:
            raise HTTPException(status_code=400, detail="granularity must be one of: file, grouped, all")
        if depth is not None and depth < 1:
            raise HTTPException(status_code=400, detail="depth must be >= 1")
        if max_depth is not None and max_depth < 1:
            raise HTTPException(status_code=400, detail="max_depth must be >= 1")

        all_files = get_tracked_files(*_ALL_EXTENSIONS)
        filtered_files = _filter_files_by_path(all_files, normalized_path)
        dependencies, _ = _resolve_file_dependencies(filtered_files)

        edge_map = {
            (dep.source, dep.target): set(dep.import_names)
            for dep in dependencies
        }
        cycles = _find_dependency_cycles(edge_map)
        filtered_cycles = [cycle for cycle in cycles if len(cycle) >= min_cycle_size]
        filtered_cycles.sort(key=lambda cycle: (-len(cycle), cycle))

        limited_cycles = filtered_cycles[:max_cycles]
        files_in_cycles = sorted({fpath for cycle in filtered_cycles for fpath in cycle})
        file_level = DependencyCycleLevel(
            granularity="file",
            depth=None,
            cycle_count=len(filtered_cycles),
            returned_cycles=len(limited_cycles),
            cycles=[
                DependencyCycle(files=cycle, size=len(cycle))
                for cycle in limited_cycles
            ],
        )

        levels = []
        if normalized_granularity in {"file", "all"}:
            levels.append(file_level)
        if normalized_granularity in {"grouped", "all"}:
            grouped_depths = _select_grouped_cycle_depths(filtered_files, depth, max_depth)
            levels.extend(
                _build_grouped_cycle_level(
                    dependencies,
                    group_depth,
                    max_cycles=max_cycles,
                    min_cycle_size=min_cycle_size,
                )
                for group_depth in grouped_depths
            )

        grouped_cycle_depths = [
            level.depth for level in levels
            if level.granularity == "grouped" and level.cycle_count > 0
        ]
        summary = {
            "path": normalized_path,
            "cycle_count": len(filtered_cycles),
            "returned_cycles": len(limited_cycles),
            "files_in_cycles": len(files_in_cycles),
            "largest_cycle": max((len(cycle) for cycle in filtered_cycles), default=0),
        }
        if normalized_granularity != "file" or depth is not None or max_depth is not None:
            summary.update({
                "granularity": normalized_granularity,
                "depth": depth,
                "file_cycle_count": len(filtered_cycles),
                "grouped_cycle_depths": grouped_cycle_depths,
                "max_depth": _max_dependency_depth(filtered_files),
            })

        return DependencyCyclesResult(
            summary=summary,
            cycles=file_level.cycles,
            levels=levels,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error obteniendo ciclos de dependencias: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@register_function(http_methods=["GET"], interfaces=["mcp"])
def get_dependency_slice(
    target: str,
    direction: str = "both",
    max_depth: int = 2,
    path: str = ".",
    max_nodes: int = 50,
) -> DependencySliceResult:
    """Return a compact local dependency slice around an exact file target."""
    try:
        normalized_path = path.strip() or "."
        normalized_target = target.strip()
        normalized_direction = direction.strip().lower()

        if not normalized_target:
            raise HTTPException(status_code=400, detail="target is required")
        if normalized_direction not in {"in", "out", "both"}:
            raise HTTPException(status_code=400, detail="direction must be one of: in, out, both")
        if max_depth < 0:
            raise HTTPException(status_code=400, detail="max_depth must be >= 0")
        if max_nodes < 1:
            raise HTTPException(status_code=400, detail="max_nodes must be >= 1")

        all_files = get_tracked_files(*_ALL_EXTENSIONS)
        filtered_files = _filter_files_by_path(all_files, normalized_path)
        if normalized_target not in filtered_files:
            raise HTTPException(
                status_code=404,
                detail=f"target not found in path scope: {normalized_target}",
            )

        dependencies, _ = _resolve_file_dependencies(filtered_files)
        edge_map = {
            (dep.source, dep.target): set(dep.import_names)
            for dep in dependencies
        }
        outgoing = _build_dependency_adjacency(edge_map)
        incoming = _build_reverse_dependency_adjacency(edge_map)

        allowed_nodes = {normalized_target}
        in_layers: List[List[str]] = []
        out_layers: List[List[str]] = []
        truncated = False

        if normalized_direction in {"in", "both"}:
            in_layers, in_truncated = _collect_dependency_layers(
                normalized_target,
                incoming,
                max_depth=max_depth,
                max_nodes=max_nodes,
                allowed_nodes=allowed_nodes,
            )
            truncated = truncated or in_truncated

        if normalized_direction in {"out", "both"}:
            out_layers, out_truncated = _collect_dependency_layers(
                normalized_target,
                outgoing,
                max_depth=max_depth,
                max_nodes=max_nodes,
                allowed_nodes=allowed_nodes,
            )
            truncated = truncated or out_truncated

        slice_edges = [
            DependencyEdge(source=source, target=target)
            for source, target in sorted(edge_map)
            if source in allowed_nodes and target in allowed_nodes
        ]
        cycles = [
            cycle for cycle in _find_dependency_cycles(edge_map)
            if normalized_target in cycle and set(cycle).issubset(allowed_nodes)
        ]

        return DependencySliceResult(
            target=normalized_target,
            summary={
                "path": normalized_path,
                "direction": normalized_direction,
                "max_depth": max_depth,
                "max_nodes": max_nodes,
                "node_count": len(allowed_nodes),
                "edge_count": len(slice_edges),
                "cycles_count": len(cycles),
                "truncated": truncated,
            },
            in_layers=in_layers,
            out_layers=out_layers,
            edges=slice_edges,
            cycles=cycles,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error obteniendo slice de dependencias: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@register_function(http_methods=["GET"], interfaces=["mcp"])
def get_architecture_hotspots(
    limit: int = 10,
    path: str = ".",
) -> ArchitectureHotspotsResult:
    """Return a compact ranking of architecture hotspots for agent triage."""
    try:
        normalized_path = path.strip() or "."
        if limit < 1:
            raise HTTPException(status_code=400, detail="limit must be >= 1")

        all_files = get_tracked_files(*_ALL_EXTENSIONS)
        filtered_files = _filter_files_by_path(all_files, normalized_path)
        nodes = _build_architecture_nodes(filtered_files)
        file_nodes = sorted(
            (node for node in nodes if node.type == "file"),
            key=lambda node: node.path,
        )

        dependencies, _ = _resolve_file_dependencies(filtered_files)
        edge_map = {
            (dep.source, dep.target): set(dep.import_names)
            for dep in dependencies
        }
        cycles = _find_dependency_cycles(edge_map)

        hotspots = _rank_architecture_hotspots(file_nodes, edge_map, cycles)[:limit]

        return ArchitectureHotspotsResult(
            summary={
                "path": normalized_path,
                "files_analyzed": len(file_nodes),
                "hotspot_count": len(hotspots),
                "cycle_files": len({node for cycle in cycles for node in cycle}),
                "returned_limit": limit,
            },
            hotspots=hotspots,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error obteniendo hotspots de arquitectura: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==============================================================================
# HIERARCHY BUILDING
# ==============================================================================


def _build_architecture_nodes(
    py_files: List[str], content_reader=None
) -> List[ArchitectureNode]:
    """Build a flat list of ArchitectureNode from a list of .py file paths.

    Creates the root node, intermediate directory nodes, and file nodes
    with metrics from _analyze_content.

    Args:
        py_files: List of relative paths to Python files (from git ls-files)
        content_reader: Optional callable(fpath) -> str to read file content.
            Defaults to Path(fpath).read_text(encoding="utf-8") when None.

    Returns:
        List of ArchitectureNode in adjacency-list format
    """
    if content_reader is None:
        content_reader = lambda fpath: Path(fpath).read_text(encoding="utf-8")

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
            content = content_reader(fpath)
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
            nodes.append(file_node)
            # Create function/class/method child nodes from FileMetrics
            nodes.extend(_create_function_class_nodes(fpath, fm))
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


def _create_function_class_nodes(fpath: str, fm) -> List[ArchitectureNode]:
    """Create function, class, and method ArchitectureNodes for a file.

    Groups FunctionMetrics by class_name:
    - Methods (class_name set) → one class container node + one method node each
    - Standalone functions (no class_name) → one function node each

    Args:
        fpath: Relative file path (used as the file node ID / parent)
        fm: FileMetrics object with a populated ``functions`` list

    Returns:
        List of new ArchitectureNode objects (class + method + function nodes)
    """
    nodes: List[ArchitectureNode] = []

    # Fast-path: nothing to process at all
    if not fm.functions and not getattr(fm, "classes", []):
        return []


    # Separate methods (have a class) from standalone functions
    classes: Dict[str, list] = defaultdict(list)
    standalone = []
    for func in fm.functions:
        if func.class_name:
            classes[func.class_name].append(func)
        else:
            standalone.append(func)

    # --- Class nodes + their method children ---
    for class_name, methods in classes.items():
        class_id = f"{fpath}::{class_name}"
        method_sloc = sum(m.sloc for m in methods)
        complexities = [m.complexity for m in methods]
        class_node = ArchitectureNode(
            id=class_id,
            parent_id=fpath,
            name=class_name,
            type="class",
            path=fpath,
            sloc=method_sloc,
            avg_complexity=round(sum(complexities) / len(complexities), 2) if complexities else 0.0,
            max_complexity=max(complexities, default=0),
            functions_count=len(methods),
        )
        nodes.append(class_node)

        for method in methods:
            method_name = method.name.split(".")[-1]
            method_id = f"{fpath}::{class_name}::{method_name}"
            method_mi = round(maintainability_index(
                sloc=method.sloc,
                avg_cc=float(method.complexity),
                total_loc=method.sloc,
            ), 1)
            nodes.append(ArchitectureNode(
                id=method_id,
                parent_id=class_id,
                name=method.name.split(".")[-1],
                type="method",
                path=fpath,
                loc=method.sloc,
                sloc=method.sloc,
                mi=method_mi,
                complexity=method.complexity,
                rank=method.rank,
                avg_complexity=float(method.complexity),
                max_complexity=method.complexity,
            ))

    # --- Orphan classes (detected by AST but with no methods) ---
    classes_with_methods = set(classes.keys())
    for cls_info in getattr(fm, "classes", []):
        if cls_info.name not in classes_with_methods:
            class_id = f"{fpath}::{cls_info.name}"
            orphan_mi = round(maintainability_index(
                sloc=cls_info.sloc,
                avg_cc=0.0,
                total_loc=cls_info.sloc,
            ), 1)
            nodes.append(ArchitectureNode(
                id=class_id,
                parent_id=fpath,
                name=cls_info.name,
                type="class",
                path=fpath,
                loc=cls_info.sloc,
                sloc=cls_info.sloc,
                mi=orphan_mi,
                functions_count=0,
            ))

    # --- Standalone function nodes ---
    for func in standalone:
        func_id = f"{fpath}::{func.name}"
        func_mi = round(maintainability_index(
            sloc=func.sloc,
            avg_cc=float(func.complexity),
            total_loc=func.sloc,
        ), 1)
        nodes.append(ArchitectureNode(
            id=func_id,
            parent_id=fpath,
            name=func.name,
            type="function",
            path=fpath,
            loc=func.sloc,
            sloc=func.sloc,
            mi=func_mi,
            complexity=func.complexity,
            rank=func.rank,
            avg_complexity=float(func.complexity),
            max_complexity=func.complexity,
        ))

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

    # Process container nodes (directories + classes) bottom-up (deepest first)
    # Class nodes aggregate from their method children, just like directories do.
    CONTAINER_TYPES = {"directory", "class"}
    dir_nodes = [n for n in nodes if n.type in CONTAINER_TYPES]
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
    content_reader=None,
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
        content_reader: Optional callable(fpath) -> str to read file content.
            Defaults to Path(fpath).read_text(encoding="utf-8") when None.

    Returns:
        Tuple of (dependencies, circular_dependencies) where:
        - dependencies: List[FileDependency] with resolved source→target pairs
        - circular_dependencies: List[List[str]] with [source, target] circular pairs
    """
    if not all_files:
        return [], []

    if content_reader is None:
        content_reader = lambda fpath: Path(fpath).read_text(encoding="utf-8")

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
    _collect_python_file_deps(py_files, top_packages, module_to_file, file_set, edges, content_reader)

    # --- JS files (regex) ---
    _collect_js_file_deps(js_files, file_set, edges, content_reader)

    # Build FileDependency list and detect circulars
    dependencies = _build_dependency_list(edges)
    circular_dependencies = _detect_circular_pairs(edges)

    return dependencies, circular_dependencies


def _filter_files_by_path(all_files: List[str], path: str) -> List[str]:
    """Filter tracked files by relative path prefix, preserving deterministic order."""
    if path == ".":
        return sorted(all_files)

    normalized = path.rstrip("/\\")
    prefix = f"{normalized}/"
    return sorted(
        fpath for fpath in all_files
        if fpath == normalized or fpath.startswith(prefix)
    )


def _build_dependency_adjacency(
    edges: Dict[Tuple[str, str], Set[str]],
) -> Dict[str, List[str]]:
    """Build a deterministic adjacency list from raw dependency edges."""
    adjacency: Dict[str, Set[str]] = defaultdict(set)

    for source, target in edges:
        adjacency[source].add(target)
        adjacency.setdefault(target, set())

    return {
        node: sorted(neighbors)
        for node, neighbors in sorted(adjacency.items())
    }


def _find_strongly_connected_components(
    adjacency: Dict[str, List[str]],
) -> List[List[str]]:
    """Find strongly connected components using Tarjan's algorithm.

    Returns SCCs with stable ordering so tests and downstream consumers get
    deterministic results.
    """
    index = 0
    stack: List[str] = []
    on_stack: Set[str] = set()
    indices: Dict[str, int] = {}
    lowlinks: Dict[str, int] = {}
    components: List[List[str]] = []

    def strongconnect(node: str) -> None:
        nonlocal index
        indices[node] = index
        lowlinks[node] = index
        index += 1
        stack.append(node)
        on_stack.add(node)

        for neighbor in adjacency.get(node, []):
            if neighbor not in indices:
                strongconnect(neighbor)
                lowlinks[node] = min(lowlinks[node], lowlinks[neighbor])
            elif neighbor in on_stack:
                lowlinks[node] = min(lowlinks[node], indices[neighbor])

        if lowlinks[node] == indices[node]:
            component: List[str] = []
            while stack:
                member = stack.pop()
                on_stack.remove(member)
                component.append(member)
                if member == node:
                    break
            components.append(sorted(component))

    for node in sorted(adjacency):
        if node not in indices:
            strongconnect(node)

    components.sort(key=lambda component: (len(component), component))
    return components


def _find_dependency_cycles(
    edges: Dict[Tuple[str, str], Set[str]],
) -> List[List[str]]:
    """Find real file dependency cycles from raw edges.

    A cycle is any strongly connected component with more than one file.
    """
    adjacency = _build_dependency_adjacency(edges)
    components = _find_strongly_connected_components(adjacency)
    return [component for component in components if len(component) > 1]


def _max_dependency_depth(files: List[str]) -> int:
    """Return the deepest path segment count in the analyzed files."""
    return max((len(fpath.replace("\\", "/").split("/")) for fpath in files), default=1)


def _select_grouped_cycle_depths(
    files: List[str],
    depth: Optional[int],
    max_depth: Optional[int],
) -> List[int]:
    """Select grouped depths to analyze, excluding file-level depth."""
    file_depth = _max_dependency_depth(files)
    highest_group_depth = max(1, file_depth - 1)
    if depth is not None:
        return [min(depth, highest_group_depth)]

    upper = min(max_depth or highest_group_depth, highest_group_depth)
    return list(range(1, upper + 1))


def _file_to_dependency_group(fpath: str, depth: int) -> str:
    """Group a file path by its first ``depth`` path segments."""
    parts = fpath.replace("\\", "/").split("/")
    return "/".join(parts[:depth]) or "."


def _build_grouped_dependency_edges(
    dependencies: List[FileDependency],
    depth: int,
) -> Dict[Tuple[str, str], List[dict]]:
    """Aggregate file-level dependencies into group-level edges."""
    grouped_edges: Dict[Tuple[str, str], List[dict]] = defaultdict(list)
    for dep in dependencies:
        source_group = _file_to_dependency_group(dep.source, depth)
        target_group = _file_to_dependency_group(dep.target, depth)
        if source_group == target_group:
            continue

        grouped_edges[(source_group, target_group)].append({
            "source": dep.source,
            "target": dep.target,
            "import_names": sorted(dep.import_names),
        })

    for file_edges in grouped_edges.values():
        file_edges.sort(key=lambda edge: (edge["source"], edge["target"], edge["import_names"]))
    return dict(sorted(grouped_edges.items()))


def _build_grouped_cycle_level(
    dependencies: List[FileDependency],
    depth: int,
    max_cycles: int,
    min_cycle_size: int,
) -> DependencyCycleLevel:
    """Build grouped SCC cycles for one package depth."""
    grouped_edges = _build_grouped_dependency_edges(dependencies, depth)
    adjacency = _build_dependency_adjacency({edge: set() for edge in grouped_edges})
    cycles = [
        cycle for cycle in _find_strongly_connected_components(adjacency)
        if len(cycle) >= min_cycle_size
    ]
    cycles.sort(key=lambda cycle: (-len(cycle), cycle))

    cycle_models: List[DependencyCycle] = []
    for cycle in cycles[:max_cycles]:
        cycle_nodes = set(cycle)
        supporting_edges = [
            {
                "source": source,
                "target": target,
                "file_edges": grouped_edges[(source, target)],
            }
            for source, target in sorted(grouped_edges)
            if source in cycle_nodes and target in cycle_nodes
        ]
        cycle_models.append(DependencyCycle(
            nodes=cycle,
            size=len(cycle),
            granularity="grouped",
            depth=depth,
            supporting_edges=supporting_edges,
        ))

    return DependencyCycleLevel(
        granularity="grouped",
        depth=depth,
        cycle_count=len(cycles),
        returned_cycles=len(cycle_models),
        cycles=cycle_models,
    )


def _build_reverse_dependency_adjacency(
    edges: Dict[Tuple[str, str], Set[str]],
) -> Dict[str, List[str]]:
    """Build deterministic reverse adjacency for incoming dependency traversal."""
    reversed_edges = {
        (target, source): names
        for (source, target), names in edges.items()
    }
    return _build_dependency_adjacency(reversed_edges)


def _collect_dependency_layers(
    start: str,
    adjacency: Dict[str, List[str]],
    max_depth: int,
    max_nodes: int,
    allowed_nodes: Set[str],
) -> Tuple[List[List[str]], bool]:
    """Collect deterministic BFS layers, capping total nodes across the slice."""
    if max_depth == 0 or len(allowed_nodes) >= max_nodes:
        return [], False

    visited = set(allowed_nodes)
    current_layer = [start]
    layers: List[List[str]] = []
    truncated = False
    reached_depth_limit_with_more = False

    for depth in range(max_depth):
        next_candidates: List[str] = []
        seen_in_layer: Set[str] = set()

        for node in current_layer:
            for neighbor in adjacency.get(node, []):
                if neighbor in visited or neighbor in seen_in_layer:
                    continue
                next_candidates.append(neighbor)
                seen_in_layer.add(neighbor)

        if not next_candidates:
            break

        remaining_capacity = max_nodes - len(allowed_nodes)
        if remaining_capacity <= 0:
            truncated = True
            break

        accepted = next_candidates[:remaining_capacity]
        if len(accepted) < len(next_candidates):
            truncated = True

        if not accepted:
            break

        layers.append(accepted)
        allowed_nodes.update(accepted)
        visited.update(accepted)
        current_layer = accepted

        if depth == max_depth - 1:
            for node in current_layer:
                for neighbor in adjacency.get(node, []):
                    if neighbor not in visited:
                        reached_depth_limit_with_more = True
                        break
                if reached_depth_limit_with_more:
                    break

        if len(allowed_nodes) >= max_nodes:
            truncated = True
            break

    return layers, (truncated or reached_depth_limit_with_more)


def _rank_architecture_hotspots(
    file_nodes: List[ArchitectureNode],
    edges: Dict[Tuple[str, str], Set[str]],
    cycles: List[List[str]],
) -> List[ArchitectureHotspot]:
    """Rank files using a simple transparent score for agent-oriented triage."""
    outgoing = _build_dependency_adjacency(edges)
    incoming = _build_reverse_dependency_adjacency(edges)
    cycle_members = {node for cycle in cycles for node in cycle}

    hotspots: List[ArchitectureHotspot] = []
    for node in file_nodes:
        fan_out = len(outgoing.get(node.path, []))
        fan_in = len(incoming.get(node.path, []))
        in_cycle = node.path in cycle_members
        cycle_bonus = 5.0 if in_cycle else 0.0
        mi_penalty = max(0.0, (60.0 - node.mi) / 10.0)
        score = round(
            node.avg_complexity
            + (node.max_complexity * 0.5)
            + fan_in
            + fan_out
            + cycle_bonus
            + mi_penalty,
            2,
        )

        reasons: List[str] = []
        if node.avg_complexity > 0:
            reasons.append(f"avg_complexity={node.avg_complexity}")
        if node.max_complexity > 0:
            reasons.append(f"max_complexity={node.max_complexity}")
        if fan_in > 0:
            reasons.append(f"fan_in={fan_in}")
        if fan_out > 0:
            reasons.append(f"fan_out={fan_out}")
        if in_cycle:
            reasons.append("in_cycle")
        if node.mi < 60:
            reasons.append(f"mi={node.mi}")

        hotspots.append(
            ArchitectureHotspot(
                path=node.path,
                score=score,
                avg_complexity=node.avg_complexity,
                max_complexity=node.max_complexity,
                fan_in=fan_in,
                fan_out=fan_out,
                in_cycle=in_cycle,
                reasons=reasons,
            )
        )

    hotspots.sort(key=lambda hotspot: (-hotspot.score, hotspot.path))
    return hotspots


def _build_dependency_list(
    edges: Dict[Tuple[str, str], Set[str]],
) -> List[FileDependency]:
    """Convert raw edge dict to a sorted list of FileDependency objects.

    Merges all import names for each (source, target) pair into a single
    FileDependency with sorted import_names.

    Args:
        edges: Dict mapping (source_file, target_file) → set of import names

    Returns:
        Sorted list of FileDependency objects
    """
    dependencies: List[FileDependency] = []
    for (source, target), names in sorted(edges.items()):
        dependencies.append(
            FileDependency(
                source=source,
                target=target,
                import_names=sorted(names),
            )
        )
    return dependencies


def _detect_circular_pairs(
    edges: Dict[Tuple[str, str], Set[str]],
) -> List[List[str]]:
    """Detect circular dependencies (A→B and B→A) in the edge set.

    Args:
        edges: Dict mapping (source_file, target_file) → set of import names

    Returns:
        List of [file_a, file_b] pairs (sorted) where both directions exist
    """
    circular_dependencies: List[List[str]] = []
    seen_pairs: Set[Tuple[str, str]] = set()
    edge_keys = set(edges.keys())

    for component in _find_dependency_cycles(edges):
        if len(component) < 2:
            continue
        for idx, source in enumerate(component):
            for target in component[idx + 1:]:
                if (source, target) in edge_keys and (target, source) in edge_keys:
                    pair = (source, target)
                    if pair not in seen_pairs:
                        seen_pairs.add(pair)
                        circular_dependencies.append(list(pair))

    circular_dependencies.sort()
    return circular_dependencies


def _collect_python_file_deps(
    py_files: List[str],
    top_packages: Set[str],
    module_to_file: Dict[str, str],
    file_set: Set[str],
    edges: Dict[Tuple[str, str], Set[str]],
    content_reader=None,
) -> None:
    """Collect file-level dependencies from Python files using AST."""
    if content_reader is None:
        content_reader = lambda fpath: Path(fpath).read_text(encoding="utf-8")
    for fpath in py_files:
        try:
            content = content_reader(fpath)
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
    content_reader=None,
) -> None:
    """Collect file-level dependencies from JS files using regex.

    Only relative imports (starting with './' or '../') are processed.
    Bare specifiers like 'lit' or 'd3' are external and skipped.
    """
    if content_reader is None:
        content_reader = lambda fpath: Path(fpath).read_text(encoding="utf-8")
    for fpath in js_files:
        try:
            content = content_reader(fpath)
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
