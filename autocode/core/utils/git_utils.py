"""
Utilities for interacting with Git.
"""
import subprocess
import logging
from typing import List, Literal, Optional
from pathlib import Path
from pydantic import BaseModel, Field
from git import Repo
from git.exc import GitCommandError

from autocode.interfaces.registry import register_function
from autocode.interfaces.models import GenericOutput

logger = logging.getLogger(__name__)


# ============================================================================
# GIT OPERATIONS CLASS (GitPython-based)
# ============================================================================

class GitOperations:
    """
    Wrapper para operaciones Git usando GitPython.
    
    Proporciona una API pythónica para operaciones git comunes,
    usando GitPython donde sea posible y subprocess para casos edge.
    """
    
    def __init__(self, repo_path: str = "."):
        """
        Inicializa el wrapper con un repositorio.
        
        Args:
            repo_path: Ruta al repositorio git (default: directorio actual)
            
        Raises:
            GitCommandError: Si la ruta no es un repositorio git válido
        """
        try:
            self.repo = Repo(repo_path)
        except Exception as e:
            raise GitCommandError(f"No es un repositorio git válido: {repo_path}", 128) from e
    
    # ============== Status & Info ==============
    
    def is_repo_clean(self, untracked: bool = True) -> bool:
        """Verifica si el working directory está limpio."""
        return not self.repo.is_dirty(untracked_files=untracked)
    
    def get_current_branch(self) -> str:
        """Obtiene el nombre de la branch actual."""
        try:
            return self.repo.active_branch.name
        except TypeError:
            # HEAD detached
            return self.repo.head.commit.hexsha[:7]

    def list_branches(self, pattern: Optional[str] = None) -> List[str]:
        """
        Lista ramas locales, opcionalmente filtrando por patrón.
        
        Args:
            pattern: Patrón opcional (ej: "ai/*") - filtrado simple de startswith
            
        Returns:
            Lista de nombres de ramas
        """
        branches = [head.name for head in self.repo.heads]
        if pattern:
            # Simple wildmatch substitution
            prefix = pattern.replace("*", "")
            branches = [b for b in branches if b.startswith(prefix)]
        return branches

    def get_file_content_from_branch(self, branch: str, file_path: str) -> Optional[str]:
        """
        Lee el contenido de un archivo en otra rama sin hacer checkout.
        
        Args:
            branch: Nombre de la rama
            file_path: Ruta del archivo
            
        Returns:
            Contenido del archivo como string, o None si no existe/error
        """
        try:
            # Usar git show branch:path
            # Nota: repo.git.show devuelve string
            content = self.repo.git.show(f"{branch}:{file_path}")
            return content
        except Exception as e:
            logger.debug(f"No se pudo leer {file_path} de {branch}: {e}")
            return None
    
    # ============== Branch Operations ==============
    
    def create_and_checkout_branch(
        self, 
        branch_name: str, 
        base_branch: str = "main"
    ) -> None:
        """Crea una nueva branch desde base_branch y hace checkout."""
        try:
            base = self.repo.heads[base_branch]
            new_branch = self.repo.create_head(branch_name, base)
            new_branch.checkout()
            logger.info(f"Branch '{branch_name}' creada y checkout desde '{base_branch}'")
        except Exception as e:
            logger.error(f"Error creando branch '{branch_name}': {e}")
            raise GitCommandError(f"No se pudo crear branch '{branch_name}'", 128) from e
    
    def checkout_branch(self, branch_name: str) -> None:
        """Hace checkout a una branch existente."""
        try:
            self.repo.heads[branch_name].checkout()
            logger.info(f"Checkout a branch '{branch_name}'")
        except Exception as e:
            logger.error(f"Error en checkout a '{branch_name}': {e}")
            raise GitCommandError(f"Branch '{branch_name}' no encontrada", 128) from e
    
    def delete_branch(self, branch_name: str, force: bool = False) -> None:
        """Elimina una branch."""
        try:
            self.repo.delete_head(branch_name, force=force)
            logger.info(f"Branch '{branch_name}' eliminada")
        except Exception as e:
            logger.error(f"Error eliminando branch '{branch_name}': {e}")
            raise GitCommandError(f"No se pudo eliminar branch '{branch_name}'", 128) from e
    
    # ============== Commit Operations ==============
    
    def add_paths(self, paths: List[str]) -> None:
        """Agrega archivos/directorios al staging area."""
        try:
            self.repo.index.add(paths)
            logger.debug(f"Agregados al staging: {paths}")
        except Exception as e:
            logger.error(f"Error agregando paths: {e}")
            raise GitCommandError("Error en git add", 128) from e
    
    def commit(self, message: str) -> None:
        """Crea un commit con los cambios staged."""
        try:
            self.repo.index.commit(message)
            logger.info(f"Commit creado: {message}")
        except Exception as e:
            logger.error(f"Error en commit: {e}")
            raise GitCommandError("Error creando commit", 128) from e
    
    def add_and_commit(self, paths: List[str], message: str) -> None:
        """Add + commit en una operación atómica."""
        self.add_paths(paths)
        self.commit(message)
    
    # ============== Merge Operations ==============
    
    def merge_squash(
        self, 
        source_branch: str,
        target_branch: str,
        auto_commit: bool = False,
        commit_message: Optional[str] = None
    ) -> None:
        """Squash merge de source_branch a target_branch."""
        try:
            self.checkout_branch(target_branch)
            # GitPython no tiene soporte directo para --squash
            subprocess.run(
                ["git", "merge", "--squash", "--no-commit", source_branch],
                capture_output=True, text=True, check=True
            )
            logger.info(f"Squash merge de '{source_branch}' a '{target_branch}'")
            if auto_commit and commit_message:
                self.commit(commit_message)
        except subprocess.CalledProcessError as e:
            error_msg = e.stderr if e.stderr else str(e)
            logger.error(f"Error en squash merge: {error_msg}")
            raise GitCommandError(f"Squash merge falló: {error_msg}", 128) from e
    
    def reset_paths(self, paths: List[str], mode: str = "HEAD") -> None:
        """Reset paths del staging area y working directory."""
        try:
            for path in paths:
                subprocess.run(["git", "reset", mode, path], check=False, capture_output=True)
                subprocess.run(["git", "checkout", mode, path], check=False, capture_output=True)
            logger.debug(f"Paths reseteados: {paths}")
        except Exception as e:
            logger.warning(f"Error reseteando paths: {e}")


# ============================================================================
# REGISTERED FUNCTIONS
# ============================================================================

class GitNodeEntry(BaseModel):
    """Flat representation of a node in the git tree (non-recursive / adjacency list)."""

    id: str = Field(description="Stable node id (we use full path; root is empty string)")
    parent_id: Optional[str] = Field(default=None, description="Parent node id; None only for root")
    name: str = Field(description="Name of the file or directory")
    path: str = Field(description="Full path from repository root")
    type: Literal["file", "directory"] = Field(description="Type of the node")
    size: int = Field(default=0, description="Size in bytes (files only)")


class GitTreeGraph(BaseModel):
    """Non-recursive tree representation as a graph."""

    root_id: str = Field(description="Id of the root node")
    nodes: List[GitNodeEntry] = Field(default_factory=list, description="All nodes in the tree")


class GitTreeOutput(GenericOutput):
    """Specific output for git tree structure."""

    result: Optional[GitTreeGraph] = Field(default=None, description="Graph representation of the git tree")

@register_function(http_methods=["GET"])
def get_git_tree() -> GitTreeOutput:
    """
    Retrieves the project structure from git index including file sizes.
    
    Returns:
        GitTreeOutput containing the file tree structure.
    """
    try:
        # Get all files tracked by git
        # -r: recursive (list files in subdirectories)
        # -l: long format (includes file size)
        # HEAD: current commit reference
        cmd = ["git", "ls-tree", "-r", "-l", "HEAD"]
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True
        )
        
        lines = result.stdout.strip().split('\n')
        lines = [line for line in lines if line]  # Filter empty strings
        
        # Build a non-recursive graph (adjacency list) to avoid recursive schemas in OpenAPI.
        # We use id=path. Root is the empty path "".
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
            """Ensure a directory node exists for a given path."""
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
            # Ensure parent exists too
            if parent != root_id:
                ensure_dir(parent)

        for line in lines:
            try:
                # Output format: "100644 blob <sha> <size_padded>\t<path>"
                # Split by tab to separate metadata from path (handles spaces in path)
                if "\t" in line:
                    metadata, file_path = line.split("\t", 1)
                else:
                    parts = line.split()
                    file_path = parts[-1]
                    metadata = " ".join(parts[:-1])

                meta_parts = metadata.split()
                size_str = meta_parts[3] if len(meta_parts) > 3 else "0"
                size = int(size_str) if size_str.isdigit() else 0

                # Ensure all directory segments exist
                if "/" in file_path:
                    dir_path = file_path.rsplit("/", 1)[0]
                    ensure_dir(dir_path)
                    parent_id = dir_path
                else:
                    parent_id = root_id

                # Add file node
                nodes_by_id[file_path] = GitNodeEntry(
                    id=file_path,
                    parent_id=parent_id,
                    name=file_path.rsplit("/", 1)[-1],
                    path=file_path,
                    type="file",
                    size=size,
                )
            except Exception as loop_e:
                logger.warning(f"Error parsing line '{line}': {loop_e}")
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
