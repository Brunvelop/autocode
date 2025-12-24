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
        """Test parsing of git ls-tree output into a non-recursive graph."""
        # Skip if module not implemented yet (to allow running this test file progressively)
        if git_utils is None:
            pytest.fail("Module git_utils not implemented")

        # Mock git output
        # Simulating:
        # root.txt (100 bytes)
        # src/main.py (200 bytes)
        # src/utils/helper.py (300 bytes)
        # Format: mode type sha size path
        mock_output = (
            "100644 blob aaaaaa   100\troot.txt\n"
            "100644 blob bbbbbb   200\tsrc/main.py\n"
            "100644 blob cccccc   300\tsrc/utils/helper.py\n"
        )
        
        mock_process = Mock()
        mock_process.stdout = mock_output
        mock_process.returncode = 0
        mock_run.return_value = mock_process
        
        result = git_utils.get_git_tree()
        
        # Verify result structure
        assert result.success is True
        graph = result.result
        assert graph is not None
        assert graph.root_id == ""
        assert len(graph.nodes) >= 1

        nodes = {n.id: n for n in graph.nodes}
        assert "" in nodes
        assert nodes[""].type == "directory"
        assert nodes[""].parent_id is None
        assert nodes[""].name == "root"

        # root.txt
        assert "root.txt" in nodes
        assert nodes["root.txt"].type == "file"
        assert nodes["root.txt"].size == 100
        assert nodes["root.txt"].parent_id == ""

        # src directory
        assert "src" in nodes
        assert nodes["src"].type == "directory"
        assert nodes["src"].parent_id == ""

        # src/main.py
        assert "src/main.py" in nodes
        assert nodes["src/main.py"].type == "file"
        assert nodes["src/main.py"].size == 200
        assert nodes["src/main.py"].parent_id == "src"

        # src/utils directory
        assert "src/utils" in nodes
        assert nodes["src/utils"].type == "directory"
        assert nodes["src/utils"].parent_id == "src"

        # src/utils/helper.py
        assert "src/utils/helper.py" in nodes
        assert nodes["src/utils/helper.py"].type == "file"
        assert nodes["src/utils/helper.py"].size == 300
        assert nodes["src/utils/helper.py"].parent_id == "src/utils"
        
        # Verify git command call
        mock_run.assert_called_with(
            ['git', 'ls-tree', '-r', '-l', 'HEAD'],
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
        graph = result.result
        assert graph is not None
        assert graph.root_id == ""
        assert len(graph.nodes) == 1
        assert graph.nodes[0].id == ""
