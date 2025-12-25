"""
Git Operations - Wrapper para operaciones Git usando GitPython.

Este módulo proporciona una API pythónica para operaciones git comunes,
usando GitPython donde sea posible y subprocess para casos edge.
"""
import subprocess
import logging
from typing import List, Optional

from git import Repo
from git.exc import GitCommandError

logger = logging.getLogger(__name__)


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
    
    # ========================================================================
    # STATUS & INFO
    # ========================================================================
    
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
            content = self.repo.git.show(f"{branch}:{file_path}")
            return content
        except Exception as e:
            logger.debug(f"No se pudo leer {file_path} de {branch}: {e}")
            return None
    
    # ========================================================================
    # BRANCH OPERATIONS
    # ========================================================================
    
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
    
    # ========================================================================
    # COMMIT OPERATIONS
    # ========================================================================
    
    def add_paths(self, paths: List[str]) -> None:
        """Agrega archivos/directorios al staging area."""
        try:
            self.repo.index.add(paths)
            logger.debug(f"Agregados al staging: {paths}")
        except Exception as e:
            logger.error(f"Error agregando paths: {e}")
            raise GitCommandError("Error en git add", 128) from e
    
    def stage_all(self) -> None:
        """Agrega todos los cambios (incluyendo untracked) al staging."""
        try:
            self.repo.git.add(A=True)
            logger.debug("Todos los cambios agregados al staging")
        except Exception as e:
            logger.error(f"Error en git add -A: {e}")
            raise GitCommandError("Error agregando todos los cambios", 128) from e

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
    
    # ========================================================================
    # MERGE OPERATIONS
    # ========================================================================
    
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
