"""
Unit tests for pipelines.py - high-level AI operation pipelines.

All tests use mocks to avoid real API calls.
Coverage target: calculate_context_usage, chat, chat_stream, get_chat_config.
"""
import pytest
import os
from unittest.mock import Mock, patch

from autocode.core.ai.pipelines import (
    calculate_context_usage,
    chat,
    chat_stream,
    get_chat_config,
)
from autocode.core.ai.models import DspyOutput
from autocode.core.models import GenericOutput


# =============================================================================
# calculate_context_usage
# =============================================================================

class TestCalculateContextUsage:
    """Tests for calculate_context_usage."""

    @patch('autocode.core.ai.pipelines.litellm')
    def test_happy_path_returns_correct_fields(self, mock_litellm):
        """Returns success=True with current, max, percentage calculated from litellm."""
        mock_litellm.token_counter.return_value = 500
        mock_litellm.get_max_tokens.return_value = 4000

        messages = [{"role": "user", "content": "Hello"}]
        result = calculate_context_usage(
            model='openrouter/openai/gpt-4o',
            messages=messages
        )

        assert isinstance(result, GenericOutput)
        assert result.success is True
        assert result.result["current"] == 500
        assert result.result["max"] == 4000
        assert result.result["percentage"] == 12.5

        mock_litellm.token_counter.assert_called_once_with(
            model='openrouter/openai/gpt-4o', messages=messages
        )
        mock_litellm.get_max_tokens.assert_called_once_with('openrouter/openai/gpt-4o')

    @patch('autocode.core.ai.pipelines.litellm')
    def test_percentage_rounded_to_two_decimals(self, mock_litellm):
        """Percentage is rounded to 2 decimal places (e.g. 33.33 not 33.333...)."""
        mock_litellm.token_counter.return_value = 1
        mock_litellm.get_max_tokens.return_value = 3  # 33.333...%

        result = calculate_context_usage(
            model='openrouter/openai/gpt-4o',
            messages=[{"role": "user", "content": "x"}]
        )

        assert result.success is True
        assert result.result["percentage"] == 33.33

    @patch('autocode.core.ai.pipelines.litellm')
    def test_max_tokens_zero_no_division_error(self, mock_litellm):
        """If get_max_tokens returns 0, percentage is 0 (no ZeroDivisionError)."""
        mock_litellm.token_counter.return_value = 500
        mock_litellm.get_max_tokens.return_value = 0

        result = calculate_context_usage(
            model='openrouter/openai/gpt-4o',
            messages=[{"role": "user", "content": "Hello"}]
        )

        assert result.success is True
        assert result.result["percentage"] == 0
        assert result.result["current"] == 500
        assert result.result["max"] == 0

    @patch('autocode.core.ai.pipelines.litellm')
    def test_litellm_error_returns_failure(self, mock_litellm):
        """If litellm raises an exception, returns success=False with zero values."""
        mock_litellm.token_counter.side_effect = Exception("Model not found")

        result = calculate_context_usage(
            model='openrouter/openai/gpt-4o',
            messages=[{"role": "user", "content": "Hello"}]
        )

        assert result.success is False
        assert result.result["current"] == 0
        assert result.result["max"] == 0
        assert result.result["percentage"] == 0
        assert "Model not found" in result.message


# =============================================================================
# calculate_context_usage — path parameter
# =============================================================================

class TestCalculateContextUsageWithPath:
    """Tests for calculate_context_usage with the path parameter."""

    @patch('autocode.core.ai.pipelines.litellm')
    def test_path_only_directory_reads_files_and_counts_tokens(self, mock_litellm, tmp_path):
        """With only path (no messages), reads files recursively and counts tokens."""
        (tmp_path / "main.py").write_text("def hello(): pass")
        (tmp_path / "README.md").write_text("# Project")

        mock_litellm.token_counter.return_value = 200
        mock_litellm.get_max_tokens.return_value = 4000

        result = calculate_context_usage(
            model='openrouter/openai/gpt-4o',
            path=str(tmp_path)
        )

        assert result.success is True
        assert result.result["current"] == 200

        # token_counter was called with a list containing one user message with the file content
        call_kwargs = mock_litellm.token_counter.call_args.kwargs
        messages_passed = call_kwargs['messages']
        assert len(messages_passed) == 1
        assert messages_passed[0]["role"] == "user"
        assert "def hello(): pass" in messages_passed[0]["content"]
        assert "# Project" in messages_passed[0]["content"]

    @patch('autocode.core.ai.pipelines.litellm')
    def test_path_and_messages_combines_both(self, mock_litellm, tmp_path):
        """When both messages and path are given, both contribute to the token count."""
        (tmp_path / "code.py").write_text("x = 42")

        mock_litellm.token_counter.return_value = 300
        mock_litellm.get_max_tokens.return_value = 8000

        messages = [{"role": "user", "content": "Analyze this"}]
        result = calculate_context_usage(
            model='openrouter/openai/gpt-4o',
            messages=messages,
            path=str(tmp_path)
        )

        assert result.success is True
        assert result.result["current"] == 300

        # token_counter was called with the original message + the path content message
        call_kwargs = mock_litellm.token_counter.call_args.kwargs
        messages_passed = call_kwargs['messages']
        assert len(messages_passed) == 2
        assert messages_passed[0]["content"] == "Analyze this"
        assert "x = 42" in messages_passed[1]["content"]

    @patch('autocode.core.ai.pipelines.litellm')
    def test_path_single_file_reads_its_content(self, mock_litellm, tmp_path):
        """When path points to a single file, reads that file directly."""
        single_file = tmp_path / "config.py"
        single_file.write_text("DEBUG = True")

        mock_litellm.token_counter.return_value = 10
        mock_litellm.get_max_tokens.return_value = 4000

        result = calculate_context_usage(
            model='openrouter/openai/gpt-4o',
            path=str(single_file)
        )

        assert result.success is True
        call_kwargs = mock_litellm.token_counter.call_args.kwargs
        messages_passed = call_kwargs['messages']
        assert len(messages_passed) == 1
        assert messages_passed[0]["content"] == "DEBUG = True"

    @patch('autocode.core.ai.pipelines.litellm')
    def test_path_ignores_unreadable_binary_files(self, mock_litellm, tmp_path):
        """Binary files that can't be decoded as UTF-8 are silently skipped."""
        (tmp_path / "readable.py").write_text("print('hi')")
        (tmp_path / "binary.bin").write_bytes(b'\x80\x81\x82\xff')  # invalid UTF-8

        mock_litellm.token_counter.return_value = 50
        mock_litellm.get_max_tokens.return_value = 4000

        result = calculate_context_usage(
            model='openrouter/openai/gpt-4o',
            path=str(tmp_path)
        )

        assert result.success is True
        # The readable file content is passed; binary file is ignored
        call_kwargs = mock_litellm.token_counter.call_args.kwargs
        messages_passed = call_kwargs['messages']
        assert len(messages_passed) == 1
        assert "print('hi')" in messages_passed[0]["content"]

    @patch('autocode.core.ai.pipelines.litellm')
    def test_path_nonexistent_returns_failure(self, mock_litellm):
        """A path that does not exist returns success=False with a clear message."""
        mock_litellm.get_max_tokens.return_value = 4000

        result = calculate_context_usage(
            model='openrouter/openai/gpt-4o',
            path='/this/path/definitely/does/not/exist/xyz123'
        )

        assert result.success is False
        assert result.result["current"] == 0
        assert "Path no encontrado" in result.message

    @patch('autocode.core.ai.pipelines.litellm')
    def test_path_empty_directory_adds_no_content(self, mock_litellm, tmp_path):
        """An empty directory produces no content and is not added to messages."""
        mock_litellm.token_counter.return_value = 0
        mock_litellm.get_max_tokens.return_value = 4000

        result = calculate_context_usage(
            model='openrouter/openai/gpt-4o',
            path=str(tmp_path)  # empty directory
        )

        assert result.success is True
        # No content to add → token_counter called with empty messages list
        call_kwargs = mock_litellm.token_counter.call_args.kwargs
        assert call_kwargs['messages'] == []

    @patch('autocode.core.ai.pipelines.litellm')
    def test_messages_not_mutated_by_path_processing(self, mock_litellm, tmp_path):
        """The original messages list is not mutated when path content is added."""
        (tmp_path / "file.py").write_text("x = 1")
        mock_litellm.token_counter.return_value = 100
        mock_litellm.get_max_tokens.return_value = 4000

        original_messages = [{"role": "user", "content": "hello"}]
        messages_copy = list(original_messages)

        calculate_context_usage(
            model='openrouter/openai/gpt-4o',
            messages=original_messages,
            path=str(tmp_path)
        )

        # Original list must not have been modified
        assert original_messages == messages_copy


# =============================================================================
# chat
# =============================================================================

class TestChat:
    """Tests for chat function."""

    @patch('autocode.core.ai.pipelines.generate_with_dspy')
    @patch('autocode.core.ai.pipelines.prepare_chat_tools')
    def test_happy_path_returns_dspy_output(self, mock_prepare_tools, mock_generate):
        """Returns the DspyOutput produced by generate_with_dspy."""
        mock_prepare_tools.return_value = []
        expected = DspyOutput(
            success=True,
            result={"response": "Hello!"},
            message="Generación exitosa"
        )
        mock_generate.return_value = expected

        result = chat(message="Hello", conversation_history="")

        assert isinstance(result, DspyOutput)
        assert result.success is True
        assert result.result["response"] == "Hello!"

    @patch('autocode.core.ai.pipelines.generate_with_dspy')
    @patch('autocode.core.ai.pipelines.prepare_chat_tools')
    def test_react_injects_tools_and_max_iters(self, mock_prepare_tools, mock_generate):
        """With module_type='ReAct', tools and max_iters=5 are auto-injected."""
        mock_tools = [Mock(name="tool_a"), Mock(name="tool_b")]
        mock_prepare_tools.return_value = mock_tools
        mock_generate.return_value = DspyOutput(success=True, result={})

        chat(
            message="Hello",
            conversation_history="",
            module_type='ReAct',
            module_kwargs=None,  # Not provided — should be initialized
        )

        call_kwargs = mock_generate.call_args.kwargs
        module_kwargs_used = call_kwargs['module_kwargs']

        assert 'tools' in module_kwargs_used
        assert module_kwargs_used['tools'] == mock_tools
        assert module_kwargs_used['max_iters'] == 5

    @patch('autocode.core.ai.pipelines.generate_with_dspy')
    @patch('autocode.core.ai.pipelines.prepare_chat_tools')
    def test_react_does_not_overwrite_existing_tools(self, mock_prepare_tools, mock_generate):
        """If module_kwargs already has 'tools', it is NOT overwritten."""
        mock_prepare_tools.return_value = [Mock()]
        mock_generate.return_value = DspyOutput(success=True, result={})
        custom_tools = [Mock(name="custom")]

        chat(
            message="Hello",
            conversation_history="",
            module_type='ReAct',
            module_kwargs={'tools': custom_tools},
        )

        call_kwargs = mock_generate.call_args.kwargs
        module_kwargs_used = call_kwargs['module_kwargs']

        assert module_kwargs_used['tools'] == custom_tools  # not overwritten

    @patch('autocode.core.ai.pipelines.generate_with_dspy')
    @patch('autocode.core.ai.pipelines.prepare_chat_tools')
    def test_non_react_no_tools_injection(self, mock_prepare_tools, mock_generate):
        """With non-ReAct module types, tools are NOT injected into module_kwargs."""
        mock_prepare_tools.return_value = []
        mock_generate.return_value = DspyOutput(success=True, result={})

        chat(
            message="Hello",
            conversation_history="",
            module_type='Predict',
        )

        call_kwargs = mock_generate.call_args.kwargs
        module_kwargs_used = call_kwargs['module_kwargs']

        assert 'tools' not in module_kwargs_used
        assert 'max_iters' not in module_kwargs_used

    @patch('autocode.core.ai.pipelines.generate_with_dspy')
    @patch('autocode.core.ai.pipelines.prepare_chat_tools')
    def test_prompt_cache_default_enabled(self, mock_prepare_tools, mock_generate):
        """By default, cache_control_injection_points is added to lm_kwargs."""
        mock_prepare_tools.return_value = []
        mock_generate.return_value = DspyOutput(success=True, result={})

        chat(message="Hello", conversation_history="", enable_prompt_cache=True)

        call_kwargs = mock_generate.call_args.kwargs
        assert 'cache_control_injection_points' in call_kwargs

    @patch('autocode.core.ai.pipelines.generate_with_dspy')
    @patch('autocode.core.ai.pipelines.prepare_chat_tools')
    def test_prompt_cache_disabled(self, mock_prepare_tools, mock_generate):
        """With enable_prompt_cache=False, cache_control_injection_points is NOT added."""
        mock_prepare_tools.return_value = []
        mock_generate.return_value = DspyOutput(success=True, result={})

        chat(message="Hello", conversation_history="", enable_prompt_cache=False)

        call_kwargs = mock_generate.call_args.kwargs
        assert 'cache_control_injection_points' not in call_kwargs

    @patch('autocode.core.ai.pipelines.generate_with_dspy')
    @patch('autocode.core.ai.pipelines.prepare_chat_tools')
    def test_exception_returns_error_dspy_output(self, mock_prepare_tools, mock_generate):
        """If generate_with_dspy raises an exception, returns DspyOutput with success=False."""
        mock_prepare_tools.return_value = []
        mock_generate.side_effect = RuntimeError("Unexpected failure")

        result = chat(message="Hello", conversation_history="")

        assert isinstance(result, DspyOutput)
        assert result.success is False
        assert "Unexpected failure" in result.message

    @patch('autocode.core.ai.pipelines.generate_with_dspy')
    @patch('autocode.core.ai.pipelines.prepare_chat_tools')
    def test_inputs_passed_correctly_to_generate(self, mock_prepare_tools, mock_generate):
        """Verifies message and conversation_history are passed as inputs dict."""
        mock_prepare_tools.return_value = []
        mock_generate.return_value = DspyOutput(success=True, result={})

        chat(message="What is Python?", conversation_history="User: hi | Assistant: hello")

        call_kwargs = mock_generate.call_args.kwargs
        inputs = call_kwargs['inputs']
        assert inputs['message'] == "What is Python?"
        assert inputs['conversation_history'] == "User: hi | Assistant: hello"


# =============================================================================
# chat_stream
# =============================================================================

class TestChatStream:
    """Tests for chat_stream function (synchronous delegation to chat)."""

    @patch('autocode.core.ai.pipelines.chat')
    def test_delegates_to_chat_with_all_params(self, mock_chat):
        """chat_stream delegates to chat() passing all parameters unchanged."""
        expected = DspyOutput(success=True, result={"response": "hi"})
        mock_chat.return_value = expected

        result = chat_stream(
            message="Test message",
            conversation_history="prev: hello",
            model='openrouter/openai/gpt-4o',
            max_tokens=8000,
            temperature=0.5,
            module_type='Predict',
            module_kwargs={"n": 2},
            enabled_tools=["tool_a"],
            lm_kwargs={"top_p": 0.9},
            enable_prompt_cache=False
        )

        mock_chat.assert_called_once_with(
            message="Test message",
            conversation_history="prev: hello",
            model='openrouter/openai/gpt-4o',
            max_tokens=8000,
            temperature=0.5,
            module_type='Predict',
            module_kwargs={"n": 2},
            enabled_tools=["tool_a"],
            lm_kwargs={"top_p": 0.9},
            enable_prompt_cache=False
        )
        assert result == expected


# =============================================================================
# get_chat_config
# =============================================================================

class TestGetChatConfig:
    """Tests for get_chat_config function."""

    @patch('autocode.core.ai.pipelines.get_available_tools_info')
    @patch('autocode.core.ai.pipelines.get_all_module_kwargs_schemas')
    @patch('autocode.core.ai.pipelines.Refract')
    @patch('autocode.core.ai.pipelines.fetch_models_info')
    def test_happy_path_returns_all_sections(
        self, mock_fetch_models, mock_refract_cls, mock_schemas, mock_tools_info
    ):
        """Returns success=True with module_kwargs_schemas, available_tools, models."""
        mock_fetch_models.return_value = {}
        mock_app = Mock()
        mock_refract_cls.current.return_value = mock_app
        mock_app.get_functions_for_interface.return_value = []
        mock_schemas.return_value = {
            "Predict": {"params": [], "supports_tools": False},
            "ReAct": {"params": [{"name": "max_iters"}], "supports_tools": True},
        }
        mock_tools_info.return_value = [
            {"name": "tool_a", "description": "A tool", "enabled_by_default": True}
        ]

        result = get_chat_config()

        assert isinstance(result, GenericOutput)
        assert result.success is True
        assert "module_kwargs_schemas" in result.result
        assert "available_tools" in result.result
        assert "models" in result.result

        assert result.result["module_kwargs_schemas"]["ReAct"]["supports_tools"] is True
        assert result.result["available_tools"][0]["name"] == "tool_a"

    @patch('autocode.core.ai.pipelines.get_available_tools_info')
    @patch('autocode.core.ai.pipelines.get_all_module_kwargs_schemas')
    @patch('autocode.core.ai.pipelines.Refract')
    @patch('autocode.core.ai.pipelines.fetch_models_info')
    def test_models_data_structure(
        self, mock_fetch_models, mock_refract_cls, mock_schemas, mock_tools_info
    ):
        """Each model entry has the expected fields from merge of base list + OpenRouter info."""
        mock_fetch_models.return_value = {
            'openrouter/openai/gpt-4o': {
                "name": "GPT-4o",
                "context_length": 128000,
                "top_provider": {"max_completion_tokens": 4096},
                "pricing": {"prompt": "0.005", "completion": "0.015"},
                "supported_parameters": ["temperature", "max_tokens"],
            }
        }
        mock_app = Mock()
        mock_refract_cls.current.return_value = mock_app
        mock_app.get_functions_for_interface.return_value = []
        mock_schemas.return_value = {}
        mock_tools_info.return_value = []

        result = get_chat_config()

        assert result.success is True
        models = result.result["models"]
        assert isinstance(models, list)
        assert len(models) > 0

        gpt4o = next((m for m in models if m["id"] == 'openrouter/openai/gpt-4o'), None)
        assert gpt4o is not None
        assert gpt4o["name"] == "GPT-4o"
        assert gpt4o["context_length"] == 128000
        assert gpt4o["pricing"]["prompt"] == "0.005"
        assert "top_provider" in gpt4o
        assert "supported_parameters" in gpt4o

    @patch('autocode.core.ai.pipelines.get_available_tools_info')
    @patch('autocode.core.ai.pipelines.get_all_module_kwargs_schemas')
    @patch('autocode.core.ai.pipelines.Refract')
    @patch('autocode.core.ai.pipelines.fetch_models_info')
    def test_model_without_openrouter_info_uses_defaults(
        self, mock_fetch_models, mock_refract_cls, mock_schemas, mock_tools_info
    ):
        """Models not found in OpenRouter still appear with id and fallback name."""
        mock_fetch_models.return_value = {}  # No OpenRouter info for any model
        mock_app = Mock()
        mock_refract_cls.current.return_value = mock_app
        mock_app.get_functions_for_interface.return_value = []
        mock_schemas.return_value = {}
        mock_tools_info.return_value = []

        result = get_chat_config()

        assert result.success is True
        models = result.result["models"]
        # All base models should still be present
        assert len(models) > 0

        # Each model should have at least id and name (fallback to last segment of id)
        for model in models:
            assert "id" in model
            assert "name" in model
            assert model["name"] != ""  # Not empty

    @patch('autocode.core.ai.pipelines.fetch_models_info')
    def test_error_returns_failure(self, mock_fetch_models):
        """If an internal call raises, returns success=False with empty result."""
        mock_fetch_models.side_effect = RuntimeError("Network error")

        result = get_chat_config()

        assert result.success is False
        assert result.result == {}
        assert "Network error" in result.message


# =============================================================================
# _read_path_content — private helper
# =============================================================================

class TestReadPathContent:
    """Direct unit tests for _read_path_content() private helper."""

    def test_unreadable_single_file_returns_empty_string(self, tmp_path):
        """When a single file raises on read, returns empty string (lines 42-43)."""
        from autocode.core.ai.pipelines import _read_path_content

        single_file = tmp_path / "locked.py"
        single_file.write_text("content")

        with patch('builtins.open', side_effect=PermissionError("no access")):
            result = _read_path_content(str(single_file))

        assert result == ""

    def test_readable_single_file_returns_content(self, tmp_path):
        """When a single file is readable, returns its full content."""
        from autocode.core.ai.pipelines import _read_path_content

        single_file = tmp_path / "script.py"
        single_file.write_text("print('hello')")

        result = _read_path_content(str(single_file))

        assert result == "print('hello')"

    def test_directory_concatenates_readable_files(self, tmp_path):
        """Directory path returns concatenated content of all readable files."""
        from autocode.core.ai.pipelines import _read_path_content

        (tmp_path / "a.py").write_text("x = 1")
        (tmp_path / "b.py").write_text("y = 2")

        result = _read_path_content(str(tmp_path))

        assert "x = 1" in result
        assert "y = 2" in result
