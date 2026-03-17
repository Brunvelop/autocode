"""
Tests for plan executor with ReAct + streaming SSE.

Tests cover:
- stream_execute_plan: async SSE streaming with status transitions, cost tracking
- review_mode flow: human vs auto review
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
from tests.unit.core.planning.conftest import (
    _create_test_plan,
    _parse_sse,
    _mock_task_generator,
)


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
                    "autocode.core.planning.executor.save_plan",
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
        with patch("autocode.core.planning.persistence.PLANS_DIR", str(tmp_path)):
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
                patch("autocode.core.planning.executor.git_add_and_commit")
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
                patch("autocode.core.planning.executor.git_add_and_commit")
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
                    "autocode.core.planning.executor.save_plan",
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
                    "autocode.core.planning.executor.save_plan",
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
                patch("autocode.core.planning.executor.git_add_and_commit",
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
                    "autocode.core.planning.executor.save_plan",
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
                patch("autocode.core.planning.executor.git_add_and_commit")
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
                    "autocode.core.planning.executor.save_plan",
                    side_effect=spy_save,
                )
            )
            mock_exec = stack.enter_context(
                patch("autocode.core.planning.executor._execute_single_task")
            )
            mock_git = stack.enter_context(
                patch("autocode.core.planning.executor.git_add_and_commit")
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
                patch("autocode.core.planning.executor.git_add_and_commit",
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
                    "autocode.core.planning.executor.save_plan",
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
                patch("autocode.core.planning.executor.git_add_and_commit",
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
                    "autocode.core.planning.executor.save_plan",
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
