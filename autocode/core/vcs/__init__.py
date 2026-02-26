"""
VCS Module - Operaciones y utilidades de control de versiones para Autocode.

Este módulo proporciona:
- GitOperations: Wrapper para operaciones Git usando GitPython
- Modelos Pydantic para estructuras de datos Git
- Función get_git_tree() para obtener la estructura del repositorio
- Función get_git_status() para obtener el estado actual del repositorio
- Función get_git_log() para obtener el historial de commits como grafo
- Función get_commit_detail() para obtener detalle de un commit
"""

from autocode.core.vcs.operations import GitOperations
from autocode.core.vcs.models import (
    # Tree models
    GitNodeEntry,
    GitTreeGraph,
    GitTreeOutput,
    # Log/Graph models
    GitCommit,
    GitBranch,
    GitLogGraph,
    GitLogOutput,
    GitFileChange,
    GitCommitDetail,
    GitCommitDetailOutput,
)
from autocode.core.vcs.tree import get_git_tree
from autocode.core.vcs.status import (
    get_git_status,
    GitFileStatus,
    GitStatusResult,
    GitStatusOutput,
)
from autocode.core.vcs.log import get_git_log, get_commit_detail

__all__ = [
    # Operations
    "GitOperations",
    # Models - Tree
    "GitNodeEntry",
    "GitTreeGraph",
    "GitTreeOutput",
    # Models - Log/Graph
    "GitCommit",
    "GitBranch",
    "GitLogGraph",
    "GitLogOutput",
    "GitFileChange",
    "GitCommitDetail",
    "GitCommitDetailOutput",
    # Models - Status
    "GitFileStatus",
    "GitStatusResult",
    "GitStatusOutput",
    # Functions
    "get_git_tree",
    "get_git_status",
    "get_git_log",
    "get_commit_detail",
]
