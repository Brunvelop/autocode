"""
structure.py
Función principal para obtener estructura de código.

Construye un grafo plano (adjacency list) para evitar recursión en OpenAPI schema.
Usa get_git_tree() para obtener solo archivos trackeados por git.
"""

from pathlib import Path
from typing import List, Optional, Dict

from autocode.interfaces.registry import register_function
from autocode.core.vcs import get_git_tree
from .models import CodeNode, CodeGraph, CodeStructureOutput, CodeStructureResult, CodeSummaryOutput


# Extensiones parseables
PARSEABLE_EXTENSIONS = {'.py', '.js', '.mjs', '.jsx'}


@register_function(http_methods=["GET"], interfaces=["api"])
def get_code_structure(
    path: str = ".",
    depth: int = -1,
    include_imports: bool = True
) -> CodeStructureOutput:
    """
    Obtiene la estructura del código en un directorio.
    
    Analiza archivos Python y JavaScript extrayendo clases, 
    funciones, métodos e imports de forma automática.
    Solo incluye archivos trackeados por git.
    
    Args:
        path: Path relativo al directorio a analizar (default: directorio actual)
        depth: Profundidad máxima de recursión (-1 para ilimitado)
        include_imports: Si incluir nodos de import en la estructura
        
    Returns:
        Estructura del código con métricas agregadas
    """
    try:
        # Obtener archivos trackeados por git
        git_tree_output = get_git_tree()
        
        if not git_tree_output.success or not git_tree_output.result:
            return CodeStructureOutput(
                success=False,
                message=f"Error obteniendo git tree: {git_tree_output.message}"
            )
        
        git_nodes = git_tree_output.result.nodes
        
        # Filtrar archivos parseables y dentro del path solicitado
        # Si path es ".", incluir todos los archivos; si no, filtrar por prefijo
        path_prefix = '' if path == '.' else path.rstrip('/\\')
        
        parseable_files = []
        for node in git_nodes:
            if node.type != 'file':
                continue
            
            # Verificar extensión
            file_path = Path(node.path)
            if file_path.suffix not in PARSEABLE_EXTENSIONS:
                continue
            
            # Verificar que está dentro del path solicitado (si no es root)
            if path_prefix and not node.path.startswith(path_prefix):
                continue
            
            parseable_files.append(node.path)
        
        # Construir estructura de directorios y archivos
        # Usar "." como root_id para evitar string vacío (falsy en JS)
        nodes: List[CodeNode] = []
        root_id = path  # Mantener "." como valor válido
        
        _build_tree_from_git_files(
            parseable_files, 
            root_id, 
            depth, 
            include_imports, 
            nodes
        )
        
        # Calcular métricas
        metrics = _calculate_metrics(nodes)
        
        graph = CodeGraph(
            root_id=root_id,
            nodes=nodes
        )
        
        result = CodeStructureResult(
            graph=graph,
            languages=list(metrics['languages']),
            total_files=metrics['files'],
            total_loc=metrics['loc'],
            total_functions=metrics['functions'],
            total_classes=metrics['classes']
        )
        
        return CodeStructureOutput(
            success=True,
            result=result,
            message=f"Estructura cargada: {metrics['files']} archivos, {metrics['loc']} LOC (solo git)"
        )
        
    except Exception as e:
        return CodeStructureOutput(
            success=False,
            message=f"Error analizando estructura: {str(e)}"
        )


@register_function(http_methods=["GET"], interfaces=["api", "mcp"])
def get_code_summary(
    path: str = ".",
    depth: int = -1,
) -> CodeSummaryOutput:
    """
    Obtiene un resumen compacto de la estructura del código en formato texto.
    
    Versión ligera de get_code_structure, optimizada para LLMs.
    Devuelve un árbol tipo 'tree' con nombres de archivos/directorios y
    métricas básicas (LOC, funciones, clases) sin datos detallados por nodo.
    
    Args:
        path: Path relativo al directorio a analizar (default: directorio actual)
        depth: Profundidad máxima de recursión (-1 para ilimitado)
        
    Returns:
        Resumen compacto en texto plano con estructura y métricas
    """
    try:
        # Reutilizar get_code_structure para obtener los nodos
        structure_output = get_code_structure(path=path, depth=depth, include_imports=False)
        
        if not structure_output.success or not structure_output.result:
            return CodeSummaryOutput(
                success=False,
                message=structure_output.message or "Error obteniendo estructura"
            )
        
        result = structure_output.result
        nodes = result.graph.nodes
        root_id = result.graph.root_id
        
        # Construir mapa de hijos por parent_id
        children_map: Dict[str, List[CodeNode]] = {}
        node_map: Dict[str, CodeNode] = {}
        for node in nodes:
            node_map[node.id] = node
            pid = node.parent_id
            if pid is not None:
                children_map.setdefault(pid, []).append(node)
        
        # Ordenar hijos: directorios primero, luego por nombre
        for pid in children_map:
            children_map[pid].sort(key=lambda n: (
                0 if n.type == "directory" else 1,
                n.name
            ))
        
        # Generar texto tipo tree
        lines: List[str] = []
        
        # Header con métricas globales
        root_name = path if path != "." else "project"
        lines.append(
            f"{root_name}/ ({result.total_files} files, "
            f"{result.total_loc} LOC, "
            f"{result.total_functions} functions, "
            f"{result.total_classes} classes, "
            f"languages: {', '.join(result.languages) or 'none'})"
        )
        
        # Renderizar árbol recursivamente
        _render_summary_tree(root_id, children_map, node_map, lines, prefix="")
        
        summary_text = "\n".join(lines)
        
        return CodeSummaryOutput(
            success=True,
            result=summary_text,
            message=f"Resumen: {result.total_files} archivos, {result.total_loc} LOC"
        )
        
    except Exception as e:
        return CodeSummaryOutput(
            success=False,
            message=f"Error generando resumen: {str(e)}"
        )


def _render_summary_tree(
    node_id: str,
    children_map: Dict[str, List[CodeNode]],
    node_map: Dict[str, CodeNode],
    lines: List[str],
    prefix: str
) -> None:
    """
    Renderiza recursivamente el árbol en formato texto compacto.
    
    Solo muestra directorios y archivos con sus métricas inline.
    Clases y funciones se resumen como conteos por archivo.
    """
    children = children_map.get(node_id, [])
    
    # Separar hijos directos: dirs y archivos (ignorar clases/funciones/métodos sueltos)
    visible_children = [c for c in children if c.type in ("directory", "file")]
    
    for i, child in enumerate(visible_children):
        is_last = (i == len(visible_children) - 1)
        connector = "└── " if is_last else "├── "
        extension = "    " if is_last else "│   "
        
        if child.type == "directory":
            # Contar métricas del directorio
            dir_info = f"{child.name}/ ({child.loc} LOC)"
            lines.append(f"{prefix}{connector}{dir_info}")
            _render_summary_tree(child.id, children_map, node_map, lines, prefix + extension)
        
        elif child.type == "file":
            # Contar clases y funciones/métodos dentro del archivo
            file_children = children_map.get(child.id, [])
            n_classes = sum(1 for c in file_children if c.type == "class")
            n_funcs = sum(1 for c in file_children if c.type in ("function", "method"))
            # Contar métodos dentro de clases de este archivo
            for fc in file_children:
                if fc.type == "class":
                    class_children = children_map.get(fc.id, [])
                    n_funcs += sum(1 for cc in class_children if cc.type == "method")
            
            # Formato compacto: nombre - LOC, conteos
            parts = [f"{child.loc} LOC"]
            if n_classes:
                parts.append(f"{n_classes}c")
            if n_funcs:
                parts.append(f"{n_funcs}f")
            
            file_info = f"{child.name} ({', '.join(parts)})"
            lines.append(f"{prefix}{connector}{file_info}")


def _build_tree_from_git_files(
    file_paths: List[str],
    root_id: str,
    depth: int,
    include_imports: bool,
    nodes: List[CodeNode]
) -> None:
    """
    Construye el árbol de nodos a partir de una lista de paths de archivos git.
    
    Args:
        file_paths: Lista de paths de archivos (desde git)
        root_id: ID del nodo raíz ("." para root del proyecto)
        depth: Profundidad máxima (-1 para ilimitado)
        include_imports: Si incluir nodos de import
        nodes: Lista de nodos a poblar (se modifica in-place)
    """
    # Determinar si es el root del proyecto
    is_project_root = root_id == '.'
    
    # Crear nodo raíz
    root_name = 'root' if is_project_root else Path(root_id).name
    root_node = CodeNode(
        id=root_id,
        parent_id=None,
        name=root_name,
        type="directory",
        path=root_id,
        loc=0
    )
    nodes.append(root_node)
    
    # Track de directorios creados para evitar duplicados
    created_dirs: Dict[str, CodeNode] = {root_id: root_node}
    
    # Procesar cada archivo
    for file_path in file_paths:
        # Calcular path relativo al root
        if is_project_root:
            # Para root del proyecto, el relative_path es el file_path completo
            relative_path = file_path
        elif file_path.startswith(root_id):
            relative_path = file_path[len(root_id):].lstrip('/\\')
        else:
            # Archivo no está dentro del root solicitado
            continue
        
        # Verificar profundidad
        if depth != -1:
            path_depth = relative_path.count('/') + relative_path.count('\\')
            if path_depth > depth:
                continue
        
        # Crear directorios intermedios
        parts = relative_path.replace('\\', '/').split('/')
        current_path = root_id
        
        for i, part in enumerate(parts[:-1]):  # Todos menos el último (el archivo)
            # Construir dir_path correctamente
            # Para root del proyecto, no usar "./" como prefijo
            if is_project_root and current_path == '.':
                dir_path = part
            elif current_path and current_path != '.':
                dir_path = f"{current_path}/{part}"
            else:
                dir_path = part
            
            if dir_path not in created_dirs:
                parent_id = current_path if current_path in created_dirs else root_id
                dir_node = CodeNode(
                    id=dir_path,
                    parent_id=parent_id,
                    name=part,
                    type="directory",
                    path=dir_path,
                    loc=0
                )
                nodes.append(dir_node)
                created_dirs[dir_path] = dir_node
            
            current_path = dir_path
        
        # Agregar nodos del archivo
        parent_id = current_path if current_path in created_dirs else root_id
        file_loc = _add_file_nodes(Path(file_path), include_imports, nodes, parent_id)
        
        # Actualizar LOC de directorios padres
        _update_parent_loc(created_dirs, parent_id, file_loc, root_id)


def _update_parent_loc(
    created_dirs: Dict[str, CodeNode],
    current_id: str,
    loc: int,
    root_id: str
) -> None:
    """
    Actualiza el LOC de los directorios padres recursivamente.
    
    Args:
        created_dirs: Diccionario de directorios creados
        current_id: ID del directorio actual
        loc: LOC a agregar
        root_id: ID del nodo raíz
    """
    while current_id in created_dirs:
        created_dirs[current_id].loc += loc
        if current_id == root_id:
            break
        # Subir al padre
        parent = created_dirs[current_id].parent_id
        if parent is None:
            break
        current_id = parent


def _add_file_nodes(
    path: Path, 
    include_imports: bool, 
    nodes: List[CodeNode],
    parent_id: Optional[str]
) -> int:
    """
    Agrega nodos para un archivo y su contenido.
    
    Args:
        path: Path al archivo
        include_imports: Si incluir imports
        nodes: Lista de nodos a poblar
        parent_id: ID del nodo padre
        
    Returns:
        LOC del archivo
    """
    from .parsers import get_parser
    
    path_str = str(path)
    parser = get_parser(path.suffix)
    
    if parser:
        # Usar parser para obtener estructura
        file_nodes = parser.parse_flat(path_str)
        
        if file_nodes:
            file_node = file_nodes[0]  # El primero es el archivo
            file_node.parent_id = parent_id
            
            # Filtrar imports si no se quieren
            if not include_imports:
                file_nodes = [n for n in file_nodes if n.type != "import"]
            
            nodes.extend(file_nodes)
            return file_node.loc
    
    # Sin parser o error, agregar nodo básico
    try:
        content = path.read_text(encoding='utf-8')
        loc = sum(1 for line in content.split('\n') if line.strip())
    except:
        loc = 0
    
    file_node = CodeNode(
        id=path_str,
        parent_id=parent_id,
        name=path.name,
        type="file",
        path=path_str,
        loc=loc
    )
    nodes.append(file_node)
    
    return loc


def _calculate_metrics(nodes: List[CodeNode]) -> dict:
    """
    Calcula métricas a partir de la lista plana de nodos.
    
    Args:
        nodes: Lista de todos los nodos
        
    Returns:
        Dict con métricas
    """
    metrics = {
        'languages': set(),
        'files': 0,
        'loc': 0,
        'functions': 0,
        'classes': 0
    }
    
    for node in nodes:
        if node.type == "file":
            metrics['files'] += 1
            metrics['loc'] += node.loc
            if node.language:
                metrics['languages'].add(node.language)
        
        elif node.type in ("function", "method"):
            metrics['functions'] += 1
        
        elif node.type == "class":
            metrics['classes'] += 1
    
    return metrics
