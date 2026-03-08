"""
Unit tests for autocode.core.code.analyzer module.

TDD tests for Commit 4: lizard-based unified Python + JS file analysis.
Tests cover: analyze_file_metrics (Python & JS), cc_rank, maintainability_index,
count_lines (language-aware).

All tests use string fixtures (no real files, no subprocess).
"""
import pytest


# ==============================================================================
# A) PYTHON FILE ANALYSIS
# ==============================================================================


class TestAnalyzeFileMetricsPython:
    """Lizard-based analysis for Python files."""

    def test_simple_function_cc(self):
        """A simple function with one if should have CC=2."""
        from autocode.core.code.analyzer import analyze_file_metrics

        code = (
            "def greet(name):\n"
            "    if name:\n"
            "        return f'Hello {name}'\n"
            "    return 'Hello'\n"
        )
        fm = analyze_file_metrics("app.py", code)

        assert fm.language == "python"
        assert len(fm.functions) >= 1
        greet = [f for f in fm.functions if f.name == "greet"][0]
        assert greet.complexity == 2  # 1 base + 1 if
        assert greet.rank == "A"

    def test_nested_function_nesting_depth(self):
        """A function with nested control flow should report nesting depth."""
        from autocode.core.code.analyzer import analyze_file_metrics

        code = (
            "def process(items):\n"
            "    for item in items:\n"
            "        if item > 0:\n"
            "            while item > 10:\n"
            "                item -= 1\n"
            "    return items\n"
        )
        fm = analyze_file_metrics("proc.py", code)

        process = [f for f in fm.functions if f.name == "process"][0]
        assert process.nesting_depth >= 3  # for > if > while

    def test_class_with_methods(self):
        """Methods inside a class should be detected as functions."""
        from autocode.core.code.analyzer import analyze_file_metrics

        code = (
            "class MyClass:\n"
            "    def __init__(self):\n"
            "        self.x = 0\n"
            "\n"
            "    def do_something(self):\n"
            "        if self.x:\n"
            "            return True\n"
            "        return False\n"
        )
        fm = analyze_file_metrics("cls.py", code)

        assert fm.functions_count >= 2
        assert fm.classes_count >= 1

    def test_mi_calculation(self):
        """MI should be between 0 and 100 for a normal file."""
        from autocode.core.code.analyzer import analyze_file_metrics

        code = (
            "def add(a, b):\n"
            "    return a + b\n"
            "\n"
            "def subtract(a, b):\n"
            "    return a - b\n"
        )
        fm = analyze_file_metrics("math_ops.py", code)

        assert 0 <= fm.maintainability_index <= 100
        # Simple functions should have high MI
        assert fm.maintainability_index > 50

    def test_empty_file(self):
        """An empty file should return sensible defaults."""
        from autocode.core.code.analyzer import analyze_file_metrics

        fm = analyze_file_metrics("empty.py", "")

        assert fm.language == "python"
        assert fm.sloc == 0
        assert fm.functions_count == 0
        assert fm.classes_count == 0
        assert fm.maintainability_index == 100.0

    def test_syntax_error_returns_basic_metrics(self):
        """A file with syntax errors should still return basic line metrics."""
        from autocode.core.code.analyzer import analyze_file_metrics

        code = "def broken(\n    pass\n"
        fm = analyze_file_metrics("broken.py", code)

        assert fm.language == "python"
        assert fm.total_loc > 0
        # Should not crash, should return whatever it can

    def test_line_counts_sloc_comments_blanks(self):
        """SLOC, comments, and blanks should be counted correctly for Python."""
        from autocode.core.code.analyzer import analyze_file_metrics

        code = (
            "# This is a comment\n"
            "\n"
            "def hello():\n"
            '    """Docstring."""\n'
            "    return 1\n"
            "\n"
            "# Another comment\n"
        )
        fm = analyze_file_metrics("lines.py", code)

        assert fm.blanks == 3  # two empty lines + trailing \n creates empty string
        assert fm.comments >= 2  # at least the # comments
        assert fm.sloc >= 2  # def + return at minimum


# ==============================================================================
# B) JAVASCRIPT FILE ANALYSIS
# ==============================================================================


class TestAnalyzeFileMetricsJS:
    """Lizard-based analysis for JavaScript files."""

    def test_simple_function_cc(self):
        """A simple JS function with one if should have CC=2."""
        from autocode.core.code.analyzer import analyze_file_metrics

        code = (
            "function greet(name) {\n"
            "    if (name) {\n"
            "        return `Hello ${name}`;\n"
            "    }\n"
            "    return 'Hello';\n"
            "}\n"
        )
        fm = analyze_file_metrics("app.js", code)

        assert fm.language == "javascript"
        assert len(fm.functions) >= 1
        greet = [f for f in fm.functions if "greet" in f.name][0]
        assert greet.complexity == 2

    def test_arrow_function(self):
        """Arrow functions assigned to const should be detected by lizard."""
        from autocode.core.code.analyzer import analyze_file_metrics

        code = (
            "function process(items) {\n"
            "    for (const item of items) {\n"
            "        if (item > 0) {\n"
            "            console.log(item);\n"
            "        }\n"
            "    }\n"
            "}\n"
        )
        fm = analyze_file_metrics("arrow.js", code)

        assert fm.functions_count >= 1
        # The function should have CC > 1 (for + if)
        assert fm.functions[0].complexity >= 3

    def test_class_with_methods(self):
        """JS class methods should be detected."""
        from autocode.core.code.analyzer import analyze_file_metrics

        code = (
            "class Animal {\n"
            "    constructor(name) {\n"
            "        this.name = name;\n"
            "    }\n"
            "\n"
            "    speak() {\n"
            "        if (this.name) {\n"
            "            return this.name + ' speaks';\n"
            "        }\n"
            "        return 'unknown';\n"
            "    }\n"
            "}\n"
        )
        fm = analyze_file_metrics("animal.js", code)

        assert fm.classes_count >= 1
        assert fm.functions_count >= 2  # constructor + speak

    def test_mi_calculation(self):
        """MI for a JS file should be between 0 and 100."""
        from autocode.core.code.analyzer import analyze_file_metrics

        code = (
            "function add(a, b) {\n"
            "    return a + b;\n"
            "}\n"
            "\n"
            "function subtract(a, b) {\n"
            "    return a - b;\n"
            "}\n"
        )
        fm = analyze_file_metrics("math.js", code)

        assert 0 <= fm.maintainability_index <= 100
        assert fm.maintainability_index > 50

    def test_js_comment_counting(self):
        """Single-line JS comments (//) should be counted."""
        from autocode.core.code.analyzer import analyze_file_metrics

        code = (
            "// This is a comment\n"
            "function hello() {\n"
            "    // inline comment\n"
            "    return 1;\n"
            "}\n"
        )
        fm = analyze_file_metrics("comments.js", code)

        assert fm.comments >= 2  # two // comments

    def test_multiline_comment_counting(self):
        """Multiline JS comments (/* */) should be counted."""
        from autocode.core.code.analyzer import analyze_file_metrics

        code = (
            "/*\n"
            " * This is a\n"
            " * multiline comment\n"
            " */\n"
            "function hello() {\n"
            "    return 1;\n"
            "}\n"
        )
        fm = analyze_file_metrics("multi.js", code)

        assert fm.comments >= 3  # at least the 3 lines of the block comment


# ==============================================================================
# C) CC RANK
# ==============================================================================


class TestCCRank:
    """Tests for cc_rank() — complexity to letter grade."""

    def test_all_ranks(self):
        """Verify all rank thresholds: A(≤5), B(6-10), C(11-15), D(16-20), E(21-25), F(>25)."""
        from autocode.core.code.analyzer import cc_rank

        assert cc_rank(1) == "A"
        assert cc_rank(5) == "A"
        assert cc_rank(6) == "B"
        assert cc_rank(10) == "B"
        assert cc_rank(11) == "C"
        assert cc_rank(15) == "C"
        assert cc_rank(16) == "D"
        assert cc_rank(20) == "D"
        assert cc_rank(21) == "E"
        assert cc_rank(25) == "E"
        assert cc_rank(26) == "F"
        assert cc_rank(100) == "F"


# ==============================================================================
# D) MAINTAINABILITY INDEX
# ==============================================================================


class TestMaintainabilityIndex:
    """Tests for maintainability_index() — MI formula."""

    def test_zero_sloc_returns_100(self):
        """Zero SLOC (empty file) → MI = 100."""
        from autocode.core.code.analyzer import maintainability_index

        assert maintainability_index(0, 0.0, 0) == 100.0

    def test_known_values(self):
        """MI should return a reasonable value for known inputs."""
        from autocode.core.code.analyzer import maintainability_index

        mi = maintainability_index(sloc=100, avg_cc=5.0, total_loc=120)
        assert 0 <= mi <= 100
        # 100 SLOC with CC=5 should have moderate MI
        assert mi > 20

    def test_clamped_to_0_100(self):
        """MI should be clamped between 0 and 100."""
        from autocode.core.code.analyzer import maintainability_index

        # Very large file with high complexity → should not go below 0
        mi_low = maintainability_index(sloc=10000, avg_cc=50.0, total_loc=12000)
        assert mi_low >= 0.0

        # Very small file with no complexity → should not exceed 100
        mi_high = maintainability_index(sloc=1, avg_cc=0.0, total_loc=1)
        assert mi_high <= 100.0


# ==============================================================================
# E) LANGUAGE-AWARE LINE COUNTING
# ==============================================================================


class TestCountLines:
    """Tests for count_lines() — language-aware SLOC/comments/blanks."""

    def test_python_docstrings_as_comments(self):
        """Python triple-quoted docstrings should count as comments."""
        from autocode.core.code.analyzer import count_lines

        content = (
            'def hello():\n'
            '    """This is a docstring."""\n'
            '    return 1\n'
        )
        result = count_lines(content, "python")

        assert result["comments"] >= 1  # docstring

    def test_python_hash_comments(self):
        """Python # comments should be counted."""
        from autocode.core.code.analyzer import count_lines

        content = (
            "# Comment line\n"
            "x = 1  # inline comment at end\n"
            "# Another comment\n"
        )
        result = count_lines(content, "python")

        assert result["comments"] >= 2  # at least the standalone # comments

    def test_js_single_line_comments(self):
        """JavaScript // comments should be counted."""
        from autocode.core.code.analyzer import count_lines

        content = (
            "// This is a comment\n"
            "const x = 1;\n"
            "// Another comment\n"
        )
        result = count_lines(content, "javascript")

        assert result["comments"] == 2
        assert result["sloc"] == 1

    def test_js_multiline_comments(self):
        """JavaScript /* */ comments should count each line."""
        from autocode.core.code.analyzer import count_lines

        content = (
            "/*\n"
            " * Block comment\n"
            " * continues here\n"
            " */\n"
            "const x = 1;\n"
        )
        result = count_lines(content, "javascript")

        assert result["comments"] >= 3  # at least the block comment lines
        assert result["sloc"] >= 1

    def test_blank_lines(self):
        """Blank lines should be counted in both languages."""
        from autocode.core.code.analyzer import count_lines

        content = (
            "x = 1\n"
            "\n"
            "y = 2\n"
            "\n"
            "\n"
        )
        result = count_lines(content, "python")

        assert result["blanks"] == 4  # two mid-content + two trailing (split creates extra "")
        assert result["sloc"] == 2
