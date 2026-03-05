"""
Tests for reviewer.py — compute_review_metrics.

RED phase: These tests define the expected behavior for computing
before/after metrics of changed files during plan review.

Uses real git repos in tmp_path for integration-like testing
(same pattern as _analyze_commit in metrics.py).
"""

import os
import subprocess
import pytest

from autocode.core.planning.reviewer import compute_review_metrics
from autocode.core.planning.models import ReviewFileMetrics


def _git(tmp_path, *args: str) -> str:
    """Run a git command in the given directory."""
    result = subprocess.run(
        ["git"] + list(args),
        capture_output=True, text=True, check=False,
        cwd=str(tmp_path),
    )
    return result.stdout.strip()


def _init_repo(tmp_path):
    """Initialize a git repo with an initial commit."""
    _git(tmp_path, "init")
    _git(tmp_path, "config", "user.email", "test@test.com")
    _git(tmp_path, "config", "user.name", "Test")
    # Initial empty commit so HEAD exists
    _git(tmp_path, "commit", "--allow-empty", "-m", "initial")


class TestComputeReviewMetrics:
    """Tests for compute_review_metrics()."""

    def test_computes_metrics_for_python_files(self, tmp_path):
        """Crea un .py, lo commitea, lo modifica en disco → before/after/deltas correctos."""
        _init_repo(tmp_path)

        # Create a simple Python file and commit it
        py_file = tmp_path / "module.py"
        py_file.write_text(
            "def hello():\n"
            "    return 'hello'\n"
        )
        _git(tmp_path, "add", "module.py")
        _git(tmp_path, "commit", "-m", "add module")

        # Modify the file on disk (not committed)
        py_file.write_text(
            "def hello():\n"
            "    return 'hello'\n"
            "\n"
            "def goodbye():\n"
            "    if True:\n"
            "        return 'bye'\n"
            "    return 'nope'\n"
        )

        # Compute metrics — parent_commit=HEAD means "before" is the committed version
        results = compute_review_metrics(
            files_changed=["module.py"],
            parent_commit="HEAD",
            repo_path=str(tmp_path),
        )

        assert len(results) == 1
        r = results[0]
        assert isinstance(r, ReviewFileMetrics)
        assert r.path == "module.py"

        # Before should have metrics from the committed version (1 function)
        assert r.before != {}
        assert r.before["functions_count"] == 1
        assert r.before["sloc"] > 0

        # After should have metrics from the modified version (2 functions)
        assert r.after != {}
        assert r.after["functions_count"] == 2
        assert r.after["sloc"] > r.before["sloc"]

        # Deltas should reflect the changes
        assert "delta_sloc" in r.deltas
        assert r.deltas["delta_sloc"] > 0
        assert "delta_functions_count" in r.deltas
        assert r.deltas["delta_functions_count"] == 1

    def test_skips_non_python_files(self, tmp_path):
        """Archivos no-.py se ignoran → retorna lista vacía."""
        _init_repo(tmp_path)

        results = compute_review_metrics(
            files_changed=["readme.md", "style.css", "app.js", "data.json"],
            parent_commit="HEAD",
            repo_path=str(tmp_path),
        )

        assert results == []

    def test_handles_new_file_no_before(self, tmp_path):
        """Archivo .py nuevo (no existe en parent_commit) → before={}, after={métricas}."""
        _init_repo(tmp_path)

        # Create a new .py file on disk (never committed)
        new_file = tmp_path / "new_module.py"
        new_file.write_text(
            "def new_func():\n"
            "    return 42\n"
        )

        results = compute_review_metrics(
            files_changed=["new_module.py"],
            parent_commit="HEAD",
            repo_path=str(tmp_path),
        )

        assert len(results) == 1
        r = results[0]
        assert r.path == "new_module.py"
        assert r.before == {}
        assert r.after != {}
        assert r.after["functions_count"] == 1
        assert r.after["sloc"] > 0
        # Deltas should reflect all-new
        assert r.deltas["delta_sloc"] == r.after["sloc"]

    def test_handles_deleted_file_no_after(self, tmp_path):
        """Archivo .py eliminado (existía en parent_commit, ya no en disco) → before={métricas}, after={}."""
        _init_repo(tmp_path)

        # Create and commit a file
        py_file = tmp_path / "to_delete.py"
        py_file.write_text(
            "def doomed():\n"
            "    return 'gone'\n"
        )
        _git(tmp_path, "add", "to_delete.py")
        _git(tmp_path, "commit", "-m", "add file to delete")

        # Delete the file from disk
        py_file.unlink()

        results = compute_review_metrics(
            files_changed=["to_delete.py"],
            parent_commit="HEAD",
            repo_path=str(tmp_path),
        )

        assert len(results) == 1
        r = results[0]
        assert r.path == "to_delete.py"
        assert r.before != {}
        assert r.before["functions_count"] == 1
        assert r.before["sloc"] > 0
        assert r.after == {}
        # Deltas should be negative
        assert r.deltas["delta_sloc"] == -r.before["sloc"]

    def test_returns_empty_for_no_files(self, tmp_path):
        """Sin archivos → lista vacía."""
        _init_repo(tmp_path)

        results = compute_review_metrics(
            files_changed=[],
            parent_commit="HEAD",
            repo_path=str(tmp_path),
        )

        assert results == []

    def test_uses_git_show_for_before_content(self, tmp_path):
        """Verifica que usa git show HEAD:path para el estado 'before'.

        We commit version A, then version B. After committing B,
        we ask for metrics with parent_commit=HEAD~1.
        The 'before' should reflect version A's metrics.
        """
        _init_repo(tmp_path)

        # Version A: 1 function
        py_file = tmp_path / "evolving.py"
        py_file.write_text("def v1():\n    pass\n")
        _git(tmp_path, "add", "evolving.py")
        _git(tmp_path, "commit", "-m", "version A")

        # Version B: 2 functions (committed)
        py_file.write_text("def v1():\n    pass\n\ndef v2():\n    pass\n")
        _git(tmp_path, "add", "evolving.py")
        _git(tmp_path, "commit", "-m", "version B")

        # Version C: 3 functions (on disk, not committed)
        py_file.write_text(
            "def v1():\n    pass\n\ndef v2():\n    pass\n\ndef v3():\n    pass\n"
        )

        # Ask with parent_commit=HEAD~1 → before should be version A (1 func)
        results = compute_review_metrics(
            files_changed=["evolving.py"],
            parent_commit="HEAD~1",
            repo_path=str(tmp_path),
        )

        assert len(results) == 1
        r = results[0]
        assert r.before["functions_count"] == 1  # version A
        assert r.after["functions_count"] == 3   # version C (disk)

    def test_mixed_python_and_non_python(self, tmp_path):
        """Mezcla de archivos .py y no-.py → solo procesa los .py."""
        _init_repo(tmp_path)

        py_file = tmp_path / "real.py"
        py_file.write_text("x = 1\n")

        results = compute_review_metrics(
            files_changed=["real.py", "readme.md", "config.yaml"],
            parent_commit="HEAD",
            repo_path=str(tmp_path),
        )

        assert len(results) == 1
        assert results[0].path == "real.py"

    def test_metrics_dict_keys(self, tmp_path):
        """Verifica que before/after dicts contienen las claves de métricas esperadas."""
        _init_repo(tmp_path)

        py_file = tmp_path / "check_keys.py"
        py_file.write_text("def func():\n    return 1\n")
        _git(tmp_path, "add", "check_keys.py")
        _git(tmp_path, "commit", "-m", "add file")

        # Modify slightly
        py_file.write_text("def func():\n    return 2\n\ndef func2():\n    return 3\n")

        results = compute_review_metrics(
            files_changed=["check_keys.py"],
            parent_commit="HEAD",
            repo_path=str(tmp_path),
        )

        expected_keys = {
            "sloc", "avg_complexity", "max_complexity",
            "maintainability_index", "functions_count",
            "classes_count", "max_nesting",
        }

        r = results[0]
        assert expected_keys.issubset(set(r.before.keys()))
        assert expected_keys.issubset(set(r.after.keys()))

        # Deltas should have delta_ prefixed versions
        for key in expected_keys:
            assert f"delta_{key}" in r.deltas
