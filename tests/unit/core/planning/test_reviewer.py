"""
Tests for reviewer.py — compute_review_metrics + auto_review.

RED phase: These tests define the expected behavior for computing
before/after metrics of changed files during plan review,
and for auto-review with quality gates.

Uses real git repos in tmp_path for integration-like testing
(same pattern as _analyze_commit in metrics.py).
"""

import os
import subprocess
import pytest

from autocode.core.planning.reviewer import (
    compute_review_metrics,
    auto_review,
    _evaluate_quality_gates,
    QUALITY_GATES,
)
from autocode.core.planning.models import ReviewFileMetrics, ReviewResult


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


# ==============================================================================
# AUTO-REVIEW TESTS
# ==============================================================================


class TestAutoReview:
    """Tests for auto_review() — end-to-end auto-review with quality gates."""

    def test_approves_when_all_gates_pass(self, tmp_path):
        """Cambios limpios y simples → approved."""
        _init_repo(tmp_path)

        py_file = tmp_path / "clean.py"
        py_file.write_text("def hello():\n    return 'hello'\n")
        _git(tmp_path, "add", "clean.py")
        _git(tmp_path, "commit", "-m", "add clean")

        # Small clean change — add another simple function
        py_file.write_text(
            "def hello():\n"
            "    return 'hello'\n"
            "\n"
            "def world():\n"
            "    return 'world'\n"
        )

        result = auto_review(
            files_changed=["clean.py"],
            parent_commit="HEAD",
            repo_path=str(tmp_path),
        )

        assert isinstance(result, ReviewResult)
        assert result.mode == "auto"
        assert result.verdict == "approved"
        assert result.reviewed_by == "auto"
        assert result.reviewed_at != ""

    def test_rejects_when_complexity_increases_significantly(self, tmp_path):
        """avg_complexity aumenta >30% → rejected con issue sobre complejidad."""
        _init_repo(tmp_path)

        # Start with a moderately complex function (CC ~3)
        py_file = tmp_path / "complex.py"
        py_file.write_text(
            "def process(x):\n"
            "    if x > 0:\n"
            "        for i in range(x):\n"
            "            if i % 2 == 0:\n"
            "                print(i)\n"
        )
        _git(tmp_path, "add", "complex.py")
        _git(tmp_path, "commit", "-m", "add complex")

        # Make it much more complex (many nested branches)
        py_file.write_text(
            "def process(x):\n"
            "    if x > 0:\n"
            "        for i in range(x):\n"
            "            if i % 2 == 0:\n"
            "                if i % 3 == 0:\n"
            "                    if i % 5 == 0:\n"
            "                        for j in range(i):\n"
            "                            if j > 0:\n"
            "                                if j % 2 == 0:\n"
            "                                    print(i, j)\n"
            "                                elif j % 3 == 0:\n"
            "                                    print('three')\n"
            "                            elif j == 0:\n"
            "                                print('zero')\n"
            "                    elif i % 7 == 0:\n"
            "                        print('seven')\n"
            "                elif i % 4 == 0:\n"
            "                    print('four')\n"
            "            elif i % 5 == 0:\n"
            "                print('five')\n"
        )

        result = auto_review(
            files_changed=["complex.py"],
            parent_commit="HEAD",
            repo_path=str(tmp_path),
        )

        assert result.verdict == "rejected"
        assert result.mode == "auto"
        # Should have issues mentioning complexity
        assert len(result.issues) > 0
        assert any("complex" in issue.lower() for issue in result.issues)

    def test_rejects_when_mi_drops_below_threshold(self, tmp_path):
        """MI cae bajo 40 → rejected con issue sobre mantenibilidad."""
        _init_repo(tmp_path)

        py_file = tmp_path / "maintainable.py"
        py_file.write_text("def simple():\n    return 1\n")
        _git(tmp_path, "add", "maintainable.py")
        _git(tmp_path, "commit", "-m", "add maintainable")

        # Create a very long, complex file that drops MI below 40
        # Long function with many branches → low MI
        lines = ["def monster(a, b, c, d, e, f, g, h):"]
        for i in range(60):
            indent = "    "
            lines.append(f"{indent}if a == {i}:")
            lines.append(f"{indent}    for x_{i} in range({i}):")
            lines.append(f"{indent}        if x_{i} > {i}:")
            lines.append(f"{indent}            while b > {i}:")
            lines.append(f"{indent}                if c and d or e:")
            lines.append(f"{indent}                    result_{i} = a + b + c + {i}")
        lines.append("    return 0")
        py_file.write_text("\n".join(lines) + "\n")

        result = auto_review(
            files_changed=["maintainable.py"],
            parent_commit="HEAD",
            repo_path=str(tmp_path),
        )

        assert result.verdict == "rejected"
        assert any("maintainab" in issue.lower() for issue in result.issues)

    def test_warns_on_moderate_degradation(self, tmp_path):
        """Pequeña degradación (debajo del threshold) → approved con suggestions."""
        _init_repo(tmp_path)

        py_file = tmp_path / "moderate.py"
        py_file.write_text(
            "def func_a():\n"
            "    return 1\n"
            "\n"
            "def func_b():\n"
            "    return 2\n"
        )
        _git(tmp_path, "add", "moderate.py")
        _git(tmp_path, "commit", "-m", "add moderate")

        # Add slightly more complexity but still within gates
        py_file.write_text(
            "def func_a():\n"
            "    if True:\n"
            "        return 1\n"
            "    return 0\n"
            "\n"
            "def func_b():\n"
            "    return 2\n"
            "\n"
            "def func_c():\n"
            "    if True:\n"
            "        return 3\n"
            "    return 0\n"
        )

        result = auto_review(
            files_changed=["moderate.py"],
            parent_commit="HEAD",
            repo_path=str(tmp_path),
        )

        assert result.verdict == "approved"
        # May have suggestions about the slight increase
        # (the key point is it's not rejected)

    def test_approves_empty_metrics(self, tmp_path):
        """Sin archivos .py → approved (nada que verificar)."""
        _init_repo(tmp_path)

        result = auto_review(
            files_changed=["readme.md", "config.yaml"],
            parent_commit="HEAD",
            repo_path=str(tmp_path),
        )

        assert result.verdict == "approved"
        assert result.mode == "auto"
        assert result.file_metrics == []
        assert all(v is True for v in result.quality_gates.values())

    def test_quality_gates_dict_populated(self, tmp_path):
        """quality_gates contiene las 4 gates con valores boolean."""
        _init_repo(tmp_path)

        py_file = tmp_path / "gated.py"
        py_file.write_text("def f():\n    return 1\n")
        _git(tmp_path, "add", "gated.py")
        _git(tmp_path, "commit", "-m", "add gated")

        py_file.write_text("def f():\n    return 2\n\ndef g():\n    return 3\n")

        result = auto_review(
            files_changed=["gated.py"],
            parent_commit="HEAD",
            repo_path=str(tmp_path),
        )

        expected_gates = {"complexity_increase", "mi_minimum", "max_nesting", "sloc_growth"}
        assert expected_gates == set(result.quality_gates.keys())
        for gate_name, passed in result.quality_gates.items():
            assert isinstance(passed, bool), f"Gate {gate_name} should be bool, got {type(passed)}"

    def test_plan_review_result_fields(self, tmp_path):
        """ReviewResult contiene todos los campos esperados."""
        _init_repo(tmp_path)

        py_file = tmp_path / "fields.py"
        py_file.write_text("x = 1\n")
        _git(tmp_path, "add", "fields.py")
        _git(tmp_path, "commit", "-m", "add fields")

        py_file.write_text("x = 1\ny = 2\n")

        result = auto_review(
            files_changed=["fields.py"],
            parent_commit="HEAD",
            repo_path=str(tmp_path),
        )

        assert hasattr(result, "mode")
        assert hasattr(result, "verdict")
        assert hasattr(result, "summary")
        assert hasattr(result, "issues")
        assert hasattr(result, "suggestions")
        assert hasattr(result, "file_metrics")
        assert hasattr(result, "quality_gates")
        assert hasattr(result, "reviewed_at")
        assert hasattr(result, "reviewed_by")
        assert isinstance(result.summary, str)
        assert result.summary != ""  # Should always have a summary


# ==============================================================================
# QUALITY GATES UNIT TESTS (pure, no git)
# ==============================================================================


class TestEvaluateQualityGates:
    """Tests for _evaluate_quality_gates() — unit tests with hand-built metrics."""

    def test_complexity_gate_fails_on_large_increase(self):
        """avg_complexity aumenta >30% → complexity_increase gate falla."""
        metrics = [
            ReviewFileMetrics(
                path="bad.py",
                before={"avg_complexity": 5.0, "maintainability_index": 70.0,
                        "max_nesting": 3, "sloc": 50},
                after={"avg_complexity": 7.0, "maintainability_index": 65.0,
                       "max_nesting": 3, "sloc": 55},
                deltas={"delta_avg_complexity": 2.0, "delta_maintainability_index": -5.0,
                        "delta_max_nesting": 0, "delta_sloc": 5},
            )
        ]

        gates, issues, suggestions = _evaluate_quality_gates(metrics)

        assert gates["complexity_increase"] is False  # 5→7 = 40% increase > 30%
        assert any("complex" in i.lower() for i in issues)

    def test_complexity_gate_passes_on_small_increase(self):
        """avg_complexity aumenta <30% → complexity_increase gate pasa."""
        metrics = [
            ReviewFileMetrics(
                path="ok.py",
                before={"avg_complexity": 5.0, "maintainability_index": 70.0,
                        "max_nesting": 3, "sloc": 50},
                after={"avg_complexity": 6.0, "maintainability_index": 68.0,
                       "max_nesting": 3, "sloc": 52},
                deltas={"delta_avg_complexity": 1.0, "delta_maintainability_index": -2.0,
                        "delta_max_nesting": 0, "delta_sloc": 2},
            )
        ]

        gates, issues, suggestions = _evaluate_quality_gates(metrics)

        assert gates["complexity_increase"] is True  # 5→6 = 20% < 30%

    def test_maintainability_gate_fails_below_threshold(self):
        """MI cae bajo 40 → mi_minimum gate falla."""
        metrics = [
            ReviewFileMetrics(
                path="ugly.py",
                before={"avg_complexity": 10.0, "maintainability_index": 50.0,
                        "max_nesting": 4, "sloc": 200},
                after={"avg_complexity": 12.0, "maintainability_index": 35.0,
                       "max_nesting": 5, "sloc": 250},
                deltas={"delta_avg_complexity": 2.0, "delta_maintainability_index": -15.0,
                        "delta_max_nesting": 1, "delta_sloc": 50},
            )
        ]

        gates, issues, suggestions = _evaluate_quality_gates(metrics)

        assert gates["mi_minimum"] is False
        assert any("maintainab" in i.lower() for i in issues)

    def test_maintainability_gate_passes_above_threshold(self):
        """MI sobre 40 → mi_minimum gate pasa."""
        metrics = [
            ReviewFileMetrics(
                path="decent.py",
                before={"avg_complexity": 3.0, "maintainability_index": 70.0,
                        "max_nesting": 2, "sloc": 30},
                after={"avg_complexity": 4.0, "maintainability_index": 60.0,
                       "max_nesting": 3, "sloc": 40},
                deltas={"delta_avg_complexity": 1.0, "delta_maintainability_index": -10.0,
                        "delta_max_nesting": 1, "delta_sloc": 10},
            )
        ]

        gates, issues, suggestions = _evaluate_quality_gates(metrics)

        assert gates["mi_minimum"] is True

    def test_max_nesting_gate_fails_above_threshold(self):
        """max_nesting > 6 → max_nesting gate falla."""
        metrics = [
            ReviewFileMetrics(
                path="nested.py",
                before={"avg_complexity": 5.0, "maintainability_index": 60.0,
                        "max_nesting": 4, "sloc": 80},
                after={"avg_complexity": 8.0, "maintainability_index": 50.0,
                       "max_nesting": 7, "sloc": 100},
                deltas={"delta_avg_complexity": 3.0, "delta_maintainability_index": -10.0,
                        "delta_max_nesting": 3, "delta_sloc": 20},
            )
        ]

        gates, issues, suggestions = _evaluate_quality_gates(metrics)

        assert gates["max_nesting"] is False
        assert any("nesting" in i.lower() for i in issues)

    def test_max_nesting_gate_passes_within_threshold(self):
        """max_nesting ≤ 6 → max_nesting gate pasa."""
        metrics = [
            ReviewFileMetrics(
                path="flat.py",
                before={"avg_complexity": 3.0, "maintainability_index": 70.0,
                        "max_nesting": 2, "sloc": 30},
                after={"avg_complexity": 4.0, "maintainability_index": 65.0,
                       "max_nesting": 4, "sloc": 40},
                deltas={"delta_avg_complexity": 1.0, "delta_maintainability_index": -5.0,
                        "delta_max_nesting": 2, "delta_sloc": 10},
            )
        ]

        gates, issues, suggestions = _evaluate_quality_gates(metrics)

        assert gates["max_nesting"] is True

    def test_sloc_growth_gate_fails_on_large_growth(self):
        """SLOC crece >50% → sloc_growth gate falla."""
        metrics = [
            ReviewFileMetrics(
                path="bloated.py",
                before={"avg_complexity": 3.0, "maintainability_index": 70.0,
                        "max_nesting": 2, "sloc": 100},
                after={"avg_complexity": 3.0, "maintainability_index": 65.0,
                       "max_nesting": 2, "sloc": 160},
                deltas={"delta_avg_complexity": 0.0, "delta_maintainability_index": -5.0,
                        "delta_max_nesting": 0, "delta_sloc": 60},
            )
        ]

        gates, issues, suggestions = _evaluate_quality_gates(metrics)

        assert gates["sloc_growth"] is False  # 100→160 = 60% growth > 50%
        assert any("sloc" in i.lower() or "growth" in i.lower() for i in issues)

    def test_sloc_growth_gate_passes_on_moderate_growth(self):
        """SLOC crece <50% → sloc_growth gate pasa."""
        metrics = [
            ReviewFileMetrics(
                path="growing.py",
                before={"avg_complexity": 3.0, "maintainability_index": 70.0,
                        "max_nesting": 2, "sloc": 100},
                after={"avg_complexity": 3.0, "maintainability_index": 68.0,
                       "max_nesting": 2, "sloc": 130},
                deltas={"delta_avg_complexity": 0.0, "delta_maintainability_index": -2.0,
                        "delta_max_nesting": 0, "delta_sloc": 30},
            )
        ]

        gates, issues, suggestions = _evaluate_quality_gates(metrics)

        assert gates["sloc_growth"] is True  # 100→130 = 30% < 50%

    def test_all_gates_pass_for_clean_metrics(self):
        """Métricas limpias → todos los gates pasan, sin issues."""
        metrics = [
            ReviewFileMetrics(
                path="clean.py",
                before={"avg_complexity": 2.0, "maintainability_index": 80.0,
                        "max_nesting": 1, "sloc": 20},
                after={"avg_complexity": 2.5, "maintainability_index": 75.0,
                       "max_nesting": 2, "sloc": 25},
                deltas={"delta_avg_complexity": 0.5, "delta_maintainability_index": -5.0,
                        "delta_max_nesting": 1, "delta_sloc": 5},
            )
        ]

        gates, issues, suggestions = _evaluate_quality_gates(metrics)

        assert all(v is True for v in gates.values())
        assert len(issues) == 0

    def test_empty_metrics_all_gates_pass(self):
        """Sin métricas → todos los gates pasan."""
        gates, issues, suggestions = _evaluate_quality_gates([])

        assert all(v is True for v in gates.values())
        assert len(issues) == 0

    def test_new_file_no_before_skips_relative_gates(self):
        """Archivo nuevo (before={}) → gates relativos se saltan, absolutos se evalúan."""
        metrics = [
            ReviewFileMetrics(
                path="new.py",
                before={},
                after={"avg_complexity": 3.0, "maintainability_index": 70.0,
                       "max_nesting": 2, "sloc": 30},
                deltas={"delta_avg_complexity": 3.0, "delta_maintainability_index": 70.0,
                        "delta_max_nesting": 2, "delta_sloc": 30},
            )
        ]

        gates, issues, suggestions = _evaluate_quality_gates(metrics)

        # Relative gates (complexity_increase, sloc_growth) should pass for new files
        assert gates["complexity_increase"] is True
        assert gates["sloc_growth"] is True
        # Absolute gates should evaluate normally
        assert gates["mi_minimum"] is True  # 70 > 40
        assert gates["max_nesting"] is True  # 2 ≤ 6

    def test_multiple_files_worst_case_evaluated(self):
        """Con múltiples archivos, el peor caso determina cada gate."""
        metrics = [
            ReviewFileMetrics(
                path="good.py",
                before={"avg_complexity": 2.0, "maintainability_index": 80.0,
                        "max_nesting": 1, "sloc": 20},
                after={"avg_complexity": 2.5, "maintainability_index": 75.0,
                       "max_nesting": 2, "sloc": 25},
                deltas={"delta_avg_complexity": 0.5, "delta_maintainability_index": -5.0,
                        "delta_max_nesting": 1, "delta_sloc": 5},
            ),
            ReviewFileMetrics(
                path="bad.py",
                before={"avg_complexity": 5.0, "maintainability_index": 50.0,
                        "max_nesting": 4, "sloc": 100},
                after={"avg_complexity": 5.0, "maintainability_index": 35.0,
                       "max_nesting": 8, "sloc": 100},
                deltas={"delta_avg_complexity": 0.0, "delta_maintainability_index": -15.0,
                        "delta_max_nesting": 4, "delta_sloc": 0},
            ),
        ]

        gates, issues, suggestions = _evaluate_quality_gates(metrics)

        # bad.py has MI=35 < 40 and nesting=8 > 6
        assert gates["mi_minimum"] is False
        assert gates["max_nesting"] is False
        # But good.py metrics shouldn't trigger complexity/sloc gates
        assert gates["complexity_increase"] is True
        assert gates["sloc_growth"] is True
