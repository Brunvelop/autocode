"""
Tests for executor helper functions.

Tests cover:
- _build_task_instruction: prompt construction from task + plan context
- _extract_files_changed: file path extraction from ReAct trajectory
- _extract_cost_from_history: cost/token extraction from LM history
- _with_heartbeat: async heartbeat wrapper
- _validate_and_prepare_plan: plan validation and setup
- _execute_task_loop: task execution loop
- _run_review_flow: post-execution review flow
"""

from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from autocode.core.planning.models import (
    CommitPlan,
    PlanTask,
    PlanContext,
    TaskExecutionResult,
    PlanExecutionState,
    ReviewResult,
)
from tests.unit.core.planning.conftest import (
    _create_test_plan,
    _parse_sse,
    _mock_task_generator,
)


# ==============================================================================
# TESTS: _build_task_instruction
# ==============================================================================


class TestBuildTaskInstruction:
    """Tests for _build_task_instruction helper."""

    def test_includes_task_description(self):
        """La instrucción incluye la descripción de la task."""
        from autocode.core.planning.executor_helpers import _build_task_instruction

        task = PlanTask(type="modify", path="src/main.py", description="Add logging")
        plan = CommitPlan(id="t", title="t")
        instruction = _build_task_instruction(task, plan)
        assert "Add logging" in instruction

    def test_includes_task_details(self):
        """Si la task tiene details, se incluyen."""
        from autocode.core.planning.executor_helpers import _build_task_instruction

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
        from autocode.core.planning.executor_helpers import _build_task_instruction

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
        from autocode.core.planning.executor_helpers import _build_task_instruction

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
        from autocode.core.planning.executor_helpers import _extract_files_changed

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
        from autocode.core.planning.executor_helpers import _extract_files_changed

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
        from autocode.core.planning.executor_helpers import _extract_files_changed

        assert _extract_files_changed({}) == []
        assert _extract_files_changed(None) == []


# ==============================================================================
# TESTS: _extract_cost_from_history
# ==============================================================================


class TestExtractCostFromHistory:
    """Tests for _extract_cost_from_history helper."""

    def test_no_history(self):
        """Sin historial retorna zeros."""
        from autocode.core.planning.executor_helpers import _extract_cost_from_history

        lm = MagicMock()
        lm.history = []
        result = _extract_cost_from_history(lm)
        assert result["total_tokens"] == 0
        assert result["total_cost"] == 0.0

    def test_no_history_attr(self):
        """Sin atributo history retorna zeros."""
        from autocode.core.planning.executor_helpers import _extract_cost_from_history

        lm = MagicMock(spec=[])  # no attributes
        result = _extract_cost_from_history(lm)
        assert result["total_tokens"] == 0
        assert result["total_cost"] == 0.0

    def test_sums_tokens_from_usage(self):
        """Suma tokens de usage de cada llamada."""
        from autocode.core.planning.executor_helpers import _extract_cost_from_history

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
        from autocode.core.planning.executor_helpers import _extract_cost_from_history

        lm = MagicMock()
        lm.history = [
            {"usage": {"prompt_tokens": 100, "completion_tokens": 50}, "cost": 0.001},
            {"usage": {"prompt_tokens": 200, "completion_tokens": 75}, "cost": 0.002},
        ]
        result = _extract_cost_from_history(lm)
        assert abs(result["total_cost"] - 0.003) < 1e-9

    def test_handles_input_output_tokens(self):
        """Maneja variante input_tokens/output_tokens de LiteLLM."""
        from autocode.core.planning.executor_helpers import _extract_cost_from_history

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
        from autocode.core.planning.executor_helpers import _extract_cost_from_history

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
        from autocode.core.planning.executor_helpers import _extract_cost_from_history

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
# TESTS: _with_heartbeat
# ==============================================================================


@pytest.mark.asyncio
class TestWithHeartbeat:
    """Tests for _with_heartbeat async generator wrapper."""

    async def test_forwards_all_items_from_source(self):
        """Todos los items del source generator se forwardean sin modificación."""
        from autocode.core.planning.executor_helpers import _with_heartbeat

        async def _source():
            yield "event_1"
            yield "event_2"
            yield TaskExecutionResult(task_index=0, status="completed")

        items = []
        async for item in _with_heartbeat(_source(), task_index=0, interval=100):
            items.append(item)

        assert items[0] == "event_1"
        assert items[1] == "event_2"
        assert isinstance(items[2], TaskExecutionResult)
        assert items[2].status == "completed"

    async def test_emits_heartbeat_during_delay(self):
        """Emite heartbeat events cuando el source generator tarda."""
        import asyncio
        from autocode.core.planning.executor_helpers import _with_heartbeat

        async def _slow_source():
            await asyncio.sleep(0.25)  # Enough for 2 heartbeats at 0.1s interval
            yield TaskExecutionResult(task_index=0, status="completed")

        items = []
        async for item in _with_heartbeat(
            _slow_source(), task_index=0, interval=0.1
        ):
            items.append(item)

        # Should have heartbeat events + the final TaskExecutionResult
        heartbeat_items = [
            i for i in items if isinstance(i, str) and "heartbeat" in i
        ]
        assert len(heartbeat_items) >= 1, "Expected at least 1 heartbeat event"

        # Verify heartbeat content
        hb = _parse_sse(heartbeat_items[0])
        assert hb["event"] == "heartbeat"
        assert hb["data"]["task_index"] == 0
        assert "elapsed_s" in hb["data"]
        assert "timestamp" in hb["data"]

    async def test_heartbeat_cancelled_after_completion(self):
        """El heartbeat task se cancela después de que el source termina."""
        import asyncio
        from autocode.core.planning.executor_helpers import _with_heartbeat

        async def _fast_source():
            yield "done"

        items = []
        async for item in _with_heartbeat(
            _fast_source(), task_index=0, interval=0.05
        ):
            items.append(item)

        # Wait a bit — no more heartbeats should appear
        await asyncio.sleep(0.15)
        # If we got here without errors, heartbeat was properly cancelled
        assert items == ["done"]

    async def test_propagates_exception_from_source(self):
        """Excepciones del source generator se propagan correctamente."""
        from autocode.core.planning.executor_helpers import _with_heartbeat

        async def _failing_source():
            yield "first"
            raise ValueError("source error")

        items = []
        with pytest.raises(ValueError, match="source error"):
            async for item in _with_heartbeat(
                _failing_source(), task_index=0, interval=100
            ):
                items.append(item)

        assert items == ["first"]

    async def test_heartbeat_includes_elapsed_time(self):
        """El campo elapsed_s del heartbeat refleja tiempo real transcurrido."""
        import asyncio
        from autocode.core.planning.executor_helpers import _with_heartbeat

        async def _slow_source():
            await asyncio.sleep(0.15)
            yield "done"

        heartbeats = []
        async for item in _with_heartbeat(
            _slow_source(), task_index=5, interval=0.05
        ):
            if isinstance(item, str) and "heartbeat" in item:
                heartbeats.append(_parse_sse(item))

        assert len(heartbeats) >= 1
        # First heartbeat should be ~0.05s, check it's reasonable
        assert heartbeats[0]["data"]["elapsed_s"] >= 0.04
        assert heartbeats[0]["data"]["task_index"] == 5


# ==============================================================================
# TESTS: _validate_and_prepare_plan
# ==============================================================================


@pytest.mark.asyncio
class TestValidateAndPreparePlan:
    """Tests for _validate_and_prepare_plan async generator."""

    def _execution_patches(self, tmp_path):
        """Returns a contextmanager stack with common mocks."""
        from contextlib import ExitStack

        stack = ExitStack()
        stack.enter_context(
            patch("autocode.core.planning.persistence.PLANS_DIR", str(tmp_path))
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

    async def test_yields_error_if_plan_not_found(self, tmp_path):
        """Emite error SSE si el plan no existe."""
        from autocode.core.planning.executor import _validate_and_prepare_plan

        events = []
        with self._execution_patches(tmp_path):
            async for item in _validate_and_prepare_plan(
                "nonexistent", "model", 1000, 0.3
            ):
                events.append(item)

        assert len(events) == 1
        parsed = _parse_sse(events[0])
        assert parsed["event"] == "error"

    async def test_yields_error_if_status_not_executable(self, tmp_path):
        """Emite error SSE si el plan no es ejecutable (e.g., completed)."""
        from autocode.core.planning.executor import _validate_and_prepare_plan

        _create_test_plan(tmp_path, status="completed")

        events = []
        with self._execution_patches(tmp_path):
            async for item in _validate_and_prepare_plan(
                "20260101-000000", "model", 1000, 0.3
            ):
                events.append(item)

        assert len(events) == 1
        parsed = _parse_sse(events[0])
        assert parsed["event"] == "error"

    async def test_yields_plan_start_and_tuple(self, tmp_path):
        """Emite plan_start SSE y finalmente yields (plan, lm, tools)."""
        from autocode.core.planning.executor import _validate_and_prepare_plan

        _create_test_plan(tmp_path, title="Test Plan", num_tasks=2)

        items = []
        with self._execution_patches(tmp_path):
            async for item in _validate_and_prepare_plan(
                "20260101-000000", "model", 1000, 0.3
            ):
                items.append(item)

        # Should have SSE event(s) + final tuple
        assert len(items) >= 2

        # Last item should be a tuple (plan, lm, tools)
        last = items[-1]
        assert isinstance(last, tuple)
        assert len(last) == 3
        plan, lm, tools = last
        assert plan.status == "executing"
        assert plan.execution is not None

        # First item(s) should include plan_start event
        sse_events = [_parse_sse(i) for i in items[:-1] if isinstance(i, str)]
        assert any(e["event"] == "plan_start" for e in sse_events)

    async def test_marks_plan_as_executing(self, tmp_path):
        """El plan se guarda con status='executing' y execution state."""
        from autocode.core.planning.executor import _validate_and_prepare_plan

        _create_test_plan(tmp_path, num_tasks=1)

        saved_plans = []

        def spy_save(p):
            saved_plans.append(p.model_copy(deep=True))
            plans_dir = Path(tmp_path)
            plans_dir.mkdir(parents=True, exist_ok=True)
            path = plans_dir / f"{p.id}.json"
            path.write_text(p.model_dump_json(indent=2), encoding="utf-8")

        with self._execution_patches(tmp_path) as stack:
            stack.enter_context(
                patch(
                    "autocode.core.planning.executor.save_plan",
                    side_effect=spy_save,
                )
            )
            async for _ in _validate_and_prepare_plan(
                "20260101-000000", "model", 1000, 0.3
            ):
                pass

        assert any(p.status == "executing" for p in saved_plans)


# ==============================================================================
# TESTS: _execute_task_loop
# ==============================================================================


@pytest.mark.asyncio
class TestExecuteTaskLoop:
    """Tests for _execute_task_loop async generator."""

    async def test_yields_task_start_and_complete_for_each_task(self):
        """Emite task_start y task_complete para cada tarea."""
        from autocode.core.planning.executor import _execute_task_loop

        plan = CommitPlan(
            id="test",
            title="test",
            status="executing",
            tasks=[
                PlanTask(type="modify", path="a.py", description="Task A"),
                PlanTask(type="modify", path="b.py", description="Task B"),
            ],
            execution=PlanExecutionState(started_at="2026-01-01T00:00:00"),
        )
        lm = MagicMock()
        tools = []

        events = []
        with patch(
            "autocode.core.planning.executor._execute_single_task"
        ) as mock_exec:
            mock_exec.side_effect = (
                lambda task, plan, lm, tools, idx: _mock_task_generator(
                    TaskExecutionResult(
                        task_index=idx, status="completed", llm_summary="Done"
                    )
                )
            )
            async for item in _execute_task_loop(plan, lm, tools):
                events.append(item)

        sse_events = [_parse_sse(e) for e in events if isinstance(e, str)]
        assert sum(1 for e in sse_events if e["event"] == "task_start") == 2
        assert sum(1 for e in sse_events if e["event"] == "task_complete") == 2

    async def test_yields_metrics_summary_as_last_item(self):
        """El último item es un dict con métricas acumuladas."""
        from autocode.core.planning.executor import _execute_task_loop

        plan = CommitPlan(
            id="test",
            title="test",
            status="executing",
            tasks=[PlanTask(type="modify", path="a.py", description="Task A")],
            execution=PlanExecutionState(started_at="2026-01-01T00:00:00"),
        )
        lm = MagicMock()
        tools = []

        items = []
        with patch(
            "autocode.core.planning.executor._execute_single_task"
        ) as mock_exec:
            mock_exec.return_value = _mock_task_generator(
                TaskExecutionResult(
                    task_index=0,
                    status="completed",
                    total_tokens=500,
                    total_cost=0.001,
                    files_changed=["a.py"],
                )
            )
            async for item in _execute_task_loop(plan, lm, tools):
                items.append(item)

        last = items[-1]
        assert isinstance(last, dict)
        assert last["tasks_completed"] == 1
        assert last["tasks_failed"] == 0
        assert "a.py" in last["all_files_changed"]
        assert last["plan_total_tokens"] == 500

    async def test_accumulates_metrics_across_tasks(self):
        """Acumula tokens y costes de todas las tareas."""
        from autocode.core.planning.executor import _execute_task_loop

        plan = CommitPlan(
            id="test",
            title="test",
            status="executing",
            tasks=[
                PlanTask(type="modify", path="a.py", description="A"),
                PlanTask(type="modify", path="b.py", description="B"),
            ],
            execution=PlanExecutionState(started_at="2026-01-01T00:00:00"),
        )
        lm = MagicMock()
        tools = []

        items = []
        with patch(
            "autocode.core.planning.executor._execute_single_task"
        ) as mock_exec:
            mock_exec.side_effect = (
                lambda task, plan, lm, tools, idx: _mock_task_generator(
                    TaskExecutionResult(
                        task_index=idx,
                        status="completed",
                        total_tokens=300,
                        total_cost=0.001,
                        files_changed=[f"file{idx}.py"],
                    )
                )
            )
            async for item in _execute_task_loop(plan, lm, tools):
                items.append(item)

        last = items[-1]
        assert last["plan_total_tokens"] == 600
        assert abs(last["plan_total_cost"] - 0.002) < 1e-9
        assert last["tasks_completed"] == 2

    async def test_handles_task_failure(self):
        """Si una tarea falla, la cuenta como failed y continúa."""
        from autocode.core.planning.executor import _execute_task_loop

        plan = CommitPlan(
            id="test",
            title="test",
            status="executing",
            tasks=[PlanTask(type="modify", path="a.py", description="A")],
            execution=PlanExecutionState(started_at="2026-01-01T00:00:00"),
        )
        lm = MagicMock()
        tools = []

        items = []
        with patch(
            "autocode.core.planning.executor._execute_single_task"
        ) as mock_exec:
            mock_exec.return_value = _mock_task_generator(
                TaskExecutionResult(
                    task_index=0, status="failed", error="LLM error"
                )
            )
            async for item in _execute_task_loop(plan, lm, tools):
                items.append(item)

        last = items[-1]
        assert last["tasks_failed"] == 1
        assert last["tasks_completed"] == 0


# ==============================================================================
# TESTS: _run_review_flow
# ==============================================================================


@pytest.mark.asyncio
class TestRunReviewFlow:
    """Tests for _run_review_flow async generator."""

    async def test_human_mode_sets_pending_review(self):
        """review_mode='human' siempre termina en pending_review."""
        from autocode.core.planning.executor import _run_review_flow

        plan = CommitPlan(
            id="test",
            title="test",
            status="executing",
            execution=PlanExecutionState(
                started_at="2026-01-01T00:00:00",
                total_tokens=500,
                total_cost=0.001,
            ),
        )

        items = []
        with patch(
            "autocode.core.planning.executor.compute_review_metrics",
            return_value=[],
        ), patch("autocode.core.planning.executor.save_plan"):
            async for item in _run_review_flow(plan, "human", ["a.py"]):
                items.append(item)

        assert plan.status == "pending_review"
        sse_events = [_parse_sse(e) for e in items if isinstance(e, str)]
        assert any(e["event"] == "review_start" for e in sse_events)
        assert any(e["event"] == "review_complete" for e in sse_events)

    async def test_auto_approved_commits_and_completes(self):
        """review_mode='auto' con quality gates OK → commit + completed."""
        from autocode.core.planning.executor import _run_review_flow

        plan = CommitPlan(
            id="test",
            title="Test Commit",
            status="executing",
            execution=PlanExecutionState(
                started_at="2026-01-01T00:00:00",
                total_tokens=500,
                total_cost=0.001,
            ),
        )

        approved_review = ReviewResult(
            mode="auto",
            verdict="approved",
            summary="OK",
            quality_gates={},
            reviewed_by="auto",
        )

        items = []
        with patch(
            "autocode.core.planning.executor.auto_review",
            return_value=approved_review,
        ), patch(
            "autocode.core.planning.executor.git_add_and_commit",
            return_value="abc123",
        ), patch("autocode.core.planning.executor.save_plan"):
            async for item in _run_review_flow(plan, "auto", ["a.py"]):
                items.append(item)

        assert plan.status == "completed"
        last = items[-1]
        assert isinstance(last, dict)
        assert last["commit_hash"] == "abc123"

    async def test_auto_rejected_sets_pending_review(self):
        """review_mode='auto' con quality gates fallidos → pending_review."""
        from autocode.core.planning.executor import _run_review_flow

        plan = CommitPlan(
            id="test",
            title="test",
            status="executing",
            execution=PlanExecutionState(
                started_at="2026-01-01T00:00:00",
                total_tokens=500,
                total_cost=0.001,
            ),
        )

        rejected_review = ReviewResult(
            mode="auto",
            verdict="rejected",
            summary="Failed",
            quality_gates={"mi_minimum": False},
            reviewed_by="auto",
        )

        items = []
        with patch(
            "autocode.core.planning.executor.auto_review",
            return_value=rejected_review,
        ), patch("autocode.core.planning.executor.save_plan"):
            async for item in _run_review_flow(plan, "auto", ["a.py"]):
                items.append(item)

        assert plan.status == "pending_review"

    async def test_emits_review_start_and_complete(self):
        """Emite SSE events review_start y review_complete."""
        from autocode.core.planning.executor import _run_review_flow

        plan = CommitPlan(
            id="test",
            title="test",
            status="executing",
            execution=PlanExecutionState(
                started_at="2026-01-01T00:00:00",
                total_tokens=500,
                total_cost=0.001,
            ),
        )

        items = []
        with patch(
            "autocode.core.planning.executor.compute_review_metrics",
            return_value=[],
        ), patch("autocode.core.planning.executor.save_plan"):
            async for item in _run_review_flow(plan, "human", ["a.py"]):
                items.append(item)

        sse_events = [_parse_sse(e) for e in items if isinstance(e, str)]
        event_types = [e["event"] for e in sse_events]
        assert "review_start" in event_types
        assert "review_complete" in event_types
