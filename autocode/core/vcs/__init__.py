"""
VCS Module - Operaciones y utilidades de control de versiones para Autocode.

Este módulo proporciona:
- GitOperations: Wrapper para operaciones Git usando GitPython
- Modelos Pydantic para estructuras de datos Git
- Función get_git_tree() para obtener la estructura del repositorio
"""

from autocode.core.vcs.operations import GitOperations
from autocode.core.vcs.models import GitNodeEntry, GitTreeGraph, GitTreeOutput
from autocode.core.vcs.tree import get_git_tree

__all__ = [
    # Operations
    "GitOperations",
    # Models
    "GitNodeEntry",
    "GitTreeGraph", 
    "GitTreeOutput",
    # Functions
    "get_git_tree",
]
