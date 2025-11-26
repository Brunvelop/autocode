"""
Unit tests for DSPy utilities.
"""
import pytest
from unittest.mock import Mock, patch
from autocode.core.ai.dspy_utils import generate_with_dspy
from autocode.core.ai.signatures import QASignature

class MockPrediction:
    def __init__(self, response):
        self.response = response
        
    def __str__(self):
        return self.response

class TestGenerateWithDspy:

    @patch('autocode.core.ai.dspy_utils.get_dspy_lm')
    @patch('autocode.core.ai.dspy_utils._create_and_execute_module')
    def test_generate_with_dspy_normalizes_predictions(self, mock_execute, mock_get_lm):
        """
        Test that generate_with_dspy handles DSPy Prediction objects in completions
        by converting them to strings, avoiding Pydantic validation errors.
        """
        # Setup mocks
        mock_lm = Mock()
        mock_lm.history = []  # Setup empty history to avoid iteration error
        mock_get_lm.return_value = mock_lm
        
        # Simulate a DSPy response that contains Prediction objects in completions
        # This happens typically with dspy.Predict module
        mock_response = Mock()
        mock_response.response = "Answer"
        mock_response.completions = [
            MockPrediction("Answer 1"),
            MockPrediction("Answer 2")
        ]
        
        mock_execute.return_value = mock_response
        
        # Execute
        result = generate_with_dspy(
            signature_class=QASignature,
            inputs={"question": "Test"},
            module_type='Predict'
        )
        
        # Assert
        assert result.success is True
        # Verify completions are strings, not objects
        assert isinstance(result.completions, list)
        assert len(result.completions) == 2
        assert result.completions[0] == "Answer 1"
        assert result.completions[1] == "Answer 2"
        assert isinstance(result.completions[0], str)
