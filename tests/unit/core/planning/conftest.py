"""
Shared test helpers for planning tests.
"""

import asyncio
import json
from typing import List
from unittest.mock import AsyncMock, patch

from autocode.core.planning.models import CommitPlan, ExecutionStep
from autocode.core.planning.backends.base import ExecutionResult


def _create_test_plan(tmp_path, title="Test", num_tasks=1, status="draft"):
    """Crea un plan de test en tmp_path y retorna el CommitPlan."""
    plan = CommitPlan(
        id="20260101-000000",
        title=title,
        description="Test plan description",
        status=status,
        created_at="2026-01-01T00:00:00",
    )
    (tmp_path / f"{plan.id}.json").write_text(plan.model_dump_json(indent=2))
    return plan


def _parse_sse(raw_event):
    """Parsea un string SSE 'event: X\\ndata: {...}\\n\\n' a dict."""
    lines = raw_event.strip().split("\n")
    event_type = lines[0].replace("event: ", "")
    data = json.loads(lines[1].replace("data: ", ""))
    return {"event": event_type, "data": data}


# ============================================================================
# PLAN / RESULT FACTORIES
# ============================================================================


def _make_plan(status="draft", **kwargs) -> CommitPlan:
    """Create a minimal CommitPlan for testing."""
    defaults = dict(
        id="20260101-120000",
        title="Add validation",
        description="Add input validation to the API endpoint.\n\n- Validate email format\n- Check required fields",
        parent_commit="abc123",
        branch="main",
        status=status,
        created_at="2026-01-01T12:00:00",
        updated_at="2026-01-01T12:00:00",
    )
    defaults.update(kwargs)
    return CommitPlan(**defaults)


def _make_execution_result(success=True, **kwargs) -> ExecutionResult:
    """Create an ExecutionResult for testing."""
    defaults = dict(
        success=success,
        files_changed=["src/api.py", "src/validators.py"],
        steps=[
            ExecutionStep(type="thinking", content="Analyzing requirements"),
            ExecutionStep(type="tool_use", tool="read_file", path="src/api.py", content="Reading file"),
            ExecutionStep(type="tool_use", tool="write_file", path="src/api.py", content="Writing changes"),
        ],
        total_tokens=1500,
        total_cost=0.003,
        session_id="sess-abc123",
        error="",
    )
    defaults.update(kwargs)
    return ExecutionResult(**defaults)


async def _collect_events(async_gen) -> List[dict]:
    """Collect all SSE events from an async generator, parsed."""
    events = []
    async for raw in async_gen:
        try:
            events.append(_parse_sse(raw))
        except (json.JSONDecodeError, IndexError):
            pass
    return events


def _find_event(events: List[dict], event_type: str) -> dict | None:
    """Find first event of a given type."""
    return next((e for e in events if e["event"] == event_type), None)


def _find_events(events: List[dict], event_type: str) -> List[dict]:
    """Find all events of a given type."""
    return [e for e in events if e["event"] == event_type]


# ============================================================================
# MOCK BACKEND
# ============================================================================


class MockBackend:
    """A fake backend that returns a preconfigured ExecutionResult."""

    name = "mock"

    def __init__(self, result: ExecutionResult | None = None):
        self._result = result or _make_execution_result()
        self.execute_called_with = None

    def abort(self) -> None:
        """No-op abort for tests."""
        pass

    async def execute(self, instruction, cwd, model, on_step):
        self.execute_called_with = {
            "instruction": instruction,
            "cwd": cwd,
            "model": model,
        }
        for step in self._result.steps:
            await on_step(step)
        return self._result


# ============================================================================
# PATCHES — shared across tests
# ============================================================================


def _patch_load_plan(plan):
    """Patch load_plan to return the given plan."""
    return patch("autocode.core.planning.executor.load_plan", return_value=plan)


def _patch_save_plan():
    """Patch save_plan to be a no-op."""
    return patch("autocode.core.planning.executor.save_plan")


def _patch_backend(backend):
    """Patch get_backend to return the given backend instance."""
    return patch("autocode.core.planning.executor.get_backend", return_value=backend)


def _patch_auto_review(verdict="approved", summary="All good"):
    """Patch auto_review to return a ReviewResult with given verdict."""
    from autocode.core.planning.models import ReviewResult
    result = ReviewResult(
        mode="auto",
        verdict=verdict,
        summary=summary,
        reviewed_by="auto",
    )
    return patch("autocode.core.planning.executor.auto_review", return_value=result)


def _patch_compute_review_metrics(metrics=None):
    """Patch compute_review_metrics."""
    return patch(
        "autocode.core.planning.executor.compute_review_metrics",
        return_value=metrics or [],
    )


def _patch_git_add_and_commit(commit_hash="def456"):
    """Patch git_add_and_commit."""
    return patch(
        "autocode.core.planning.executor.git_add_and_commit",
        return_value=commit_hash,
    )


def _patch_getcwd(cwd="/fake/project"):
    """Patch os.getcwd."""
    return patch("autocode.core.planning.executor.os.getcwd", return_value=cwd)


def _patch_sandbox(files=None, head="abc123"):
    """Patch ExecutionSandbox to return controlled files_changed and a no-op revert.

    Args:
        files: List of file paths collect_changes() should return. Defaults to [].
        head: SHA hash snapshot() should return.
    """
    if files is None:
        files = []
    mock_instance = AsyncMock()
    mock_instance.snapshot = AsyncMock(return_value=head)
    mock_instance.collect_changes = AsyncMock(return_value=files)
    mock_instance.revert = AsyncMock()
    mock_instance.pre_exec_head = head
    return patch(
        "autocode.core.planning.executor.ExecutionSandbox",
        return_value=mock_instance,
    )
