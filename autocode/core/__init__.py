"""
Core functionality for autocode.

Submodules:
- core.ai       — AI pipelines (DSPy, streaming)
- core.code     — Code analysis, metrics, architecture, health
- core.planning — Commit plan CRUD, workflow, execution
- core.vcs      — Git operations, status, log, tree
- core.utils    — Shared utilities
"""

from autocode.core import ai, code, planning, vcs, utils

__all__ = ["ai", "code", "planning", "vcs", "utils"]
