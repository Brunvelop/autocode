"""Tests for compact architecture hotspot ranking."""

from pathlib import Path
from unittest.mock import patch


class TestGetArchitectureHotspots:
    """Tests for the compact MCP hotspot endpoint."""

    @patch("autocode.core.code.architecture.get_tracked_files")
    @patch("pathlib.Path.read_text")
    def test_ranks_by_combined_architecture_signals(self, mock_read, mock_tracked_files):
        from autocode.core.code.architecture import get_architecture_hotspots

        contents = {
            "pkg/a.py": (
                "from pkg.b import B\n"
                "from pkg.c import C\n"
                "def alpha(x):\n"
                "    if x > 0:\n"
                "        return x\n"
                "    return -x\n"
            ),
            "pkg/b.py": (
                "from pkg.a import alpha\n"
                "def beta(x):\n"
                "    if x > 0:\n"
                "        if x > 10:\n"
                "            return x\n"
                "    return 0\n"
            ),
            "pkg/c.py": "from pkg.a import alpha\nVALUE = 1\n",
        }
        mock_tracked_files.return_value = list(contents.keys())

        def patched_read(self, *args, **kwargs):
            return contents.get(str(self), "")

        with patch.object(Path, "read_text", patched_read):
            result = get_architecture_hotspots(limit=2)

        assert result.summary == {
            "path": ".",
            "files_analyzed": 3,
            "hotspot_count": 2,
            "cycle_files": 3,
            "returned_limit": 2,
        }
        assert [hotspot.path for hotspot in result.hotspots] == ["pkg/a.py", "pkg/b.py"]
        assert result.hotspots[0].in_cycle is True
        assert "fan_in=2" in result.hotspots[0].reasons
        assert "fan_out=2" in result.hotspots[0].reasons
        assert "in_cycle" in result.hotspots[0].reasons

    @patch("autocode.core.code.architecture.get_tracked_files")
    def test_respects_path_filter(self, mock_tracked_files):
        from autocode.core.code.architecture import get_architecture_hotspots

        mock_tracked_files.return_value = [
            "pkg/a.py",
            "pkg/b.py",
            "web/x.js",
        ]

        with patch(
            "autocode.core.code.architecture._build_architecture_nodes",
            return_value=[
                type("Node", (), {"type": "file", "path": "pkg/a.py", "avg_complexity": 1.0, "max_complexity": 2, "mi": 80.0})(),
                type("Node", (), {"type": "file", "path": "pkg/b.py", "avg_complexity": 2.0, "max_complexity": 3, "mi": 70.0})(),
            ],
        ) as mock_nodes, patch(
            "autocode.core.code.architecture._resolve_file_dependencies",
            return_value=([], []),
        ):
            result = get_architecture_hotspots(path="pkg")

        assert mock_nodes.call_args.args[0] == ["pkg/a.py", "pkg/b.py"]
        assert result.summary["path"] == "pkg"

    @patch("autocode.core.code.architecture.get_tracked_files")
    def test_returns_empty_list_when_scope_has_no_files(self, mock_tracked_files):
        from autocode.core.code.architecture import get_architecture_hotspots

        mock_tracked_files.return_value = []

        result = get_architecture_hotspots()

        assert result.summary == {
            "path": ".",
            "files_analyzed": 0,
            "hotspot_count": 0,
            "cycle_files": 0,
            "returned_limit": 10,
        }
        assert result.hotspots == []

    def test_rank_helper_includes_mi_penalty_and_cycle_bonus(self):
        from autocode.core.code.architecture import _rank_architecture_hotspots

        node = type(
            "Node",
            (),
            {
                "path": "pkg/a.py",
                "avg_complexity": 4.0,
                "max_complexity": 10,
                "mi": 40.0,
            },
        )()

        hotspots = _rank_architecture_hotspots(
            [node],
            {
                ("pkg/a.py", "pkg/b.py"): {"X"},
                ("pkg/b.py", "pkg/a.py"): {"Y"},
                ("pkg/c.py", "pkg/a.py"): {"Z"},
            },
            [["pkg/a.py", "pkg/b.py"]],
        )

        assert len(hotspots) == 1
        hotspot = hotspots[0]
        assert hotspot.path == "pkg/a.py"
        assert hotspot.fan_in == 2
        assert hotspot.fan_out == 1
        assert hotspot.in_cycle is True
        assert hotspot.score == 19.0
        assert "mi=40.0" in hotspot.reasons