"""
Unit tests for autocode.core.code.coupling module.

TDD tests for Commit 2: extract coupling analysis from metrics.py.
Tests cover: top-level package detection, Python import extraction,
coupling metrics computation (Ce/Ca/Instability), and circular detection.
"""
import pytest
from unittest.mock import patch
from pathlib import Path


# ==============================================================================
# A) TOP-LEVEL PACKAGES
# ==============================================================================


class TestTopLevelPackages:
    """Tests for _top_level_packages() — extracts first dir component."""

    def test_extracts_first_dir_component(self):
        """Should return the first directory in each file path."""
        from autocode.core.code.coupling import _top_level_packages

        files = [
            "autocode/core/code/metrics.py",
            "autocode/core/vcs/git.py",
            "tests/unit/test_foo.py",
        ]
        result = _top_level_packages(files)
        assert result == {"autocode", "tests"}

    def test_handles_root_files(self):
        """Root-level files (no dir) should use the filename stem as package."""
        from autocode.core.code.coupling import _top_level_packages

        files = ["setup.py", "autocode/main.py"]
        result = _top_level_packages(files)
        assert "setup.py" in result
        assert "autocode" in result

    def test_empty_list(self):
        """Empty file list → empty set."""
        from autocode.core.code.coupling import _top_level_packages

        result = _top_level_packages([])
        assert result == set()

    def test_handles_backslashes(self):
        """Windows-style backslashes should be normalized."""
        from autocode.core.code.coupling import _top_level_packages

        files = ["autocode\\core\\metrics.py"]
        result = _top_level_packages(files)
        assert "autocode" in result


# ==============================================================================
# B) PYTHON IMPORT EXTRACTION
# ==============================================================================


class TestExtractPythonImports:
    """Tests for _extract_python_imports() — AST-based import extraction."""

    def test_extracts_from_import(self):
        """'from autocode.core import X' should produce (src_pkg, tgt_pkg)."""
        from autocode.core.code.coupling import _extract_python_imports

        content = "from autocode.core.code.models import FileMetrics\n"
        top_pkgs = {"autocode"}
        result = _extract_python_imports(
            "autocode/interfaces/api.py", content, top_pkgs
        )
        # src_pkg = autocode.interfaces, tgt_pkg = autocode.core
        assert len(result) == 1
        src, tgt = result[0]
        assert src == "autocode.interfaces"
        assert tgt == "autocode.core"

    def test_extracts_import_statement(self):
        """'import autocode.core.code.models' should produce (src_pkg, tgt_pkg)."""
        from autocode.core.code.coupling import _extract_python_imports

        content = "import autocode.core.code.models\n"
        top_pkgs = {"autocode"}
        result = _extract_python_imports(
            "autocode/interfaces/api.py", content, top_pkgs
        )
        assert len(result) == 1
        src, tgt = result[0]
        assert src == "autocode.interfaces"
        assert tgt == "autocode.core"

    def test_filters_stdlib_imports(self):
        """Imports of stdlib modules (os, sys, json) should be filtered out."""
        from autocode.core.code.coupling import _extract_python_imports

        content = (
            "import os\n"
            "import sys\n"
            "from pathlib import Path\n"
            "from typing import List\n"
            "import json\n"
        )
        top_pkgs = {"autocode"}
        result = _extract_python_imports(
            "autocode/core/code/metrics.py", content, top_pkgs
        )
        assert result == []

    def test_keeps_internal_imports(self):
        """Imports within the project should be kept."""
        from autocode.core.code.coupling import _extract_python_imports

        content = (
            "from autocode.core.code.models import FileMetrics\n"
            "from autocode.interfaces.registry import register_function\n"
        )
        top_pkgs = {"autocode"}
        result = _extract_python_imports(
            "autocode/core/code/metrics.py", content, top_pkgs
        )
        # Both are internal: metrics→models is same pkg, metrics→registry is cross-pkg
        # src_pkg = autocode.core for both
        # First tgt_pkg = autocode.core (same pkg → filtered by caller)
        # Second tgt_pkg = autocode.interfaces (different → kept)
        # The function returns ALL internal imports; filtering same-pkg is done by caller
        assert len(result) == 2

    def test_ignores_same_package(self):
        """Imports within same 2-level package should still be returned (caller filters)."""
        from autocode.core.code.coupling import _extract_python_imports

        content = "from autocode.core.code.models import FileMetrics\n"
        top_pkgs = {"autocode"}
        result = _extract_python_imports(
            "autocode/core/code/metrics.py", content, top_pkgs
        )
        # Both src and tgt are autocode.core — returned, but analyze_coupling filters
        assert len(result) == 1
        src, tgt = result[0]
        assert src == "autocode.core"
        assert tgt == "autocode.core"

    def test_syntax_error_returns_empty(self):
        """Files with syntax errors should return empty list."""
        from autocode.core.code.coupling import _extract_python_imports

        content = "def broken(\n"
        top_pkgs = {"autocode"}
        result = _extract_python_imports(
            "autocode/core/broken.py", content, top_pkgs
        )
        assert result == []

    def test_multiple_import_targets(self):
        """Multiple imports from different packages should all be extracted."""
        from autocode.core.code.coupling import _extract_python_imports

        content = (
            "from autocode.core.vcs.git import git\n"
            "from autocode.interfaces.registry import register_function\n"
            "from tests.conftest import fixture\n"
        )
        top_pkgs = {"autocode", "tests"}
        result = _extract_python_imports(
            "autocode/core/code/metrics.py", content, top_pkgs
        )
        # All 3 are internal
        assert len(result) == 3


# ==============================================================================
# C) ANALYZE COUPLING (full pipeline)
# ==============================================================================


class TestAnalyzeCoupling:
    """Tests for analyze_coupling() — Ce/Ca/Instability + circular detection."""

    def test_simple_two_packages(self):
        """Two packages with one-way dependency: Ce=1 for source, Ca=1 for target."""
        from autocode.core.code.coupling import analyze_coupling

        contents = {
            "autocode/core/code/metrics.py": (
                "from autocode.interfaces.registry import register_function\n"
            ),
            "autocode/interfaces/registry.py": (
                "# no internal imports\nx = 1\n"
            ),
        }

        def patched_read(self, *args, **kwargs):
            return contents.get(str(self), "")

        with patch.object(Path, "read_text", patched_read):
            coupling, circulars = analyze_coupling(list(contents.keys()))

        # Should have 2 packages: autocode.core and autocode.interfaces
        pkg_map = {c.name: c for c in coupling}
        assert "autocode.core" in pkg_map
        assert "autocode.interfaces" in pkg_map

        # autocode.core imports autocode.interfaces → Ce=1
        assert pkg_map["autocode.core"].ce == 1
        assert pkg_map["autocode.core"].ca == 0

        # autocode.interfaces is imported by autocode.core → Ca=1
        assert pkg_map["autocode.interfaces"].ce == 0
        assert pkg_map["autocode.interfaces"].ca == 1

        # No circulars
        assert circulars == []

    def test_no_files_returns_empty(self):
        """No files → empty coupling and no circulars."""
        from autocode.core.code.coupling import analyze_coupling

        coupling, circulars = analyze_coupling([])
        assert coupling == []
        assert circulars == []

    def test_circular_detection(self):
        """A→B and B→A should be detected as circular."""
        from autocode.core.code.coupling import analyze_coupling

        # Use 3-level paths so 2-level packages are pkg_a.core / pkg_b.core
        contents = {
            "pkg_a/core/module.py": "from pkg_b.core.module import X\n",
            "pkg_b/core/module.py": "from pkg_a.core.module import Y\n",
        }

        def patched_read(self, *args, **kwargs):
            return contents.get(str(self), "")

        with patch.object(Path, "read_text", patched_read):
            coupling, circulars = analyze_coupling(list(contents.keys()))

        assert len(circulars) == 1
        pair = sorted(circulars[0])
        assert pair == ["pkg_a.core", "pkg_b.core"]

    def test_instability_calculation(self):
        """Instability = Ce / (Ce + Ca). Package with only outgoing → I=1.0."""
        from autocode.core.code.coupling import analyze_coupling

        # Use 3-level paths so 2-level packages are source.core / target.core
        contents = {
            "source/core/app.py": (
                "from target.core.utils import helper\n"
            ),
            "target/core/utils.py": "def helper(): pass\n",
            "target/core/models.py": "class Model: pass\n",
        }

        def patched_read(self, *args, **kwargs):
            return contents.get(str(self), "")

        with patch.object(Path, "read_text", patched_read):
            coupling, circulars = analyze_coupling(list(contents.keys()))

        pkg_map = {c.name: c for c in coupling}

        # source.core only imports (Ce=1, Ca=0) → Instability = 1.0
        assert pkg_map["source.core"].instability == 1.0

        # target.core only imported (Ce=0, Ca=1) → Instability = 0.0
        assert pkg_map["target.core"].instability == 0.0

    def test_only_internal_imports_counted(self):
        """Stdlib/third-party imports should NOT appear in coupling."""
        from autocode.core.code.coupling import analyze_coupling

        contents = {
            "myproject/app.py": (
                "import os\n"
                "import json\n"
                "from pathlib import Path\n"
                "from typing import List\n"
            ),
        }

        def patched_read(self, *args, **kwargs):
            return contents.get(str(self), "")

        with patch.object(Path, "read_text", patched_read):
            coupling, circulars = analyze_coupling(list(contents.keys()))

        assert coupling == []
        assert circulars == []

    def test_imports_to_and_imported_by_fields(self):
        """PackageCoupling should correctly populate imports_to and imported_by."""
        from autocode.core.code.coupling import analyze_coupling

        contents = {
            "autocode/core/code/metrics.py": (
                "from autocode.interfaces.registry import register_function\n"
                "from autocode.core.vcs.git import git\n"
            ),
            "autocode/interfaces/registry.py": "x = 1\n",
            "autocode/core/vcs/git.py": "def git(): pass\n",
        }

        def patched_read(self, *args, **kwargs):
            return contents.get(str(self), "")

        with patch.object(Path, "read_text", patched_read):
            coupling, circulars = analyze_coupling(list(contents.keys()))

        pkg_map = {c.name: c for c in coupling}

        # autocode.core imports autocode.interfaces
        assert "autocode.interfaces" in pkg_map["autocode.core"].imports_to

        # autocode.interfaces is imported by autocode.core
        assert "autocode.core" in pkg_map["autocode.interfaces"].imported_by

    def test_self_package_imports_excluded(self):
        """Imports within the same 2-level package should NOT create coupling edges."""
        from autocode.core.code.coupling import analyze_coupling  # noqa: F811

        contents = {
            "autocode/core/code/metrics.py": (
                "from autocode.core.code.models import FileMetrics\n"
            ),
            "autocode/core/code/models.py": "class FileMetrics: pass\n",
        }

        def patched_read(self, *args, **kwargs):
            return contents.get(str(self), "")

        with patch.object(Path, "read_text", patched_read):
            coupling, circulars = analyze_coupling(list(contents.keys()))

        # Both files are in autocode.core → no cross-package coupling
        assert coupling == []
        assert circulars == []


# ==============================================================================
# D) JAVASCRIPT IMPORT EXTRACTION (Commit 6)
# ==============================================================================


class TestExtractJSImports:
    """Tests for _extract_js_imports() — regex-based JS import extraction."""

    def test_extracts_relative_import(self):
        """import X from './foo' should produce (src_pkg, tgt_pkg)."""
        from autocode.core.code.coupling import _extract_js_imports

        content = "import { Component } from './component.js';\n"
        result = _extract_js_imports(
            "web/elements/index.js", content, {"web"}
        )
        # src_pkg = web.elements, tgt_pkg = web.elements (same → caller filters)
        assert len(result) >= 1
        src, tgt = result[0]
        assert src == "web.elements"

    def test_extracts_parent_relative_import(self):
        """import X from '../bar' should resolve to parent directory package."""
        from autocode.core.code.coupling import _extract_js_imports

        content = "import { helper } from '../utils/helper.js';\n"
        result = _extract_js_imports(
            "web/elements/graph/index.js", content, {"web"}
        )
        # src_pkg = web.elements (from web/elements/graph/index.js → 2-level)
        # tgt = ../utils/helper.js relative to web/elements/graph/ → web/elements/utils/helper.js
        # tgt_pkg = web.elements
        assert len(result) == 1
        src, tgt = result[0]
        assert src == "web.elements"

    def test_ignores_package_import(self):
        """import X from 'lit' (bare specifier, no ./) should be ignored as external."""
        from autocode.core.code.coupling import _extract_js_imports

        content = (
            "import { LitElement, html, css } from 'lit';\n"
            "import { property } from 'lit/decorators.js';\n"
        )
        result = _extract_js_imports(
            "web/elements/index.js", content, {"web"}
        )
        assert result == []

    def test_ignores_node_modules(self):
        """import from 'lodash/get' or 'd3' should be ignored as external."""
        from autocode.core.code.coupling import _extract_js_imports

        content = (
            "import * as d3 from 'd3';\n"
            "import get from 'lodash/get';\n"
        )
        result = _extract_js_imports(
            "web/elements/index.js", content, {"web"}
        )
        assert result == []

    def test_extracts_named_imports(self):
        """import { X, Y } from './foo' should be extracted."""
        from autocode.core.code.coupling import _extract_js_imports

        content = "import { theme, colors } from './styles/theme.js';\n"
        result = _extract_js_imports(
            "web/elements/index.js", content, {"web"}
        )
        assert len(result) == 1
        src, tgt = result[0]
        assert src == "web.elements"

    def test_extracts_namespace_import(self):
        """import * as X from './foo' should be extracted."""
        from autocode.core.code.coupling import _extract_js_imports

        content = "import * as styles from './styles/index.js';\n"
        result = _extract_js_imports(
            "web/elements/index.js", content, {"web"}
        )
        assert len(result) == 1

    def test_extracts_export_from(self):
        """export { X } from './foo' should be extracted as a dependency."""
        from autocode.core.code.coupling import _extract_js_imports

        content = "export { Component } from './component.js';\n"
        result = _extract_js_imports(
            "web/elements/index.js", content, {"web"}
        )
        assert len(result) == 1

    def test_cross_package_import(self):
        """Relative import resolving to a different 2-level package should create coupling."""
        from autocode.core.code.coupling import _extract_js_imports

        # web/elements/arch/index.js imports from ../../utils/helper.js
        # → resolves to web/utils/helper.js → pkg = web.utils
        content = "import { helper } from '../../utils/helper.js';\n"
        result = _extract_js_imports(
            "web/elements/arch/index.js", content, {"web"}
        )
        assert len(result) == 1
        src, tgt = result[0]
        assert src == "web.elements"
        assert tgt == "web.utils"

    def test_single_quoted_imports(self):
        """Imports with single quotes should also be matched."""
        from autocode.core.code.coupling import _extract_js_imports

        content = "import { foo } from './bar.js';\n"
        result = _extract_js_imports(
            "web/elements/index.js", content, {"web"}
        )
        assert len(result) == 1


# ==============================================================================
# E) MIXED-LANGUAGE COUPLING ANALYSIS (Commit 6)
# ==============================================================================


class TestAnalyzeCouplingMixedLanguages:
    """Tests for analyze_coupling() with Python + JS files."""

    def test_mixed_py_and_js_coupling(self):
        """Mixed Python and JS files: each language's imports analyzed correctly."""
        from autocode.core.code.coupling import analyze_coupling

        contents = {
            # Python file importing from autocode.interfaces
            "autocode/core/code/metrics.py": (
                "from autocode.interfaces.registry import register_function\n"
            ),
            "autocode/interfaces/registry.py": "x = 1\n",
            # JS file with only external imports (no coupling)
            "autocode/web/elements/index.js": (
                "import { LitElement } from 'lit';\n"
            ),
        }

        def patched_read(self, *args, **kwargs):
            return contents.get(str(self), "")

        with patch.object(Path, "read_text", patched_read):
            coupling, circulars = analyze_coupling(list(contents.keys()))

        pkg_map = {c.name: c for c in coupling}
        # Python coupling should still work
        assert "autocode.core" in pkg_map
        assert "autocode.interfaces" in pkg_map
        assert pkg_map["autocode.core"].ce == 1

    def test_js_only_coupling(self):
        """JS-only project with relative imports should produce coupling."""
        from autocode.core.code.coupling import analyze_coupling

        contents = {
            # web/elements/arch/index.js imports from web/elements/shared
            "web/elements/arch/index.js": (
                "import { theme } from '../../shared/styles.js';\n"
            ),
            "web/shared/styles.js": "export const theme = {};\n",
            "web/elements/shared/other.js": "export const x = 1;\n",
        }

        def patched_read(self, *args, **kwargs):
            return contents.get(str(self), "")

        with patch.object(Path, "read_text", patched_read):
            coupling, circulars = analyze_coupling(list(contents.keys()))

        # Should have coupling between web.elements and web.shared
        pkg_map = {c.name: c for c in coupling}
        assert "web.elements" in pkg_map or "web.shared" in pkg_map

    def test_js_circular_detection(self):
        """JS files with mutual relative imports should trigger circular detection."""
        from autocode.core.code.coupling import analyze_coupling

        contents = {
            "pkg_a/core/app.js": "import { helper } from '../../pkg_b/core/helper.js';\n",
            "pkg_b/core/helper.js": "import { util } from '../../pkg_a/core/util.js';\n",
            "pkg_a/core/util.js": "export const util = 1;\n",
        }

        def patched_read(self, *args, **kwargs):
            return contents.get(str(self), "")

        with patch.object(Path, "read_text", patched_read):
            coupling, circulars = analyze_coupling(list(contents.keys()))

        assert len(circulars) == 1
        pair = sorted(circulars[0])
        assert pair == ["pkg_a.core", "pkg_b.core"]

    def test_js_relative_imports_resolved_to_packages(self):
        """JS relative imports should resolve to correct 2-level package names."""
        from autocode.core.code.coupling import _extract_js_imports

        # File in web/elements/graph/index.js importing from ../shared/styles.js
        # Resolved: web/elements/shared/styles.js → package web.elements
        content = "import { theme } from '../shared/styles.js';\n"
        result = _extract_js_imports(
            "web/elements/graph/index.js", content, {"web"}
        )
        assert len(result) == 1
        src, tgt = result[0]
        assert src == "web.elements"
        assert tgt == "web.elements"  # same 2-level package
