"""
Tests for plan executor with ReAct + streaming SSE.

Tests cover:
- _build_task_instruction: prompt construction from task + plan context
- _git_diff_changed_files: file detection via git diff
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
    ReviewResult,
    ReviewFileMetrics,
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
# TESTS: _git_diff_changed_files
# ==============================================================================


class TestGitDiffChangedFiles:
    """Tests for _git_diff_changed_files helper (git-based file detection)."""

    def test_returns_changed_files(self):
        """Retorna archivos modificados según git diff."""
        from autocode.core.planning.executor import _git_diff_changed_files

        with patch("autocode.core.planning.executor.subprocess.run") as mock_run:
            mock_run.return_value.returncode = 0
            mock_run.return_value.stdout = "src/main.py\nsrc/utils.js\nREADME.md\n"
            mock_run.return_value.stderr = ""

            files = _git_diff_changed_files("abc123")

        assert files == ["src/main.py", "src/utils.js", "README.md"]
        # Verify git diff was called with the parent commit
        mock_run.assert_called_once()
        assert "abc123" in mock_run.call_args[0][0]

    def test_returns_empty_on_no_changes(self):
        """Retorna lista vacía si no hay cambios."""
        from autocode.core.planning.executor import _git_diff_changed_files

        with patch("autocode.core.planning.executor.subprocess.run") as mock_run:
            mock_run.return_value.returncode = 0
            mock_run.return_value.stdout = ""
            mock_run.return_value.stderr = ""

            files = _git_diff_changed_files("abc123")

        assert files == []

    def test_returns_empty_on_git_failure(self):
        """Retorna lista vacía si git diff falla."""
        from autocode.core.planning.executor import _git_diff_changed_files

        with patch("autocode.core.planning.executor.subprocess.run") as mock_run:
            mock_run.return_value.returncode = 128
            mock_run.return_value.stdout = ""
            mock_run.return_value.stderr = "fatal: bad object"

            files = _git_diff_changed_files("invalid_ref")

        assert files == []

    def test_works_with_any_file_type(self):
        """Detecta archivos de cualquier tipo (.py, .js, .md, etc.)."""
        from autocode.core.planning.executor import _git_diff_changed_files

        with patch("autocode.core.planning.executor.subprocess.run") as mock_run:
            mock_run.return_value.returncode = 0
            mock_run.return_value.stdout = "app.js\nstyle.css\nindex.html\nlib.py\n"
            mock_run.return_value.stderr = ""

            files = _git_diff_changed_files("HEAD")

        assert "app.js" in files
        assert "style.css" in files
        assert "index.html" in files
        assert "lib.py" in files


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
                plan_id=plan.id, review_mode="human"
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
                plan_id=plan.id, review_mode="human"
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
                plan_id=plan.id, review_mode="human"
            ):
                events.append(_parse_sse(event))

        last = events[-1]
        assert last["event"] == "plan_complete"
        assert last["data"]["success"] is True

    async def test_plan_transitions_to_executing_then_pending_review(self, tmp_path):
        """El plan pasa a 'executing' al empezar y 'pending_review' con review_mode=human."""
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
                plan_id=plan.id, review_mode="human"
            ):
                pass

        assert "executing" in statuses_seen
        assert "pending_review" in statuses_seen

    async def test_plan_transitions_to_failed_on_task_error(self, tmp_path):
        """Si una task falla, el plan pasa a 'failed' (sin review)."""
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
                plan_id=plan.id, review_mode="human"
            ):
                events.append(_parse_sse(event))

        last = events[-1]
        assert last["event"] == "plan_complete"
        assert last["data"]["success"] is False

    async def test_rejects_invalid_plan_status(self, tmp_path):
        """Rechaza ejecutar un plan que ya está completed o abandoned."""
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

    async def test_review_mode_auto_commits_on_approval(self, tmp_path):
        """Con review_mode=auto y quality gates OK, ejecuta git commit."""
        from autocode.core.planning.executor import stream_execute_plan

        plan = _create_test_plan(tmp_path, num_tasks=1)

        approved_review = ReviewResult(
            mode="auto", verdict="approved", summary="All gates passed",
            quality_gates={"complexity_increase": True, "mi_minimum": True},
            reviewed_by="auto",
        )

        with self._execution_patches(tmp_path) as stack:
            mock_exec = stack.enter_context(
                patch("autocode.core.planning.executor._execute_single_task")
            )
            mock_git = stack.enter_context(
                patch("autocode.core.planning.executor._git_add_and_commit")
            )
            mock_review = stack.enter_context(
                patch("autocode.core.planning.executor.auto_review",
                      return_value=approved_review)
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
                plan_id=plan.id, review_mode="auto"
            ):
                events.append(_parse_sse(event))

        mock_git.assert_called_once()
        last = [e for e in events if e["event"] == "plan_complete"][0]
        assert last["data"]["commit_hash"] == "abc1234"

    async def test_no_commit_on_failure(self, tmp_path):
        """Con review_mode=auto pero task fallida, NO hace review ni commit."""
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
                plan_id=plan.id, review_mode="auto"
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
                plan_id=plan.id, review_mode="human"
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
                plan_id=plan.id, review_mode="human"
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
                plan_id=plan.id, review_mode="human"
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
                plan_id=plan.id, review_mode="human"
            ):
                events.append(_parse_sse(event))

        task_complete = [e for e in events if e["event"] == "task_complete"][0]
        assert task_complete["data"]["total_tokens"] == 750
        assert abs(task_complete["data"]["total_cost"] - 0.0025) < 1e-9

    async def test_can_reexecute_plan_in_executing_status(self, tmp_path):
        """Un plan stuck en 'executing' puede re-ejecutarse (recovery)."""
        from autocode.core.planning.executor import stream_execute_plan

        # Create a plan already in "executing" status (simulating a stuck plan)
        plan = _create_test_plan(tmp_path, num_tasks=1, status="executing")

        events = []
        with self._execution_patches(tmp_path) as stack:
            mock_exec = stack.enter_context(
                patch("autocode.core.planning.executor._execute_single_task")
            )
            mock_exec.return_value = _mock_task_generator(
                TaskExecutionResult(
                    task_index=0, status="completed", llm_summary="Re-executed"
                )
            )
            async for event in stream_execute_plan(
                plan_id=plan.id, review_mode="human"
            ):
                events.append(_parse_sse(event))

        # Should execute successfully, not reject
        event_types = [e["event"] for e in events]
        assert "plan_start" in event_types
        assert "plan_complete" in event_types
        plan_complete = [e for e in events if e["event"] == "plan_complete"][0]
        assert plan_complete["data"]["success"] is True


# ==============================================================================
# TESTS: stream_execute_plan — review_mode flow
# ==============================================================================


@pytest.mark.asyncio
class TestExecutorReviewMode:
    """Tests for the review_mode flow in stream_execute_plan.

    Verifies that:
    - review_mode="human" → pending_review (never auto-commits)
    - review_mode="auto" → auto_review → approved → commit / rejected → pending_review
    - SSE events review_start and review_complete are emitted
    - plan.execution.review stores ReviewResult
    - plan.execution.files_changed is populated for later revert
    """

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

    async def test_default_review_mode_is_human(self, tmp_path):
        """El review_mode por defecto es 'human' → status=pending_review."""
        from autocode.core.planning.executor import stream_execute_plan

        plan = _create_test_plan(tmp_path, num_tasks=1)

        statuses_seen = []

        def spy_save(p):
            statuses_seen.append(p.status)
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
            # No review_mode argument → uses default
            async for _ in stream_execute_plan(plan_id=plan.id):
                pass

        assert "pending_review" in statuses_seen
        assert "completed" not in statuses_seen

    async def test_review_mode_auto_runs_auto_review(self, tmp_path):
        """review_mode=auto ejecuta auto_review y aprueba → completed + commit."""
        from autocode.core.planning.executor import stream_execute_plan

        plan = _create_test_plan(tmp_path, num_tasks=1)

        approved_review = ReviewResult(
            mode="auto", verdict="approved", summary="All gates passed",
            quality_gates={"complexity_increase": True, "mi_minimum": True},
            reviewed_by="auto",
        )

        statuses_seen = []

        def spy_save(p):
            statuses_seen.append(p.status)
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
            mock_review = stack.enter_context(
                patch("autocode.core.planning.executor.auto_review",
                      return_value=approved_review)
            )
            mock_git = stack.enter_context(
                patch("autocode.core.planning.executor._git_add_and_commit",
                      return_value="def5678")
            )
            mock_exec.return_value = _mock_task_generator(
                TaskExecutionResult(
                    task_index=0, status="completed",
                    files_changed=["src/file0.py"],
                )
            )
            async for _ in stream_execute_plan(
                plan_id=plan.id, review_mode="auto"
            ):
                pass

        mock_review.assert_called_once()
        mock_git.assert_called_once()
        assert "executing" in statuses_seen
        assert "completed" in statuses_seen

    async def test_review_mode_auto_rejects_bad_code(self, tmp_path):
        """review_mode=auto + quality gates fail → pending_review (no commit)."""
        from autocode.core.planning.executor import stream_execute_plan

        plan = _create_test_plan(tmp_path, num_tasks=1)

        rejected_review = ReviewResult(
            mode="auto", verdict="rejected",
            summary="Quality gates failed",
            issues=["❌ complexity_increase: too complex"],
            quality_gates={"complexity_increase": False, "mi_minimum": True},
            reviewed_by="auto",
        )

        statuses_seen = []

        def spy_save(p):
            statuses_seen.append(p.status)
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
            mock_review = stack.enter_context(
                patch("autocode.core.planning.executor.auto_review",
                      return_value=rejected_review)
            )
            mock_git = stack.enter_context(
                patch("autocode.core.planning.executor._git_add_and_commit")
            )
            mock_exec.return_value = _mock_task_generator(
                TaskExecutionResult(
                    task_index=0, status="completed",
                    files_changed=["src/file0.py"],
                )
            )
            async for _ in stream_execute_plan(
                plan_id=plan.id, review_mode="auto"
            ):
                pass

        mock_review.assert_called_once()
        mock_git.assert_not_called()
        assert "pending_review" in statuses_seen
        assert "completed" not in statuses_seen

    async def test_review_mode_human_always_pending_review(self, tmp_path):
        """review_mode=human → siempre pending_review, nunca commit automático."""
        from autocode.core.planning.executor import stream_execute_plan

        plan = _create_test_plan(tmp_path, num_tasks=1)

        statuses_seen = []

        def spy_save(p):
            statuses_seen.append(p.status)
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
            mock_git = stack.enter_context(
                patch("autocode.core.planning.executor._git_add_and_commit")
            )
            mock_exec.return_value = _mock_task_generator(
                TaskExecutionResult(
                    task_index=0, status="completed",
                    files_changed=["src/file0.py"],
                )
            )
            async for _ in stream_execute_plan(
                plan_id=plan.id, review_mode="human"
            ):
                pass

        mock_git.assert_not_called()
        assert "pending_review" in statuses_seen
        assert "completed" not in statuses_seen

    async def test_emits_review_start_and_complete_events(self, tmp_path):
        """Se emiten SSE events review_start y review_complete."""
        from autocode.core.planning.executor import stream_execute_plan

        plan = _create_test_plan(tmp_path, num_tasks=1)

        approved_review = ReviewResult(
            mode="auto", verdict="approved", summary="OK",
            quality_gates={}, reviewed_by="auto",
        )

        events = []
        with self._execution_patches(tmp_path) as stack:
            mock_exec = stack.enter_context(
                patch("autocode.core.planning.executor._execute_single_task")
            )
            stack.enter_context(
                patch("autocode.core.planning.executor.auto_review",
                      return_value=approved_review)
            )
            stack.enter_context(
                patch("autocode.core.planning.executor._git_add_and_commit",
                      return_value="abc123")
            )
            mock_exec.return_value = _mock_task_generator(
                TaskExecutionResult(
                    task_index=0, status="completed",
                    files_changed=["src/file0.py"],
                )
            )
            async for event in stream_execute_plan(
                plan_id=plan.id, review_mode="auto"
            ):
                events.append(_parse_sse(event))

        event_types = [e["event"] for e in events]
        assert "review_start" in event_types
        assert "review_complete" in event_types

        # review_complete should include verdict
        review_complete = [e for e in events if e["event"] == "review_complete"][0]
        assert review_complete["data"]["verdict"] == "approved"

    async def test_plan_stores_review_result(self, tmp_path):
        """plan.execution.review contiene un ReviewResult tras la ejecución."""
        from autocode.core.planning.executor import stream_execute_plan

        plan = _create_test_plan(tmp_path, num_tasks=1)

        approved_review = ReviewResult(
            mode="auto", verdict="approved", summary="All good",
            quality_gates={"mi_minimum": True},
            reviewed_by="auto",
        )

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
                    "autocode.core.planning.executor._save_plan",
                    side_effect=spy_save,
                )
            )
            mock_exec = stack.enter_context(
                patch("autocode.core.planning.executor._execute_single_task")
            )
            stack.enter_context(
                patch("autocode.core.planning.executor.auto_review",
                      return_value=approved_review)
            )
            stack.enter_context(
                patch("autocode.core.planning.executor._git_add_and_commit",
                      return_value="abc123")
            )
            mock_exec.return_value = _mock_task_generator(
                TaskExecutionResult(
                    task_index=0, status="completed",
                    files_changed=["src/file0.py"],
                )
            )
            async for _ in stream_execute_plan(
                plan_id=plan.id, review_mode="auto"
            ):
                pass

        # The final saved plan should have a review result
        final_plan = saved_plans[-1]
        assert final_plan.execution is not None
        assert final_plan.execution.review is not None
        assert final_plan.execution.review.verdict == "approved"
        assert final_plan.execution.review.mode == "auto"

    async def test_files_changed_stored_in_execution(self, tmp_path):
        """Los archivos cambiados se guardan en execution.files_changed para revert."""
        from autocode.core.planning.executor import stream_execute_plan

        plan = _create_test_plan(tmp_path, num_tasks=2)

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
                    "autocode.core.planning.executor._save_plan",
                    side_effect=spy_save,
                )
            )
            mock_exec = stack.enter_context(
                patch("autocode.core.planning.executor._execute_single_task")
            )
            mock_exec.side_effect = lambda task, plan, lm, tools, idx: _mock_task_generator(
                TaskExecutionResult(
                    task_index=idx, status="completed",
                    files_changed=[f"src/file{idx}.py"],
                )
            )
            async for _ in stream_execute_plan(
                plan_id=plan.id, review_mode="human"
            ):
                pass

        # The final saved plan should have files_changed populated
        final_plan = saved_plans[-1]
        assert final_plan.execution is not None
        assert "src/file0.py" in final_plan.execution.files_changed
        assert "src/file1.py" in final_plan.execution.files_changed


# ==============================================================================
# TESTS: _with_heartbeat
# ==============================================================================


@pytest.mark.asyncio
class TestWithHeartbeat:
    """Tests for _with_heartbeat async generator wrapper."""

    async def test_forwards_all_items_from_source(self):
        """Todos los items del source generator se forwardean sin modificación."""
        from autocode.core.planning.executor import _with_heartbeat

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
        from autocode.core.planning.executor import _with_heartbeat

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
        from autocode.core.planning.executor import _with_heartbeat

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
        from autocode.core.planning.executor import _with_heartbeat

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
        from autocode.core.planning.executor import _with_heartbeat

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


