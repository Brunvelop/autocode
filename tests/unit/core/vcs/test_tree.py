"""
Unit tests for autocode.core.git.tree module (get_git_tree function).
"""
import pytest
from unittest.mock import Mock, patch
from subprocess import CalledProcessError

from autocode.core.vcs import get_git_tree


class TestGetGitTree:
    """Tests para la función get_git_tree."""

    @patch('subprocess.run')
    def test_get_git_tree_success(self, mock_run):
        """Test parsing of git ls-tree output into a non-recursive graph."""
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
        
        result = get_git_tree()
        
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
        # Simulate git error (e.g., not a git repo)
        mock_run.side_effect = CalledProcessError(128, ['git'], stderr="Not a git repository")
        
        result = get_git_tree()
        
        assert result.success is False
        assert "Not a git repository" in result.message
        assert result.result is None

    @patch('subprocess.run')
    def test_get_git_tree_empty(self, mock_run):
        """Test handling of empty git repo."""
        mock_process = Mock()
        mock_process.stdout = ""
        mock_process.returncode = 0
        mock_run.return_value = mock_process
        
        result = get_git_tree()
        
        assert result.success is True
        graph = result.result
        assert graph is not None
        assert graph.root_id == ""
        assert len(graph.nodes) == 1
        assert graph.nodes[0].id == ""

    @patch('subprocess.run')
    def test_get_git_tree_deep_nesting(self, mock_run):
        """Test handling of deeply nested directories."""
        mock_output = (
            "100644 blob aaa   100\ta/b/c/d/e/file.txt\n"
        )
        
        mock_process = Mock()
        mock_process.stdout = mock_output
        mock_process.returncode = 0
        mock_run.return_value = mock_process
        
        result = get_git_tree()
        
        assert result.success is True
        nodes = {n.id: n for n in result.result.nodes}
        
        # All intermediate directories should exist
        assert "a" in nodes
        assert "a/b" in nodes
        assert "a/b/c" in nodes
        assert "a/b/c/d" in nodes
        assert "a/b/c/d/e" in nodes
        assert "a/b/c/d/e/file.txt" in nodes
        
        # Verify parent chain
        assert nodes["a"].parent_id == ""
        assert nodes["a/b"].parent_id == "a"
        assert nodes["a/b/c"].parent_id == "a/b"
        assert nodes["a/b/c/d"].parent_id == "a/b/c"
        assert nodes["a/b/c/d/e"].parent_id == "a/b/c/d"
        assert nodes["a/b/c/d/e/file.txt"].parent_id == "a/b/c/d/e"
