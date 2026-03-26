"""
Unit tests for DSPy utilities.
"""
import pytest
from unittest.mock import Mock, patch
from autocode.core.ai.dspy_utils import generate_with_dspy
from autocode.core.ai.signatures import ChatSignature

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
            signature_class=ChatSignature,
            inputs={"message": "Test", "conversation_history": ""},
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
    
    @patch('autocode.core.ai.dspy_utils.Refract')
    def test_returns_tools_list(self, mock_refract_cls):
        """prepare_chat_tools returns a list of tool wrappers."""
        from autocode.core.ai.dspy_utils import prepare_chat_tools
        from autocode.core.models import FunctionInfo, ParamSchema, GenericOutput
        
        mock_app = Mock()
        mock_refract_cls.current.return_value = mock_app
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
        mock_app.get_functions_for_interface.return_value = [func_info]
        
        tools = prepare_chat_tools()
        assert len(tools) == 1
        assert tools[0].__name__ == "test_tool"
        assert "A test tool" in tools[0].__doc__
    
    @patch('autocode.core.ai.dspy_utils.Refract')
    def test_filters_by_enabled_tools(self, mock_refract_cls):
        """prepare_chat_tools filters by enabled_tools list."""
        from autocode.core.ai.dspy_utils import prepare_chat_tools
        from autocode.core.models import FunctionInfo, ParamSchema, GenericOutput
        
        mock_app = Mock()
        mock_refract_cls.current.return_value = mock_app
        func1 = FunctionInfo(
            name="tool_a", func=Mock(), description="Tool A",
            params=[], http_methods=["GET"], interfaces=["mcp"], return_type=GenericOutput
        )
        func2 = FunctionInfo(
            name="tool_b", func=Mock(), description="Tool B",
            params=[], http_methods=["GET"], interfaces=["mcp"], return_type=GenericOutput
        )
        mock_app.get_functions_for_interface.return_value = [func1, func2]
        
        tools = prepare_chat_tools(enabled_tools=["tool_a"])
        assert len(tools) == 1
        assert tools[0].__name__ == "tool_a"
    
    @patch('autocode.core.ai.dspy_utils.Refract')
    def test_empty_when_no_mcp_functions(self, mock_refract_cls):
        """prepare_chat_tools returns empty list when no MCP functions."""
        from autocode.core.ai.dspy_utils import prepare_chat_tools
        
        mock_app = Mock()
        mock_refract_cls.current.return_value = mock_app
        mock_app.get_functions_for_interface.return_value = []
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


# ============================================================================
# NEW TESTS — COMMIT 8 EXPANSION
# ============================================================================


class TestGetDspyLm:
    """Tests for get_dspy_lm() public API."""

    @patch.dict('os.environ', {}, clear=True)
    def test_raises_without_api_key(self):
        """Raises ValueError when no API key in params or environment."""
        from autocode.core.ai.dspy_utils import get_dspy_lm

        with pytest.raises(ValueError, match="OPENROUTER_API_KEY"):
            get_dspy_lm('openrouter/openai/gpt-4o')

    @patch('autocode.core.ai.dspy_utils.dspy.LM')
    def test_uses_explicit_api_key(self, mock_lm_class):
        """When api_key is passed explicitly, configures dspy.LM correctly."""
        from autocode.core.ai.dspy_utils import get_dspy_lm

        get_dspy_lm('openrouter/openai/gpt-4o', api_key='test-key-123')

        mock_lm_class.assert_called_once_with(
            'openrouter/openai/gpt-4o',
            api_key='test-key-123',
            max_tokens=16000,
            temperature=0.7,
        )

    @patch('autocode.core.ai.dspy_utils.dspy.LM')
    def test_passes_extra_kwargs_to_lm(self, mock_lm_class):
        """Extra kwargs (e.g. cache=False) are forwarded to dspy.LM."""
        from autocode.core.ai.dspy_utils import get_dspy_lm

        get_dspy_lm('openrouter/openai/gpt-4o', api_key='key', cache=False, num_retries=3)

        _, call_kwargs = mock_lm_class.call_args
        assert call_kwargs['cache'] is False
        assert call_kwargs['num_retries'] == 3


class TestGenerateWithDspyErrorPaths:
    """Tests for generate_with_dspy() error-handling paths."""

    def test_invalid_module_type_returns_error(self):
        """Invalid module_type returns DspyOutput with success=False."""
        from autocode.core.ai.dspy_utils import generate_with_dspy

        result = generate_with_dspy(
            signature_class=ChatSignature,
            inputs={"message": "Hi", "conversation_history": ""},
            module_type='NonExistent',
        )

        assert result.success is False
        assert "NonExistent" in result.message

    @patch('autocode.core.ai.dspy_utils.get_dspy_lm', side_effect=ValueError("OPENROUTER_API_KEY no está configurada"))
    def test_lm_config_error_returns_error(self, mock_get_lm):
        """When get_dspy_lm raises ValueError, returns DspyOutput with success=False."""
        from autocode.core.ai.dspy_utils import generate_with_dspy

        result = generate_with_dspy(
            signature_class=ChatSignature,
            inputs={"message": "Hi", "conversation_history": ""},
        )

        assert result.success is False
        assert "Error configurando LM" in result.message

    @patch('autocode.core.ai.dspy_utils.get_dspy_lm')
    @patch('autocode.core.ai.dspy_utils._create_and_execute_module', side_effect=RuntimeError("API timeout"))
    def test_execution_exception_returns_error(self, mock_execute, mock_get_lm):
        """When module execution raises, returns DspyOutput with success=False."""
        from autocode.core.ai.dspy_utils import generate_with_dspy

        mock_get_lm.return_value = Mock(history=[])

        result = generate_with_dspy(
            signature_class=ChatSignature,
            inputs={"message": "Hi", "conversation_history": ""},
        )

        assert result.success is False
        assert "Error en generación DSPy" in result.message
        assert "API timeout" in result.message

    @patch('autocode.core.ai.dspy_utils.get_dspy_lm')
    @patch('autocode.core.ai.dspy_utils._create_and_execute_module')
    def test_response_without_output_fields_returns_error_with_metadata(self, mock_execute, mock_get_lm):
        """Response with no matching output fields returns error but preserves metadata."""
        from autocode.core.ai.dspy_utils import generate_with_dspy

        mock_lm = Mock()
        mock_lm.history = [{"prompt": "test", "response": "test"}]
        mock_get_lm.return_value = mock_lm

        # Response con atributo 'response' pero ChatSignature espera 'response'
        # Simular que ningún output_field está en el response
        mock_response = Mock(spec=[])  # spec vacío: ningún atributo
        mock_response.completions = None
        mock_response.reasoning = "some reasoning"
        mock_response.trajectory = None
        mock_execute.return_value = mock_response

        result = generate_with_dspy(
            signature_class=ChatSignature,
            inputs={"message": "Hi", "conversation_history": ""},
        )

        assert result.success is False
        assert result.history is not None  # metadata de debug preservada


class TestNormalizeMetadata:
    """Tests for _normalize_metadata() private helper."""

    def test_reasoning_non_string_converted_to_str(self):
        """Non-string reasoning is converted to string."""
        from autocode.core.ai.dspy_utils import _normalize_metadata

        obj_reasoning = Mock()
        obj_reasoning.__str__ = Mock(return_value="my reasoning")

        reasoning, _, _, _ = _normalize_metadata(obj_reasoning, None, None, None)
        assert isinstance(reasoning, str)
        assert reasoning == "my reasoning"

    def test_reasoning_none_stays_none(self):
        """None reasoning stays None."""
        from autocode.core.ai.dspy_utils import _normalize_metadata

        reasoning, _, _, _ = _normalize_metadata(None, None, None, None)
        assert reasoning is None

    def test_completions_with_prediction_objects_converted(self):
        """Completion objects with .response attribute are converted to strings."""
        from autocode.core.ai.dspy_utils import _normalize_metadata

        pred1 = MockPrediction("Answer 1")
        pred2 = MockPrediction("Answer 2")

        _, completions, _, _ = _normalize_metadata(None, [pred1, pred2], None, None)
        assert completions == ["Answer 1", "Answer 2"]
        assert all(isinstance(c, str) for c in completions)

    def test_completions_plain_strings_stay(self):
        """String completions pass through unchanged."""
        from autocode.core.ai.dspy_utils import _normalize_metadata

        _, completions, _, _ = _normalize_metadata(None, ["a", "b"], None, None)
        assert completions == ["a", "b"]

    def test_history_with_model_dump_serialized(self):
        """History items with model_dump() are converted to dicts."""
        from autocode.core.ai.dspy_utils import _normalize_metadata

        item = Mock()
        item.model_dump = Mock(return_value={"prompt": "hello", "response": "world"})
        del item.__dict__  # force model_dump path

        _, _, history, _ = _normalize_metadata(None, None, [item], None)
        assert history == [{"prompt": "hello", "response": "world"}]

    def test_history_with_dict_attribute_serialized(self):
        """History items with __dict__ (but no model_dump) are converted."""
        from autocode.core.ai.dspy_utils import _normalize_metadata

        class SimpleItem:
            def __init__(self):
                self.prompt = "hello"
                self.tokens = 42

        _, _, history, _ = _normalize_metadata(None, None, [SimpleItem()], None)
        assert isinstance(history[0], dict)
        assert history[0]["prompt"] == "hello"

    def test_trajectory_dict_serialized(self):
        """Trajectory as dict with complex values is serialized."""
        from autocode.core.ai.dspy_utils import _normalize_metadata

        class Step:
            def __init__(self):
                self.action = "search"

        _, _, _, trajectory = _normalize_metadata(None, None, None, {"step_0": Step()})
        assert isinstance(trajectory, dict)
        assert isinstance(trajectory["step_0"], dict)

    def test_trajectory_list_serialized(self):
        """Trajectory as list with complex values is serialized."""
        from autocode.core.ai.dspy_utils import _normalize_metadata

        class Step:
            def __init__(self):
                self.action = "search"

        _, _, _, trajectory = _normalize_metadata(None, None, None, [Step()])
        assert isinstance(trajectory, list)
        assert isinstance(trajectory[0], dict)

    def test_trajectory_unknown_type_becomes_none(self):
        """Non-dict, non-list trajectory becomes None to avoid validation errors."""
        from autocode.core.ai.dspy_utils import _normalize_metadata

        _, _, _, trajectory = _normalize_metadata(None, None, None, object())
        assert trajectory is None


class TestExtractSignatureOutputs:
    """Tests for _extract_signature_outputs() private helper."""

    def test_extracts_existing_fields(self):
        """Fields present in both response and signature are extracted."""
        from autocode.core.ai.dspy_utils import _extract_signature_outputs

        response = Mock()
        response.response = "Hello!"  # ChatSignature output field

        result = _extract_signature_outputs(response, ChatSignature)

        assert "response" in result
        assert result["response"] == "Hello!"

    def test_skips_none_fields(self):
        """Fields that exist on response but are None are not included."""
        from autocode.core.ai.dspy_utils import _extract_signature_outputs

        response = Mock()
        response.response = None  # None → should be skipped

        result = _extract_signature_outputs(response, ChatSignature)

        assert "response" not in result


class TestGetModuleKwargsSchema:
    """Tests for get_module_kwargs_schema()."""

    def test_invalid_module_returns_empty_schema(self):
        """Unknown module_type returns empty schema with supports_tools=False."""
        from autocode.core.ai.dspy_utils import get_module_kwargs_schema

        schema = get_module_kwargs_schema('NonExistentModule')

        assert schema == {'params': [], 'supports_tools': False}

    def test_react_supports_tools(self):
        """ReAct module reports supports_tools=True."""
        from autocode.core.ai.dspy_utils import get_module_kwargs_schema

        schema = get_module_kwargs_schema('ReAct')

        assert schema['supports_tools'] is True

    def test_predict_schema_has_no_tools(self):
        """Predict module reports supports_tools=False."""
        from autocode.core.ai.dspy_utils import get_module_kwargs_schema

        schema = get_module_kwargs_schema('Predict')

        assert schema['supports_tools'] is False

    def test_schema_returns_params_list(self):
        """get_module_kwargs_schema returns a list under 'params' key."""
        from autocode.core.ai.dspy_utils import get_module_kwargs_schema

        schema = get_module_kwargs_schema('ChainOfThought')

        assert 'params' in schema
        assert isinstance(schema['params'], list)


class TestGetAllModuleKwargsSchemas:
    """Tests for get_all_module_kwargs_schemas()."""

    def test_returns_schema_for_all_modules(self):
        """Returns a dict with an entry for every module in MODULE_MAP."""
        from autocode.core.ai.dspy_utils import get_all_module_kwargs_schemas, MODULE_MAP

        schemas = get_all_module_kwargs_schemas()

        assert set(schemas.keys()) == set(MODULE_MAP.keys())

    def test_each_entry_has_expected_keys(self):
        """Each schema entry has 'params' and 'supports_tools' keys."""
        from autocode.core.ai.dspy_utils import get_all_module_kwargs_schemas

        schemas = get_all_module_kwargs_schemas()

        for module_type, schema in schemas.items():
            assert 'params' in schema, f"{module_type} missing 'params'"
            assert 'supports_tools' in schema, f"{module_type} missing 'supports_tools'"


class TestGetAvailableToolsInfo:
    """Tests for get_available_tools_info()."""

    def test_none_returns_empty_list(self):
        """None input returns empty list."""
        from autocode.core.ai.dspy_utils import get_available_tools_info

        result = get_available_tools_info(None)
        assert result == []

    def test_empty_list_returns_empty_list(self):
        """Empty list returns empty list."""
        from autocode.core.ai.dspy_utils import get_available_tools_info

        result = get_available_tools_info([])
        assert result == []

    def test_returns_sorted_tool_info(self):
        """Returns sorted list of dicts with name, description, enabled_by_default."""
        from autocode.core.ai.dspy_utils import get_available_tools_info
        from autocode.core.models import FunctionInfo, GenericOutput

        func_b = FunctionInfo(
            name="zebra_tool", func=Mock(), description="Z tool",
            params=[], http_methods=["GET"], interfaces=["mcp"], return_type=GenericOutput
        )
        func_a = FunctionInfo(
            name="alpha_tool", func=Mock(), description="A tool",
            params=[], http_methods=["GET"], interfaces=["mcp"], return_type=GenericOutput
        )

        result = get_available_tools_info([func_b, func_a])

        assert len(result) == 2
        # Sorted alphabetically
        assert result[0]['name'] == 'alpha_tool'
        assert result[1]['name'] == 'zebra_tool'
        # Each entry has required keys
        assert result[0]['description'] == 'A tool'
        assert result[0]['enabled_by_default'] is True


# ============================================================================
# COVERAGE GAP TESTS — fill remaining uncovered branches
# ============================================================================


class TestNormalizeMetadataEdgeCases:
    """Additional branch coverage for _normalize_metadata()."""

    def test_completions_no_response_attr_converted_to_str(self):
        """Completion objects without .response are converted via str()."""
        from autocode.core.ai.dspy_utils import _normalize_metadata

        class NoResponseObj:
            def __str__(self):
                return "fallback-str"

        _, completions, _, _ = _normalize_metadata(None, [NoResponseObj()], None, None)
        assert completions == ["fallback-str"]
        assert isinstance(completions[0], str)

    def test_trajectory_dict_with_model_dump_values(self):
        """Trajectory dict values with model_dump() use that method."""
        from autocode.core.ai.dspy_utils import _normalize_metadata

        class WithModelDump:
            def model_dump(self):
                return {"step": "search", "result": "found"}

        _, _, _, trajectory = _normalize_metadata(
            None, None, None, {"step_0": WithModelDump()}
        )
        assert trajectory == {"step_0": {"step": "search", "result": "found"}}

    def test_trajectory_list_with_model_dump_items(self):
        """Trajectory list items with model_dump() use that method."""
        from autocode.core.ai.dspy_utils import _normalize_metadata

        class WithModelDump:
            def model_dump(self):
                return {"action": "tool_call"}

        _, _, _, trajectory = _normalize_metadata(
            None, None, None, [WithModelDump()]
        )
        assert trajectory == [{"action": "tool_call"}]

    def test_trajectory_dict_with_plain_values(self):
        """Trajectory dict values without model_dump or __dict__ are kept as-is (else branch)."""
        from autocode.core.ai.dspy_utils import _normalize_metadata

        # Plain str/int values have neither model_dump nor __dict__
        _, _, _, trajectory = _normalize_metadata(
            None, None, None, {"step_0": "plain string", "step_1": 42}
        )
        assert trajectory == {"step_0": "plain string", "step_1": 42}

    def test_trajectory_list_with_plain_values(self):
        """Trajectory list items without model_dump or __dict__ are kept as-is (else branch)."""
        from autocode.core.ai.dspy_utils import _normalize_metadata

        # Plain str/int values have neither model_dump nor __dict__
        _, _, _, trajectory = _normalize_metadata(
            None, None, None, ["step_a", "step_b", 99]
        )
        assert trajectory == ["step_a", "step_b", 99]


class TestCreateAndExecuteModule:
    """Tests for _create_and_execute_module() private helper (lines 215-218)."""

    def test_creates_and_executes_module_with_context(self):
        """_create_and_execute_module creates the correct module and calls it."""
        from autocode.core.ai.dspy_utils import _create_and_execute_module
        import dspy

        mock_lm = Mock()
        mock_response = Mock()
        mock_generator = Mock(return_value=mock_response)
        mock_module_class = Mock(return_value=mock_generator)

        with patch('autocode.core.ai.dspy_utils.MODULE_MAP', {'Predict': mock_module_class}), \
             patch('autocode.core.ai.dspy_utils.dspy.context') as mock_ctx:
            mock_ctx.return_value.__enter__ = Mock(return_value=None)
            mock_ctx.return_value.__exit__ = Mock(return_value=False)

            result = _create_and_execute_module(
                mock_lm,
                ChatSignature,
                {"message": "hi", "conversation_history": ""},
                'Predict',
                {}
            )

        mock_module_class.assert_called_once_with(ChatSignature)
        mock_generator.assert_called_once_with(message="hi", conversation_history="")
        assert result == mock_response


class TestGetModuleKwargsSchemaEdgeCases:
    """Additional tests for get_module_kwargs_schema() edge branches."""

    def test_react_tools_excluded_from_params_list(self):
        """'tools' parameter is excluded from ReAct schema params list."""
        from autocode.core.ai.dspy_utils import get_module_kwargs_schema

        schema = get_module_kwargs_schema('ReAct')

        param_names = [p['name'] for p in schema['params']]
        assert 'tools' not in param_names

    def test_inspect_signature_failure_returns_empty_schema(self):
        """When inspect.signature raises, returns empty schema."""
        from autocode.core.ai.dspy_utils import get_module_kwargs_schema

        with patch('autocode.core.ai.dspy_utils.inspect.signature',
                   side_effect=ValueError("Cannot inspect")):
            schema = get_module_kwargs_schema('Predict')

        assert schema == {'params': [], 'supports_tools': False}

    def test_non_serializable_default_with_name_attribute(self):
        """Default values with __name__ are serialized as that name."""
        from autocode.core.ai.dspy_utils import get_module_kwargs_schema

        def my_func():
            pass

        class FakeModule:
            def __init__(self, callback=my_func):
                pass

        with patch('autocode.core.ai.dspy_utils.MODULE_MAP', {'FakeModule': FakeModule}):
            schema = get_module_kwargs_schema('FakeModule')

        assert len(schema['params']) == 1
        # Function objects have __name__, so default should be serialized as 'my_func'
        assert schema['params'][0]['default'] == 'my_func'

    def test_all_schemas_are_json_serializable(self):
        """All module kwargs schemas can be JSON-serialized without error."""
        import json
        from autocode.core.ai.dspy_utils import get_all_module_kwargs_schemas

        schemas = get_all_module_kwargs_schemas()
        # Should not raise TypeError
        json_output = json.dumps(schemas)
        assert json_output is not None
        assert len(json_output) > 0
