"""
Tests for plan executor — SKIPPED pending Phase 2 rewrite (C10-C11).

The executor is being rewritten for pluggable backends. These tests
referenced removed models (PlanTask, TaskExecutionResult) and helpers
(_mock_task_generator) that no longer exist after the model simplification
in Phase 1 (C1-C5).

This file will be completely rewritten in C10 with tests for the new
backend-based executor.
"""

import pytest

pytestmark = pytest.mark.skip(reason="Rewrite pending in Phase 2 (C10-C11)")


def test_placeholder():
    """Placeholder to avoid empty test file warnings."""
    pass
