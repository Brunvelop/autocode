"""
Workflow module for AI-assisted development workflows.

Este módulo proporciona herramientas para gestionar workflows de desarrollo
asistidos por IA, incluyendo sesiones de trabajo aisladas con Git.
"""

from autocode.core.workflow.session import (
    start_ai_session,
    save_conversation,
    finalize_ai_session,
    abort_ai_session,
    get_current_session,
    list_ai_sessions,
    AISessionManager,
)

__all__ = [
    "start_ai_session",
    "save_conversation",
    "finalize_ai_session",
    "abort_ai_session",
    "get_current_session",
    "list_ai_sessions",
    "AISessionManager",
]
