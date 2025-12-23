"""
Unit tests for GitOperations class.
tests/unit/core/workflow/test_git_operations.py
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
import subprocess

from autocode.core.utils.git_utils import GitOperations
from git.exc import GitCommandError


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def mock_repo():
    """Mock de Repo de GitPython."""
    with patch('autocode.core.utils.git_utils.Repo') as MockRepo:
        mock = MagicMock()
        mock.is_dirty.return_value = False
        mock.active_branch.name = "main"
        
        # Mock heads como diccionario-like
        main_head = MagicMock()
        main_head.name = "main"
        develop_head = MagicMock()
        develop_head.name = "develop"
        mock.heads = {"main": main_head, "develop": develop_head}
        
        MockRepo.return_value = mock
        yield mock


# ============================================================================
# TESTS: GitOperations Class
# ============================================================================

class TestGitOperations:
    """Tests para GitOperations wrapper."""

    # ---------- Initialization ----------

    def test_init_valid_repo(self, mock_repo):
        """Inicializa correctamente con repo válido."""
        git = GitOperations(".")
        assert git.repo is not None

    def test_init_invalid_repo_raises(self):
        """Lanza error si no es un repo git."""
        with patch('autocode.core.utils.git_utils.Repo', side_effect=Exception("Not a repo")):
            with pytest.raises(GitCommandError):
                GitOperations("/invalid/path")

    # ---------- is_repo_clean ----------

    def test_is_repo_clean_true(self, mock_repo):
        """is_repo_clean devuelve True si está limpio."""
        mock_repo.is_dirty.return_value = False
        git = GitOperations()
        assert git.is_repo_clean() is True

    def test_is_repo_clean_false(self, mock_repo):
        """is_repo_clean devuelve False si hay cambios."""
        mock_repo.is_dirty.return_value = True
        git = GitOperations()
        assert git.is_repo_clean() is False

    def test_is_repo_clean_with_untracked(self, mock_repo):
        """is_repo_clean considera archivos untracked por defecto."""
        git = GitOperations()
        git.is_repo_clean(untracked=True)
        mock_repo.is_dirty.assert_called_with(untracked_files=True)

    def test_is_repo_clean_without_untracked(self, mock_repo):
        """is_repo_clean puede ignorar archivos untracked."""
        git = GitOperations()
        git.is_repo_clean(untracked=False)
        mock_repo.is_dirty.assert_called_with(untracked_files=False)

    # ---------- get_current_branch ----------

    def test_get_current_branch(self, mock_repo):
        """get_current_branch devuelve nombre correcto."""
        mock_repo.active_branch.name = "feature-x"
        git = GitOperations()
        assert git.get_current_branch() == "feature-x"

    def test_get_current_branch_detached(self, mock_repo):
        """Maneja HEAD detached devolviendo hash corto."""
        # Simular TypeError cuando HEAD está detached
        type(mock_repo).active_branch = property(
            lambda self: (_ for _ in ()).throw(TypeError("HEAD is detached"))
        )
        mock_repo.head.commit.hexsha = "abc1234567890def"
        git = GitOperations()
        result = git.get_current_branch()
        # Debería devolver los primeros 7 caracteres del hash
        assert result == "abc1234"

    # ---------- list_branches ----------

    def test_list_branches_all(self, mock_repo):
        """list_branches devuelve todas las ramas."""
        head1 = MagicMock()
        head1.name = "main"
        head2 = MagicMock()
        head2.name = "develop"
        mock_repo.heads = [head1, head2]
        
        git = GitOperations()
        branches = git.list_branches()
        
        assert "main" in branches
        assert "develop" in branches
        assert len(branches) == 2

    def test_list_branches_with_pattern(self, mock_repo):
        """list_branches filtra por patrón."""
        heads = []
        for name in ["ai/session-1", "ai/session-2", "main", "develop"]:
            head = MagicMock()
            head.name = name
            heads.append(head)
        mock_repo.heads = heads
        
        git = GitOperations()
        branches = git.list_branches("ai/*")
        
        assert len(branches) == 2
        assert "ai/session-1" in branches
        assert "ai/session-2" in branches
        assert "main" not in branches

    def test_list_branches_no_match(self, mock_repo):
        """list_branches devuelve vacío si no hay matches."""
        head = MagicMock()
        head.name = "main"
        mock_repo.heads = [head]
        
        git = GitOperations()
        branches = git.list_branches("feature/*")
        
        assert branches == []

    # ---------- Branch Operations ----------

    def test_create_and_checkout_branch(self, mock_repo):
        """create_and_checkout_branch crea y hace checkout."""
        new_head = MagicMock()
        mock_repo.create_head.return_value = new_head
        base_head = MagicMock()
        mock_repo.heads = {"main": base_head}
        
        git = GitOperations()
        git.create_and_checkout_branch("feature-new", "main")
        
        mock_repo.create_head.assert_called_once_with("feature-new", base_head)
        new_head.checkout.assert_called_once()

    def test_checkout_branch(self, mock_repo):
        """checkout_branch hace checkout a rama existente."""
        develop_head = MagicMock()
        mock_repo.heads = {"develop": develop_head}
        
        git = GitOperations()
        git.checkout_branch("develop")
        
        develop_head.checkout.assert_called_once()

    def test_checkout_branch_not_found_raises(self, mock_repo):
        """checkout_branch lanza error si rama no existe."""
        mock_repo.heads = {}
        
        git = GitOperations()
        with pytest.raises(GitCommandError):
            git.checkout_branch("nonexistent")

    def test_delete_branch(self, mock_repo):
        """delete_branch elimina la rama."""
        git = GitOperations()
        git.delete_branch("feature-old")
        
        mock_repo.delete_head.assert_called_once_with("feature-old", force=False)

    def test_delete_branch_force(self, mock_repo):
        """delete_branch con force=True."""
        git = GitOperations()
        git.delete_branch("feature-old", force=True)
        
        mock_repo.delete_head.assert_called_once_with("feature-old", force=True)

    # ---------- Commit Operations ----------

    def test_add_paths(self, mock_repo):
        """add_paths agrega archivos al staging."""
        git = GitOperations()
        git.add_paths(["file1.txt", "file2.py"])
        
        mock_repo.index.add.assert_called_once_with(["file1.txt", "file2.py"])

    def test_commit(self, mock_repo):
        """commit crea un commit con el mensaje."""
        git = GitOperations()
        git.commit("feat: add new feature")
        
        mock_repo.index.commit.assert_called_once_with("feat: add new feature")

    def test_add_and_commit(self, mock_repo):
        """add_and_commit agrega y commitea en una operación."""
        git = GitOperations()
        git.add_and_commit(["file.txt"], "commit message")
        
        mock_repo.index.add.assert_called_with(["file.txt"])
        mock_repo.index.commit.assert_called_with("commit message")

    # ---------- Merge Operations ----------

    @patch('subprocess.run')
    def test_merge_squash(self, mock_subprocess, mock_repo):
        """merge_squash ejecuta git merge --squash."""
        mock_subprocess.return_value = MagicMock(returncode=0)
        target_head = MagicMock()
        mock_repo.heads = {"main": target_head}
        
        git = GitOperations()
        git.merge_squash("feature", "main")
        
        # Verificar checkout a target
        target_head.checkout.assert_called_once()
        
        # Verificar comando merge
        mock_subprocess.assert_called_once()
        call_args = mock_subprocess.call_args[0][0]
        assert "git" in call_args
        assert "merge" in call_args
        assert "--squash" in call_args
        assert "--no-commit" in call_args
        assert "feature" in call_args

    @patch('subprocess.run')
    def test_merge_squash_with_auto_commit(self, mock_subprocess, mock_repo):
        """merge_squash con auto_commit=True hace commit."""
        mock_subprocess.return_value = MagicMock(returncode=0)
        target_head = MagicMock()
        mock_repo.heads = {"main": target_head}
        
        git = GitOperations()
        git.merge_squash("feature", "main", auto_commit=True, commit_message="Merge feature")
        
        mock_repo.index.commit.assert_called_once_with("Merge feature")

    @patch('subprocess.run')
    def test_merge_squash_error(self, mock_subprocess, mock_repo):
        """merge_squash lanza error si falla."""
        mock_subprocess.side_effect = subprocess.CalledProcessError(1, ["git"], stderr="Conflict")
        target_head = MagicMock()
        mock_repo.heads = {"main": target_head}
        
        git = GitOperations()
        with pytest.raises(GitCommandError):
            git.merge_squash("feature", "main")

    @patch('subprocess.run')
    def test_reset_paths(self, mock_subprocess, mock_repo):
        """reset_paths ejecuta git reset y checkout."""
        mock_subprocess.return_value = MagicMock(returncode=0)
        
        git = GitOperations()
        git.reset_paths([".ai-context/"])
        
        # Debería llamar a subprocess para reset y checkout
        assert mock_subprocess.call_count >= 1

    # ---------- File Content from Branch ----------

    def test_get_file_content_from_branch(self, mock_repo):
        """get_file_content_from_branch lee archivos de otra rama."""
        mock_repo.git.show.return_value = '{"key": "value"}'
        
        git = GitOperations()
        content = git.get_file_content_from_branch("develop", "config.json")
        
        assert content == '{"key": "value"}'
        mock_repo.git.show.assert_called_with("develop:config.json")

    def test_get_file_content_from_branch_not_found(self, mock_repo):
        """Devuelve None si el archivo no existe en la rama."""
        mock_repo.git.show.side_effect = Exception("Path not found")
        
        git = GitOperations()
        content = git.get_file_content_from_branch("develop", "missing.json")
        
        assert content is None

    def test_get_file_content_from_branch_binary_file(self, mock_repo):
        """Maneja archivos binarios o errores de encoding."""
        mock_repo.git.show.side_effect = UnicodeDecodeError("utf-8", b"", 0, 1, "invalid")
        
        git = GitOperations()
        content = git.get_file_content_from_branch("develop", "image.png")
        
        assert content is None
