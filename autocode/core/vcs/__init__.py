"""
VCS Module - Operaciones y utilidades de control de versiones para Autocode.

Este módulo proporciona:
- GitOperations: Wrapper para operaciones Git usando GitPython
- Modelos Pydantic para estructuras de datos Git
- Función get_git_tree() para obtener la estructura del repositorio
- Función get_git_status() para obtener el estado actual del repositorio
"""

from autocode.core.vcs.operations import GitOperations
from autocode.core.vcs.models import GitNodeEntry, GitTreeGraph, GitTreeOutput
from autocode.core.vcs.tree import get_git_tree
from autocode.core.vcs.status import (
    get_git_status,
    GitFileStatus,
    GitStatusResult,
    GitStatusOutput,
)

__all__ = [
    # Operations
    "GitOperations",
    # Models - Tree
    "GitNodeEntry",
    "GitTreeGraph", 
    "GitTreeOutput",
    # Models - Status
    "GitFileStatus",
    "GitStatusResult",
    "GitStatusOutput",
    # Functions
    "get_git_tree",
    "get_git_status",
]
