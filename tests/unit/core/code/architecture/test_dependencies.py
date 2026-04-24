"""Tests for _resolve_file_dependencies() — Python and JS."""
from unittest.mock import patch
from pathlib import Path


# ==============================================================================
# E) FILE DEPENDENCY RESOLUTION TESTS
# ==============================================================================


class TestResolveFileDependencies:
    """Tests for _resolve_file_dependencies() — AST-based import resolution."""

    def test_resolve_empty_files(self):
        """No files → no dependencies, no circulars."""
        from autocode.core.code.architecture import _resolve_file_dependencies

        deps, circulars = _resolve_file_dependencies([])
        assert deps == []
        assert circulars == []

    @patch("pathlib.Path.read_text")
    def test_resolve_only_stdlib_imports(self, mock_read):
        """Files importing only stdlib/third-party → no internal dependencies."""
        from autocode.core.code.architecture import _resolve_file_dependencies

        mock_read.return_value = (
            "import os\n"
            "import sys\n"
            "from pathlib import Path\n"
            "from typing import List\n"
            "import json\n"
        )
        deps, circulars = _resolve_file_dependencies(["myproject/app.py"])
        assert deps == []
        assert circulars == []

    def test_resolve_internal_from_import(self):
        """'from autocode.core.code.models import X' should produce FileDependency."""
        from autocode.core.code.architecture import _resolve_file_dependencies

        contents = {
            "autocode/core/code/architecture.py": (
                "from autocode.core.code.models import ArchitectureNode, FileDependency\n"
            ),
            "autocode/core/code/models.py": "class ArchitectureNode: pass\n",
        }
        files = list(contents.keys())

        def patched_read(self, *args, **kwargs):
            return contents.get(str(self), "")

        with patch.object(Path, "read_text", patched_read):
            deps, circulars = _resolve_file_dependencies(files)

        assert len(deps) == 1
        assert deps[0].source == "autocode/core/code/architecture.py"
        assert deps[0].target == "autocode/core/code/models.py"
        assert "ArchitectureNode" in deps[0].import_names
        assert "FileDependency" in deps[0].import_names

    @patch("pathlib.Path.read_text")
    def test_resolve_internal_import_statement(self, mock_read):
        """'import autocode.core.code.models' should resolve to file path."""
        from autocode.core.code.architecture import _resolve_file_dependencies

        contents = {
            "autocode/app.py": "import autocode.core.code.models\n",
            "autocode/core/code/models.py": "X = 1\n",
        }

        def patched_read(self, *args, **kwargs):
            return contents.get(str(self), "")

        with patch.object(Path, "read_text", patched_read):
            deps, circulars = _resolve_file_dependencies(list(contents.keys()))

        assert len(deps) == 1
        assert deps[0].source == "autocode/app.py"
        assert deps[0].target == "autocode/core/code/models.py"

    @patch("pathlib.Path.read_text")
    def test_resolve_package_import_to_init(self, mock_read):
        """'from autocode.core import code' should resolve to __init__.py."""
        from autocode.core.code.architecture import _resolve_file_dependencies

        contents = {
            "autocode/app.py": "from autocode.core import code\n",
            "autocode/core/__init__.py": "# core package\n",
            "autocode/core/code/__init__.py": "# code package\n",
        }

        def patched_read(self, *args, **kwargs):
            return contents.get(str(self), "")

        with patch.object(Path, "read_text", patched_read):
            deps, circulars = _resolve_file_dependencies(list(contents.keys()))

        assert len(deps) == 1
        assert deps[0].source == "autocode/app.py"
        assert deps[0].target == "autocode/core/__init__.py"

    @patch("pathlib.Path.read_text")
    def test_resolve_nonexistent_target_filtered(self, mock_read):
        """Import to a module not in the file list → filtered out."""
        from autocode.core.code.architecture import _resolve_file_dependencies

        contents = {
            "autocode/app.py": "from autocode.nonexistent import something\n",
        }

        def patched_read(self, *args, **kwargs):
            return contents.get(str(self), "")

        with patch.object(Path, "read_text", patched_read):
            deps, circulars = _resolve_file_dependencies(list(contents.keys()))

        assert deps == []

    @patch("pathlib.Path.read_text")
    def test_resolve_circular_detection(self, mock_read):
        """A imports B and B imports A → circular detected."""
        from autocode.core.code.architecture import _resolve_file_dependencies

        contents = {
            "pkg/a.py": "from pkg.b import X\n",
            "pkg/b.py": "from pkg.a import Y\n",
        }

        def patched_read(self, *args, **kwargs):
            return contents.get(str(self), "")

        with patch.object(Path, "read_text", patched_read):
            deps, circulars = _resolve_file_dependencies(list(contents.keys()))

        assert len(deps) == 2
        assert len(circulars) == 1
        pair = sorted(circulars[0])
        assert pair == ["pkg/a.py", "pkg/b.py"]

    @patch("pathlib.Path.read_text")
    def test_resolve_transitive_cycle_detected_by_backend_helpers(self, mock_read):
        """A -> B -> C -> A should be detected as a real cycle by SCC helpers."""
        from autocode.core.code.architecture import (
            _find_dependency_cycles,
            _resolve_file_dependencies,
        )

        contents = {
            "pkg/a.py": "from pkg.b import X\n",
            "pkg/b.py": "from pkg.c import Y\n",
            "pkg/c.py": "from pkg.a import Z\n",
        }

        def patched_read(self, *args, **kwargs):
            return contents.get(str(self), "")

        with patch.object(Path, "read_text", patched_read):
            deps, circulars = _resolve_file_dependencies(list(contents.keys()))

        assert len(deps) == 3
        assert circulars == []

        edge_map = {(dep.source, dep.target): set(dep.import_names) for dep in deps}
        cycles = _find_dependency_cycles(edge_map)
        assert cycles == [["pkg/a.py", "pkg/b.py", "pkg/c.py"]]

    def test_find_dependency_cycles_ignores_acyclic_branches(self):
        """SCC detection should only return cyclic components."""
        from autocode.core.code.architecture import _find_dependency_cycles

        edges = {
            ("pkg/a.py", "pkg/b.py"): {"X"},
            ("pkg/b.py", "pkg/c.py"): {"Y"},
            ("pkg/c.py", "pkg/a.py"): {"Z"},
            ("pkg/c.py", "pkg/d.py"): {"W"},
        }

        cycles = _find_dependency_cycles(edges)
        assert cycles == [["pkg/a.py", "pkg/b.py", "pkg/c.py"]]

    @patch("pathlib.Path.read_text")
    def test_resolve_aggregates_import_names(self, mock_read):
        """Multiple imports from same target should merge into one FileDependency."""
        from autocode.core.code.architecture import _resolve_file_dependencies

        contents = {
            "pkg/a.py": (
                "from pkg.b import X\n"
                "from pkg.b import Y, Z\n"
            ),
            "pkg/b.py": "X = 1\nY = 2\nZ = 3\n",
        }

        def patched_read(self, *args, **kwargs):
            return contents.get(str(self), "")

        with patch.object(Path, "read_text", patched_read):
            deps, circulars = _resolve_file_dependencies(list(contents.keys()))

        a_to_b = [d for d in deps if d.source == "pkg/a.py" and d.target == "pkg/b.py"]
        assert len(a_to_b) == 1
        assert sorted(a_to_b[0].import_names) == ["X", "Y", "Z"]

    @patch("pathlib.Path.read_text")
    def test_resolve_self_import_excluded(self, mock_read):
        """A file importing from itself should not create a dependency."""
        from autocode.core.code.architecture import _resolve_file_dependencies

        contents = {
            "pkg/a.py": "from pkg.a import something\n",
        }

        def patched_read(self, *args, **kwargs):
            return contents.get(str(self), "")

        with patch.object(Path, "read_text", patched_read):
            deps, circulars = _resolve_file_dependencies(list(contents.keys()))

        assert deps == []

    @patch("pathlib.Path.read_text")
    def test_resolve_syntax_error_skipped(self, mock_read):
        """Files with syntax errors should be skipped gracefully."""
        from autocode.core.code.architecture import _resolve_file_dependencies

        contents = {
            "pkg/good.py": "from pkg.bad import X\n",
            "pkg/bad.py": "def broken(\n",  # syntax error
        }

        def patched_read(self, *args, **kwargs):
            return contents.get(str(self), "")

        with patch.object(Path, "read_text", patched_read):
            deps, circulars = _resolve_file_dependencies(list(contents.keys()))

        assert len(deps) == 1
        assert deps[0].source == "pkg/good.py"
        assert deps[0].target == "pkg/bad.py"


class TestGetDependencyCycles:
    """Tests for the compact MCP dependency cycle endpoint."""

    @patch("autocode.core.code.architecture.get_tracked_files")
    @patch("pathlib.Path.read_text")
    def test_returns_transitive_cycles(self, mock_read, mock_tracked_files):
        from autocode.core.code.architecture import get_dependency_cycles

        contents = {
            "pkg/a.py": "from pkg.b import X\n",
            "pkg/b.py": "from pkg.c import Y\n",
            "pkg/c.py": "from pkg.a import Z\n",
        }
        mock_tracked_files.return_value = list(contents.keys())

        def patched_read(self, *args, **kwargs):
            return contents.get(str(self), "")

        with patch.object(Path, "read_text", patched_read):
            result = get_dependency_cycles()

        assert result.summary == {
            "path": ".",
            "cycle_count": 1,
            "returned_cycles": 1,
            "files_in_cycles": 3,
            "largest_cycle": 3,
        }
        assert len(result.cycles) == 1
        assert result.cycles[0].files == ["pkg/a.py", "pkg/b.py", "pkg/c.py"]
        assert result.cycles[0].size == 3

    @patch("autocode.core.code.architecture.get_tracked_files")
    def test_respects_path_filter(self, mock_tracked_files):
        from autocode.core.code.architecture import get_dependency_cycles

        mock_tracked_files.return_value = [
            "pkg/a.py",
            "pkg/b.py",
            "pkg/c.py",
            "web/x.js",
            "web/y.js",
        ]

        with patch(
            "autocode.core.code.architecture._resolve_file_dependencies",
            return_value=(
                [
                    type("Dep", (), {"source": "pkg/a.py", "target": "pkg/b.py", "import_names": ["X"]})(),
                    type("Dep", (), {"source": "pkg/b.py", "target": "pkg/a.py", "import_names": ["Y"]})(),
                ],
                [],
            ),
        ) as mock_resolve:
            result = get_dependency_cycles(path="pkg")

        assert mock_resolve.call_args.args[0] == ["pkg/a.py", "pkg/b.py", "pkg/c.py"]
        assert result.summary["path"] == "pkg"

    @patch("autocode.core.code.architecture.get_tracked_files")
    def test_orders_by_size_and_limits_results(self, mock_tracked_files):
        from autocode.core.code.architecture import get_dependency_cycles

        mock_tracked_files.return_value = ["pkg/a.py"]

        with patch(
            "autocode.core.code.architecture._resolve_file_dependencies",
            return_value=([], []),
        ), patch(
            "autocode.core.code.architecture._find_dependency_cycles",
            return_value=[
                ["pkg/d.py", "pkg/e.py"],
                ["pkg/a.py", "pkg/b.py", "pkg/c.py"],
            ],
        ):
            result = get_dependency_cycles(max_cycles=1)

        assert result.summary["cycle_count"] == 2
        assert result.summary["returned_cycles"] == 1
        assert result.summary["largest_cycle"] == 3
        assert result.cycles[0].files == ["pkg/a.py", "pkg/b.py", "pkg/c.py"]

    @patch("autocode.core.code.architecture.get_tracked_files")
    def test_applies_min_cycle_size(self, mock_tracked_files):
        from autocode.core.code.architecture import get_dependency_cycles

        mock_tracked_files.return_value = ["pkg/a.py"]

        with patch(
            "autocode.core.code.architecture._resolve_file_dependencies",
            return_value=([], []),
        ), patch(
            "autocode.core.code.architecture._find_dependency_cycles",
            return_value=[
                ["pkg/a.py", "pkg/b.py"],
                ["pkg/c.py", "pkg/d.py", "pkg/e.py"],
            ],
        ):
            result = get_dependency_cycles(min_cycle_size=3)

        assert result.summary["cycle_count"] == 1
        assert result.cycles == [
            type(result.cycles[0])(files=["pkg/c.py", "pkg/d.py", "pkg/e.py"], size=3)
        ]

    @patch("autocode.core.code.architecture.get_tracked_files")
    def test_returns_empty_result_when_no_cycles_exist(self, mock_tracked_files):
        from autocode.core.code.architecture import get_dependency_cycles

        mock_tracked_files.return_value = ["pkg/a.py"]

        with patch(
            "autocode.core.code.architecture._resolve_file_dependencies",
            return_value=([], []),
        ):
            result = get_dependency_cycles()

        assert result.summary == {
            "path": ".",
            "cycle_count": 0,
            "returned_cycles": 0,
            "files_in_cycles": 0,
            "largest_cycle": 0,
        }
        assert result.cycles == []


# ==============================================================================
# I) JS FILE DEPENDENCY RESOLUTION
# ==============================================================================


class TestResolveFileDependenciesJS:
    """Tests for _resolve_file_dependencies() with JavaScript files."""

    def test_js_relative_import_creates_dependency(self):
        """JS relative import './foo' should create a FileDependency."""
        from autocode.core.code.architecture import _resolve_file_dependencies

        contents = {
            "web/elements/index.js": "import { Component } from './component.js';\n",
            "web/elements/component.js": "export class Component {}\n",
        }

        def patched_read(self, *args, **kwargs):
            return contents.get(str(self), "")

        with patch.object(Path, "read_text", patched_read):
            deps, circulars = _resolve_file_dependencies(list(contents.keys()))

        assert len(deps) == 1
        assert deps[0].source == "web/elements/index.js"
        assert deps[0].target == "web/elements/component.js"

    def test_js_package_import_excluded(self):
        """JS bare package imports (e.g., 'lit') should NOT create dependencies."""
        from autocode.core.code.architecture import _resolve_file_dependencies

        contents = {
            "web/elements/index.js": (
                "import { LitElement } from 'lit';\n"
                "import * as d3 from 'd3';\n"
            ),
        }

        def patched_read(self, *args, **kwargs):
            return contents.get(str(self), "")

        with patch.object(Path, "read_text", patched_read):
            deps, circulars = _resolve_file_dependencies(list(contents.keys()))

        assert deps == []

    def test_js_circular_detection(self):
        """Mutual JS relative imports should be detected as circular."""
        from autocode.core.code.architecture import _resolve_file_dependencies

        contents = {
            "web/a.js": "import { B } from './b.js';\n",
            "web/b.js": "import { A } from './a.js';\n",
        }

        def patched_read(self, *args, **kwargs):
            return contents.get(str(self), "")

        with patch.object(Path, "read_text", patched_read):
            deps, circulars = _resolve_file_dependencies(list(contents.keys()))

        assert len(deps) == 2
        assert len(circulars) == 1
        pair = sorted(circulars[0])
        assert pair == ["web/a.js", "web/b.js"]

    def test_js_transitive_cycle_detected_by_backend_helpers(self):
        """JS A -> B -> C -> A should be detected by SCC helpers."""
        from autocode.core.code.architecture import (
            _find_dependency_cycles,
            _resolve_file_dependencies,
        )

        contents = {
            "web/a.js": "import { B } from './b.js';\n",
            "web/b.js": "import { C } from './c.js';\n",
            "web/c.js": "import { A } from './a.js';\n",
        }

        def patched_read(self, *args, **kwargs):
            return contents.get(str(self), "")

        with patch.object(Path, "read_text", patched_read):
            deps, circulars = _resolve_file_dependencies(list(contents.keys()))

        assert len(deps) == 3
        assert circulars == []

        edge_map = {(dep.source, dep.target): set(dep.import_names) for dep in deps}
        cycles = _find_dependency_cycles(edge_map)
        assert cycles == [["web/a.js", "web/b.js", "web/c.js"]]

    def test_mixed_py_and_js_dependencies(self):
        """Mixed Python and JS files should each resolve their own imports."""
        from autocode.core.code.architecture import _resolve_file_dependencies

        contents = {
            "pkg/app.py": "from pkg.models import Model\n",
            "pkg/models.py": "class Model: pass\n",
            "web/index.js": "import { utils } from './utils.js';\n",
            "web/utils.js": "export const utils = {};\n",
        }

        def patched_read(self, *args, **kwargs):
            return contents.get(str(self), "")

        with patch.object(Path, "read_text", patched_read):
            deps, circulars = _resolve_file_dependencies(list(contents.keys()))

        assert len(deps) == 2
        sources = {d.source for d in deps}
        assert "pkg/app.py" in sources
        assert "web/index.js" in sources

    def test_js_parent_relative_import(self):
        """JS import from '../utils.js' should resolve correctly."""
        from autocode.core.code.architecture import _resolve_file_dependencies

        contents = {
            "web/elements/graph/index.js": "import { theme } from '../shared/theme.js';\n",
            "web/elements/shared/theme.js": "export const theme = {};\n",
        }

        def patched_read(self, *args, **kwargs):
            return contents.get(str(self), "")

        with patch.object(Path, "read_text", patched_read):
            deps, circulars = _resolve_file_dependencies(list(contents.keys()))

        assert len(deps) == 1
        assert deps[0].source == "web/elements/graph/index.js"
        assert deps[0].target == "web/elements/shared/theme.js"

    def test_js_import_nonexistent_target_filtered(self):
        """JS import resolving to a file not in the tracked list should be filtered."""
        from autocode.core.code.architecture import _resolve_file_dependencies

        contents = {
            "web/index.js": "import { foo } from './nonexistent.js';\n",
        }

        def patched_read(self, *args, **kwargs):
            return contents.get(str(self), "")

        with patch.object(Path, "read_text", patched_read):
            deps, circulars = _resolve_file_dependencies(list(contents.keys()))

        assert deps == []

    def test_js_export_from_creates_dependency(self):
        """'export { X } from './foo.js'' should create a dependency."""
        from autocode.core.code.architecture import _resolve_file_dependencies

        contents = {
            "web/index.js": "export { Component } from './component.js';\n",
            "web/component.js": "export class Component {}\n",
        }

        def patched_read(self, *args, **kwargs):
            return contents.get(str(self), "")

        with patch.object(Path, "read_text", patched_read):
            deps, circulars = _resolve_file_dependencies(list(contents.keys()))

        assert len(deps) == 1
        assert deps[0].source == "web/index.js"
        assert deps[0].target == "web/component.js"
