"""
Unit tests for git_utils module.
"""
import pytest
from unittest.mock import Mock, patch
from subprocess import CalledProcessError

# We import the module to be tested (even if it doesn't exist yet, for TDD)
# This will fail until we create the module
try:
    from autocode.core.utils import git_utils
except ImportError:
    git_utils = None


class TestGitUtils:
    
    def test_module_exists(self):
        """Verify that the module can be imported."""
        assert git_utils is not None, "autocode.core.utils.git_utils module should exist"

    @patch('subprocess.run')
    def test_get_git_tree_success(self, mock_run):
        """Test parsing of git ls-tree output into a hierarchical tree."""
        # Skip if module not implemented yet (to allow running this test file progressively)
        if git_utils is None:
            pytest.fail("Module git_utils not implemented")

        # Mock git output
        # Simulating:
        # root.txt
        # src/main.py
        # src/utils/helper.py
        mock_output = "root.txt\nsrc/main.py\nsrc/utils/helper.py\n"
        
        mock_process = Mock()
        mock_process.stdout = mock_output
        mock_process.returncode = 0
        mock_run.return_value = mock_process
        
        result = git_utils.get_git_tree()
        
        # Verify result structure (D3-friendly format)
        assert result.success is True
        tree = result.result
        
        # Pydantic model validation instead of dict access
        assert tree.name == 'root'
        assert tree.type == 'directory'
        assert len(tree.children) == 2  # root.txt and src/
        
        # Check root.txt
        root_txt = next((c for c in tree.children if c.name == 'root.txt'), None)
        assert root_txt is not None
        assert root_txt.type == 'file'
        
        # Check src/
        src = next((c for c in tree.children if c.name == 'src'), None)
        assert src is not None
        assert src.type == 'directory'
        
        # Check src/main.py
        main_py = next((c for c in src.children if c.name == 'main.py'), None)
        assert main_py is not None
        assert main_py.type == 'file'
        
        # Check src/utils/
        utils = next((c for c in src.children if c.name == 'utils'), None)
        assert utils is not None
        assert utils.type == 'directory'
        
        # Check src/utils/helper.py
        helper = next((c for c in utils.children if c.name == 'helper.py'), None)
        assert helper is not None
        assert helper.type == 'file'
        
        # Verify git command call
        mock_run.assert_called_with(
            ['git', 'ls-tree', '-r', 'HEAD', '--name-only'],
            capture_output=True,
            text=True,
            check=True
        )

    @patch('subprocess.run')
    def test_get_git_tree_error(self, mock_run):
        """Test handling of git command errors."""
        if git_utils is None:
            pytest.fail("Module git_utils not implemented")
            
        # Simulate git error (e.g., not a git repo)
        mock_run.side_effect = CalledProcessError(128, ['git'], stderr="Not a git repository")
        
        result = git_utils.get_git_tree()
        
        assert result.success is False
        assert "Not a git repository" in result.message
        assert result.result is None

    @patch('subprocess.run')
    def test_get_git_tree_empty(self, mock_run):
        """Test handling of empty git repo."""
        if git_utils is None:
            pytest.fail("Module git_utils not implemented")
            
        mock_process = Mock()
        mock_process.stdout = ""
        mock_process.returncode = 0
        mock_run.return_value = mock_process
        
        result = git_utils.get_git_tree()
        
        assert result.success is True
        tree = result.result
        assert tree.name == 'root'
        assert tree.children == []
