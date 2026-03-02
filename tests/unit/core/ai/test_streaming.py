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
    async def test_stream_chat_no_prediction_emits_failed_complete(self):
        """When no Prediction is received, emit a failed complete event."""
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
            
            complete_events = [e for e in events if "event: complete" in e]
            assert len(complete_events) == 1
            data_line = complete_events[0].split("\n")[1]
            data = json.loads(data_line.replace("data: ", ""))
            assert data["success"] is False
            assert "No prediction" in data["message"]
