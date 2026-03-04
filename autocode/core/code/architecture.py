"""
architecture.py
Motor de análisis de arquitectura de código y endpoint registrado.

Proporciona:
- Snapshot de arquitectura: jerarquía de directorios/archivos con métricas de calidad
- Propagación bottom-up de MI/CC desde archivos a directorios (ponderada por LOC)
- Endpoint registrado para el frontend (treemap + grafo de dependencias)

Reutiliza funciones de metrics.py: _analyze_content, _get_tracked_py_files, _git
"""

import logging
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional

from autocode.interfaces.registry import register_function
from autocode.core.code.models import (
    ArchitectureNode,
    ArchitectureSnapshot,
    ArchitectureSnapshotOutput,
)
from autocode.core.code.metrics import (
    _analyze_content,
    _get_tracked_py_files,
    _git,
)

logger = logging.getLogger(__name__)


# ==============================================================================
# REGISTERED ENDPOINTS
# ==============================================================================


@register_function(http_methods=["GET"], interfaces=["api"])
def get_architecture_snapshot(path: str = ".") -> ArchitectureSnapshotOutput:
    """
    Obtiene un snapshot de la arquitectura del proyecto con métricas por nodo.

    Analiza todos los archivos .py trackeados por git, construye una jerarquía
    de directorios/archivos, calcula métricas de calidad (MI, CC, LOC) por archivo
    y las propaga hacia arriba a los directorios padres como promedios ponderados
    por líneas de código fuente (SLOC).

    Args:
        path: Path relativo al directorio a analizar (default: directorio actual)
    """
    try:
        # Git metadata
        commit_hash = _git("rev-parse", "HEAD")
        commit_short = _git("rev-parse", "--short", "HEAD")
        branch = _git("rev-parse", "--abbrev-ref", "HEAD")

        # Get tracked .py files
        py_files = _get_tracked_py_files()

        # Build hierarchy with per-file metrics
        nodes = _build_architecture_nodes(py_files)

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
            fm = _analyze_content(content, fpath)
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
