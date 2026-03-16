"""Tests for _build_architecture_nodes() and _propagate_metrics()."""
from unittest.mock import patch
from pathlib import Path

from .conftest import make_simple_file_metrics


# ==============================================================================
# B) HIERARCHY BUILDING TESTS
# ==============================================================================


class TestBuildArchitectureNodes:
    """Tests for _build_architecture_nodes() — hierarchy construction."""

    def _mock_analyze_file_metrics(self, path, content):
        """Helper: returns a FileMetrics-like object with predictable values."""
        from autocode.core.code.models import FileMetrics

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

        assert "." in node_map

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
        assert root_node.max_complexity == 10
        assert root_node.sloc == 300
        assert root_node.loc == 370
        assert root_node.functions_count == 8
        assert root_node.classes_count == 3
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

        assert node_map["src"].sloc == 100
        assert node_map["src"].mi == 70.0
        assert node_map["src"].avg_complexity == 3.0
        assert node_map["src"].max_complexity == 7
        assert node_map["src"].children_count == 1

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
        root_file = ArchitectureNode(
            id="setup.py", parent_id=".", name="setup.py", type="file", path="setup.py",
            sloc=50, loc=60, mi=90.0, avg_complexity=1.0, max_complexity=2,
            functions_count=1, classes_count=0,
        )
        pkg_file = ArchitectureNode(
            id="pkg/main.py", parent_id="pkg", name="main.py", type="file", path="pkg/main.py",
            sloc=150, loc=180, mi=60.0, avg_complexity=5.0, max_complexity=15,
            functions_count=6, classes_count=2,
        )
        nodes = [root, sub_dir, root_file, pkg_file]
        _propagate_metrics(nodes, ".")

        node_map = {n.id: n for n in nodes}

        assert node_map["pkg"].sloc == 150
        assert node_map["pkg"].mi == 60.0

        assert node_map["."].sloc == 200
        # MI weighted: (90*50 + 60*150) / 200 = (4500+9000)/200 = 67.5
        assert abs(node_map["."].mi - 67.5) < 0.1
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
# H) MULTI-LANGUAGE ARCHITECTURE NODES
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

        assert "autocode/core/code/metrics.py" in node_map
        assert "autocode/web/elements/app.js" in node_map
        assert "autocode/web/elements/utils.mjs" in node_map

        assert node_map["autocode/core/code/metrics.py"].type == "file"
        assert node_map["autocode/web/elements/app.js"].type == "file"
        assert node_map["autocode/web/elements/utils.mjs"].type == "file"

        assert "autocode/web/elements" in node_map
        assert "autocode/web" in node_map
        assert "autocode/core/code" in node_map


# ==============================================================================
# M) CONTENT READER INJECTION
# ==============================================================================


class TestBuildArchitectureNodesContentReader:
    """Tests for content_reader injection in _build_architecture_nodes."""

    def test_uses_custom_content_reader(self):
        """_build_architecture_nodes should call content_reader instead of Path.read_text."""
        from autocode.core.code.architecture import _build_architecture_nodes

        contents = {"app.py": "x = 1\ny = 2\n"}
        reader = lambda fpath: contents[fpath]

        with patch("autocode.core.code.architecture.analyze_file_metrics") as mock_analyze:
            mock_analyze.return_value = make_simple_file_metrics("app.py")
            _build_architecture_nodes(["app.py"], content_reader=reader)

        mock_analyze.assert_called_once_with("app.py", "x = 1\ny = 2\n")

    def test_default_content_reader_uses_disk(self):
        """Without content_reader, falls back to Path.read_text (backward compatible)."""
        from autocode.core.code.architecture import _build_architecture_nodes

        with patch.object(Path, "read_text", return_value="z = 3\n") as mock_read, \
             patch("autocode.core.code.architecture.analyze_file_metrics") as mock_analyze:
            mock_analyze.return_value = make_simple_file_metrics("app.py")
            _build_architecture_nodes(["app.py"])

        mock_read.assert_called_once()

    def test_custom_reader_not_calling_path_read_text(self):
        """When content_reader is provided, Path.read_text must NOT be called."""
        from autocode.core.code.architecture import _build_architecture_nodes

        reader = lambda fpath: "injected content\n"

        with patch.object(Path, "read_text") as mock_read, \
             patch("autocode.core.code.architecture.analyze_file_metrics") as mock_analyze:
            mock_analyze.return_value = make_simple_file_metrics("app.py")
            _build_architecture_nodes(["app.py"], content_reader=reader)

        mock_read.assert_not_called()
