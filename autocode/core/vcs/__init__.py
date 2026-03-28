"""
VCS Module - Operaciones y utilidades de control de versiones para Autocode.

Este módulo proporciona:
- GitOperations: Wrapper para operaciones Git usando GitPython
- Modelos Pydantic para estructuras de datos Git
- Función get_git_tree() para obtener la estructura del repositorio (API only)
- Función get_git_status() para obtener el estado actual del repositorio (API only)
- Función get_git_status_summary() para resumen compacto del status (MCP/LLM)
- Función get_git_log() para obtener el historial de commits como grafo (API only)
- Función get_git_log_summary() para resumen compacto del log (MCP/LLM)
- Función get_commit_detail() para obtener detalle de un commit
- ExecutionSandbox: Lifecycle manager para snapshot/collect/revert de cambios del agente
- async_rev_parse_head, async_diff_name_only, async_reset_mixed, async_reset_hard: primitivas async de git
"""

from autocode.core.vcs.operations import GitOperations
from autocode.core.vcs.models import (
    # Tree models
    GitNodeEntry,
    GitTreeGraph,
    # Status models
    FileStatus,
    GitFileStatus,
    GitStatusResult,
    GitStatusSummary,
    # Log/Graph models
    GitCommit,
    GitBranch,
    GitLogGraph,
    GitLogSummary,
    GitFileChange,
    GitCommitDetail,
)
from autocode.core.vcs.tree import get_git_tree
from autocode.core.vcs.status import (
    get_git_status,
    get_git_status_summary,
)
from autocode.core.vcs.log import get_git_log, get_git_log_summary, get_commit_detail
from autocode.core.vcs.git import git, git_checked, git_show, git_add_and_commit, get_tracked_files, get_tracked_files_at_commit
from autocode.core.vcs.execution import (
    ExecutionSandbox,
    async_rev_parse_head,
    async_diff_name_only,
    async_reset_mixed,
    async_reset_hard,
)

__all__ = [
    # Operations
    "GitOperations",
    # Models - Tree
    "GitNodeEntry",
    "GitTreeGraph",
    # Models - Status
    "GitStatusSummary",
    "GitFileStatus",
    "GitStatusResult",
    # Models - Log/Graph
    "GitCommit",
    "GitBranch",
    "GitLogGraph",
    "GitLogSummary",
    "GitFileChange",
    "GitCommitDetail",
    # Functions - API (full data for frontend)
    "get_git_tree",
    "get_git_status",
    "get_git_log",
    "get_commit_detail",
    # Functions - MCP/LLM (compact text summaries)
    "get_git_status_summary",
    "get_git_log_summary",
    # Git helpers (shared across modules)
    "git",
    "git_checked",
    "git_show",
    "git_add_and_commit",
    "get_tracked_files",
    "get_tracked_files_at_commit",
    # Execution sandbox & async git primitives
    "ExecutionSandbox",
    "async_rev_parse_head",
    "async_diff_name_only",
    "async_reset_mixed",
    "async_reset_hard",
]
