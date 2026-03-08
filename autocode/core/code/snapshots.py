"""
snapshots.py
Persistencia de snapshots de métricas en .autocode/metrics/.

Proporciona:
- Guardado de snapshots como JSON
- Carga por commit hash, snapshot previo, historial
- Listado de snapshots con resumen
"""
import json
import logging
from pathlib import Path
from typing import Optional

from autocode.core.code.models import (
    MetricsSnapshot,
    MetricsHistoryPoint,
)

logger = logging.getLogger(__name__)

# Directorio de snapshots (relativo al CWD del proyecto host)
METRICS_DIR = ".autocode/metrics"


def save_snapshot(snapshot: MetricsSnapshot, *, metrics_dir: str = METRICS_DIR) -> None:
    """Save snapshot as JSON in the metrics directory."""
    dir_path = Path(metrics_dir)
    dir_path.mkdir(parents=True, exist_ok=True)
    fname = f"{snapshot.commit_short}.json"
    path = dir_path / fname
    path.write_text(snapshot.model_dump_json(indent=2), encoding="utf-8")
    logger.debug(f"Snapshot saved: {path}")


def load_snapshot_by_hash(
    commit_hash: str, *, metrics_dir: str = METRICS_DIR
) -> Optional[MetricsSnapshot]:
    """Load a snapshot matching the given commit hash (full), if it exists."""
    dir_path = Path(metrics_dir)
    if not dir_path.exists():
        return None
    for f in dir_path.glob("*.json"):
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
            if data.get("commit_hash") == commit_hash:
                return MetricsSnapshot(**data)
        except Exception:
            continue
    return None


def load_previous_snapshot(
    current_hash: str, *, metrics_dir: str = METRICS_DIR
) -> Optional[MetricsSnapshot]:
    """Load the most recent snapshot that isn't the current commit."""
    dir_path = Path(metrics_dir)
    if not dir_path.exists():
        return None
    files = sorted(dir_path.glob("*.json"), reverse=True)
    for f in files:
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
            snap = MetricsSnapshot(**data)
            if snap.commit_hash != current_hash:
                return snap
        except Exception:
            continue
    return None


def load_history_points(
    max_count: int, *, metrics_dir: str = METRICS_DIR
) -> list[MetricsHistoryPoint]:
    """Load all snapshots and extract lightweight history points for charting."""
    dir_path = Path(metrics_dir)
    if not dir_path.exists():
        return []

    points: list[MetricsHistoryPoint] = []
    for f in sorted(dir_path.glob("*.json")):
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
            dist = data.get("complexity_distribution", {})
            circular = data.get("circular_deps", [])
            points.append(MetricsHistoryPoint(
                commit_hash=data.get("commit_hash", ""),
                commit_short=data.get("commit_short", ""),
                branch=data.get("branch", ""),
                timestamp=data.get("timestamp", ""),
                total_sloc=data.get("total_sloc", 0),
                total_files=data.get("total_files", 0),
                total_functions=data.get("total_functions", 0),
                total_classes=data.get("total_classes", 0),
                total_comments=data.get("total_comments", 0),
                total_blanks=data.get("total_blanks", 0),
                avg_complexity=data.get("avg_complexity", 0.0),
                avg_mi=data.get("avg_mi", 0.0),
                rank_a=dist.get("A", 0),
                rank_b=dist.get("B", 0),
                rank_c=dist.get("C", 0),
                rank_d=dist.get("D", 0),
                rank_e=dist.get("E", 0),
                rank_f=dist.get("F", 0),
                circular_deps_count=len(circular),
            ))
        except Exception as e:
            logger.debug(f"Skip snapshot {f.name}: {e}")
            continue

    # Sort by timestamp (oldest first) and limit
    points.sort(key=lambda p: p.timestamp)
    return points[-max_count:] if len(points) > max_count else points


def list_snapshots(*, metrics_dir: str = METRICS_DIR) -> list[dict]:
    """List all saved snapshots with summary info."""
    dir_path = Path(metrics_dir)
    if not dir_path.exists():
        return []
    result = []
    for f in sorted(dir_path.glob("*.json"), reverse=True):
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
            result.append({
                "filename": f.name,
                "commit_short": data.get("commit_short", ""),
                "branch": data.get("branch", ""),
                "timestamp": data.get("timestamp", ""),
                "total_files": data.get("total_files", 0),
                "total_sloc": data.get("total_sloc", 0),
                "avg_complexity": data.get("avg_complexity", 0),
                "avg_mi": data.get("avg_mi", 0),
            })
        except Exception:
            continue
    return result
