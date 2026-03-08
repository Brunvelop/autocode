"""
Unit tests for autocode.core.code.architecture module.

TDD tests for architecture snapshot (Commits 1 & 2).
Tests cover: models, hierarchy building, metric propagation, endpoint,
file-level dependency resolution, and circular detection.
"""
import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path


# ==============================================================================
# A) MODEL TESTS
# ==============================================================================


class TestArchitectureModels:
    """Tests for ArchitectureNode, ArchitectureSnapshot, ArchitectureSnapshotOutput."""

    def test_architecture_node_file_defaults(self):
        """A file node should have sensible defaults for all metric fields."""
        from autocode.core.code.models import ArchitectureNode

        node = ArchitectureNode(
            id="autocode/core/code/metrics.py",
            parent_id="autocode/core/code",
            name="metrics.py",
            type="file",
            path="autocode/core/code/metrics.py",
        )
        assert node.type == "file"
        assert node.loc == 0
        assert node.sloc == 0
        assert node.mi == 100.0
        assert node.avg_complexity == 0.0
        assert node.max_complexity == 0
        assert node.functions_count == 0
        assert node.classes_count == 0
        assert node.children_count == 0

    def test_architecture_node_directory(self):
        """A directory node should accept all fields."""
        from autocode.core.code.models import ArchitectureNode

        node = ArchitectureNode(
            id="autocode/core",
            parent_id="autocode",
            name="core",
            type="directory",
            path="autocode/core",
            loc=500,
            sloc=400,
            mi=72.5,
            avg_complexity=3.2,
            max_complexity=15,
            functions_count=20,
            classes_count=5,
            children_count=3,
        )
        assert node.type == "directory"
        assert node.sloc == 400
        assert node.mi == 72.5
        assert node.children_count == 3

    def test_architecture_snapshot_structure(self):
        """Snapshot should hold nodes + metadata + global aggregates."""
        from autocode.core.code.models import ArchitectureNode, ArchitectureSnapshot

        root = ArchitectureNode(
            id=".", parent_id=None, name="root", type="directory", path="."
        )
        file_node = ArchitectureNode(
            id="main.py", parent_id=".", name="main.py", type="file", path="main.py",
            sloc=100, mi=75.0,
        )
        snapshot = ArchitectureSnapshot(
            root_id=".",
            nodes=[root, file_node],
            commit_hash="abc123def456",
            commit_short="abc123d",
            branch="main",
            timestamp="2025-01-01T00:00:00",
            total_files=1,
            total_sloc=100,
            total_functions=5,
            total_classes=2,
            avg_mi=75.0,
            avg_complexity=2.5,
        )
        assert snapshot.root_id == "."
        assert len(snapshot.nodes) == 2
        assert snapshot.total_files == 1
        assert snapshot.avg_mi == 75.0

    def test_architecture_snapshot_output_success(self):
        """Output wrapper should carry snapshot in result field."""
        from autocode.core.code.models import (
            ArchitectureNode, ArchitectureSnapshot, ArchitectureSnapshotOutput,
        )

        root = ArchitectureNode(
            id=".", parent_id=None, name="root", type="directory", path="."
        )
        snapshot = ArchitectureSnapshot(
            root_id=".", nodes=[root],
            commit_hash="abc", commit_short="abc", branch="main", timestamp="now",
        )
        output = ArchitectureSnapshotOutput(
            success=True, result=snapshot, message="ok"
        )
        assert output.success is True
        assert output.result.root_id == "."

    def test_architecture_snapshot_output_error(self):
        """Output wrapper should support error state with result=None."""
        from autocode.core.code.models import ArchitectureSnapshotOutput

        output = ArchitectureSnapshotOutput(
            success=False, result=None, message="git error"
        )
        assert output.success is False
        assert output.result is None


# ==============================================================================
# B) HIERARCHY BUILDING TESTS
# ==============================================================================


class TestBuildArchitectureNodes:
    """Tests for _build_architecture_nodes() — hierarchy construction."""

    def _mock_analyze_file_metrics(self, path, content):
        """Helper: returns a FileMetrics-like object with predictable values."""
        from autocode.core.code.models import FileMetrics

        # Simple heuristic: count lines for LOC
        lines = content.split("\n")
        loc = len(lines)
        sloc = sum(1 for l in lines if l.strip() and not l.strip().startswith("#"))
        return FileMetrics(
            path=path,
            language="python",
            sloc=sloc,
            comments=0,
            blanks=loc - sloc,
            total_loc=loc,
            functions=[],
            classes_count=1,
            functions_count=2,
            avg_complexity=3.5,
            max_complexity=8,
            max_nesting=2,
            maintainability_index=72.0,
        )

    @patch("autocode.core.code.architecture.analyze_file_metrics")
    def test_build_nodes_single_file(self, mock_analyze):
        """A single file should produce root + file node."""
        from autocode.core.code.architecture import _build_architecture_nodes

        mock_analyze.return_value = self._mock_analyze_file_metrics(
            "x = 1\ny = 2\n", "main.py"
        )

        nodes = _build_architecture_nodes(["main.py"])

        node_map = {n.id: n for n in nodes}
        assert "." in node_map  # root
        assert "main.py" in node_map
        assert node_map["main.py"].type == "file"
        assert node_map["main.py"].parent_id == "."
        assert node_map["."].type == "directory"
        assert node_map["."].parent_id is None

    @patch("autocode.core.code.architecture.analyze_file_metrics")
    def test_build_nodes_nested_dirs(self, mock_analyze):
        """Files in subdirs should create intermediate directory nodes."""
        from autocode.core.code.architecture import _build_architecture_nodes

        mock_analyze.return_value = self._mock_analyze_file_metrics("x=1\n", "dummy")

        py_files = [
            "autocode/core/code/metrics.py",
            "autocode/core/code/models.py",
            "autocode/core/vcs/tree.py",
        ]
        nodes = _build_architecture_nodes(py_files)
        node_map = {n.id: n for n in nodes}

        # Root exists
        assert "." in node_map

        # Intermediate dirs exist
        assert "autocode" in node_map
        assert node_map["autocode"].type == "directory"
        assert node_map["autocode"].parent_id == "."

        assert "autocode/core" in node_map
        assert node_map["autocode/core"].type == "directory"
        assert node_map["autocode/core"].parent_id == "autocode"

        assert "autocode/core/code" in node_map
        assert node_map["autocode/core/code"].parent_id == "autocode/core"

        assert "autocode/core/vcs" in node_map
        assert node_map["autocode/core/vcs"].parent_id == "autocode/core"

        # Files exist with correct parents
        assert "autocode/core/code/metrics.py" in node_map
        assert node_map["autocode/core/code/metrics.py"].parent_id == "autocode/core/code"

    @patch("autocode.core.code.architecture.analyze_file_metrics")
    def test_build_nodes_empty(self, mock_analyze):
        """No files should produce only the root node."""
        from autocode.core.code.architecture import _build_architecture_nodes

        nodes = _build_architecture_nodes([])
        assert len(nodes) == 1
        assert nodes[0].id == "."
        assert nodes[0].type == "directory"
        mock_analyze.assert_not_called()

    @patch("autocode.core.code.architecture.analyze_file_metrics")
    @patch("pathlib.Path.read_text")
    def test_build_nodes_metrics_on_files(self, mock_read, mock_analyze):
        """File nodes should carry MI, CC, LOC from _analyze_content."""
        from autocode.core.code.architecture import _build_architecture_nodes
        from autocode.core.code.models import FileMetrics

        mock_read.return_value = "def foo():\n    pass\n"
        mock_analyze.return_value = FileMetrics(
            path="app.py", language="python",
            sloc=50, comments=5, blanks=10, total_loc=65,
            functions=[], classes_count=2, functions_count=3,
            avg_complexity=4.5, max_complexity=12, max_nesting=3,
            maintainability_index=68.3,
        )

        nodes = _build_architecture_nodes(["app.py"])
        node_map = {n.id: n for n in nodes}
        file_node = node_map["app.py"]

        assert file_node.sloc == 50
        assert file_node.loc == 65
        assert file_node.mi == 68.3
        assert file_node.avg_complexity == 4.5
        assert file_node.max_complexity == 12
        assert file_node.functions_count == 3
        assert file_node.classes_count == 2


# ==============================================================================
# C) METRIC PROPAGATION TESTS
# ==============================================================================


class TestPropagateMetrics:
    """Tests for _propagate_metrics() — bottom-up MI/CC aggregation."""

    def test_propagate_simple_two_files(self):
        """Dir with 2 files: MI/CC should be LOC-weighted average."""
        from autocode.core.code.models import ArchitectureNode
        from autocode.core.code.architecture import _propagate_metrics

        root = ArchitectureNode(
            id=".", parent_id=None, name="root", type="directory", path="."
        )
        file_a = ArchitectureNode(
            id="a.py", parent_id=".", name="a.py", type="file", path="a.py",
            sloc=100, loc=120, mi=80.0, avg_complexity=2.0, max_complexity=5,
            functions_count=3, classes_count=1,
        )
        file_b = ArchitectureNode(
            id="b.py", parent_id=".", name="b.py", type="file", path="b.py",
            sloc=200, loc=250, mi=60.0, avg_complexity=4.0, max_complexity=10,
            functions_count=5, classes_count=2,
        )
        nodes = [root, file_a, file_b]
        _propagate_metrics(nodes, ".")

        node_map = {n.id: n for n in nodes}
        root_node = node_map["."]

        # LOC-weighted MI: (80*100 + 60*200) / (100+200) = 20000/300 = 66.67
        assert abs(root_node.mi - 66.67) < 0.1
        # LOC-weighted CC: (2*100 + 4*200) / (100+200) = 1000/300 = 3.33
        assert abs(root_node.avg_complexity - 3.33) < 0.1
        # Max complexity = max of children
        assert root_node.max_complexity == 10
        # Aggregated LOC/SLOC
        assert root_node.sloc == 300
        assert root_node.loc == 370
        # Aggregated counts
        assert root_node.functions_count == 8
        assert root_node.classes_count == 3
        # Children count
        assert root_node.children_count == 2

    def test_propagate_nested_directories(self):
        """Nested dirs: metrics propagate from leaf files up through all levels."""
        from autocode.core.code.models import ArchitectureNode
        from autocode.core.code.architecture import _propagate_metrics

        root = ArchitectureNode(
            id=".", parent_id=None, name="root", type="directory", path="."
        )
        sub_dir = ArchitectureNode(
            id="src", parent_id=".", name="src", type="directory", path="src"
        )
        file_a = ArchitectureNode(
            id="src/a.py", parent_id="src", name="a.py", type="file", path="src/a.py",
            sloc=100, loc=110, mi=70.0, avg_complexity=3.0, max_complexity=7,
            functions_count=4, classes_count=1,
        )
        nodes = [root, sub_dir, file_a]
        _propagate_metrics(nodes, ".")

        node_map = {n.id: n for n in nodes}

        # sub_dir should get file_a's metrics
        assert node_map["src"].sloc == 100
        assert node_map["src"].mi == 70.0
        assert node_map["src"].avg_complexity == 3.0
        assert node_map["src"].max_complexity == 7
        assert node_map["src"].children_count == 1

        # root should also get the same (only one file in tree)
        assert node_map["."].sloc == 100
        assert node_map["."].mi == 70.0
        assert node_map["."].children_count == 1  # one direct child (src/)

    def test_propagate_mixed_tree(self):
        """Mixed tree: root has a file and a subdir with files."""
        from autocode.core.code.models import ArchitectureNode
        from autocode.core.code.architecture import _propagate_metrics

        root = ArchitectureNode(
            id=".", parent_id=None, name="root", type="directory", path="."
        )
        sub_dir = ArchitectureNode(
            id="pkg", parent_id=".", name="pkg", type="directory", path="pkg"
        )
        # File directly under root
        root_file = ArchitectureNode(
            id="setup.py", parent_id=".", name="setup.py", type="file", path="setup.py",
            sloc=50, loc=60, mi=90.0, avg_complexity=1.0, max_complexity=2,
            functions_count=1, classes_count=0,
        )
        # File under pkg/
        pkg_file = ArchitectureNode(
            id="pkg/main.py", parent_id="pkg", name="main.py", type="file", path="pkg/main.py",
            sloc=150, loc=180, mi=60.0, avg_complexity=5.0, max_complexity=15,
            functions_count=6, classes_count=2,
        )
        nodes = [root, sub_dir, root_file, pkg_file]
        _propagate_metrics(nodes, ".")

        node_map = {n.id: n for n in nodes}

        # pkg/ should have pkg_file's metrics
        assert node_map["pkg"].sloc == 150
        assert node_map["pkg"].mi == 60.0

        # root should aggregate both: setup.py(sloc=50) + pkg/(sloc=150)
        assert node_map["."].sloc == 200
        # MI weighted: (90*50 + 60*150) / 200 = (4500+9000)/200 = 67.5
        assert abs(node_map["."].mi - 67.5) < 0.1
        # Root has 2 direct children
        assert node_map["."].children_count == 2

    def test_propagate_no_files(self):
        """Empty tree (just root) should keep defaults."""
        from autocode.core.code.models import ArchitectureNode
        from autocode.core.code.architecture import _propagate_metrics

        root = ArchitectureNode(
            id=".", parent_id=None, name="root", type="directory", path="."
        )
        nodes = [root]
        _propagate_metrics(nodes, ".")

        assert root.sloc == 0
        assert root.mi == 100.0
        assert root.children_count == 0


# ==============================================================================
# D) ENDPOINT TESTS
# ==============================================================================


class TestGetArchitectureSnapshot:
    """Tests for the registered get_architecture_snapshot endpoint."""

    @patch("autocode.core.code.architecture.git")
    @patch("autocode.core.code.architecture.get_tracked_files")
    @patch("autocode.core.code.architecture.analyze_file_metrics")
    @patch("pathlib.Path.read_text")
    def test_snapshot_success(self, mock_read, mock_analyze, mock_get_files, mock_git):
        """Successful snapshot should return valid structure with totals."""
        from autocode.core.code.architecture import get_architecture_snapshot
        from autocode.core.code.models import FileMetrics

        mock_git.side_effect = lambda *args: {
            ("rev-parse", "HEAD"): "abc123def456789",
            ("rev-parse", "--short", "HEAD"): "abc123d",
            ("rev-parse", "--abbrev-ref", "HEAD"): "main",
        }.get(args, "")

        mock_get_files.return_value = ["src/app.py", "src/utils.py"]
        mock_read.return_value = "x = 1\n"

        def analyze_side_effect(path, content):
            return FileMetrics(
                path=path, language="python",
                sloc=100, comments=10, blanks=5, total_loc=115,
                functions=[], classes_count=1, functions_count=3,
                avg_complexity=2.5, max_complexity=6, max_nesting=2,
                maintainability_index=75.0,
            )

        mock_analyze.side_effect = analyze_side_effect

        result = get_architecture_snapshot()

        assert result.success is True
        snapshot = result.result
        assert snapshot is not None
        assert snapshot.root_id == "."
        assert snapshot.commit_hash == "abc123def456789"
        assert snapshot.commit_short == "abc123d"
        assert snapshot.branch == "main"
        assert snapshot.total_files == 2
        assert snapshot.total_sloc == 200
        assert snapshot.total_functions == 6
        assert snapshot.total_classes == 2
        assert snapshot.avg_mi == 75.0
        assert snapshot.avg_complexity == 2.5

        # Check nodes exist
        node_ids = {n.id for n in snapshot.nodes}
        assert "." in node_ids
        assert "src" in node_ids
        assert "src/app.py" in node_ids
        assert "src/utils.py" in node_ids

    @patch("autocode.core.code.architecture.git")
    @patch("autocode.core.code.architecture.get_tracked_files")
    def test_snapshot_error_no_git(self, mock_get_files, mock_git):
        """Should return error gracefully when git fails."""
        from autocode.core.code.architecture import get_architecture_snapshot

        mock_git.side_effect = Exception("Not a git repository")
        mock_get_files.side_effect = Exception("git failed")

        result = get_architecture_snapshot()

        assert result.success is False
        assert result.result is None
        assert result.message is not None

    @patch("autocode.core.code.architecture.git")
    @patch("autocode.core.code.architecture.get_tracked_files")
    def test_snapshot_no_py_files(self, mock_get_files, mock_git):
        """Empty project (no .py files) should return valid but empty snapshot."""
        from autocode.core.code.architecture import get_architecture_snapshot

        mock_git.side_effect = lambda *args: {
            ("rev-parse", "HEAD"): "abc123",
            ("rev-parse", "--short", "HEAD"): "abc",
            ("rev-parse", "--abbrev-ref", "HEAD"): "main",
        }.get(args, "")

        mock_get_files.return_value = []

        result = get_architecture_snapshot()

        assert result.success is True
        snapshot = result.result
        assert snapshot is not None
        assert snapshot.total_files == 0
        assert snapshot.total_sloc == 0
        assert len(snapshot.nodes) == 1  # only root
        assert snapshot.nodes[0].id == "."


# ==============================================================================
# E) FILE DEPENDENCY MODEL TESTS (Commit 2)
# ==============================================================================


class TestFileDependencyModel:
    """Tests for FileDependency model and dependency fields on ArchitectureSnapshot."""

    def test_file_dependency_defaults(self):
        """FileDependency should have empty import_names by default."""
        from autocode.core.code.models import FileDependency

        dep = FileDependency(source="a.py", target="b.py")
        assert dep.source == "a.py"
        assert dep.target == "b.py"
        assert dep.import_names == []

    def test_file_dependency_with_import_names(self):
        """FileDependency should accept a list of imported names."""
        from autocode.core.code.models import FileDependency

        dep = FileDependency(
            source="autocode/core/code/architecture.py",
            target="autocode/core/code/models.py",
            import_names=["ArchitectureNode", "ArchitectureSnapshot"],
        )
        assert dep.import_names == ["ArchitectureNode", "ArchitectureSnapshot"]

    def test_architecture_snapshot_dependencies_default_empty(self):
        """ArchitectureSnapshot should have empty dependencies/circular by default."""
        from autocode.core.code.models import ArchitectureNode, ArchitectureSnapshot

        root = ArchitectureNode(
            id=".", parent_id=None, name="root", type="directory", path="."
        )
        snapshot = ArchitectureSnapshot(
            root_id=".", nodes=[root],
            commit_hash="abc", commit_short="abc", branch="main", timestamp="now",
        )
        assert snapshot.dependencies == []
        assert snapshot.circular_dependencies == []

    def test_architecture_snapshot_with_dependencies(self):
        """ArchitectureSnapshot should carry dependencies and circulars."""
        from autocode.core.code.models import (
            ArchitectureNode, ArchitectureSnapshot, FileDependency,
        )

        root = ArchitectureNode(
            id=".", parent_id=None, name="root", type="directory", path="."
        )
        dep = FileDependency(
            source="a.py", target="b.py", import_names=["foo"],
        )
        snapshot = ArchitectureSnapshot(
            root_id=".", nodes=[root],
            commit_hash="abc", commit_short="abc", branch="main", timestamp="now",
            dependencies=[dep],
            circular_dependencies=[["a.py", "b.py"]],
        )
        assert len(snapshot.dependencies) == 1
        assert snapshot.dependencies[0].source == "a.py"
        assert snapshot.circular_dependencies == [["a.py", "b.py"]]


# ==============================================================================
# F) FILE DEPENDENCY RESOLUTION TESTS (Commit 2)
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

        # Should find architecture.py → models.py
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

        # Should resolve to autocode/core/__init__.py (where 'code' is importable from)
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
        # Circular pair should contain both files (sorted)
        pair = sorted(circulars[0])
        assert pair == ["pkg/a.py", "pkg/b.py"]

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

        # Should be a single dependency with all names merged
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

        # Should still resolve the dependency (target exists in file list)
        # but the bad file's own imports are skipped
        assert len(deps) == 1
        assert deps[0].source == "pkg/good.py"
        assert deps[0].target == "pkg/bad.py"


# ==============================================================================
# G) ENDPOINT INTEGRATION WITH DEPENDENCIES (Commit 2)
# ==============================================================================


class TestSnapshotWithDependencies:
    """Tests that get_architecture_snapshot() includes dependency resolution."""

    @patch("autocode.core.code.architecture.git")
    @patch("autocode.core.code.architecture.get_tracked_files")
    @patch("autocode.core.code.architecture.analyze_file_metrics")
    def test_snapshot_includes_dependencies(
        self, mock_analyze, mock_get_files, mock_git
    ):
        """Snapshot should contain dependencies and circular_dependencies."""
        from autocode.core.code.architecture import get_architecture_snapshot
        from autocode.core.code.models import FileMetrics

        mock_git.side_effect = lambda *args: {
            ("rev-parse", "HEAD"): "abc123def",
            ("rev-parse", "--short", "HEAD"): "abc123d",
            ("rev-parse", "--abbrev-ref", "HEAD"): "main",
        }.get(args, "")

        mock_get_files.return_value = [
            "pkg/a.py",
            "pkg/b.py",
        ]

        # a.py imports from b.py
        contents = {
            "pkg/a.py": "from pkg.b import helper\n",
            "pkg/b.py": "def helper(): pass\n",
        }

        def patched_read(self_path, *args, **kwargs):
            return contents.get(str(self_path), "x = 1\n")

        def analyze_side_effect(path, content):
            return FileMetrics(
                path=path, language="python",
                sloc=10, comments=0, blanks=0, total_loc=10,
                functions=[], classes_count=0, functions_count=1,
                avg_complexity=1.0, max_complexity=1, max_nesting=0,
                maintainability_index=80.0,
            )
        mock_analyze.side_effect = analyze_side_effect

        with patch.object(Path, "read_text", patched_read):
            result = get_architecture_snapshot()

        assert result.success is True
        snapshot = result.result
        assert snapshot is not None

        # Should have dependencies
        assert hasattr(snapshot, "dependencies")
        assert isinstance(snapshot.dependencies, list)
        assert len(snapshot.dependencies) >= 1

        # Check the specific dependency
        dep = snapshot.dependencies[0]
        assert dep.source == "pkg/a.py"
        assert dep.target == "pkg/b.py"
        assert "helper" in dep.import_names

        # No circulars in this case
        assert hasattr(snapshot, "circular_dependencies")
        assert snapshot.circular_dependencies == []

    @patch("autocode.core.code.architecture.git")
    @patch("autocode.core.code.architecture.get_tracked_files")
    @patch("autocode.core.code.architecture.analyze_file_metrics")
    @patch("pathlib.Path.read_text")
    def test_snapshot_no_py_files_has_empty_deps(
        self, mock_read, mock_analyze, mock_get_files, mock_git
    ):
        """Empty project should still have dependencies fields (empty lists)."""
        from autocode.core.code.architecture import get_architecture_snapshot

        mock_git.side_effect = lambda *args: {
            ("rev-parse", "HEAD"): "abc123",
            ("rev-parse", "--short", "HEAD"): "abc",
            ("rev-parse", "--abbrev-ref", "HEAD"): "main",
        }.get(args, "")
        mock_get_files.return_value = []

        result = get_architecture_snapshot()

        assert result.success is True
        assert result.result.dependencies == []
        assert result.result.circular_dependencies == []


# ==============================================================================
# H) MULTI-LANGUAGE ARCHITECTURE NODES (Commit 5)
# ==============================================================================


class TestBuildArchitectureNodesMultiLang:
    """Tests for _build_architecture_nodes() with mixed Python and JS files."""

    @patch("autocode.core.code.architecture.analyze_file_metrics")
    @patch("pathlib.Path.read_text")
    def test_build_nodes_includes_js_files(self, mock_read, mock_analyze):
        """JS files should produce file nodes in the architecture tree."""
        from autocode.core.code.architecture import _build_architecture_nodes
        from autocode.core.code.models import FileMetrics

        mock_read.return_value = "function hello() { return 1; }\n"
        mock_analyze.return_value = FileMetrics(
            path="web/app.js", language="javascript",
            sloc=30, comments=5, blanks=3, total_loc=38,
            functions=[], classes_count=0, functions_count=2,
            avg_complexity=2.0, max_complexity=3, max_nesting=1,
            maintainability_index=80.0,
        )

        nodes = _build_architecture_nodes(["web/app.js"])
        node_map = {n.id: n for n in nodes}

        assert "web/app.js" in node_map
        assert node_map["web/app.js"].type == "file"
        assert node_map["web/app.js"].parent_id == "web"
        assert node_map["web/app.js"].sloc == 30
        assert node_map["web/app.js"].mi == 80.0
        assert "web" in node_map
        assert node_map["web"].type == "directory"

    @patch("autocode.core.code.architecture.analyze_file_metrics")
    @patch("pathlib.Path.read_text")
    def test_build_nodes_mixed_py_and_js(self, mock_read, mock_analyze):
        """A mix of Python and JS files should all appear in the architecture tree."""
        from autocode.core.code.architecture import _build_architecture_nodes
        from autocode.core.code.models import FileMetrics

        mock_read.return_value = "x = 1\n"

        def analyze_side_effect(path, content):
            lang = "python" if path.endswith(".py") else "javascript"
            return FileMetrics(
                path=path, language=lang,
                sloc=50, comments=5, blanks=5, total_loc=60,
                functions=[], classes_count=1, functions_count=2,
                avg_complexity=2.0, max_complexity=4, max_nesting=1,
                maintainability_index=75.0,
            )

        mock_analyze.side_effect = analyze_side_effect

        files = [
            "autocode/core/code/metrics.py",
            "autocode/web/elements/app.js",
            "autocode/web/elements/utils.mjs",
        ]
        nodes = _build_architecture_nodes(files)
        node_map = {n.id: n for n in nodes}

        # All files should be present
        assert "autocode/core/code/metrics.py" in node_map
        assert "autocode/web/elements/app.js" in node_map
        assert "autocode/web/elements/utils.mjs" in node_map

        # All should be file nodes
        assert node_map["autocode/core/code/metrics.py"].type == "file"
        assert node_map["autocode/web/elements/app.js"].type == "file"
        assert node_map["autocode/web/elements/utils.mjs"].type == "file"

        # Intermediate directories should exist
        assert "autocode/web/elements" in node_map
        assert "autocode/web" in node_map
        assert "autocode/core/code" in node_map


class TestArchitectureSnapshotWithJS:
    """Tests for get_architecture_snapshot() including JS files (Commit 5)."""

    @patch("autocode.core.code.architecture._resolve_file_dependencies")
    @patch("autocode.core.code.architecture.git")
    @patch("autocode.core.code.architecture.get_tracked_files")
    @patch("autocode.core.code.architecture.analyze_file_metrics")
    @patch("pathlib.Path.read_text")
    def test_get_architecture_requests_js_extensions(
        self, mock_read, mock_analyze, mock_get_files, mock_git, mock_resolve_deps
    ):
        """get_architecture_snapshot should request JS extensions from get_tracked_files."""
        from autocode.core.code.architecture import get_architecture_snapshot
        from autocode.core.code.models import FileMetrics

        mock_git.side_effect = lambda *args: {
            ("rev-parse", "HEAD"): "abc123",
            ("rev-parse", "--short", "HEAD"): "abc",
            ("rev-parse", "--abbrev-ref", "HEAD"): "main",
        }.get(args, "")
        mock_get_files.return_value = []
        mock_resolve_deps.return_value = ([], [])

        get_architecture_snapshot()

        call_args = mock_get_files.call_args
        extensions = call_args[0]  # positional args
        assert ".py" in extensions
        assert ".js" in extensions
        assert ".mjs" in extensions
        assert ".jsx" in extensions

    @patch("autocode.core.code.architecture._resolve_file_dependencies")
    @patch("autocode.core.code.architecture.git")
    @patch("autocode.core.code.architecture.get_tracked_files")
    @patch("autocode.core.code.architecture.analyze_file_metrics")
    @patch("pathlib.Path.read_text")
    def test_snapshot_includes_js_file_metrics(
        self, mock_read, mock_analyze, mock_get_files, mock_git, mock_resolve_deps
    ):
        """Architecture snapshot should include JS files with their metrics."""
        from autocode.core.code.architecture import get_architecture_snapshot
        from autocode.core.code.models import FileMetrics

        mock_git.side_effect = lambda *args: {
            ("rev-parse", "HEAD"): "abc123def456789",
            ("rev-parse", "--short", "HEAD"): "abc123d",
            ("rev-parse", "--abbrev-ref", "HEAD"): "main",
        }.get(args, "")

        mock_get_files.return_value = [
            "src/app.py",
            "web/index.js",
            "web/utils.mjs",
        ]
        mock_read.return_value = "x = 1\n"
        mock_resolve_deps.return_value = ([], [])

        def analyze_side_effect(path, content):
            lang = "python" if path.endswith(".py") else "javascript"
            return FileMetrics(
                path=path, language=lang,
                sloc=100, comments=10, blanks=5, total_loc=115,
                functions=[], classes_count=1, functions_count=3,
                avg_complexity=2.5, max_complexity=6, max_nesting=2,
                maintainability_index=75.0,
            )

        mock_analyze.side_effect = analyze_side_effect

        result = get_architecture_snapshot()

        assert result.success is True
        snapshot = result.result
        assert snapshot is not None
        assert snapshot.total_files == 3  # 1 py + 2 js
        assert snapshot.total_sloc == 300  # 3 * 100

        node_ids = {n.id for n in snapshot.nodes}
        assert "src/app.py" in node_ids
        assert "web/index.js" in node_ids
        assert "web/utils.mjs" in node_ids
