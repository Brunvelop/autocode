"""
Git Tree - Función para obtener la estructura del repositorio.

Este módulo proporciona una función registrada que permite
consultar la estructura de archivos del repositorio git.
"""
import subprocess
import logging

from autocode.interfaces.registry import register_function
from autocode.core.vcs.models import GitNodeEntry, GitTreeGraph, GitTreeOutput

logger = logging.getLogger(__name__)


@register_function(http_methods=["GET"])
def get_git_tree() -> GitTreeOutput:
    """
    Obtiene la estructura del proyecto desde el índice git incluyendo tamaños de archivo.
    
    Returns:
        GitTreeOutput conteniendo la estructura del árbol de archivos.
    """
    try:
        # Obtener todos los archivos trackeados por git
        # -r: recursive (listar archivos en subdirectorios)
        # -l: long format (incluye tamaño de archivo)
        # HEAD: referencia al commit actual
        cmd = ["git", "ls-tree", "-r", "-l", "HEAD"]
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True
        )
        
        lines = result.stdout.strip().split('\n')
        lines = [line for line in lines if line]  # Filtrar strings vacíos
        
        # Construir grafo no-recursivo (adjacency list) para evitar schemas recursivos en OpenAPI.
        # Usamos id=path. Root es el path vacío "".
        root_id = ""
        nodes_by_id = {
            root_id: GitNodeEntry(
                id=root_id,
                parent_id=None,
                name="root",
                path=root_id,
                type="directory",
                size=0,
            )
        }

        def ensure_dir(path: str) -> None:
            """Asegura que exista un nodo directorio para el path dado."""
            if path in nodes_by_id:
                return
            parent = path.rsplit("/", 1)[0] if "/" in path else root_id
            name = path.rsplit("/", 1)[-1] if path else "root"
            nodes_by_id[path] = GitNodeEntry(
                id=path,
                parent_id=parent if parent != path else root_id,
                name=name,
                path=path,
                type="directory",
                size=0,
            )
            # Asegurar que el padre también existe
            if parent != root_id:
                ensure_dir(parent)

        for line in lines:
            try:
                # Formato de output: "100644 blob <sha> <size_padded>\t<path>"
                # Separar por tab para separar metadata de path (maneja espacios en path)
                if "\t" in line:
                    metadata, file_path = line.split("\t", 1)
                else:
                    parts = line.split()
                    file_path = parts[-1]
                    metadata = " ".join(parts[:-1])

                meta_parts = metadata.split()
                size_str = meta_parts[3] if len(meta_parts) > 3 else "0"
                size = int(size_str) if size_str.isdigit() else 0

                # Asegurar que existan todos los segmentos de directorio
                if "/" in file_path:
                    dir_path = file_path.rsplit("/", 1)[0]
                    ensure_dir(dir_path)
                    parent_id = dir_path
                else:
                    parent_id = root_id

                # Agregar nodo de archivo
                nodes_by_id[file_path] = GitNodeEntry(
                    id=file_path,
                    parent_id=parent_id,
                    name=file_path.rsplit("/", 1)[-1],
                    path=file_path,
                    type="file",
                    size=size,
                )
            except Exception as loop_e:
                logger.warning(f"Error parseando línea '{line}': {loop_e}")
                continue

        graph = GitTreeGraph(
            root_id=root_id,
            nodes=list(nodes_by_id.values()),
        )

        return GitTreeOutput(
            success=True,
            result=graph,
            message="Git tree retrieved successfully"
        )
        
    except subprocess.CalledProcessError as e:
        error_msg = f"Git error: {e.stderr.strip() if e.stderr else str(e)}"
        logger.error(error_msg)
        return GitTreeOutput(
            success=False,
            result=None,
            message=error_msg
        )
    except Exception as e:
        error_msg = f"Unexpected error retrieving git tree: {str(e)}"
        logger.error(error_msg)
        return GitTreeOutput(
            success=False,
            result=None,
            message=error_msg
        )
