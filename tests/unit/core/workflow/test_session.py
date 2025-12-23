"""
Unit tests for AI Session Management module.
tests/unit/core/workflow/test_session.py
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
import json
from pathlib import Path

# Importar módulos a testear
from autocode.core.workflow.session import (
    AISessionManager,
    start_ai_session,
    save_conversation,
    finalize_ai_session,
    abort_ai_session,
    get_current_session,
    list_ai_sessions,
    CONTEXT_DIR_NAME,
    VALID_SESSION_TYPES,
)
from autocode.interfaces.models import GenericOutput


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def mock_git_operations():
    """Mock GitOperations para aislar tests de Git real."""
    with patch('autocode.core.workflow.session.GitOperations') as MockGit:
        mock_git = MagicMock()
        mock_git.is_repo_clean.return_value = True
        mock_git.get_current_branch.return_value = "main"
        mock_git.list_branches.return_value = []
        MockGit.return_value = mock_git
        yield mock_git


@pytest.fixture
def sample_session_data():
    """Datos de sesión de ejemplo."""
    return {
        "session_id": "20231223-120000",
        "description": "Test session",
        "base_branch": "main",
        "session_type": "session",
        "started_at": "2023-12-23T12:00:00",
        "status": "in_progress",
        "branch": "ai/session-20231223-120000"
    }


@pytest.fixture  
def sample_messages():
    """Mensajes de conversación de ejemplo."""
    return [
        {"role": "user", "content": "Hola"},
        {"role": "assistant", "content": "¿En qué puedo ayudarte?"},
    ]


# ============================================================================
# TESTS: AISessionManager Class
# ============================================================================

class TestAISessionManager:
    """Tests para la clase AISessionManager."""

    # ---------- Initialization ----------
    
    def test_init_creates_git_operations(self, mock_git_operations):
        """Manager debe inicializar GitOperations."""
        manager = AISessionManager()
        assert manager.git is not None
        assert manager.context_dir == Path(CONTEXT_DIR_NAME)

    def test_init_custom_context_dir(self, mock_git_operations):
        """Manager acepta directorio de contexto personalizado."""
        manager = AISessionManager(context_dir=".custom-context")
        assert manager.context_dir == Path(".custom-context")

    # ---------- start_session ----------

    def test_start_session_success(self, mock_git_operations):
        """Iniciar sesión crea rama y archivos correctamente."""
        manager = AISessionManager()
        
        with patch.object(manager, '_save_json') as mock_save:
            result = manager.start_session(
                description="Test feature",
                base_branch="main",
                session_type="session"
            )
        
        # Verificar que se creó la rama
        mock_git_operations.create_and_checkout_branch.assert_called_once()
        branch_name = mock_git_operations.create_and_checkout_branch.call_args[0][0]
        assert branch_name.startswith("ai/session-")
        
        # Verificar datos de sesión
        assert result["description"] == "Test feature"
        assert result["status"] == "in_progress"
        assert "branch" in result

    def test_start_session_dirty_repo_fails(self, mock_git_operations):
        """No permite iniciar sesión si hay cambios sin commit."""
        mock_git_operations.is_repo_clean.return_value = False
        manager = AISessionManager()
        
        with pytest.raises(ValueError, match="cambios sin commit"):
            manager.start_session("Test")

    def test_start_session_invalid_type_fails(self, mock_git_operations):
        """Rechaza tipos de sesión inválidos."""
        manager = AISessionManager()
        
        with pytest.raises(ValueError, match="session_type debe ser"):
            manager.start_session("Test", session_type="invalid_type")

    @pytest.mark.parametrize("session_type", VALID_SESSION_TYPES)
    def test_start_session_all_valid_types(self, mock_git_operations, session_type):
        """Todos los tipos válidos funcionan."""
        manager = AISessionManager()
        
        with patch.object(manager, '_save_json'):
            result = manager.start_session("Test", session_type=session_type)
        
        assert result["session_type"] == session_type
        assert f"ai/{session_type}-" in result["branch"]

    # ---------- save_conversation_to_session ----------

    def test_save_conversation_success(self, mock_git_operations, sample_messages):
        """Guardar conversación funciona en sesión activa."""
        mock_git_operations.get_current_branch.return_value = "ai/session-123"
        manager = AISessionManager()
        
        with patch.object(manager, '_save_json') as mock_save:
            result = manager.save_conversation_to_session(sample_messages)
        
        mock_save.assert_called_once()
        assert result["message_count"] == 2
        assert result["branch"] == "ai/session-123"

    def test_save_conversation_not_in_session_fails(self, mock_git_operations):
        """Error si no estamos en una rama de sesión."""
        mock_git_operations.get_current_branch.return_value = "main"
        manager = AISessionManager()
        
        with pytest.raises(ValueError, match="No estás en una sesión AI"):
            manager.save_conversation_to_session([])

    # ---------- finalize_session ----------

    def test_finalize_session_success(self, mock_git_operations, sample_session_data):
        """Finalizar sesión hace merge correctamente."""
        mock_git_operations.get_current_branch.return_value = "ai/session-123"
        manager = AISessionManager()
        
        with patch.object(manager, '_load_json', return_value=sample_session_data):
            with patch.object(manager, '_save_json'):
                result = manager.finalize_session(
                    commit_message="feat: new feature",
                    merge_to="main",
                    keep_branch=True
                )
        
        # Verificar operaciones Git
        mock_git_operations.merge_squash.assert_called_once()
        mock_git_operations.reset_paths.assert_called_once()
        mock_git_operations.commit.assert_called_with("feat: new feature")
        
        # Verificar resultado
        assert result["merged_to"] == "main"
        assert result["branch_kept"] is True

    def test_finalize_session_not_in_session_fails(self, mock_git_operations):
        """Error si no estamos en sesión."""
        mock_git_operations.get_current_branch.return_value = "main"
        manager = AISessionManager()
        
        with pytest.raises(ValueError, match="No estás en una sesión AI"):
            manager.finalize_session("commit msg")

    def test_finalize_session_delete_branch(self, mock_git_operations, sample_session_data):
        """keep_branch=False elimina la rama después."""
        mock_git_operations.get_current_branch.return_value = "ai/session-123"
        manager = AISessionManager()
        
        with patch.object(manager, '_load_json', return_value=sample_session_data):
            with patch.object(manager, '_save_json'):
                manager.finalize_session("msg", keep_branch=False)
        
        mock_git_operations.delete_branch.assert_called_once_with("ai/session-123", force=True)

    def test_finalize_session_rollback_on_error(self, mock_git_operations, sample_session_data):
        """Rollback automático si falla durante merge."""
        mock_git_operations.get_current_branch.return_value = "ai/session-123"
        mock_git_operations.merge_squash.side_effect = Exception("Merge conflict")
        manager = AISessionManager()
        
        with patch.object(manager, '_load_json', return_value=sample_session_data):
            with patch.object(manager, '_save_json'):
                with pytest.raises(Exception, match="Merge conflict"):
                    manager.finalize_session("msg")
        
        # Debe intentar rollback
        mock_git_operations.checkout_branch.assert_called_with("ai/session-123")

    # ---------- abort_session ----------

    def test_abort_session_success(self, mock_git_operations, sample_session_data):
        """Abortar sesión vuelve a main y elimina rama."""
        mock_git_operations.get_current_branch.return_value = "ai/session-123"
        manager = AISessionManager()
        
        with patch.object(manager, '_load_json', return_value=sample_session_data):
            result = manager.abort_session(delete_branch=True)
        
        mock_git_operations.checkout_branch.assert_called_with("main")
        mock_git_operations.delete_branch.assert_called_with("ai/session-123", force=True)
        assert result["aborted"] == "ai/session-123"

    def test_abort_session_keep_branch(self, mock_git_operations, sample_session_data):
        """Abortar sin eliminar rama."""
        mock_git_operations.get_current_branch.return_value = "ai/session-123"
        manager = AISessionManager()
        
        with patch.object(manager, '_load_json', return_value=sample_session_data):
            result = manager.abort_session(delete_branch=False)
        
        mock_git_operations.delete_branch.assert_not_called()
        assert result["branch_deleted"] is False

    # ---------- get_current_session ----------

    def test_get_current_session_active(self, mock_git_operations, sample_session_data):
        """Obtener sesión activa devuelve datos."""
        mock_git_operations.get_current_branch.return_value = "ai/session-123"
        manager = AISessionManager()
        
        with patch.object(manager, '_load_json', return_value=sample_session_data):
            result = manager.get_current_session()
        
        assert result == sample_session_data

    def test_get_current_session_not_in_session(self, mock_git_operations):
        """Devuelve None si no hay sesión activa."""
        mock_git_operations.get_current_branch.return_value = "main"
        manager = AISessionManager()
        
        result = manager.get_current_session()
        assert result is None

    # ---------- list_sessions ----------

    def test_list_sessions_multiple(self, mock_git_operations):
        """Lista múltiples sesiones correctamente."""
        mock_git_operations.list_branches.return_value = [
            "ai/session-20231220-100000",
            "ai/docs-20231221-110000",
        ]
        mock_git_operations.get_file_content_from_branch.side_effect = [
            json.dumps({"session_id": "20231220-100000", "started_at": "2023-12-20"}),
            json.dumps({"session_id": "20231221-110000", "started_at": "2023-12-21"}),
        ]
        manager = AISessionManager()
        
        sessions = manager.list_sessions()
        
        assert len(sessions) == 2
        # Ordenadas por fecha (más reciente primero)
        assert sessions[0]["session_id"] == "20231221-110000"

    def test_list_sessions_empty(self, mock_git_operations):
        """Lista vacía si no hay sesiones."""
        mock_git_operations.list_branches.return_value = []
        manager = AISessionManager()
        
        sessions = manager.list_sessions()
        assert sessions == []

    def test_list_sessions_fallback_for_missing_json(self, mock_git_operations):
        """Crea entrada fallback si falta session.json."""
        mock_git_operations.list_branches.return_value = ["ai/session-orphan"]
        mock_git_operations.get_file_content_from_branch.return_value = None
        manager = AISessionManager()
        
        sessions = manager.list_sessions()
        
        assert len(sessions) == 1
        assert sessions[0]["branch"] == "ai/session-orphan"
        assert sessions[0]["status"] == "unknown"


# ============================================================================
# TESTS: Registered Functions (API endpoints)
# ============================================================================

class TestRegisteredFunctions:
    """Tests para funciones registradas (API/CLI/MCP)."""

    def test_start_ai_session_returns_generic_output(self, mock_git_operations):
        """start_ai_session devuelve GenericOutput."""
        with patch('autocode.core.workflow.session.AISessionManager') as MockManager:
            MockManager.return_value.start_session.return_value = {"branch": "ai/test"}
            
            result = start_ai_session("Test description")
            
            assert isinstance(result, GenericOutput)
            assert result.success is True
            assert "branch" in result.result

    def test_start_ai_session_handles_error(self, mock_git_operations):
        """start_ai_session captura errores."""
        with patch('autocode.core.workflow.session.AISessionManager') as MockManager:
            MockManager.return_value.start_session.side_effect = ValueError("Dirty repo")
            
            result = start_ai_session("Test")
            
            assert result.success is False
            assert "Dirty repo" in result.message

    def test_save_conversation_returns_generic_output(self, mock_git_operations):
        """save_conversation devuelve GenericOutput."""
        with patch('autocode.core.workflow.session.AISessionManager') as MockManager:
            MockManager.return_value.save_conversation_to_session.return_value = {"message_count": 5}
            
            result = save_conversation([{"role": "user", "content": "Hi"}])
            
            assert isinstance(result, GenericOutput)
            assert result.success is True

    def test_finalize_ai_session_returns_generic_output(self, mock_git_operations):
        """finalize_ai_session devuelve GenericOutput."""
        with patch('autocode.core.workflow.session.AISessionManager') as MockManager:
            MockManager.return_value.finalize_session.return_value = {"merged_to": "main"}
            
            result = finalize_ai_session("feat: done")
            
            assert isinstance(result, GenericOutput)
            assert result.success is True

    def test_get_current_session_returns_generic_output(self, mock_git_operations):
        """get_current_session devuelve GenericOutput."""
        with patch('autocode.core.workflow.session.AISessionManager') as MockManager:
            MockManager.return_value.get_current_session.return_value = {"branch": "ai/x"}
            
            result = get_current_session()
            
            assert isinstance(result, GenericOutput)
            assert result.success is True

    def test_list_ai_sessions_returns_generic_output(self, mock_git_operations):
        """list_ai_sessions devuelve GenericOutput."""
        with patch('autocode.core.workflow.session.AISessionManager') as MockManager:
            MockManager.return_value.list_sessions.return_value = []
            
            result = list_ai_sessions()
            
            assert isinstance(result, GenericOutput)
            assert result.success is True
            assert "sessions" in result.result

    def test_abort_ai_session_returns_generic_output(self, mock_git_operations):
        """abort_ai_session devuelve GenericOutput."""
        with patch('autocode.core.workflow.session.AISessionManager') as MockManager:
            MockManager.return_value.abort_session.return_value = {"aborted": "ai/x"}
            
            result = abort_ai_session()
            
            assert isinstance(result, GenericOutput)
            assert result.success is True
