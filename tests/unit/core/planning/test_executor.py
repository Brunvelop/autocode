"""
Tests for plan executor with ReAct + streaming SSE.

Tests cover:
- _build_task_instruction: prompt construction from task + plan context
- _extract_files_changed: file path extraction from ReAct trajectory
- _extract_cost_from_history: cost/token extraction from LM history
- stream_execute_plan: async SSE streaming with status transitions, cost tracking
"""

import json
from datetime import datetime
from pathlib import Path
from unittest.mock import patch, AsyncMock, MagicMock

import pytest

from autocode.core.planning.models import (
    CommitPlan,
    PlanTask,
    PlanContext,
    TaskExecutionResult,
    PlanExecutionState,
)


# ==============================================================================
# TEST HELPERS
# ==============================================================================


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


# ==============================================================================
# TESTS: _build_task_instruction
# ==============================================================================


class TestBuildTaskInstruction:
    """Tests for _build_task_instruction helper."""

    def test_includes_task_description(self):
        """La instrucción incluye la descripción de la task."""
        from autocode.core.planning.executor import _build_task_instruction

        task = PlanTask(type="modify", path="src/main.py", description="Add logging")
        plan = CommitPlan(id="t", title="t")
        instruction = _build_task_instruction(task, plan)
        assert "Add logging" in instruction

    def test_includes_task_details(self):
        """Si la task tiene details, se incluyen."""
        from autocode.core.planning.executor import _build_task_instruction

        task = PlanTask(
            type="modify",
            path="src/main.py",
            description="Add logging",
            details="Use Python logging module",
        )
        plan = CommitPlan(id="t", title="t")
        instruction = _build_task_instruction(task, plan)
        assert "Python logging module" in instruction

    def test_includes_acceptance_criteria(self):
        """Si la task tiene acceptance_criteria, se incluyen."""
        from autocode.core.planning.executor import _build_task_instruction

        task = PlanTask(
            type="create",
            path="src/utils.py",
            description="Create utils",
            acceptance_criteria=["Must have type hints", "Must have docstrings"],
        )
        plan = CommitPlan(id="t", title="t")
        instruction = _build_task_instruction(task, plan)
        assert "type hints" in instruction
        assert "docstrings" in instruction

    def test_includes_plan_context(self):
        """La instrucción incluye el contexto del plan (description, architectural_notes)."""
        from autocode.core.planning.executor import _build_task_instruction

        task = PlanTask(type="modify", path="x.py", description="Change x")
        plan = CommitPlan(
            id="t",
            title="t",
            description="Refactor for performance",
            context=PlanContext(architectural_notes="Use async/await"),
        )
        instruction = _build_task_instruction(task, plan)
        assert "Refactor for performance" in instruction
        assert "async/await" in instruction


# ==============================================================================
# TESTS: _extract_files_changed
# ==============================================================================


class TestExtractFilesChanged:
    """Tests for _extract_files_changed helper."""

    def test_extract_from_trajectory_dict(self):
        """Extrae paths de archivos de las tool calls en la trajectory de ReAct."""
        from autocode.core.planning.executor import _extract_files_changed

        trajectory = {
            "Action_1": "write_file_content",
            "Action_1_args": {"path": "src/main.py", "content": "..."},
            "Action_2": "replace_in_file",
            "Action_2_args": {
                "path": "src/utils.py",
                "old_string": "...",
                "new_string": "...",
            },
            "Action_3": "read_file_content",
            "Action_3_args": {"path": "src/other.py"},  # read no es un cambio
        }
        files = _extract_files_changed(trajectory)
        assert "src/main.py" in files
        assert "src/utils.py" in files
        assert "src/other.py" not in files  # read no cuenta

    def test_extract_deduplicates(self):
        """No retorna duplicados si un archivo fue tocado múltiples veces."""
        from autocode.core.planning.executor import _extract_files_changed

        trajectory = {
            "Action_1": "replace_in_file",
            "Action_1_args": {
                "path": "src/main.py",
                "old_string": "a",
                "new_string": "b",
            },
            "Action_2": "replace_in_file",
            "Action_2_args": {
                "path": "src/main.py",
                "old_string": "c",
                "new_string": "d",
            },
        }
        files = _extract_files_changed(trajectory)
        assert files == ["src/main.py"]

    def test_extract_empty_trajectory(self):
        """Trajectory vacía retorna lista vacía."""
        from autocode.core.planning.executor import _extract_files_changed

        assert _extract_files_changed({}) == []
        assert _extract_files_changed(None) == []


# ==============================================================================
# TESTS: _extract_cost_from_history
# ==============================================================================


class TestExtractCostFromHistory:
    """Tests for _extract_cost_from_history helper."""

    def test_no_history(self):
        """Sin historial retorna zeros."""
        from autocode.core.planning.executor import _extract_cost_from_history

        lm = MagicMock()
        lm.history = []
        result = _extract_cost_from_history(lm)
        assert result["total_tokens"] == 0
        assert result["total_cost"] == 0.0

    def test_no_history_attr(self):
        """Sin atributo history retorna zeros."""
        from autocode.core.planning.executor import _extract_cost_from_history

        lm = MagicMock(spec=[])  # no attributes
        result = _extract_cost_from_history(lm)
        assert result["total_tokens"] == 0
        assert result["total_cost"] == 0.0

    def test_sums_tokens_from_usage(self):
        """Suma tokens de usage de cada llamada."""
        from autocode.core.planning.executor import _extract_cost_from_history

        lm = MagicMock()
        lm.history = [
            {"usage": {"prompt_tokens": 100, "completion_tokens": 50}},
            {"usage": {"prompt_tokens": 200, "completion_tokens": 75}},
        ]
        result = _extract_cost_from_history(lm)
        assert result["prompt_tokens"] == 300
        assert result["completion_tokens"] == 125
        assert result["total_tokens"] == 425

    def test_sums_cost_from_response_cost(self):
        """Suma coste de response_cost de cada llamada."""
        from autocode.core.planning.executor import _extract_cost_from_history

        lm = MagicMock()
        lm.history = [
            {"usage": {"prompt_tokens": 100, "completion_tokens": 50}, "cost": 0.001},
            {"usage": {"prompt_tokens": 200, "completion_tokens": 75}, "cost": 0.002},
        ]
        result = _extract_cost_from_history(lm)
        assert abs(result["total_cost"] - 0.003) < 1e-9

    def test_handles_input_output_tokens(self):
        """Maneja variante input_tokens/output_tokens de LiteLLM."""
        from autocode.core.planning.executor import _extract_cost_from_history

        lm = MagicMock()
        lm.history = [
            {"usage": {"input_tokens": 150, "output_tokens": 60}},
        ]
        result = _extract_cost_from_history(lm)
        assert result["prompt_tokens"] == 150
        assert result["completion_tokens"] == 60
        assert result["total_tokens"] == 210

    def test_handles_hidden_params_cost(self):
        """Extrae coste de _hidden_params.response_cost."""
        from autocode.core.planning.executor import _extract_cost_from_history

        lm = MagicMock()
        lm.history = [
            {
                "usage": {"prompt_tokens": 100, "completion_tokens": 50},
                "_hidden_params": {"response_cost": 0.005},
            },
        ]
        result = _extract_cost_from_history(lm)
        assert abs(result["total_cost"] - 0.005) < 1e-9

    def test_handles_non_dict_entries(self):
        """Ignora entradas que no son dict en el historial."""
        from autocode.core.planning.executor import _extract_cost_from_history

        lm = MagicMock()
        lm.history = [
            "not a dict",
            {"usage": {"prompt_tokens": 100, "completion_tokens": 50}},
            42,
        ]
        result = _extract_cost_from_history(lm)
        assert result["prompt_tokens"] == 100
        assert result["completion_tokens"] == 50


# ==============================================================================
# TESTS: stream_execute_plan
# ==============================================================================


@pytest.mark.asyncio
class TestStreamExecutePlan:
    """Tests for stream_execute_plan async generator.

    All tests mock:
    - PLANS_DIR → tmp_path for plan persistence isolation
    - _execute_single_task → async generator (new pattern)
    - get_dspy_lm → to avoid needing API keys
    - _get_executor_tools → to avoid registry dependency
    """

    # Common patches for all tests that go through the full execution flow
    def _execution_patches(self, tmp_path):
        """Returns a contextmanager stack with common mocks."""
        from contextlib import ExitStack

        stack = ExitStack()
        stack.enter_context(
            patch("autocode.core.planning.planner.PLANS_DIR", str(tmp_path))
        )
        stack.enter_context(
            patch(
                "autocode.core.planning.executor.get_dspy_lm",
                return_value=MagicMock(),
            )
        )
        stack.enter_context(
            patch(
                "autocode.core.planning.executor._get_executor_tools",
                return_value=[],
            )
        )
        return stack

    async def test_emits_plan_start_event(self, tmp_path):
        """El primer evento es plan_start con metadata del plan."""
        from autocode.core.planning.executor import stream_execute_plan

        plan = _create_test_plan(tmp_path, title="Test Plan", num_tasks=1)
        task_result = TaskExecutionResult(
            task_index=0, status="completed", llm_summary="Done"
        )

        events = []
        with self._execution_patches(tmp_path) as stack:
            mock_exec = stack.enter_context(
                patch("autocode.core.planning.executor._execute_single_task")
            )
            mock_exec.return_value = _mock_task_generator(task_result)
            async for event in stream_execute_plan(
                plan_id=plan.id, auto_commit=False
            ):
                events.append(_parse_sse(event))

        assert events[0]["event"] == "plan_start"
        assert events[0]["data"]["title"] == "Test Plan"
        assert events[0]["data"]["total_tasks"] == 1

    async def test_emits_task_start_and_complete(self, tmp_path):
        """Emite task_start y task_complete para cada task."""
        from autocode.core.planning.executor import stream_execute_plan

        plan = _create_test_plan(tmp_path, num_tasks=2)

        events = []
        with self._execution_patches(tmp_path) as stack:
            mock_exec = stack.enter_context(
                patch("autocode.core.planning.executor._execute_single_task")
            )
            # Mock returns a fresh generator for each call
            mock_exec.side_effect = lambda task, plan, lm, tools, idx: _mock_task_generator(
                TaskExecutionResult(
                    task_index=idx, status="completed", llm_summary="Done"
                )
            )
            async for event in stream_execute_plan(
                plan_id=plan.id, auto_commit=False
            ):
                events.append(_parse_sse(event))

        event_types = [e["event"] for e in events]
        assert event_types.count("task_start") == 2
        assert event_types.count("task_complete") == 2

    async def test_emits_plan_complete_with_summary(self, tmp_path):
        """El último evento es plan_complete con resumen."""
        from autocode.core.planning.executor import stream_execute_plan

        plan = _create_test_plan(tmp_path, num_tasks=1)

        events = []
        with self._execution_patches(tmp_path) as stack:
            mock_exec = stack.enter_context(
                patch("autocode.core.planning.executor._execute_single_task")
            )
            mock_exec.return_value = _mock_task_generator(
                TaskExecutionResult(task_index=0, status="completed")
            )
            async for event in stream_execute_plan(
                plan_id=plan.id, auto_commit=False
            ):
                events.append(_parse_sse(event))

        last = events[-1]
        assert last["event"] == "plan_complete"
        assert last["data"]["success"] is True

    async def test_plan_transitions_to_executing_then_completed(self, tmp_path):
        """El plan pasa a 'executing' al empezar y 'completed' al terminar."""
        from autocode.core.planning.executor import stream_execute_plan

        plan = _create_test_plan(tmp_path, num_tasks=1)

        statuses_seen = []

        def spy_save(p):
            statuses_seen.append(p.status)
            # Actually save to tmp_path so subsequent loads work
            plans_dir = Path(tmp_path)
            plans_dir.mkdir(parents=True, exist_ok=True)
            path = plans_dir / f"{p.id}.json"
            path.write_text(p.model_dump_json(indent=2), encoding="utf-8")

        with self._execution_patches(tmp_path) as stack:
            stack.enter_context(
                patch(
                    "autocode.core.planning.executor._save_plan",
                    side_effect=spy_save,
                )
            )
            mock_exec = stack.enter_context(
                patch("autocode.core.planning.executor._execute_single_task")
            )
            mock_exec.return_value = _mock_task_generator(
                TaskExecutionResult(task_index=0, status="completed")
            )
            async for _ in stream_execute_plan(
                plan_id=plan.id, auto_commit=False
            ):
                pass

        assert "executing" in statuses_seen
        assert "completed" in statuses_seen

    async def test_plan_transitions_to_failed_on_task_error(self, tmp_path):
        """Si una task falla, el plan pasa a 'failed'."""
        from autocode.core.planning.executor import stream_execute_plan

        plan = _create_test_plan(tmp_path, num_tasks=1)

        events = []
        with self._execution_patches(tmp_path) as stack:
            mock_exec = stack.enter_context(
                patch("autocode.core.planning.executor._execute_single_task")
            )
            mock_exec.return_value = _mock_task_generator(
                TaskExecutionResult(
                    task_index=0, status="failed", error="LLM error"
                )
            )
            async for event in stream_execute_plan(
                plan_id=plan.id, auto_commit=False
            ):
                events.append(_parse_sse(event))

        last = events[-1]
        assert last["event"] == "plan_complete"
        assert last["data"]["success"] is False

    async def test_rejects_invalid_plan_status(self, tmp_path):
        """Rechaza ejecutar un plan que ya está completed/executing."""
        from autocode.core.planning.executor import stream_execute_plan

        plan = _create_test_plan(tmp_path, status="completed")

        events = []
        with patch("autocode.core.planning.planner.PLANS_DIR", str(tmp_path)):
            async for event in stream_execute_plan(plan_id=plan.id):
                events.append(_parse_sse(event))

        assert len(events) == 1
        assert events[0]["event"] == "error"

    async def test_rejects_nonexistent_plan(self):
        """Emite error si el plan no existe."""
        from autocode.core.planning.executor import stream_execute_plan

        events = []
        async for event in stream_execute_plan(plan_id="nonexistent"):
            events.append(_parse_sse(event))

        assert events[0]["event"] == "error"

    async def test_auto_commit_on_success(self, tmp_path):
        """Con auto_commit=True, ejecuta git add + git commit al finalizar."""
        from autocode.core.planning.executor import stream_execute_plan

        plan = _create_test_plan(tmp_path, num_tasks=1)

        with self._execution_patches(tmp_path) as stack:
            mock_exec = stack.enter_context(
                patch("autocode.core.planning.executor._execute_single_task")
            )
            mock_git = stack.enter_context(
                patch("autocode.core.planning.executor._git_add_and_commit")
            )
            mock_exec.return_value = _mock_task_generator(
                TaskExecutionResult(
                    task_index=0,
                    status="completed",
                    files_changed=["src/main.py"],
                )
            )
            mock_git.return_value = "abc1234"

            events = []
            async for event in stream_execute_plan(
                plan_id=plan.id, auto_commit=True
            ):
                events.append(_parse_sse(event))

        mock_git.assert_called_once()
        # commit_hash should be in plan_complete
        last = [e for e in events if e["event"] == "plan_complete"][0]
        assert last["data"]["commit_hash"] == "abc1234"

    async def test_no_commit_on_failure(self, tmp_path):
        """Con auto_commit=True pero task fallida, NO hace commit."""
        from autocode.core.planning.executor import stream_execute_plan

        plan = _create_test_plan(tmp_path, num_tasks=1)

        with self._execution_patches(tmp_path) as stack:
            mock_exec = stack.enter_context(
                patch("autocode.core.planning.executor._execute_single_task")
            )
            mock_git = stack.enter_context(
                patch("autocode.core.planning.executor._git_add_and_commit")
            )
            mock_exec.return_value = _mock_task_generator(
                TaskExecutionResult(
                    task_index=0, status="failed", error="error"
                )
            )
            async for _ in stream_execute_plan(
                plan_id=plan.id, auto_commit=True
            ):
                pass

        mock_git.assert_not_called()

    async def test_status_events_forwarded_in_realtime(self, tmp_path):
        """Los status events se forwardean en tiempo real (no al final)."""
        from autocode.core.planning.executor import stream_execute_plan

        plan = _create_test_plan(tmp_path, num_tasks=1)

        events = []
        with self._execution_patches(tmp_path) as stack:
            mock_exec = stack.enter_context(
                patch("autocode.core.planning.executor._execute_single_task")
            )
            mock_exec.return_value = _mock_task_generator(
                TaskExecutionResult(
                    task_index=0, status="completed", llm_summary="Done"
                ),
                status_messages=[
                    "🛠️ read_file_content(path='src/file0.py')",
                    "✅ Herramienta completada",
                    "🧠 Consultando al LLM...",
                ],
            )
            async for event in stream_execute_plan(
                plan_id=plan.id, auto_commit=False
            ):
                events.append(_parse_sse(event))

        # Status events should appear between task_start and task_complete
        event_types = [e["event"] for e in events]
        assert "status" in event_types
        status_events = [e for e in events if e["event"] == "status"]
        assert len(status_events) == 3
        assert "read_file_content" in status_events[0]["data"]["message"]

    async def test_task_debug_event_emitted(self, tmp_path):
        """Se emite un task_debug event con trajectory, history y cost info."""
        from autocode.core.planning.executor import stream_execute_plan

        plan = _create_test_plan(tmp_path, num_tasks=1)

        events = []
        with self._execution_patches(tmp_path) as stack:
            mock_exec = stack.enter_context(
                patch("autocode.core.planning.executor._execute_single_task")
            )
            mock_exec.return_value = _mock_task_generator(
                TaskExecutionResult(
                    task_index=0,
                    status="completed",
                    total_tokens=500,
                    total_cost=0.001,
                )
            )
            async for event in stream_execute_plan(
                plan_id=plan.id, auto_commit=False
            ):
                events.append(_parse_sse(event))

        debug_events = [e for e in events if e["event"] == "task_debug"]
        assert len(debug_events) == 1
        debug = debug_events[0]["data"]
        assert "trajectory" in debug
        assert "history" in debug
        assert "total_tokens" in debug
        assert "total_cost" in debug

    async def test_plan_complete_includes_total_cost(self, tmp_path):
        """plan_complete incluye total_tokens y total_cost acumulados."""
        from autocode.core.planning.executor import stream_execute_plan

        plan = _create_test_plan(tmp_path, num_tasks=2)

        events = []
        with self._execution_patches(tmp_path) as stack:
            mock_exec = stack.enter_context(
                patch("autocode.core.planning.executor._execute_single_task")
            )
            # Each task has some cost
            mock_exec.side_effect = lambda task, plan, lm, tools, idx: _mock_task_generator(
                TaskExecutionResult(
                    task_index=idx,
                    status="completed",
                    total_tokens=500,
                    total_cost=0.001,
                    prompt_tokens=400,
                    completion_tokens=100,
                )
            )
            async for event in stream_execute_plan(
                plan_id=plan.id, auto_commit=False
            ):
                events.append(_parse_sse(event))

        plan_complete = [e for e in events if e["event"] == "plan_complete"][0]
        assert plan_complete["data"]["total_tokens"] == 1000  # 500 * 2
        assert abs(plan_complete["data"]["total_cost"] - 0.002) < 1e-9

    async def test_task_complete_includes_cost(self, tmp_path):
        """task_complete incluye total_tokens y total_cost de la tarea."""
        from autocode.core.planning.executor import stream_execute_plan

        plan = _create_test_plan(tmp_path, num_tasks=1)

        events = []
        with self._execution_patches(tmp_path) as stack:
            mock_exec = stack.enter_context(
                patch("autocode.core.planning.executor._execute_single_task")
            )
            mock_exec.return_value = _mock_task_generator(
                TaskExecutionResult(
                    task_index=0,
                    status="completed",
                    llm_summary="Done",
                    total_tokens=750,
                    total_cost=0.0025,
                )
            )
            async for event in stream_execute_plan(
                plan_id=plan.id, auto_commit=False
            ):
                events.append(_parse_sse(event))

        task_complete = [e for e in events if e["event"] == "task_complete"][0]
        assert task_complete["data"]["total_tokens"] == 750
        assert abs(task_complete["data"]["total_cost"] - 0.0025) < 1e-9
