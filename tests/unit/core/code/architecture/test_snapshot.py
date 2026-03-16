"""Tests for get_architecture_snapshot() endpoint."""
from unittest.mock import patch
from pathlib import Path

from .conftest import make_simple_file_metrics


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
        assert snapshot.dependencies == []
        assert snapshot.circular_dependencies == []


# ==============================================================================
# G) ENDPOINT INTEGRATION WITH DEPENDENCIES
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

        assert hasattr(snapshot, "dependencies")
        assert isinstance(snapshot.dependencies, list)
        assert len(snapshot.dependencies) >= 1

        dep = snapshot.dependencies[0]
        assert dep.source == "pkg/a.py"
        assert dep.target == "pkg/b.py"
        assert "helper" in dep.import_names

        assert hasattr(snapshot, "circular_dependencies")
        assert snapshot.circular_dependencies == []


# ==============================================================================
# H-SNAPSHOT) ARCHITECTURE SNAPSHOT WITH JS
# ==============================================================================


class TestArchitectureSnapshotWithJS:
    """Tests for get_architecture_snapshot() including JS files."""

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


# ==============================================================================
# L2) HISTORICAL SNAPSHOT
# ==============================================================================


class TestGetArchitectureSnapshotHistorical:
    """Tests for get_architecture_snapshot(commit_hash=...) — historical mode."""

    @patch("autocode.core.code.architecture.git_show")
    @patch("autocode.core.code.architecture.get_tracked_files_at_commit")
    @patch("autocode.core.code.architecture.get_tracked_files")
    @patch("autocode.core.code.architecture.git")
    @patch("autocode.core.code.architecture.analyze_file_metrics")
    def test_snapshot_with_commit_hash_uses_get_tracked_files_at_commit(
        self, mock_analyze, mock_git, mock_get_files, mock_get_files_at, mock_git_show
    ):
        """commit_hash set → must call get_tracked_files_at_commit, NOT get_tracked_files."""
        from autocode.core.code.architecture import get_architecture_snapshot

        mock_git.side_effect = lambda *args, **kwargs: {
            ("rev-parse", "abc123"): "abc123def456",
            ("rev-parse", "--short", "abc123"): "abc123d",
            ("log", "-1", "--format=%D", "abc123"): "HEAD -> main",
        }.get(args, "")
        mock_get_files_at.return_value = ["src/app.py"]
        mock_git_show.return_value = "x = 1\n"
        mock_analyze.return_value = make_simple_file_metrics("src/app.py")

        result = get_architecture_snapshot(commit_hash="abc123")

        assert result.success is True
        mock_get_files_at.assert_called_once()
        mock_get_files.assert_not_called()

    @patch("autocode.core.code.architecture.git_show")
    @patch("autocode.core.code.architecture.get_tracked_files_at_commit")
    @patch("autocode.core.code.architecture.get_tracked_files")
    @patch("autocode.core.code.architecture.git")
    @patch("autocode.core.code.architecture.analyze_file_metrics")
    def test_snapshot_with_commit_hash_uses_git_show_as_content_reader(
        self, mock_analyze, mock_git, mock_get_files, mock_get_files_at, mock_git_show
    ):
        """commit_hash set → file content must come from git_show, NOT from disk."""
        from autocode.core.code.architecture import get_architecture_snapshot

        mock_git.side_effect = lambda *args, **kwargs: {
            ("rev-parse", "abc123"): "abc123def456",
            ("rev-parse", "--short", "abc123"): "abc123d",
            ("log", "-1", "--format=%D", "abc123"): "HEAD -> main",
        }.get(args, "")
        mock_get_files_at.return_value = ["src/app.py"]
        mock_git_show.return_value = "x = 1\n"
        mock_analyze.return_value = make_simple_file_metrics("src/app.py")

        with patch.object(Path, "read_text") as mock_read:
            result = get_architecture_snapshot(commit_hash="abc123")
            mock_read.assert_not_called()

        assert result.success is True
        mock_git_show.assert_called()
        call_args = mock_git_show.call_args_list
        assert any("abc123:src/app.py" in str(c) for c in call_args)

    @patch("autocode.core.code.architecture.git_show")
    @patch("autocode.core.code.architecture.get_tracked_files_at_commit")
    @patch("autocode.core.code.architecture.get_tracked_files")
    @patch("autocode.core.code.architecture.git")
    @patch("autocode.core.code.architecture.analyze_file_metrics")
    def test_snapshot_with_commit_hash_returns_correct_commit_metadata(
        self, mock_analyze, mock_git, mock_get_files, mock_get_files_at, mock_git_show
    ):
        """commit_hash set → result must carry the resolved hash and short hash."""
        from autocode.core.code.architecture import get_architecture_snapshot

        mock_git.side_effect = lambda *args, **kwargs: {
            ("rev-parse", "abc123"): "abc123def456789",
            ("rev-parse", "--short", "abc123"): "abc123d",
            ("log", "-1", "--format=%D", "abc123"): "HEAD -> main",
        }.get(args, "")
        mock_get_files_at.return_value = ["src/app.py"]
        mock_git_show.return_value = "x = 1\n"
        mock_analyze.return_value = make_simple_file_metrics("src/app.py")

        result = get_architecture_snapshot(commit_hash="abc123")

        assert result.success is True
        snapshot = result.result
        assert snapshot.commit_hash == "abc123def456789"
        assert snapshot.commit_short == "abc123d"

    @patch("autocode.core.code.architecture.git_show")
    @patch("autocode.core.code.architecture.get_tracked_files_at_commit")
    @patch("autocode.core.code.architecture.get_tracked_files")
    @patch("autocode.core.code.architecture.git")
    @patch("autocode.core.code.architecture.analyze_file_metrics")
    @patch("pathlib.Path.read_text")
    def test_snapshot_without_commit_hash_unchanged(
        self, mock_read, mock_analyze, mock_git,
        mock_get_files, mock_get_files_at, mock_git_show
    ):
        """commit_hash='' → existing behavior: get_tracked_files + disk reads."""
        from autocode.core.code.architecture import get_architecture_snapshot

        mock_git.side_effect = lambda *args, **kwargs: {
            ("rev-parse", "HEAD"): "abc123def456789",
            ("rev-parse", "--short", "HEAD"): "abc123d",
            ("rev-parse", "--abbrev-ref", "HEAD"): "main",
        }.get(args, "")
        mock_get_files.return_value = ["src/app.py"]
        mock_read.return_value = "x = 1\n"
        mock_analyze.return_value = make_simple_file_metrics("src/app.py")

        result = get_architecture_snapshot()  # no commit_hash

        assert result.success is True
        mock_get_files.assert_called_once()
        mock_get_files_at.assert_not_called()
        mock_git_show.assert_not_called()
