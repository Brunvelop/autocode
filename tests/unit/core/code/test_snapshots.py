"""
Tests for autocode.core.code.snapshots — snapshot persistence.

All tests use tmp_path for filesystem isolation.
"""
import json

import pytest

from autocode.core.code.models import (
    MetricsSnapshot,
    MetricsHistoryPoint,
    FileMetrics,
    FunctionMetrics,
    PackageCoupling,
)


def _make_snapshot(
    commit_hash: str = "abc123def456",
    commit_short: str = "abc123d",
    branch: str = "main",
    timestamp: str = "2025-01-15T10:00:00",
    total_files: int = 5,
    total_sloc: int = 200,
    total_comments: int = 30,
    total_blanks: int = 20,
    total_functions: int = 10,
    total_classes: int = 3,
    avg_complexity: float = 3.5,
    avg_mi: float = 65.0,
    complexity_distribution: dict | None = None,
    files: list | None = None,
    coupling: list | None = None,
    circular_deps: list | None = None,
) -> MetricsSnapshot:
    """Helper to build a MetricsSnapshot with sensible defaults."""
    return MetricsSnapshot(
        commit_hash=commit_hash,
        commit_short=commit_short,
        branch=branch,
        timestamp=timestamp,
        files=files or [],
        total_files=total_files,
        total_sloc=total_sloc,
        total_comments=total_comments,
        total_blanks=total_blanks,
        total_functions=total_functions,
        total_classes=total_classes,
        avg_complexity=avg_complexity,
        avg_mi=avg_mi,
        complexity_distribution=complexity_distribution or {"A": 8, "B": 2},
        coupling=coupling or [],
        circular_deps=circular_deps or [],
    )


# ==========================================================================
# TestSaveSnapshot
# ==========================================================================


class TestSaveSnapshot:
    """Tests for save_snapshot() — persists MetricsSnapshot as JSON."""

    def test_creates_directory_and_file(self, tmp_path):
        from autocode.core.code.snapshots import save_snapshot

        snapshot = _make_snapshot(commit_short="abc123d")
        save_snapshot(snapshot, metrics_dir=str(tmp_path / "metrics"))

        metrics_dir = tmp_path / "metrics"
        assert metrics_dir.exists()
        assert (metrics_dir / "abc123d.json").exists()

    def test_filename_uses_commit_short(self, tmp_path):
        from autocode.core.code.snapshots import save_snapshot

        snapshot = _make_snapshot(commit_short="deadbee")
        save_snapshot(snapshot, metrics_dir=str(tmp_path / "metrics"))

        assert (tmp_path / "metrics" / "deadbee.json").exists()

    def test_content_is_valid_json(self, tmp_path):
        from autocode.core.code.snapshots import save_snapshot

        snapshot = _make_snapshot(commit_hash="full_hash_123", commit_short="full_ha")
        save_snapshot(snapshot, metrics_dir=str(tmp_path / "metrics"))

        content = (tmp_path / "metrics" / "full_ha.json").read_text(encoding="utf-8")
        data = json.loads(content)
        assert data["commit_hash"] == "full_hash_123"
        assert data["total_sloc"] == 200
        assert data["avg_mi"] == 65.0


# ==========================================================================
# TestLoadSnapshotByHash
# ==========================================================================


class TestLoadSnapshotByHash:
    """Tests for load_snapshot_by_hash() — find snapshot by full commit hash."""

    def test_loads_matching_snapshot(self, tmp_path):
        from autocode.core.code.snapshots import save_snapshot, load_snapshot_by_hash

        snapshot = _make_snapshot(commit_hash="abc123def456", commit_short="abc123d")
        save_snapshot(snapshot, metrics_dir=str(tmp_path / "metrics"))

        result = load_snapshot_by_hash("abc123def456", metrics_dir=str(tmp_path / "metrics"))
        assert result is not None
        assert result.commit_hash == "abc123def456"
        assert result.total_sloc == 200

    def test_returns_none_when_not_found(self, tmp_path):
        from autocode.core.code.snapshots import save_snapshot, load_snapshot_by_hash

        snapshot = _make_snapshot(commit_hash="abc123def456", commit_short="abc123d")
        save_snapshot(snapshot, metrics_dir=str(tmp_path / "metrics"))

        result = load_snapshot_by_hash("nonexistent_hash", metrics_dir=str(tmp_path / "metrics"))
        assert result is None

    def test_returns_none_when_dir_missing(self, tmp_path):
        from autocode.core.code.snapshots import load_snapshot_by_hash

        result = load_snapshot_by_hash("any_hash", metrics_dir=str(tmp_path / "nonexistent"))
        assert result is None


# ==========================================================================
# TestLoadPreviousSnapshot
# ==========================================================================


class TestLoadPreviousSnapshot:
    """Tests for load_previous_snapshot() — most recent snapshot != current."""

    def test_loads_most_recent_non_current(self, tmp_path):
        from autocode.core.code.snapshots import save_snapshot, load_previous_snapshot

        metrics_dir = str(tmp_path / "metrics")

        # Save two snapshots
        snap_old = _make_snapshot(
            commit_hash="old_hash_111", commit_short="old_has", total_sloc=100
        )
        save_snapshot(snap_old, metrics_dir=metrics_dir)

        snap_new = _make_snapshot(
            commit_hash="new_hash_222", commit_short="new_has", total_sloc=200
        )
        save_snapshot(snap_new, metrics_dir=metrics_dir)

        result = load_previous_snapshot("new_hash_222", metrics_dir=metrics_dir)
        assert result is not None
        assert result.commit_hash == "old_hash_111"
        assert result.total_sloc == 100

    def test_returns_none_when_only_current(self, tmp_path):
        from autocode.core.code.snapshots import save_snapshot, load_previous_snapshot

        metrics_dir = str(tmp_path / "metrics")

        snap = _make_snapshot(commit_hash="only_hash", commit_short="only_ha")
        save_snapshot(snap, metrics_dir=metrics_dir)

        result = load_previous_snapshot("only_hash", metrics_dir=metrics_dir)
        assert result is None

    def test_returns_none_when_dir_missing(self, tmp_path):
        from autocode.core.code.snapshots import load_previous_snapshot

        result = load_previous_snapshot("any_hash", metrics_dir=str(tmp_path / "nope"))
        assert result is None


# ==========================================================================
# TestLoadHistoryPoints
# ==========================================================================


class TestLoadHistoryPoints:
    """Tests for load_history_points() — lightweight points for charting."""

    def test_loads_all_snapshots_sorted(self, tmp_path):
        from autocode.core.code.snapshots import save_snapshot, load_history_points

        metrics_dir = str(tmp_path / "metrics")

        snap1 = _make_snapshot(
            commit_hash="hash_1", commit_short="hash_01",
            timestamp="2025-01-01T10:00:00", total_sloc=100,
        )
        snap2 = _make_snapshot(
            commit_hash="hash_2", commit_short="hash_02",
            timestamp="2025-01-02T10:00:00", total_sloc=200,
        )
        # Save in reverse order to test sorting
        save_snapshot(snap2, metrics_dir=metrics_dir)
        save_snapshot(snap1, metrics_dir=metrics_dir)

        points = load_history_points(100, metrics_dir=metrics_dir)
        assert len(points) == 2
        # Should be sorted chronologically (oldest first)
        assert points[0].timestamp == "2025-01-01T10:00:00"
        assert points[1].timestamp == "2025-01-02T10:00:00"
        assert points[0].total_sloc == 100
        assert points[1].total_sloc == 200

    def test_respects_max_count(self, tmp_path):
        from autocode.core.code.snapshots import save_snapshot, load_history_points

        metrics_dir = str(tmp_path / "metrics")

        for i in range(5):
            snap = _make_snapshot(
                commit_hash=f"hash_{i}",
                commit_short=f"short{i}",
                timestamp=f"2025-01-0{i+1}T10:00:00",
            )
            save_snapshot(snap, metrics_dir=metrics_dir)

        points = load_history_points(3, metrics_dir=metrics_dir)
        assert len(points) == 3
        # Should keep the 3 most recent
        assert points[0].timestamp == "2025-01-03T10:00:00"
        assert points[2].timestamp == "2025-01-05T10:00:00"

    def test_returns_empty_when_no_dir(self, tmp_path):
        from autocode.core.code.snapshots import load_history_points

        points = load_history_points(100, metrics_dir=str(tmp_path / "nonexistent"))
        assert points == []

    def test_extracts_complexity_distribution(self, tmp_path):
        from autocode.core.code.snapshots import save_snapshot, load_history_points

        metrics_dir = str(tmp_path / "metrics")

        snap = _make_snapshot(
            commit_hash="hash_x", commit_short="hash_x",
            timestamp="2025-01-01T10:00:00",
            complexity_distribution={"A": 10, "B": 5, "C": 2, "D": 1, "E": 0, "F": 0},
            circular_deps=[["pkg1", "pkg2"]],
        )
        save_snapshot(snap, metrics_dir=metrics_dir)

        points = load_history_points(100, metrics_dir=metrics_dir)
        assert len(points) == 1
        assert points[0].rank_a == 10
        assert points[0].rank_b == 5
        assert points[0].rank_c == 2
        assert points[0].rank_d == 1
        assert points[0].circular_deps_count == 1


# ==========================================================================
# TestListSnapshots
# ==========================================================================


class TestListSnapshots:
    """Tests for list_snapshots() — summary listing."""

    def test_lists_all_with_summary(self, tmp_path):
        from autocode.core.code.snapshots import save_snapshot, list_snapshots

        metrics_dir = str(tmp_path / "metrics")

        snap1 = _make_snapshot(
            commit_hash="hash_a", commit_short="hash_a1",
            branch="main", total_files=3, total_sloc=100,
        )
        snap2 = _make_snapshot(
            commit_hash="hash_b", commit_short="hash_b2",
            branch="develop", total_files=5, total_sloc=200,
        )
        save_snapshot(snap1, metrics_dir=metrics_dir)
        save_snapshot(snap2, metrics_dir=metrics_dir)

        result = list_snapshots(metrics_dir=metrics_dir)
        assert len(result) == 2

        # Each entry should have summary fields
        for entry in result:
            assert "filename" in entry
            assert "commit_short" in entry
            assert "branch" in entry
            assert "timestamp" in entry
            assert "total_files" in entry
            assert "total_sloc" in entry
            assert "avg_complexity" in entry
            assert "avg_mi" in entry

    def test_returns_empty_when_no_dir(self, tmp_path):
        from autocode.core.code.snapshots import list_snapshots

        result = list_snapshots(metrics_dir=str(tmp_path / "nonexistent"))
        assert result == []
