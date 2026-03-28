"""
Tests for get_working_changes_metrics() endpoint and _analyze_working_changes().

TDD: These tests were written BEFORE the implementation.
All tests mock git/filesystem calls for isolation.
"""
import pytest
from unittest.mock import patch, MagicMock


# ===========================================================================
# Helpers
# ===========================================================================


def _make_file_metrics(
    path: str = "src/main.py",
    language: str = "python",
    sloc: int = 100,
    comments: int = 10,
    blanks: int = 5,
    avg_complexity: float = 3.0,
    maintainability_index: float = 70.0,
):
    from autocode.core.code.models import FileMetrics

    return FileMetrics(
        path=path,
        language=language,
        sloc=sloc,
        comments=comments,
        blanks=blanks,
        total_loc=sloc + comments + blanks,
        functions=[],
        classes_count=0,
        functions_count=0,
        avg_complexity=avg_complexity,
        max_complexity=int(avg_complexity),
        max_nesting=1,
        maintainability_index=maintainability_index,
    )


# ===========================================================================
# TestAnalyzeWorkingChanges
# ===========================================================================


class TestAnalyzeWorkingChanges:
    """Tests for _analyze_working_changes() and get_working_changes_metrics()."""

    @pytest.fixture
    def mock_git_clean(self):
        """Fixture: repo limpio (sin cambios)."""
        with patch("autocode.core.code.metrics.git") as mock_git, \
             patch("autocode.core.code.metrics.git_show") as mock_git_show, \
             patch("autocode.core.code.metrics.analyze_file_metrics") as mock_analyze:
            mock_git.side_effect = lambda *args: {
                ("diff", "--name-status", "HEAD"): "",
                ("ls-files", "--others", "--exclude-standard"): "",
            }.get(args, "")
            mock_git_show.return_value = None
            yield {
                "git": mock_git,
                "git_show": mock_git_show,
                "analyze": mock_analyze,
            }

    @pytest.fixture
    def mock_git_modified_py(self):
        """Fixture: un archivo .py modificado en el working tree."""
        with patch("autocode.core.code.metrics.git") as mock_git, \
             patch("autocode.core.code.metrics.git_show") as mock_git_show, \
             patch("autocode.core.code.metrics.analyze_file_metrics") as mock_analyze, \
             patch("pathlib.Path.read_text") as mock_read:
            mock_git.side_effect = lambda *args: {
                ("diff", "--name-status", "HEAD"): "M\tsrc/main.py",
                ("ls-files", "--others", "--exclude-standard"): "",
            }.get(args, "")
            mock_git_show.return_value = "def old_func():\n    pass\n"
            mock_read.return_value = "def new_func():\n    return 42\n"
            mock_analyze.return_value = _make_file_metrics("src/main.py")
            yield {
                "git": mock_git,
                "git_show": mock_git_show,
                "analyze": mock_analyze,
                "read": mock_read,
            }

    @pytest.fixture
    def mock_git_untracked_js(self):
        """Fixture: un archivo .js nuevo (untracked)."""
        with patch("autocode.core.code.metrics.git") as mock_git, \
             patch("autocode.core.code.metrics.git_show") as mock_git_show, \
             patch("autocode.core.code.metrics.analyze_file_metrics") as mock_analyze, \
             patch("pathlib.Path.read_text") as mock_read:
            mock_git.side_effect = lambda *args: {
                ("diff", "--name-status", "HEAD"): "",
                ("ls-files", "--others", "--exclude-standard"): "web/app.js",
            }.get(args, "")
            mock_git_show.return_value = None
            mock_read.return_value = "export function hello() { return 'hello'; }\n"
            mock_analyze.return_value = _make_file_metrics("web/app.js", language="javascript")
            yield {
                "git": mock_git,
                "git_show": mock_git_show,
                "analyze": mock_analyze,
                "read": mock_read,
            }

    # -----------------------------------------------------------------------

    def test_returns_commit_metrics_structure(self, mock_git_clean):
        """_analyze_working_changes() debe retornar CommitMetrics con campos correctos."""
        from autocode.core.code.metrics import _analyze_working_changes
        from autocode.core.code.models import CommitMetrics

        result = _analyze_working_changes()

        assert isinstance(result, CommitMetrics)
        assert result.commit_hash == "working"
        assert result.commit_short == "working"
        assert isinstance(result.files, list)
        assert isinstance(result.summary, dict)
        assert "delta_sloc" in result.summary
        assert "files_analyzed" in result.summary

    def test_returns_empty_when_clean(self, mock_git_clean):
        """Repo limpio → 0 archivos analizados, deltas en 0."""
        from autocode.core.code.metrics import _analyze_working_changes

        result = _analyze_working_changes()

        assert result.files == []
        assert result.summary["files_analyzed"] == 0
        assert result.summary["delta_sloc"] == 0

    def test_analyzes_modified_py_file(self, mock_git_modified_py):
        """Archivo .py modificado: before=HEAD content, after=disk content."""
        from autocode.core.code.metrics import _analyze_working_changes

        result = _analyze_working_changes()

        assert len(result.files) == 1
        cfm = result.files[0]
        assert cfm.path == "src/main.py"
        assert cfm.status == "modified"
        assert cfm.before is not None
        assert cfm.after is not None
        # git_show fue llamado con "HEAD:src/main.py"
        mock_git_modified_py["git_show"].assert_called_once_with("HEAD:src/main.py")

    def test_analyzes_added_js_file(self, mock_git_untracked_js):
        """Archivo .js untracked (nuevo): before=None, after=disk content."""
        from autocode.core.code.metrics import _analyze_working_changes

        result = _analyze_working_changes()

        assert len(result.files) == 1
        cfm = result.files[0]
        assert cfm.path == "web/app.js"
        assert cfm.status == "added"
        assert cfm.before is None
        assert cfm.after is not None
        # git_show NO debe llamarse para archivos untracked
        mock_git_untracked_js["git_show"].assert_not_called()

    def test_skips_non_code_files(self):
        """Archivos .md, .txt, etc. deben ser ignorados."""
        with patch("autocode.core.code.metrics.git") as mock_git, \
             patch("autocode.core.code.metrics.git_show") as mock_git_show, \
             patch("autocode.core.code.metrics.analyze_file_metrics") as mock_analyze, \
             patch("pathlib.Path.read_text") as mock_read:

            mock_git.side_effect = lambda *args: {
                ("diff", "--name-status", "HEAD"): (
                    "M\tREADME.md\n"
                    "M\tconfig.txt\n"
                    "M\tsrc/app.py\n"
                    "M\tstyles.css"
                ),
                ("ls-files", "--others", "--exclude-standard"): "notes.txt",
            }.get(args, "")
            mock_git_show.return_value = "old content"
            mock_read.return_value = "new content"
            mock_analyze.return_value = _make_file_metrics("src/app.py")

            from autocode.core.code.metrics import _analyze_working_changes

            result = _analyze_working_changes()

        # Solo src/app.py pasa el filtro
        assert len(result.files) == 1
        assert result.files[0].path == "src/app.py"

    def test_deltas_are_correct(self):
        """Los deltas de SLOC, CC y MI deben calcularse correctamente."""
        before_fm = _make_file_metrics(
            path="src/calc.py",
            sloc=100,
            avg_complexity=3.0,
            maintainability_index=70.0,
        )
        after_fm = _make_file_metrics(
            path="src/calc.py",
            sloc=120,
            avg_complexity=4.0,
            maintainability_index=65.0,
        )

        call_count = [0]

        def analyze_side_effect(path, content):
            call_count[0] += 1
            if call_count[0] == 1:
                return before_fm
            return after_fm

        with patch("autocode.core.code.metrics.git") as mock_git, \
             patch("autocode.core.code.metrics.git_show") as mock_git_show, \
             patch("autocode.core.code.metrics.analyze_file_metrics") as mock_analyze, \
             patch("pathlib.Path.read_text") as mock_read:

            mock_git.side_effect = lambda *args: {
                ("diff", "--name-status", "HEAD"): "M\tsrc/calc.py",
                ("ls-files", "--others", "--exclude-standard"): "",
            }.get(args, "")
            mock_git_show.return_value = "before content"
            mock_read.return_value = "after content"
            mock_analyze.side_effect = analyze_side_effect

            from autocode.core.code.metrics import _analyze_working_changes

            result = _analyze_working_changes()

        assert len(result.files) == 1
        cfm = result.files[0]
        assert cfm.delta_sloc == 20          # 120 - 100
        assert cfm.delta_complexity == 1.0   # 4.0 - 3.0
        assert cfm.delta_mi == -5.0          # 65.0 - 70.0
        assert result.summary["delta_sloc"] == 20


# ===========================================================================
# TestGetWorkingChangesMetricsEndpoint
# ===========================================================================


class TestGetWorkingChangesMetricsEndpoint:
    """Tests for the registered endpoint get_working_changes_metrics()."""

    def test_endpoint_returns_commit_metrics_directly(self):
        """El endpoint debe retornar CommitMetrics directamente."""
        from autocode.core.code.models import CommitMetrics

        fake_metrics = CommitMetrics(
            commit_hash="working",
            commit_short="working",
            files=[],
            summary={"delta_sloc": 0, "delta_avg_complexity": 0, "files_analyzed": 0},
        )

        with patch("autocode.core.code.metrics._analyze_working_changes") as mock_analyze:
            mock_analyze.return_value = fake_metrics

            from autocode.core.code.metrics import get_working_changes_metrics

            result = get_working_changes_metrics()

        assert isinstance(result, CommitMetrics)
        assert result.commit_hash == "working"
        assert result.files == []

    def test_endpoint_raises_http_exception_on_error(self):
        """El endpoint debe lanzar HTTPException cuando ocurre un error."""
        import pytest
        from fastapi import HTTPException

        with patch("autocode.core.code.metrics._analyze_working_changes") as mock_analyze:
            mock_analyze.side_effect = RuntimeError("git error")

            from autocode.core.code.metrics import get_working_changes_metrics

            with pytest.raises(HTTPException) as exc_info:
                get_working_changes_metrics()

        assert exc_info.value.status_code == 500
        assert "git error" in exc_info.value.detail
