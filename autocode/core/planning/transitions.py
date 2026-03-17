"""
transitions.py

State machine for commit plan status transitions.

Centralizes all valid status transitions, replacing scattered ad-hoc
validation in planner.py and executor.py.
"""

from autocode.core.planning.models import CommitPlan


class InvalidTransitionError(ValueError):
    """Raised when an invalid status transition is attempted."""

    def __init__(self, from_status: str, to_status: str, message: str = ""):
        if not message:
            message = f"Invalid transition: '{from_status}' → '{to_status}'"
        super().__init__(message)
        self.from_status = from_status
        self.to_status = to_status


# Complete map of valid state transitions
VALID_TRANSITIONS: dict[str, set[str]] = {
    "draft": {"ready", "executing", "abandoned"},
    "ready": {"draft", "executing", "abandoned"},
    "executing": {"pending_review", "pending_commit", "failed", "completed"},
    "pending_review": {"completed", "reverted", "pending_commit"},
    "pending_commit": {"completed", "reverted"},
    "failed": {"draft", "executing"},
    "completed": set(),  # terminal state
    "reverted": {"draft"},
    "abandoned": {"draft"},
}

# Statuses from which a plan can be executed
EXECUTABLE_STATUSES = {"draft", "ready", "failed", "executing"}

# Statuses from which a plan can be reviewed (approve/revert)
REVIEWABLE_STATUSES = {"pending_review", "pending_commit"}


def validate_transition(from_status: str, to_status: str) -> None:
    """Validate that a status transition is allowed.

    Args:
        from_status: Current status
        to_status: Target status

    Raises:
        InvalidTransitionError: If the transition is not valid
    """
    if from_status not in VALID_TRANSITIONS:
        raise InvalidTransitionError(
            from_status,
            to_status,
            f"Invalid transition: unknown status '{from_status}'",
        )

    valid_targets = VALID_TRANSITIONS[from_status]
    if to_status not in valid_targets:
        raise InvalidTransitionError(from_status, to_status)


def can_execute(plan: CommitPlan) -> bool:
    """Check if a plan can be executed based on its current status.

    Returns True if plan.status is in {draft, ready, failed, executing}.
    """
    return plan.status in EXECUTABLE_STATUSES


def can_review(plan: CommitPlan) -> bool:
    """Check if a plan can be reviewed (approved/reverted) based on its current status.

    Returns True if plan.status is in {pending_review, pending_commit}.
    """
    return plan.status in REVIEWABLE_STATUSES
