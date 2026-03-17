"""
Shared test helpers for planning executor tests.
"""

import json
from unittest.mock import MagicMock

from autocode.core.planning.models import (
    CommitPlan,
    PlanTask,
    TaskExecutionResult,
)


def _create_test_plan(tmp_path, title="Test", num_tasks=1, status="draft"):
    """Crea un plan de test en tmp_path y retorna el CommitPlan."""
    tasks = [
        PlanTask(type="modify", path=f"src/file{i}.py", description=f"Task {i}")
        for i in range(num_tasks)
    ]
    plan = CommitPlan(
        id="20260101-000000",
        title=title,
        status=status,
        tasks=tasks,
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


async def _mock_task_generator(task_result, status_messages=None):
    """Helper: creates an async generator that mimics _execute_single_task.

    Yields status SSE events first (if any), then the TaskExecutionResult.
    """
    from autocode.core.ai.streaming import _format_sse

    if status_messages:
        for msg in status_messages:
            yield _format_sse(
                "status",
                {"task_index": task_result.task_index, "message": msg},
            )

    # Emit a task_debug event (like the real implementation)
    yield _format_sse(
        "task_debug",
        {
            "task_index": task_result.task_index,
            "trajectory": [],
            "history": [],
            "prompt_tokens": task_result.prompt_tokens,
            "completion_tokens": task_result.completion_tokens,
            "total_tokens": task_result.total_tokens,
            "total_cost": task_result.total_cost,
        },
    )

    yield task_result
