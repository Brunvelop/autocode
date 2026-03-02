"""Tests for DSPy Signatures - TaskExecutionSignature."""
import pytest

from autocode.core.ai.signatures import TaskExecutionSignature


class TestTaskExecutionSignature:
    """Tests for TaskExecutionSignature DSPy signature."""

    def test_signature_has_required_input_fields(self):
        """TaskExecutionSignature tiene task_instruction y file_path como inputs."""
        assert "task_instruction" in TaskExecutionSignature.input_fields
        assert "file_path" in TaskExecutionSignature.input_fields

    def test_signature_has_completion_summary_output(self):
        """TaskExecutionSignature tiene completion_summary como output."""
        assert "completion_summary" in TaskExecutionSignature.output_fields

    def test_signature_input_count(self):
        """TaskExecutionSignature tiene exactamente 2 inputs."""
        assert len(TaskExecutionSignature.input_fields) == 2

    def test_signature_output_count(self):
        """TaskExecutionSignature tiene exactamente 1 output."""
        assert len(TaskExecutionSignature.output_fields) == 1

    def test_signature_docstring_exists(self):
        """TaskExecutionSignature tiene docstring (usado como system prompt por DSPy)."""
        assert TaskExecutionSignature.__doc__ is not None
        assert len(TaskExecutionSignature.__doc__) > 50
