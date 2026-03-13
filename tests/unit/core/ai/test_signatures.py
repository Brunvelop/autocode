"""Tests for DSPy Signatures - TaskExecutionSignature, ChatSignature."""
import pytest

from autocode.core.ai.signatures import TaskExecutionSignature, ChatSignature


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


class TestChatSignature:
    """Tests for ChatSignature DSPy signature."""

    def test_signature_has_required_input_fields(self):
        """ChatSignature tiene message y conversation_history como inputs."""
        assert "message" in ChatSignature.input_fields
        assert "conversation_history" in ChatSignature.input_fields

    def test_signature_has_response_output(self):
        """ChatSignature tiene response como output."""
        assert "response" in ChatSignature.output_fields

    def test_signature_input_count(self):
        """ChatSignature tiene exactamente 2 inputs."""
        assert len(ChatSignature.input_fields) == 2

    def test_signature_output_count(self):
        """ChatSignature tiene exactamente 1 output."""
        assert len(ChatSignature.output_fields) == 1

    def test_signature_docstring_exists(self):
        """ChatSignature tiene docstring (usado como system prompt por DSPy)."""
        assert ChatSignature.__doc__ is not None
        assert len(ChatSignature.__doc__) > 50
