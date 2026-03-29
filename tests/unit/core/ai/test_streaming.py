"""
Unit tests for streaming utilities.
"""
import asyncio
import json
import pytest
import pytest_asyncio
from unittest.mock import Mock, patch, AsyncMock, MagicMock

from autocode.core.ai.streaming import (
    _format_sse,
    AutocodeStatusProvider,
    stream_chat
)


class TestFormatSSE:
    """Tests for _format_sse helper function."""
    
    def test_format_sse_token_event(self):
        """Format a token SSE event correctly."""
        result = _format_sse("token", {"chunk": "Hello", "field": "response"})
        assert result.startswith("event: token\n")
        assert "data: " in result
        assert result.endswith("\n\n")
        
        # Parse data payload
        data_line = result.split("\n")[1]
        data = json.loads(data_line.replace("data: ", ""))
        assert data["chunk"] == "Hello"
        assert data["field"] == "response"
    
    def test_format_sse_status_event(self):
        """Format a status SSE event correctly."""
        result = _format_sse("status", {"message": "Processing..."})
        assert "event: status\n" in result
        data_line = result.split("\n")[1]
        data = json.loads(data_line.replace("data: ", ""))
        assert data["message"] == "Processing..."
    
    def test_format_sse_unicode(self):
        """Format SSE with unicode characters (ensure_ascii=False)."""
        result = _format_sse("status", {"message": "🛠️ Llamando herramienta"})
        assert "🛠️" in result
        data_line = result.split("\n")[1]
        data = json.loads(data_line.replace("data: ", ""))
        assert data["message"] == "🛠️ Llamando herramienta"
    
    def test_format_sse_complete_event(self):
        """Format a complete SSE event with full payload."""
        payload = {
            "success": True,
            "result": {"response": "Answer"},
            "message": "Done",
            "reasoning": None,
            "trajectory": None,
            "completions": None,
            "history": None
        }
        result = _format_sse("complete", payload)
        assert "event: complete\n" in result
        data_line = result.split("\n")[1]
        data = json.loads(data_line.replace("data: ", ""))
        assert data["success"] is True
        assert data["result"]["response"] == "Answer"
    
    def test_format_sse_error_event(self):
        """Format an error SSE event."""
        result = _format_sse("error", {"message": "Something failed", "success": False})
        assert "event: error\n" in result
        data_line = result.split("\n")[1]
        data = json.loads(data_line.replace("data: ", ""))
        assert data["success"] is False
        assert data["message"] == "Something failed"


class TestAutocodeStatusProvider:
    """Tests for AutocodeStatusProvider status messages."""
    
    def test_tool_start_message(self):
        """tool_start returns message with tool name."""
        provider = AutocodeStatusProvider()
        instance = Mock()
        instance.name = "search_tool"
        msg = provider.tool_start_status_message(instance, {})
        assert "search_tool" in msg
        assert "🛠️" in msg
    
    def test_tool_start_message_no_name(self):
        """tool_start falls back to str(instance) if no name attr."""
        provider = AutocodeStatusProvider()
        instance = "some_tool_string"
        msg = provider.tool_start_status_message(instance, {})
        assert "some_tool_string" in msg
    
    def test_tool_end_message(self):
        """tool_end returns completion message."""
        provider = AutocodeStatusProvider()
        msg = provider.tool_end_status_message({})
        assert "✅" in msg
    
    def test_lm_start_message(self):
        """lm_start returns LLM consultation message."""
        provider = AutocodeStatusProvider()
        msg = provider.lm_start_status_message(Mock(), {})
        assert "🧠" in msg
    
    def test_module_end_returns_empty_string(self):
        """module_end returns empty string (safe for DSPy)."""
        provider = AutocodeStatusProvider()
        msg = provider.module_end_status_message({})
        assert msg == ""
    
    def test_lm_end_returns_empty_string(self):
        """lm_end returns empty string (safe for DSPy)."""
        provider = AutocodeStatusProvider()
        msg = provider.lm_end_status_message({})
        assert msg == ""
    
    def test_module_start_message(self):
        """module_start returns processing message with class name."""
        provider = AutocodeStatusProvider()
        
        class FakeModule:
            pass
        
        msg = provider.module_start_status_message(FakeModule(), {})
        assert "FakeModule" in msg
        assert "🔄" in msg

    def test_tool_start_with_displayable_args(self):
        """tool_start formats a preview of non-empty argument values."""
        provider = AutocodeStatusProvider()
        instance = Mock()
        instance.name = "search_tool"
        # Pass real inputs with non-empty values — triggers the args-preview branch
        msg = provider.tool_start_status_message(
            instance, {"query": "test query", "limit": 10}
        )
        assert "search_tool" in msg
        assert "query=" in msg
        assert "🛠️" in msg

    def test_tool_start_filters_empty_values(self):
        """tool_start omits args that are None, empty string, list, or dict."""
        provider = AutocodeStatusProvider()
        instance = Mock()
        instance.name = "my_tool"
        # All values are 'empty' — should fall through to the no-args format
        msg = provider.tool_start_status_message(
            instance, {"x": None, "y": "", "z": [], "w": {}}
        )
        assert msg == "🛠️ my_tool()"


class TestStreamChat:
    """Tests for stream_chat async generator."""
    
    @pytest.mark.asyncio
    async def test_stream_chat_produces_events(self):
        """Mock dspy.streamify to verify flow of SSE events."""
        from dspy.streaming import StreamResponse, StatusMessage
        import dspy
        
        # Create mock chunks that the stream will produce
        mock_chunks = [
            StatusMessage(message="🧠 Consultando al LLM..."),
            StreamResponse(chunk="Hello", signature_field_name="response", 
                         predict_name="predict", is_last_chunk=False),
            StreamResponse(chunk=" World", signature_field_name="response",
                         predict_name="predict", is_last_chunk=True),
        ]
        
        # Create mock prediction
        mock_prediction = dspy.Prediction(response="Hello World")
        mock_chunks.append(mock_prediction)
        
        # Create async iterator from chunks
        async def mock_stream(*args, **kwargs):
            for chunk in mock_chunks:
                yield chunk
        
        with patch('autocode.core.ai.streaming.get_dspy_lm') as mock_lm, \
             patch('autocode.core.ai.streaming.prepare_chat_tools', return_value=[]), \
             patch('autocode.core.ai.streaming.MODULE_MAP') as mock_module_map, \
             patch('autocode.core.ai.streaming.dspy') as mock_dspy:
            
            mock_lm.return_value = Mock()
            mock_module_map.__getitem__ = Mock(return_value=Mock())
            
            # Mock dspy.streamify to return our mock stream function
            mock_dspy.streamify.return_value = mock_stream
            mock_dspy.context = dspy.context
            mock_dspy.Prediction = dspy.Prediction
            mock_dspy.streaming.StreamListener = Mock()
            mock_dspy.streaming.StreamResponse = StreamResponse
            mock_dspy.streaming.StatusMessage = StatusMessage
            
            events = []
            async for event in stream_chat(message="test", conversation_history=""):
                events.append(event)
            
            # Should have status, token, token, and complete events
            assert len(events) >= 3
            
            # Check we got token events
            token_events = [e for e in events if "event: token" in e]
            assert len(token_events) == 2
            
            # Check we got a complete event
            complete_events = [e for e in events if "event: complete" in e]
            assert len(complete_events) == 1
    
    @pytest.mark.asyncio
    async def test_stream_chat_error_produces_error_event(self):
        """Errors produce SSE error event."""
        with patch('autocode.core.ai.streaming.get_dspy_lm') as mock_lm:
            mock_lm.side_effect = ValueError("API key missing")
            
            events = []
            async for event in stream_chat(message="test", conversation_history=""):
                events.append(event)
            
            assert len(events) == 1
            assert "event: error" in events[0]
            data_line = events[0].split("\n")[1]
            data = json.loads(data_line.replace("data: ", ""))
            assert "API key missing" in data["message"]
            assert data["success"] is False
    
    @pytest.mark.asyncio
    async def test_stream_chat_filters_empty_status_messages(self):
        """StatusMessage with empty message is not emitted as SSE."""
        from dspy.streaming import StreamResponse, StatusMessage
        import dspy
        
        mock_chunks = [
            StatusMessage(message=""),  # Should be filtered
            StatusMessage(message="Real status"),
        ]
        mock_chunks.append(dspy.Prediction(response="result"))
        
        async def mock_stream(*args, **kwargs):
            for chunk in mock_chunks:
                yield chunk
        
        with patch('autocode.core.ai.streaming.get_dspy_lm') as mock_lm, \
             patch('autocode.core.ai.streaming.prepare_chat_tools', return_value=[]), \
             patch('autocode.core.ai.streaming.MODULE_MAP') as mock_module_map, \
             patch('autocode.core.ai.streaming.dspy') as mock_dspy:
            
            mock_lm.return_value = Mock()
            mock_module_map.__getitem__ = Mock(return_value=Mock())
            mock_dspy.streamify.return_value = mock_stream
            mock_dspy.context = dspy.context
            mock_dspy.Prediction = dspy.Prediction
            mock_dspy.streaming.StreamListener = Mock()
            mock_dspy.streaming.StreamResponse = StreamResponse
            mock_dspy.streaming.StatusMessage = StatusMessage
            
            events = []
            async for event in stream_chat(message="test", conversation_history=""):
                events.append(event)
            
            status_events = [e for e in events if "event: status" in e]
            assert len(status_events) == 1  # Only "Real status", empty one filtered
    
    @pytest.mark.asyncio
    async def test_stream_chat_cancellation_handling(self):
        """CancelledError is handled gracefully without emitting events."""
        import dspy
        
        async def mock_stream_cancel(*args, **kwargs):
            yield "first"  # This won't match any isinstance checks
            raise asyncio.CancelledError()
        
        with patch('autocode.core.ai.streaming.get_dspy_lm') as mock_lm, \
             patch('autocode.core.ai.streaming.prepare_chat_tools', return_value=[]), \
             patch('autocode.core.ai.streaming.MODULE_MAP') as mock_module_map, \
             patch('autocode.core.ai.streaming.dspy') as mock_dspy:
            
            mock_lm.return_value = Mock()
            mock_module_map.__getitem__ = Mock(return_value=Mock())
            mock_dspy.streamify.return_value = mock_stream_cancel
            mock_dspy.context = dspy.context
            mock_dspy.Prediction = dspy.Prediction
            mock_dspy.streaming.StreamListener = Mock()
            mock_dspy.streaming.StreamResponse = type('SR', (), {})
            mock_dspy.streaming.StatusMessage = type('SM', (), {})
            
            events = []
            async for event in stream_chat(message="test", conversation_history=""):
                events.append(event)
            
            # Should not have error events — cancellation is silent
            error_events = [e for e in events if "event: error" in e]
            assert len(error_events) == 0
    
    @pytest.mark.asyncio
    async def test_stream_chat_no_prediction_emits_error_event(self):
        """When no Prediction is received, emit an error event (not a complete event)."""
        import dspy
        from dspy.streaming import StatusMessage

        mock_chunks = [
            StatusMessage(message="Processing..."),
            # No Prediction chunk — stream ends without one
        ]

        async def mock_stream(*args, **kwargs):
            for chunk in mock_chunks:
                yield chunk

        with patch('autocode.core.ai.streaming.get_dspy_lm') as mock_lm, \
             patch('autocode.core.ai.streaming.prepare_chat_tools', return_value=[]), \
             patch('autocode.core.ai.streaming.MODULE_MAP') as mock_module_map, \
             patch('autocode.core.ai.streaming.dspy') as mock_dspy:

            mock_lm.return_value = Mock()
            mock_module_map.__getitem__ = Mock(return_value=Mock())
            mock_dspy.streamify.return_value = mock_stream
            mock_dspy.context = dspy.context
            mock_dspy.Prediction = dspy.Prediction
            mock_dspy.streaming.StreamListener = Mock()
            mock_dspy.streaming.StreamResponse = type('SR', (), {})
            mock_dspy.streaming.StatusMessage = StatusMessage

            events = []
            async for event in stream_chat(message="test", conversation_history=""):
                events.append(event)

            # No prediction → error event, not complete event
            error_events = [e for e in events if "event: error" in e]
            assert len(error_events) == 1
            complete_events = [e for e in events if "event: complete" in e]
            assert len(complete_events) == 0

            data_line = error_events[0].split("\n")[1]
            data = json.loads(data_line.replace("data: ", ""))
            assert data["success"] is False
            assert "No prediction" in data["message"]

    @pytest.mark.asyncio
    async def test_stream_chat_streaming_incompatible_error(self):
        """A streaming-incompatible error emits an error event with streaming_incompatible=True."""
        import dspy

        async def mock_stream_compat_error(*args, **kwargs):
            raise RuntimeError("streaming error: model does not support it")
            yield  # Make it a generator

        with patch('autocode.core.ai.streaming.get_dspy_lm') as mock_lm, \
             patch('autocode.core.ai.streaming.prepare_chat_tools', return_value=[]), \
             patch('autocode.core.ai.streaming.MODULE_MAP') as mock_module_map, \
             patch('autocode.core.ai.streaming.dspy') as mock_dspy:

            mock_lm.return_value = Mock(history=[])
            mock_module_map.__getitem__ = Mock(return_value=Mock())
            mock_dspy.streamify.return_value = mock_stream_compat_error
            mock_dspy.context = dspy.context
            mock_dspy.Prediction = dspy.Prediction
            mock_dspy.streaming.StreamListener = Mock()
            mock_dspy.streaming.StreamResponse = type('SR', (), {})
            mock_dspy.streaming.StatusMessage = type('SM', (), {})

            events = []
            async for event in stream_chat(message="test", conversation_history=""):
                events.append(event)

            assert len(events) == 1
            assert "event: error" in events[0]
            data_line = events[0].split("\n")[1]
            data = json.loads(data_line.replace("data: ", ""))
            assert data["success"] is False
            assert data.get("streaming_incompatible") is True


# ============================================================================
# HELPER FUNCTION UNIT TESTS — _build_complete_event, _classify_streaming_error
# ============================================================================


class TestBuildCompleteEvent:
    """Direct unit tests for _build_complete_event() helper.

    _build_complete_event now returns ChatResult-shaped dicts:
    {response, reasoning, trajectory, history, completions}.
    It is only called when prediction is not None (no-prediction case
    is handled in stream_chat as an error event).
    """

    def test_prediction_with_response_returns_chat_result_shape(self):
        """_build_complete_event with valid prediction returns ChatResult-shaped dict."""
        import dspy
        from autocode.core.ai.streaming import _build_complete_event

        prediction = dspy.Prediction(response="Hello!")
        lm = Mock()
        lm.history = []  # Empty history → history stays None

        result = _build_complete_event(prediction, lm)

        assert result["response"] == "Hello!"
        assert "success" not in result  # ChatResult shape has no success field
        assert "result" not in result   # No nested result wrapper
        assert "message" not in result  # No message field
        assert result["history"] is None
        assert result["completions"] is None

    def test_prediction_with_trajectory_is_normalized(self):
        """Trajectory dict in prediction is normalized and serialized."""
        import dspy
        from autocode.core.ai.streaming import _build_complete_event

        prediction = dspy.Prediction(
            response="Done",
            trajectory={"thought_0": "First thought", "tool_name_0": "search"}
        )
        lm = Mock()
        lm.history = []

        result = _build_complete_event(prediction, lm)

        assert isinstance(result["trajectory"], list)
        assert result["trajectory"][0]["thought"] == "First thought"

    def test_lm_history_is_serialized(self):
        """Non-empty lm.history is included in the complete event."""
        import dspy
        from autocode.core.ai.streaming import _build_complete_event

        prediction = dspy.Prediction(response="Hi")
        lm = Mock()
        lm.history = [{"prompt": "test", "response": "Hi"}]

        result = _build_complete_event(prediction, lm)

        assert result["history"] is not None
        assert isinstance(result["history"], list)

    def test_lm_history_serialization_failure_logged(self):
        """If _serialize_value raises on history, history stays None."""
        import dspy
        from autocode.core.ai.streaming import _build_complete_event

        prediction = dspy.Prediction(response="Hi")
        lm = Mock()
        lm.history = [{"some": "data"}]  # Non-empty → enters the try block

        with patch('autocode.core.ai.streaming._serialize_value', side_effect=RuntimeError("fail")):
            result = _build_complete_event(prediction, lm)

        # Exception was caught; history falls back to None
        assert result["history"] is None
        assert result["response"] == "Hi"  # Prediction is still valid

    def test_prediction_with_no_response_attr_uses_empty_string(self):
        """If prediction has no response field, response defaults to empty string."""
        import dspy
        from autocode.core.ai.streaming import _build_complete_event

        # Prediction without a response field
        prediction = dspy.Prediction()
        lm = Mock()
        lm.history = []

        result = _build_complete_event(prediction, lm)

        assert result["response"] == ""


class TestClassifyStreamingError:
    """Unit tests for _classify_streaming_error() helper."""

    def test_streaming_error_keyword(self):
        """'streaming error' string is recognized as streaming-incompatible."""
        from autocode.core.ai.streaming import _classify_streaming_error

        assert _classify_streaming_error("streaming error occurred") is True

    def test_mid_stream_fallback_error(self):
        """'MidStreamFallbackError' is recognized as streaming-incompatible."""
        from autocode.core.ai.streaming import _classify_streaming_error

        assert _classify_streaming_error("MidStreamFallbackError: ...") is True

    def test_finish_reason_error(self):
        """'finish_reason: error' is recognized as streaming-incompatible."""
        from autocode.core.ai.streaming import _classify_streaming_error

        assert _classify_streaming_error("finish_reason: error") is True

    def test_normal_error_not_classified(self):
        """Generic timeout or network errors are NOT streaming-incompatible."""
        from autocode.core.ai.streaming import _classify_streaming_error

        assert _classify_streaming_error("Connection timeout") is False
        assert _classify_streaming_error("API key missing") is False
        assert _classify_streaming_error("Model not found") is False


class TestStreamChatExceptionGroupUnwrapping:
    """Test ExceptionGroup unwrapping logic in stream_chat (line 247)."""

    @pytest.mark.asyncio
    async def test_exception_group_is_unwrapped_to_root_cause(self):
        """An exception with .exceptions list is unwrapped to find root error."""
        import dspy

        # Create a nested exception structure that mimics anyio TaskGroup behavior
        # Note: use a non-streaming-error message to avoid triggering streaming_incompatible path
        inner_error = RuntimeError("Connection timeout in nested task")

        class FakeExceptionGroup(Exception):
            """Mimics the structure of anyio ExceptionGroup."""
            def __init__(self, exceptions):
                self.exceptions = exceptions
                super().__init__(str(exceptions))

        async def mock_stream_eg(*args, **kwargs):
            raise FakeExceptionGroup([inner_error])
            yield  # Make it an async generator

        with patch('autocode.core.ai.streaming.get_dspy_lm') as mock_lm, \
             patch('autocode.core.ai.streaming.prepare_chat_tools', return_value=[]), \
             patch('autocode.core.ai.streaming.MODULE_MAP') as mock_module_map, \
             patch('autocode.core.ai.streaming.dspy') as mock_dspy:

            mock_lm.return_value = Mock(history=[])
            mock_module_map.__getitem__ = Mock(return_value=Mock())
            mock_dspy.streamify.return_value = mock_stream_eg
            mock_dspy.context = dspy.context
            mock_dspy.Prediction = dspy.Prediction
            mock_dspy.streaming.StreamListener = Mock()
            mock_dspy.streaming.StreamResponse = type('SR', (), {})
            mock_dspy.streaming.StatusMessage = type('SM', (), {})

            events = []
            async for event in stream_chat(message="test", conversation_history=""):
                events.append(event)

        # Should emit error with the unwrapped inner error message
        assert len(events) == 1
        assert "event: error" in events[0]
        data_line = events[0].split("\n")[1]
        data = json.loads(data_line.replace("data: ", ""))
        assert data["success"] is False
        # The inner error's message should be in the output (after unwrapping)
        assert "Connection timeout in nested task" in data["message"]


# ============================================================================
# SERIALIZATION UTILITY TESTS — _normalize_trajectory, _serialize_value,
#                                _serialize_complex_object
# ============================================================================


class TestNormalizeTrajectory:
    """Tests for _normalize_trajectory() (private helper in streaming.py)."""

    def test_preserves_already_clean_list_trajectory(self):
        """Should preserve a trajectory that is already a list of steps."""
        from autocode.core.ai.streaming import _normalize_trajectory

        clean_trajectory = [
            {"thought": "Thinking...", "tool": "search"},
            {"thought": "Done", "tool": "finish"}
        ]
        result = _normalize_trajectory(clean_trajectory)
        assert result == clean_trajectory

    def test_normalizes_flat_dspy_react_dict(self):
        """Should normalize flat DSPy ReAct dictionary to list of steps."""
        from autocode.core.ai.streaming import _normalize_trajectory

        flat_trajectory = {
            "thought_0": "First thought",
            "tool_name_0": "tool_1",
            "tool_args_0": {"arg": 1},
            "observation_0": "Result 1",

            "thought_1": "Second thought",
            "tool_name_1": "tool_2",
            "tool_args_1": {},
        }

        result = _normalize_trajectory(flat_trajectory)

        assert isinstance(result, list)
        assert len(result) == 2

        assert result[0]["thought"] == "First thought"
        assert result[0]["tool_name"] == "tool_1"
        assert result[0]["tool_args"] == {"arg": 1}
        assert result[0]["observation"] == "Result 1"

        assert result[1]["thought"] == "Second thought"
        assert result[1]["tool_name"] == "tool_2"

    def test_handles_mixed_keys(self):
        """Should handle mixed keys gracefully (generic suffix stripping)."""
        from autocode.core.ai.streaming import _normalize_trajectory

        mixed_trajectory = {
            "thought_0": "T0",
            "tool_0": "func",
            "some_metadata": "ignore_me"
        }

        result = _normalize_trajectory(mixed_trajectory)

        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0]["thought"] == "T0"
        assert result[0].get("tool_name") == "func"

    def test_returns_none_unchanged(self):
        """Should return None as-is."""
        from autocode.core.ai.streaming import _normalize_trajectory
        assert _normalize_trajectory(None) is None

    def test_non_indexed_dict_returned_unchanged(self):
        """A dict without indexed keys is returned as-is."""
        from autocode.core.ai.streaming import _normalize_trajectory

        d = {"some_key": "value", "another": 42}
        result = _normalize_trajectory(d)
        assert result == d

    def test_with_flat_dict_two_steps(self):
        """_normalize_trajectory works with 2 indexed steps."""
        from autocode.core.ai.streaming import _normalize_trajectory

        flat = {
            "thought_0": "First",
            "tool_name_0": "tool1",
            "thought_1": "Second",
            "tool_name_1": "tool2",
        }
        result = _normalize_trajectory(flat)
        assert isinstance(result, list)
        assert len(result) == 2
        assert result[0]["thought"] == "First"
        assert result[1]["tool_name"] == "tool2"

    def test_non_dict_non_list_returned_unchanged(self):
        """Strings, ints, etc. are returned as-is."""
        from autocode.core.ai.streaming import _normalize_trajectory
        assert _normalize_trajectory("some string") == "some string"
        assert _normalize_trajectory(42) == 42


class TestSerializeValue:
    """Tests for _serialize_value() (private helper in streaming.py)."""

    def test_none_returns_none(self):
        from autocode.core.ai.streaming import _serialize_value
        assert _serialize_value(None) is None

    def test_basic_types_unchanged(self):
        from autocode.core.ai.streaming import _serialize_value
        assert _serialize_value("hello") == "hello"
        assert _serialize_value(42) == 42
        assert _serialize_value(3.14) == 3.14
        assert _serialize_value(True) is True

    def test_list_is_recursively_serialized(self):
        from autocode.core.ai.streaming import _serialize_value
        result = _serialize_value([1, "two", [3, 4]])
        assert result == [1, "two", [3, 4]]

    def test_dict_is_recursively_serialized(self):
        from autocode.core.ai.streaming import _serialize_value
        result = _serialize_value({"a": 1, "b": {"c": 2}})
        assert result == {"a": 1, "b": {"c": 2}}

    def test_object_with_dict_is_serialized(self):
        from autocode.core.ai.streaming import _serialize_value

        class Obj:
            def __init__(self):
                self.name = "test"
                self.value = 42
                self._private = "hidden"

        result = _serialize_value(Obj())
        assert result == {"name": "test", "value": 42}
        assert "_private" not in result


class TestSerializeComplexObject:
    """Tests for _serialize_complex_object() (private helper in streaming.py)."""

    def test_pydantic_model_dump_path(self):
        """Uses model_dump() for Pydantic-like objects."""
        from autocode.core.ai.streaming import _serialize_complex_object

        class FakePydantic:
            def model_dump(self):
                return {"field": "value", "number": 7}

        result = _serialize_complex_object(FakePydantic())
        assert result == {"field": "value", "number": 7}

    def test_pydantic_model_dump_failure_falls_back_to_dict(self):
        """Falls back to __dict__ if model_dump() raises."""
        from autocode.core.ai.streaming import _serialize_complex_object

        class BrokenModelDump:
            def model_dump(self):
                raise RuntimeError("broken")

            def __init__(self):
                self.name = "fallback"
                self.value = 99

        result = _serialize_complex_object(BrokenModelDump())
        assert result == {"name": "fallback", "value": 99}

    def test_object_with_dict_path(self):
        """Uses __dict__ for plain objects, skipping private attrs."""
        from autocode.core.ai.streaming import _serialize_complex_object

        class Plain:
            def __init__(self):
                self.x = 1
                self.y = "hello"
                self._private = "hidden"

        result = _serialize_complex_object(Plain())
        assert result == {"x": 1, "y": "hello"}
        assert "_private" not in result

    def test_json_fallback_for_non_dict_objects(self):
        """Falls back to json for objects without __dict__ (e.g. tuples)."""
        from autocode.core.ai.streaming import _serialize_complex_object
        result = _serialize_complex_object((1, 2, 3))
        assert result == [1, 2, 3]  # json serializes tuples as arrays

    def test_str_fallback_for_unserializable_objects(self):
        """Returns str() as last resort via json default=str."""
        from autocode.core.ai.streaming import _serialize_complex_object

        class NoDict:
            __slots__ = []  # disables __dict__, forces json/str fallback path

            def __str__(self):
                return "NoDict-instance"

        result = _serialize_complex_object(NoDict())
        assert isinstance(result, str)
        assert "NoDict-instance" in result

    def test_nested_object_via_model_dump_is_recursively_serialized(self):
        """Recursively serializes nested objects from model_dump."""
        from autocode.core.ai.streaming import _serialize_complex_object

        class Inner:
            def __init__(self):
                self.val = 42

        class Outer:
            def model_dump(self):
                return {"inner": Inner()}  # returns a non-basic value

        result = _serialize_complex_object(Outer())
        assert result == {"inner": {"val": 42}}
