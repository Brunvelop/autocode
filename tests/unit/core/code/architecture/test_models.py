"""Tests for ArchitectureNode, ArchitectureSnapshot, ArchitectureSnapshotOutput models."""


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

    def test_architecture_snapshot_direct_return(self):
        """ArchitectureSnapshot can be returned directly without Output wrapper."""
        from autocode.core.code.models import (
            ArchitectureNode, ArchitectureSnapshot,
        )

        root = ArchitectureNode(
            id=".", parent_id=None, name="root", type="directory", path="."
        )
        snapshot = ArchitectureSnapshot(
            root_id=".", nodes=[root],
            commit_hash="abc", commit_short="abc", branch="main", timestamp="now",
        )
        assert snapshot.root_id == "."
        assert len(snapshot.nodes) == 1
        assert snapshot.nodes[0].id == "."
