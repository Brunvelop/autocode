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


class TestPrepareChatTools:
    """Tests for prepare_chat_tools helper."""
    
    @patch('autocode.core.registry.get_functions_for_interface')
    def test_returns_tools_list(self, mock_get_funcs):
        """prepare_chat_tools returns a list of tool wrappers."""
        from autocode.core.ai.dspy_utils import prepare_chat_tools
        from autocode.core.models import FunctionInfo, ParamSchema, GenericOutput
        
        mock_func = Mock(return_value=GenericOutput(result="ok", success=True))
        func_info = FunctionInfo(
            name="test_tool",
            func=mock_func,
            description="A test tool",
            params=[ParamSchema(name="x", type=int, required=True, description="Input")],
            http_methods=["GET"],
            interfaces=["mcp"],
            return_type=GenericOutput
        )
        mock_get_funcs.return_value = [func_info]
        
        tools = prepare_chat_tools()
        assert len(tools) == 1
        assert tools[0].__name__ == "test_tool"
        assert "A test tool" in tools[0].__doc__
    
    @patch('autocode.core.registry.get_functions_for_interface')
    def test_filters_by_enabled_tools(self, mock_get_funcs):
        """prepare_chat_tools filters by enabled_tools list."""
        from autocode.core.ai.dspy_utils import prepare_chat_tools
        from autocode.core.models import FunctionInfo, ParamSchema, GenericOutput
        
        func1 = FunctionInfo(
            name="tool_a", func=Mock(), description="Tool A",
            params=[], http_methods=["GET"], interfaces=["mcp"], return_type=GenericOutput
        )
        func2 = FunctionInfo(
            name="tool_b", func=Mock(), description="Tool B",
            params=[], http_methods=["GET"], interfaces=["mcp"], return_type=GenericOutput
        )
        mock_get_funcs.return_value = [func1, func2]
        
        tools = prepare_chat_tools(enabled_tools=["tool_a"])
        assert len(tools) == 1
        assert tools[0].__name__ == "tool_a"
    
    @patch('autocode.core.registry.get_functions_for_interface')
    def test_empty_when_no_mcp_functions(self, mock_get_funcs):
        """prepare_chat_tools returns empty list when no MCP functions."""
        from autocode.core.ai.dspy_utils import prepare_chat_tools
        
        mock_get_funcs.return_value = []
        tools = prepare_chat_tools()
        assert tools == []


class TestCreateToolWrapper:
    """Tests for _create_tool_wrapper helper."""
    
    def test_wrapper_has_correct_name(self):
        """Wrapper function has the correct __name__."""
        from autocode.core.ai.dspy_utils import _create_tool_wrapper
        from autocode.core.models import FunctionInfo, ParamSchema, GenericOutput
        
        func_info = FunctionInfo(
            name="my_tool", func=Mock(), description="My tool",
            params=[], http_methods=["GET"], interfaces=["mcp"], return_type=GenericOutput
        )
        wrapper = _create_tool_wrapper(func_info)
        assert wrapper.__name__ == "my_tool"
    
    def test_wrapper_has_enriched_docstring(self):
        """Wrapper has docstring with parameter info."""
        from autocode.core.ai.dspy_utils import _create_tool_wrapper
        from autocode.core.models import FunctionInfo, ParamSchema, GenericOutput
        
        func_info = FunctionInfo(
            name="search", func=Mock(), description="Search files",
            params=[
                ParamSchema(name="query", type=str, required=True, description="Search query"),
                ParamSchema(name="limit", type=int, default=10, required=False, description="Max results")
            ],
            http_methods=["GET"], interfaces=["mcp"], return_type=GenericOutput
        )
        wrapper = _create_tool_wrapper(func_info)
        
        assert "Search files" in wrapper.__doc__
        assert "query" in wrapper.__doc__
        assert "required" in wrapper.__doc__
        assert "limit" in wrapper.__doc__
        assert "optional" in wrapper.__doc__
    
    def test_wrapper_handles_kwargs_nested(self):
        """Wrapper handles DSPy ReAct nested kwargs pattern."""
        from autocode.core.ai.dspy_utils import _create_tool_wrapper
        from autocode.core.models import FunctionInfo, ParamSchema, GenericOutput
        
        real_func = Mock(return_value="result")
        func_info = FunctionInfo(
            name="my_func", func=real_func, description="Test",
            params=[ParamSchema(name="x", type=int, required=True, description="Input")],
            http_methods=["GET"], interfaces=["mcp"], return_type=GenericOutput
        )
        wrapper = _create_tool_wrapper(func_info)
        
        # DSPy sometimes passes params as kwargs={'x': 5}
        result = wrapper(kwargs={"x": 5})
        real_func.assert_called_once_with(x=5)
    
    def test_wrapper_handles_direct_kwargs(self):
        """Wrapper handles direct keyword arguments."""
        from autocode.core.ai.dspy_utils import _create_tool_wrapper
        from autocode.core.models import FunctionInfo, ParamSchema, GenericOutput
        
        real_func = Mock(return_value="result")
        func_info = FunctionInfo(
            name="my_func", func=real_func, description="Test",
            params=[ParamSchema(name="x", type=int, required=True, description="Input")],
            http_methods=["GET"], interfaces=["mcp"], return_type=GenericOutput
        )
        wrapper = _create_tool_wrapper(func_info)
        
        result = wrapper(x=5)
        real_func.assert_called_once_with(x=5)
    
    def test_wrapper_handles_execution_error(self):
        """Wrapper catches exceptions and returns error string."""
        from autocode.core.ai.dspy_utils import _create_tool_wrapper
        from autocode.core.models import FunctionInfo, ParamSchema, GenericOutput
        
        real_func = Mock(side_effect=ValueError("bad input"))
        func_info = FunctionInfo(
            name="failing_func", func=real_func, description="Fails",
            params=[], http_methods=["GET"], interfaces=["mcp"], return_type=GenericOutput
        )
        wrapper = _create_tool_wrapper(func_info)
        
        result = wrapper()
        assert "Error ejecutando failing_func" in result
        assert "bad input" in result
    
    def test_wrapper_docstring_includes_choices(self):
        """Wrapper docstring includes choices for Literal types."""
        from autocode.core.ai.dspy_utils import _create_tool_wrapper
        from autocode.core.models import FunctionInfo, ParamSchema, GenericOutput
        
        func_info = FunctionInfo(
            name="choose", func=Mock(), description="Choose option",
            params=[
                ParamSchema(name="option", type=str, required=True, 
                           description="The option", choices=["a", "b", "c"])
            ],
            http_methods=["GET"], interfaces=["mcp"], return_type=GenericOutput
        )
        wrapper = _create_tool_wrapper(func_info)
        
        assert "choices: a, b, c" in wrapper.__doc__
