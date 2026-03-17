"""
Tests for transitions.py — state transition validation for commit plans.
RED phase: autocode.core.planning.transitions does not exist yet.
Tests define the public API that will be implemented in the next commit.
"""

import pytest

from autocode.core.planning.transitions import (
    validate_transition,
    can_execute,
    can_review,
    InvalidTransitionError,
)
from autocode.core.planning.models import CommitPlan


# Valid transition map used across tests
VALID_TRANSITIONS = {
    "draft": {"ready", "executing", "abandoned"},
    "ready": {"draft", "executing", "abandoned"},
    "executing": {"pending_review", "pending_commit", "failed", "completed"},
    "pending_review": {"completed", "reverted", "pending_commit"},
    "pending_commit": {"completed", "reverted"},
    "failed": {"draft", "executing"},
    "completed": set(),
    "reverted": {"draft"},
    "abandoned": {"draft"},
}

ALL_STATUSES = set(VALID_TRANSITIONS.keys())


class TestValidateTransition:
    """Tests for validate_transition() — verifica transiciones válidas entre estados."""

    def test_draft_to_executing_valid(self):
        """draft → executing es una transición válida."""
        validate_transition("draft", "executing")

    def test_draft_to_completed_invalid(self):
        """draft → completed no es una transición válida."""
        with pytest.raises(InvalidTransitionError):
            validate_transition("draft", "completed")

    def test_executing_to_pending_review_valid(self):
        """executing → pending_review es una transición válida."""
        validate_transition("executing", "pending_review")

    def test_pending_review_to_completed_valid(self):
        """pending_review → completed es válida (ruta de aprobación)."""
        validate_transition("pending_review", "completed")

    def test_pending_review_to_reverted_valid(self):
        """pending_review → reverted es válida (ruta de revert)."""
        validate_transition("pending_review", "reverted")

    def test_completed_is_terminal(self):
        """completed es un estado terminal — no permite transiciones de salida."""
        for status in ALL_STATUSES:
            with pytest.raises(InvalidTransitionError):
                validate_transition("completed", status)

    def test_all_valid_transitions(self):
        """Todas las transiciones válidas del mapa no lanzan excepción."""
        for from_status, targets in VALID_TRANSITIONS.items():
            for to_status in targets:
                validate_transition(from_status, to_status)

    def test_invalid_transitions_raise(self):
        """Las transiciones inválidas lanzan InvalidTransitionError."""
        invalid_cases = [
            ("draft", "completed"),
            ("draft", "pending_review"),
            ("draft", "reverted"),
            ("ready", "completed"),
            ("ready", "pending_review"),
            ("executing", "draft"),
            ("executing", "ready"),
            ("failed", "completed"),
            ("failed", "pending_review"),
            ("reverted", "completed"),
            ("abandoned", "completed"),
        ]
        for from_status, to_status in invalid_cases:
            with pytest.raises(InvalidTransitionError):
                validate_transition(from_status, to_status)

    def test_invalid_from_status_raises(self):
        """Un estado de origen inexistente lanza InvalidTransitionError."""
        with pytest.raises(InvalidTransitionError):
            validate_transition("nonexistent", "draft")

    def test_invalid_to_status_raises(self):
        """Un estado de destino inexistente lanza InvalidTransitionError."""
        with pytest.raises(InvalidTransitionError):
            validate_transition("draft", "nonexistent")

    def test_same_status_transition_invalid(self):
        """Las auto-transiciones (self-loops) no están permitidas."""
        for status in ALL_STATUSES:
            with pytest.raises(InvalidTransitionError):
                validate_transition(status, status)


class TestCanExecute:
    """Tests for can_execute() — determina si un plan puede ejecutarse."""

    def _make_plan(self, status: str) -> CommitPlan:
        """Crea un CommitPlan de prueba con el estado dado."""
        return CommitPlan(id="test", title="test", status=status)

    def test_can_execute_draft(self):
        """Un plan en draft puede ejecutarse."""
        assert can_execute(self._make_plan("draft")) is True

    def test_can_execute_ready(self):
        """Un plan en ready puede ejecutarse."""
        assert can_execute(self._make_plan("ready")) is True

    def test_can_execute_failed(self):
        """Un plan en failed puede re-ejecutarse."""
        assert can_execute(self._make_plan("failed")) is True

    def test_can_execute_executing(self):
        """Un plan en executing puede re-ejecutarse (recuperación)."""
        assert can_execute(self._make_plan("executing")) is True

    def test_cannot_execute_completed(self):
        """Un plan completado no puede ejecutarse."""
        assert can_execute(self._make_plan("completed")) is False

    def test_cannot_execute_pending_review(self):
        """Un plan en pending_review no puede ejecutarse."""
        assert can_execute(self._make_plan("pending_review")) is False

    def test_cannot_execute_reverted(self):
        """Un plan revertido no puede ejecutarse."""
        assert can_execute(self._make_plan("reverted")) is False

    def test_cannot_execute_abandoned(self):
        """Un plan abandonado no puede ejecutarse."""
        assert can_execute(self._make_plan("abandoned")) is False


class TestCanReview:
    """Tests for can_review() — determina si un plan puede revisarse."""

    def _make_plan(self, status: str) -> CommitPlan:
        """Crea un CommitPlan de prueba con el estado dado."""
        return CommitPlan(id="test", title="test", status=status)

    def test_can_review_pending_review(self):
        """Un plan en pending_review puede revisarse."""
        assert can_review(self._make_plan("pending_review")) is True

    def test_can_review_pending_commit(self):
        """Un plan en pending_commit puede revisarse."""
        assert can_review(self._make_plan("pending_commit")) is True

    def test_cannot_review_draft(self):
        """Un plan en draft no puede revisarse."""
        assert can_review(self._make_plan("draft")) is False

    def test_cannot_review_executing(self):
        """Un plan en executing no puede revisarse."""
        assert can_review(self._make_plan("executing")) is False

    def test_cannot_review_completed(self):
        """Un plan completado no puede revisarse."""
        assert can_review(self._make_plan("completed")) is False

    def test_cannot_review_failed(self):
        """Un plan fallido no puede revisarse."""
        assert can_review(self._make_plan("failed")) is False
