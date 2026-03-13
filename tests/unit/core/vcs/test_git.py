"""
Unit tests for autocode.core.vcs.git module.

Tests for the shared git helper functions extracted from metrics.py,
planner.py, executor.py, and reviewer.py.

All tests mock subprocess.run to avoid needing a real git repo.
"""

from unittest.mock import patch, call, MagicMock

import pytest


# ==============================================================================
# TestGit — silent subprocess wrapper
# ==============================================================================


class TestGit:
    """Tests for git() — silent subprocess wrapper that returns stdout."""

    def test_git_returns_stdout_stripped(self):
        """git() returns stripped stdout from subprocess."""
        with patch("autocode.core.vcs.git.subprocess.run") as mock_run:
            mock_run.return_value.stdout = "abc123\n"
            mock_run.return_value.returncode = 0

            from autocode.core.vcs.git import git

            result = git("rev-parse", "HEAD")

        assert result == "abc123"
        mock_run.assert_called_once_with(
            ["git", "rev-parse", "HEAD"],
            capture_output=True, text=True, check=False, cwd=".",
        )

    def test_git_returns_empty_on_failure(self):
        """git() returns empty string (stripped stderr/stdout) on failure, no exception."""
        with patch("autocode.core.vcs.git.subprocess.run") as mock_run:
            mock_run.return_value.stdout = ""
            mock_run.return_value.returncode = 128

            from autocode.core.vcs.git import git

            result = git("rev-parse", "HEAD")

        assert result == ""

    def test_git_passes_cwd(self):
        """git() passes cwd parameter to subprocess."""
        with patch("autocode.core.vcs.git.subprocess.run") as mock_run:
            mock_run.return_value.stdout = "main\n"
            mock_run.return_value.returncode = 0

            from autocode.core.vcs.git import git

            result = git("rev-parse", "--abbrev-ref", "HEAD", cwd="/tmp/repo")

        assert result == "main"
        mock_run.assert_called_once_with(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            capture_output=True, text=True, check=False, cwd="/tmp/repo",
        )


# ==============================================================================
# TestGitChecked — raises on failure
# ==============================================================================


class TestGitChecked:
    """Tests for git_checked() — raises RuntimeError on failure."""

    def test_git_checked_returns_stdout(self):
        """git_checked() returns stripped stdout on success."""
        with patch("autocode.core.vcs.git.subprocess.run") as mock_run:
            mock_run.return_value.returncode = 0
            mock_run.return_value.stdout = "abc123\n"
            mock_run.return_value.stderr = ""

            from autocode.core.vcs.git import git_checked

            result = git_checked("rev-parse", "HEAD")

        assert result == "abc123"

    def test_git_checked_raises_on_nonzero(self):
        """git_checked() raises RuntimeError with stderr on non-zero exit."""
        with patch("autocode.core.vcs.git.subprocess.run") as mock_run:
            mock_run.return_value.returncode = 128
            mock_run.return_value.stdout = ""
            mock_run.return_value.stderr = "fatal: not a git repository"

            from autocode.core.vcs.git import git_checked

            with pytest.raises(RuntimeError, match="git error.*not a git repository"):
                git_checked("rev-parse", "HEAD")

    def test_git_checked_raises_with_fallback_message(self):
        """git_checked() uses fallback error message when stderr is empty."""
        with patch("autocode.core.vcs.git.subprocess.run") as mock_run:
            mock_run.return_value.returncode = 1
            mock_run.return_value.stdout = ""
            mock_run.return_value.stderr = ""

            from autocode.core.vcs.git import git_checked

            with pytest.raises(RuntimeError, match="git.*failed with code 1"):
                git_checked("add", "file.py")

    def test_git_checked_passes_cwd(self):
        """git_checked() passes cwd parameter to subprocess."""
        with patch("autocode.core.vcs.git.subprocess.run") as mock_run:
            mock_run.return_value.returncode = 0
            mock_run.return_value.stdout = "ok\n"
            mock_run.return_value.stderr = ""

            from autocode.core.vcs.git import git_checked

            git_checked("status", cwd="/tmp/repo")

        mock_run.assert_called_once_with(
            ["git", "status"],
            capture_output=True, text=True, check=False, cwd="/tmp/repo",
        )


# ==============================================================================
# TestGitShow — file content at ref
# ==============================================================================


class TestGitShow:
    """Tests for git_show() — get file content at a specific git ref."""

    def test_git_show_returns_content(self):
        """git_show() returns file content on success."""
        with patch("autocode.core.vcs.git.subprocess.run") as mock_run:
            mock_run.return_value.returncode = 0
            mock_run.return_value.stdout = "def hello():\n    return 'world'\n"

            from autocode.core.vcs.git import git_show

            result = git_show("HEAD:main.py")

        assert result == "def hello():\n    return 'world'\n"
        mock_run.assert_called_once_with(
            ["git", "show", "HEAD:main.py"],
            capture_output=True, text=True, check=False, cwd=".",
        )

    def test_git_show_returns_none_on_error(self):
        """git_show() returns None when git show fails (e.g., file doesn't exist at ref)."""
        with patch("autocode.core.vcs.git.subprocess.run") as mock_run:
            mock_run.return_value.returncode = 128
            mock_run.return_value.stdout = ""

            from autocode.core.vcs.git import git_show

            result = git_show("HEAD:nonexistent.py")

        assert result is None

    def test_git_show_passes_cwd(self):
        """git_show() passes cwd parameter to subprocess."""
        with patch("autocode.core.vcs.git.subprocess.run") as mock_run:
            mock_run.return_value.returncode = 0
            mock_run.return_value.stdout = "content"

            from autocode.core.vcs.git import git_show

            git_show("HEAD:file.py", cwd="/tmp/repo")

        mock_run.assert_called_once_with(
            ["git", "show", "HEAD:file.py"],
            capture_output=True, text=True, check=False, cwd="/tmp/repo",
        )


# ==============================================================================
# TestGitAddAndCommit
# ==============================================================================


class TestGitAddAndCommit:
    """Tests for git_add_and_commit() — git add + commit workflow."""

    def test_adds_files_and_commits(self):
        """git_add_and_commit() calls git add for each file then git commit."""
        with patch("autocode.core.vcs.git.subprocess.run") as mock_run:
            mock_run.return_value.returncode = 0
            mock_run.return_value.stdout = "abc123\n"
            mock_run.return_value.stderr = ""

            from autocode.core.vcs.git import git_add_and_commit

            git_add_and_commit(["src/a.py", "src/b.py"], "feat: add files")

        calls = mock_run.call_args_list
        # Should have: git add src/a.py, git add src/b.py, git commit, git rev-parse
        assert any(
            ["git", "add", "src/a.py"] == c.args[0]
            for c in calls
        ), f"Expected git add src/a.py in {calls}"
        assert any(
            ["git", "add", "src/b.py"] == c.args[0]
            for c in calls
        ), f"Expected git add src/b.py in {calls}"
        assert any(
            c.args[0][:3] == ["git", "commit", "-m"]
            for c in calls
        ), f"Expected git commit in {calls}"

    def test_returns_commit_hash(self):
        """git_add_and_commit() returns the commit hash after committing."""
        with patch("autocode.core.vcs.git.subprocess.run") as mock_run:
            mock_run.return_value.returncode = 0
            mock_run.return_value.stdout = "def456789\n"
            mock_run.return_value.stderr = ""

            from autocode.core.vcs.git import git_add_and_commit

            result = git_add_and_commit(["file.py"], "fix: bug")

        assert result == "def456789"

    def test_passes_cwd(self):
        """git_add_and_commit() passes cwd to all subprocess calls."""
        with patch("autocode.core.vcs.git.subprocess.run") as mock_run:
            mock_run.return_value.returncode = 0
            mock_run.return_value.stdout = "abc\n"
            mock_run.return_value.stderr = ""

            from autocode.core.vcs.git import git_add_and_commit

            git_add_and_commit(["f.py"], "msg", cwd="/tmp/repo")

        for c in mock_run.call_args_list:
            assert c.kwargs.get("cwd") == "/tmp/repo" or \
                (len(c.args) > 1 and False), \
                f"Expected cwd='/tmp/repo' in {c}"


# ==============================================================================
# TestGetTrackedFilesAtCommit — files tracked at a specific commit
# ==============================================================================


class TestGetTrackedFilesAtCommit:
    """Tests for get_tracked_files_at_commit() — list files tracked at a historical commit."""

    def test_returns_filtered_files_for_commit(self):
        """get_tracked_files_at_commit() returns files matching the given extensions."""
        with patch("autocode.core.vcs.git.git") as mock_git:
            mock_git.return_value = "src/app.py\nsrc/utils.js\nREADME.md"

            from autocode.core.vcs.git import get_tracked_files_at_commit

            result = get_tracked_files_at_commit("abc123", ".py", ".js")

        assert "src/app.py" in result
        assert "src/utils.js" in result
        assert "README.md" not in result

    def test_returns_empty_for_empty_output(self):
        """get_tracked_files_at_commit() returns empty list when git returns no output."""
        with patch("autocode.core.vcs.git.git") as mock_git:
            mock_git.return_value = ""

            from autocode.core.vcs.git import get_tracked_files_at_commit

            result = get_tracked_files_at_commit("abc123", ".py")

        assert result == []

    def test_calls_git_ls_tree(self):
        """get_tracked_files_at_commit() calls git ls-tree -r --name-only <commit>."""
        with patch("autocode.core.vcs.git.git") as mock_git:
            mock_git.return_value = ""

            from autocode.core.vcs.git import get_tracked_files_at_commit

            get_tracked_files_at_commit("abc123", ".py")

        mock_git.assert_called_once_with(
            "ls-tree", "-r", "--name-only", "abc123", cwd="."
        )

    def test_returns_empty_when_no_extensions_given(self):
        """get_tracked_files_at_commit() returns empty list when no extensions are requested."""
        with patch("autocode.core.vcs.git.git") as mock_git:
            from autocode.core.vcs.git import get_tracked_files_at_commit

            result = get_tracked_files_at_commit("abc123")

        mock_git.assert_not_called()
        assert result == []

    def test_passes_cwd_to_git(self):
        """get_tracked_files_at_commit() passes cwd parameter to git helper."""
        with patch("autocode.core.vcs.git.git") as mock_git:
            mock_git.return_value = "src/main.py"

            from autocode.core.vcs.git import get_tracked_files_at_commit

            get_tracked_files_at_commit("abc123", ".py", cwd="/tmp/repo")

        mock_git.assert_called_once_with(
            "ls-tree", "-r", "--name-only", "abc123", cwd="/tmp/repo"
        )


# ==============================================================================
# TestGetTrackedFiles — multi-extension
# ==============================================================================


class TestGetTrackedFiles:
    """Tests for get_tracked_files() — list git-tracked files by extension."""

    def test_returns_py_files(self):
        """get_tracked_files('.py') returns Python files from git ls-files."""
        with patch("autocode.core.vcs.git.subprocess.run") as mock_run:
            mock_run.return_value.stdout = "src/main.py\nsrc/utils.py\ntests/test_main.py\n"
            mock_run.return_value.returncode = 0

            from autocode.core.vcs.git import get_tracked_files

            result = get_tracked_files(".py")

        assert result == ["src/main.py", "src/utils.py", "tests/test_main.py"]

    def test_returns_py_and_js_files(self):
        """get_tracked_files('.py', '.js') returns both Python and JS files."""
        with patch("autocode.core.vcs.git.subprocess.run") as mock_run:
            # git ls-files with multiple patterns returns all matching files
            mock_run.return_value.stdout = (
                "src/main.py\nsrc/app.js\nlib/utils.py\nlib/helpers.js\n"
            )
            mock_run.return_value.returncode = 0

            from autocode.core.vcs.git import get_tracked_files

            result = get_tracked_files(".py", ".js")

        assert "src/main.py" in result
        assert "src/app.js" in result
        assert "lib/utils.py" in result
        assert "lib/helpers.js" in result

    def test_returns_empty_list_on_no_output(self):
        """get_tracked_files() returns empty list when git ls-files returns nothing."""
        with patch("autocode.core.vcs.git.subprocess.run") as mock_run:
            mock_run.return_value.stdout = ""
            mock_run.return_value.returncode = 0

            from autocode.core.vcs.git import get_tracked_files

            result = get_tracked_files(".py")

        assert result == []

    def test_filters_by_extension(self):
        """get_tracked_files() only returns files matching requested extensions."""
        with patch("autocode.core.vcs.git.subprocess.run") as mock_run:
            # Simulate git returning files (the actual filtering is in the function)
            mock_run.return_value.stdout = "a.py\nb.js\nc.py\nd.txt\n"
            mock_run.return_value.returncode = 0

            from autocode.core.vcs.git import get_tracked_files

            result = get_tracked_files(".py")

        assert "a.py" in result
        assert "c.py" in result
        assert "b.js" not in result
        assert "d.txt" not in result

    def test_passes_cwd(self):
        """get_tracked_files() passes cwd parameter to subprocess."""
        with patch("autocode.core.vcs.git.subprocess.run") as mock_run:
            mock_run.return_value.stdout = "f.py\n"
            mock_run.return_value.returncode = 0

            from autocode.core.vcs.git import get_tracked_files

            get_tracked_files(".py", cwd="/tmp/repo")

        mock_run.assert_called_once()
        assert mock_run.call_args.kwargs.get("cwd") == "/tmp/repo" or \
            mock_run.call_args[1].get("cwd") == "/tmp/repo"
