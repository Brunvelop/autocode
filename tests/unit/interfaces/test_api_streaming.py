"""
Tests for SSE streaming functionality in autocode.interfaces.api.

Tests the streaming endpoint registration, handler creation,
and integration with the function registry streaming support.
"""
import pytest
import asyncio
from unittest.mock import Mock, patch, MagicMock, AsyncMock
from fastapi.testclient import TestClient
from fastapi.responses import StreamingResponse

from autocode.interfaces.api import (
    _create_stream_handler,
    _register_dynamic_endpoints,
    _create_dynamic_model,
)
from autocode.interfaces.models import FunctionInfo, ParamSchema, GenericOutput


class TestCreateStreamHandler:
    """Tests for _create_stream_handler — SSE handler creation."""
    
    def test_stream_handler_returns_streaming_response(self):
        """Stream handler returns a StreamingResponse."""
        async def mock_stream_func(**kwargs):
            yield "event: token\ndata: {\"chunk\": \"hello\"}\n\n"
            yield "event: complete\ndata: {\"success\": true}\n\n"
        
        func_info = FunctionInfo(
            name="test_stream",
            func=Mock(),
            description="Test stream function",
            params=[
                ParamSchema(name="message", type=str, required=True, description="User message")
            ],
            http_methods=["POST"],
            interfaces=["api"],
            return_type=GenericOutput,
            streaming=True
        )
        
        handler = _create_stream_handler(func_info, mock_stream_func)
        
        # Create a request model and call handler
        DynamicModel = _create_dynamic_model(func_info, for_post=True)
        request = DynamicModel(message="hello")
        
        result = asyncio.run(handler(request))
        
        assert isinstance(result, StreamingResponse)
        assert result.media_type == "text/event-stream"
        assert result.headers.get("Cache-Control") == "no-cache"
        assert result.headers.get("Connection") == "keep-alive"
        assert result.headers.get("X-Accel-Buffering") == "no"
    
    def test_stream_handler_passes_params_to_stream_func(self):
        """Stream handler correctly passes request params to the stream function."""
        received_params = {}
        
        async def capture_stream_func(**kwargs):
            received_params.update(kwargs)
            yield "event: complete\ndata: {}\n\n"
        
        func_info = FunctionInfo(
            name="param_stream",
            func=Mock(),
            description="Test param passing",
            params=[
                ParamSchema(name="message", type=str, required=True, description="Message"),
                ParamSchema(name="temperature", type=float, default=0.7, required=False, description="Temp"),
            ],
            http_methods=["POST"],
            interfaces=["api"],
            return_type=GenericOutput,
            streaming=True
        )
        
        handler = _create_stream_handler(func_info, capture_stream_func)
        DynamicModel = _create_dynamic_model(func_info, for_post=True)
        request = DynamicModel(message="test", temperature=0.9)
        
        result = asyncio.run(handler(request))
        
        # Consume the generator to trigger capture
        async def consume():
            async for _ in result.body_iterator:
                pass
        asyncio.run(consume())
        
        assert received_params["message"] == "test"
        assert received_params["temperature"] == 0.9


class TestRegisterDynamicEndpointsStreaming:
    """Tests for streaming function registration in _register_dynamic_endpoints."""
    
    def test_streaming_function_registers_as_post_sse(self):
        """Streaming function is registered as POST with SSE summary."""
        stream_func_info = FunctionInfo(
            name="chat_stream_test",
            func=Mock(),
            description="Chat streaming test",
            params=[
                ParamSchema(name="message", type=str, required=True, description="Message")
            ],
            http_methods=["POST"],
            interfaces=["api"],
            return_type=GenericOutput,
            streaming=True
        )
        
        async def mock_stream(**kw):
            yield "event: complete\ndata: {}\n\n"
        
        with patch('autocode.interfaces.api.get_functions_for_interface') as mock_get_funcs, \
             patch('autocode.interfaces.api.get_stream_func') as mock_get_stream:
            mock_get_funcs.return_value = [stream_func_info]
            mock_get_stream.return_value = mock_stream
            
            mock_app = Mock()
            mock_app.add_api_route = Mock()
            
            _register_dynamic_endpoints(mock_app)
            
            # Should register exactly one route
            assert mock_app.add_api_route.call_count == 1
            
            call_args = mock_app.add_api_route.call_args
            assert call_args[0][0] == "/chat_stream_test"
            assert call_args[1]["methods"] == ["POST"]
            assert call_args[1]["operation_id"] == "chat_stream_test_stream"
            assert "[SSE Stream]" in call_args[1]["summary"]
    
    def test_non_streaming_functions_unchanged(self):
        """Non-streaming functions are registered normally."""
        normal_func_info = FunctionInfo(
            name="normal_func",
            func=lambda x: GenericOutput(result=x, success=True),
            description="Normal function",
            params=[
                ParamSchema(name="x", type=int, required=True, description="Input")
            ],
            http_methods=["GET", "POST"],
            interfaces=["api"],
            return_type=GenericOutput,
            streaming=False
        )
        
        with patch('autocode.interfaces.api.get_functions_for_interface') as mock_get_funcs:
            mock_get_funcs.return_value = [normal_func_info]
            
            mock_app = Mock()
            mock_app.add_api_route = Mock()
            
            _register_dynamic_endpoints(mock_app)
            
            # Should register GET and POST (2 routes)
            assert mock_app.add_api_route.call_count == 2
            
            call_args_list = mock_app.add_api_route.call_args_list
            methods = [c[1]["methods"][0] for c in call_args_list]
            assert "GET" in methods
            assert "POST" in methods
            
            # Should NOT have SSE prefix
            for call in call_args_list:
                assert "[SSE Stream]" not in call[1]["summary"]
    
    def test_streaming_without_stream_func_logs_error(self):
        """Streaming function without stream_func logs error and is skipped."""
        stream_func_info = FunctionInfo(
            name="broken_stream",
            func=Mock(),
            description="Broken stream",
            params=[],
            http_methods=["POST"],
            interfaces=["api"],
            return_type=GenericOutput,
            streaming=True
        )
        
        with patch('autocode.interfaces.api.get_functions_for_interface') as mock_get_funcs, \
             patch('autocode.interfaces.api.get_stream_func') as mock_get_stream, \
             patch('autocode.interfaces.api.logger') as mock_logger:
            mock_get_funcs.return_value = [stream_func_info]
            mock_get_stream.return_value = None  # No stream_func found
            
            mock_app = Mock()
            mock_app.add_api_route = Mock()
            
            _register_dynamic_endpoints(mock_app)
            
            # Should NOT register any route
            mock_app.add_api_route.assert_not_called()
            
            # Should log error
            mock_logger.error.assert_called_once()
            assert "broken_stream" in mock_logger.error.call_args[0][0]
    
    def test_mixed_streaming_and_normal_functions(self):
        """Both streaming and normal functions can coexist."""
        normal_func = FunctionInfo(
            name="normal",
            func=lambda: GenericOutput(result="ok", success=True),
            description="Normal",
            params=[],
            http_methods=["GET"],
            interfaces=["api"],
            return_type=GenericOutput,
            streaming=False
        )
        stream_func = FunctionInfo(
            name="streamer",
            func=Mock(),
            description="Stream",
            params=[ParamSchema(name="msg", type=str, required=True, description="msg")],
            http_methods=["POST"],
            interfaces=["api"],
            return_type=GenericOutput,
            streaming=True
        )
        
        async def mock_stream(**kw):
            yield "event: complete\ndata: {}\n\n"
        
        with patch('autocode.interfaces.api.get_functions_for_interface') as mock_get_funcs, \
             patch('autocode.interfaces.api.get_stream_func') as mock_get_stream:
            mock_get_funcs.return_value = [normal_func, stream_func]
            mock_get_stream.return_value = mock_stream
            
            mock_app = Mock()
            mock_app.add_api_route = Mock()
            
            _register_dynamic_endpoints(mock_app)
            
            # normal: 1 route (GET), stream: 1 route (POST SSE) = 2 total
            assert mock_app.add_api_route.call_count == 2
