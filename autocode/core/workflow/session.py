"""
AI Session Management - Git-based workflow tracking

Este módulo proporciona funciones para gestionar sesiones de trabajo con IA
usando branches de Git para aislar contexto y código.
"""
import logging
import json
from datetime import datetime
from typing import Literal, List, Dict, Any, Optional
from pathlib import Path

from git.exc import GitCommandError

from autocode.interfaces.registry import register_function
from autocode.interfaces.models import GenericOutput
from autocode.core.vcs import GitOperations

logger = logging.getLogger(__name__)

# Constante configurable para el directorio de contexto
CONTEXT_DIR_NAME = ".ai-context"

SessionType = Literal["session", "docs", "tests", "review"]
VALID_SESSION_TYPES = ["session", "docs", "tests", "review"]


# ============================================================================
# AI SESSION MANAGER CLASS
# ============================================================================

class AISessionManager:
    """
    Gestiona sesiones AI usando ramas de Git.
    """
    
    def __init__(self, context_dir: str = CONTEXT_DIR_NAME):
        self.git = GitOperations()
        self.context_dir = Path(context_dir)
    
    def start_session(
        self,
        description: str,
        base_branch: str = "main",
        session_type: SessionType = "session"
    ) -> Dict[str, Any]:
        """
        Inicia sesión creando una rama.
        """
        # Validar session_type
        if session_type not in VALID_SESSION_TYPES:
            raise ValueError(f"session_type debe ser uno de: {VALID_SESSION_TYPES}")
        
        if not self.git.is_repo_clean():
            raise ValueError("Working directory tiene cambios sin commit. Commit o stash primero.")
        
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        branch_name = f"ai/{session_type}-{timestamp}"
        
        self.git.create_and_checkout_branch(branch_name, base_branch)
        
        session_data = {
            "session_id": timestamp,
            "description": description,
            "base_branch": base_branch,
            "session_type": session_type,
            "started_at": datetime.now().isoformat(),
            "status": "in_progress",
            "branch": branch_name
        }
        
        self._save_json("session.json", session_data)
        self.git.add_and_commit([str(self.context_dir)], f"AI: Start {session_type} - {description}")
        
        logger.info(f"Sesión iniciada: {branch_name}")
        return session_data

    def save_conversation_to_session(
        self,
        messages: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Guarda conversación en la sesión actual.
        """
        current_branch = self.git.get_current_branch()
        if not current_branch.startswith("ai/"):
            raise ValueError("No estás en una sesión AI (branch debe empezar con 'ai/')")
            
        data = {
            "messages": messages,
            "last_updated": datetime.now().isoformat(),
            "message_count": len(messages)
        }
        
        self._save_json("conversation.json", data)
        self.git.add_and_commit([str(self.context_dir)], f"AI: Update conversation ({len(messages)} msgs)")
        
        logger.info(f"Conversación guardada: {len(messages)} mensajes")
        return {"message_count": len(messages), "branch": current_branch}

    def finalize_session(
        self,
        commit_message: str,
        merge_to: str = "main",
        keep_branch: bool = True
    ) -> Dict[str, Any]:
        """
        Finaliza sesión y hace squash merge a main.
        
        Incluye rollback automático si falla durante el proceso.
        """
        current_branch = self.git.get_current_branch()
        if not current_branch.startswith("ai/"):
            raise ValueError("No estás en una sesión AI")
        
        session_data = self._load_json("session.json") or {}
        
        try:
            # 1. Marcar como completada en la rama de sesión
            session_data["status"] = "completed"
            session_data["completed_at"] = datetime.now().isoformat()
            self._save_json("session.json", session_data)
            
            self.git.add_and_commit([str(self.context_dir)], "AI: Mark session as completed")
            
            # 2. Merge a rama destino
            self.git.merge_squash(current_branch, merge_to, auto_commit=False)
            
            # 3. Limpiar contexto del staging de main
            # (Para que el código vaya limpio a main sin la carpeta .ai-context)
            self.git.reset_paths([str(self.context_dir)])
            
            # 4. Commit final en main
            self.git.commit(commit_message)
            
        except Exception as e:
            # Rollback: volver a la rama de sesión original
            logger.error(f"Error en finalize_session, haciendo rollback: {e}")
            try:
                self.git.checkout_branch(current_branch)
            except Exception as rollback_error:
                logger.error(f"Error durante rollback: {rollback_error}")
            raise
        
        if not keep_branch:
            self.git.delete_branch(current_branch, force=True)
            
        logger.info(f"Sesión finalizada y mergeada a {merge_to}")
        
        return {
            "session_id": session_data.get("session_id"),
            "branch": current_branch,
            "merged_to": merge_to,
            "branch_kept": keep_branch
        }

    def abort_session(self, delete_branch: bool = True) -> Dict[str, Any]:
        """
        Cancela la sesión actual sin mergear.
        
        Args:
            delete_branch: Si True, elimina la rama de sesión
            
        Returns:
            Dict con info de la sesión abortada
        """
        current_branch = self.git.get_current_branch()
        if not current_branch.startswith("ai/"):
            raise ValueError("No estás en una sesión AI")
        
        session_data = self._load_json("session.json") or {}
        base_branch = session_data.get("base_branch", "main")
        
        # Volver a la rama base
        self.git.checkout_branch(base_branch)
        
        if delete_branch:
            self.git.delete_branch(current_branch, force=True)
            logger.info(f"Sesión abortada y rama {current_branch} eliminada")
        else:
            logger.info(f"Sesión abortada, rama {current_branch} conservada")
        
        return {
            "aborted": current_branch,
            "returned_to": base_branch,
            "branch_deleted": delete_branch,
            "session_id": session_data.get("session_id")
        }

    def get_current_session(self) -> Optional[Dict[str, Any]]:
        """Obtiene metadata de la sesión actual."""
        try:
            branch = self.git.get_current_branch()
            if not branch.startswith("ai/"):
                return None
            return self._load_json("session.json")
        except Exception as e:
            logger.error(f"Error obteniendo sesión actual: {e}")
            return None

    def list_sessions(self) -> List[Dict[str, Any]]:
        """
        Lista todas las sesiones activas buscando ramas ai/*.
        Lee el session.json de cada rama para obtener detalles.
        """
        branches = self.git.list_branches("ai/*")
        sessions = []
        
        # Usar la constante para el path del session.json
        session_file_path = f"{CONTEXT_DIR_NAME}/session.json"
        
        for branch in branches:
            # Intentar leer session.json de esa rama sin checkout
            content = self.git.get_file_content_from_branch(branch, session_file_path)
            
            if content:
                try:
                    data = json.loads(content)
                    data["branch"] = branch 
                    sessions.append(data)
                except json.JSONDecodeError as e:
                    # JSON corrupto o inválido
                    logger.warning(f"Error parsing session.json en {branch}: {e}")
                    sessions.append(self._create_fallback_session(branch))
            else:
                # Si no hay session.json, creamos una entrada básica
                sessions.append(self._create_fallback_session(branch))
        
        # Ordenar por fecha (más reciente primero)
        sessions.sort(key=lambda x: x.get("started_at", ""), reverse=True)
        return sessions

    # Helpers
    def _save_json(self, filename: str, data: Dict[str, Any]):
        self.context_dir.mkdir(exist_ok=True)
        (self.context_dir / filename).write_text(json.dumps(data, indent=2))

    def _load_json(self, filename: str) -> Optional[Dict[str, Any]]:
        path = self.context_dir / filename
        if not path.exists():
            return None
        try:
            return json.loads(path.read_text())
        except (json.JSONDecodeError, IOError) as e:
            logger.warning(f"Error loading {filename}: {e}")
            return None

    def _create_fallback_session(self, branch: str) -> Dict[str, Any]:
        return {
            "session_id": branch.split("-")[-1] if "-" in branch else "unknown",
            "branch": branch,
            "description": f"Session {branch}",
            "started_at": "",
            "status": "unknown"
        }


# ============================================================================
# REGISTERED FUNCTIONS (API/CLI/MCP endpoints)
# ============================================================================

@register_function(http_methods=["POST"])
def start_ai_session(
    description: str,
    base_branch: str = "main",
    session_type: SessionType = "session"
) -> GenericOutput:
    """
    Inicia una nueva sesión AI creando una rama.
    
    Args:
        description: Descripción breve de la sesión
        base_branch: Branch base desde donde crear (default: main)
        session_type: Tipo de workflow (session, docs, tests, review)
    """
    try:
        manager = AISessionManager()
        result = manager.start_session(description, base_branch, session_type)
        return GenericOutput(success=True, result=result, message=f"Sesión iniciada: {result['branch']}")
    except Exception as e:
        return GenericOutput(success=False, result={}, message=str(e))

@register_function(http_methods=["POST"])
def save_conversation(
    messages: List[Dict[str, Any]]
) -> GenericOutput:
    """
    Guarda el historial de conversación.
    """
    try:
        manager = AISessionManager()
        result = manager.save_conversation_to_session(messages)
        return GenericOutput(success=True, result=result, message=f"Conversación guardada ({result['message_count']} msgs)")
    except Exception as e:
        return GenericOutput(success=False, result={}, message=str(e))

@register_function(http_methods=["POST"])
def finalize_ai_session(
    commit_message: str,
    merge_to: str = "main",
    keep_branch: bool = True
) -> GenericOutput:
    """
    Finaliza sesión y mergea cambios a main.
    """
    try:
        manager = AISessionManager()
        result = manager.finalize_session(commit_message, merge_to, keep_branch)
        return GenericOutput(success=True, result=result, message=f"Sesión finalizada y mergeada a {merge_to}")
    except Exception as e:
        return GenericOutput(success=False, result={}, message=str(e))

@register_function(http_methods=["GET"])
def get_current_session() -> GenericOutput:
    """Obtiene info de la sesión actual."""
    try:
        manager = AISessionManager()
        result = manager.get_current_session()
        if result:
            return GenericOutput(success=True, result=result, message="Sesión activa encontrada")
        return GenericOutput(success=True, result=None, message="No hay sesión activa")
    except Exception as e:
        return GenericOutput(success=False, result=None, message=str(e))

@register_function(http_methods=["GET"])
def list_ai_sessions() -> GenericOutput:
    """Lista sesiones activas (ramas)."""
    try:
        manager = AISessionManager()
        sessions = manager.list_sessions()
        return GenericOutput(success=True, result={"sessions": sessions}, message=f"{len(sessions)} sesiones encontradas")
    except Exception as e:
        return GenericOutput(success=False, result={"sessions": []}, message=str(e))

@register_function(http_methods=["POST"])
def abort_ai_session(
    delete_branch: bool = True
) -> GenericOutput:
    """
    Cancela la sesión actual sin mergear.
    
    Args:
        delete_branch: Si True, elimina la rama de sesión (default: True)
    """
    try:
        manager = AISessionManager()
        result = manager.abort_session(delete_branch)
        return GenericOutput(success=True, result=result, message=f"Sesión {result['aborted']} abortada")
    except Exception as e:
        return GenericOutput(success=False, result={}, message=str(e))
