"""
Integration tests for SSE streaming functionality.

Tests the complete integration between registry streaming support,
API endpoint registration, and SSE response handling.
"""
import pytest
from unittest.mock import Mock, patch
from fastapi.testclient import TestClient

from autocode.core.registry import (
    register_function, clear_registry, get_stream_func,
    get_all_schemas, load_functions, get_function_by_name
)
from autocode.interfaces.api import create_api_app
from autocode.core.models import GenericOutput


class TestStreamingEndToEnd:
    """End-to-end integration tests for SSE streaming."""

    @pytest.fixture(autouse=True)
    def setup_streaming_functions(self):
        """Register test functions with streaming support."""
        async def mock_stream_func(message: str, temperature: float = 0.7):
            """Mock stream function that produces SSE events."""
            yield 'event: status\ndata: {"message": "Processing..."}\n\n'
            yield 'event: token\ndata: {"chunk": "Hello ", "field": "response", "predict_name": "predict", "is_last_chunk": false}\n\n'
            yield 'event: token\ndata: {"chunk": "World", "field": "response", "predict_name": "predict", "is_last_chunk": true}\n\n'
            yield 'event: complete\ndata: {"success": true, "result": {"response": "Hello World"}, "message": "Done", "reasoning": null, "trajectory": null, "completions": null, "history": null}\n\n'

        @register_function(
            http_methods=["POST"],
            interfaces=["api"],
            streaming=True,
            stream_func=mock_stream_func
        )
        def test_stream(message: str, temperature: float = 0.7) -> GenericOutput:
            """Test streaming function."""
            return GenericOutput(result="sync fallback", success=True)

        @register_function(http_methods=["GET", "POST"], interfaces=["api"])
        def test_normal(x: int = 1) -> GenericOutput:
            """Normal non-streaming function."""
            return GenericOutput(result=x * 2, success=True)

        yield

    @patch('autocode.interfaces.api.load_functions')
    def test_streaming_endpoint_exists(self, mock_load):
        """The streaming endpoint exists and accepts POST."""
        app = create_api_app()
        client = TestClient(app)

        response = client.post("/test_stream", json={"message": "hello"})
        assert response.status_code == 200

    @patch('autocode.interfaces.api.load_functions')
    def test_streaming_content_type(self, mock_load):
        """The streaming endpoint returns text/event-stream content type."""
        app = create_api_app()
        client = TestClient(app)

        response = client.post("/test_stream", json={"message": "hello"})
        assert response.status_code == 200
        assert "text/event-stream" in response.headers.get("content-type", "")

    @patch('autocode.interfaces.api.load_functions')
    def test_streaming_response_contains_sse_events(self, mock_load):
        """The streaming response body contains properly formatted SSE events."""
        app = create_api_app()
        client = TestClient(app)

        response = client.post("/test_stream", json={"message": "hello"})
        body = response.text

        # Should contain token events
        assert "event: token" in body
        assert '"chunk": "Hello "' in body
        assert '"chunk": "World"' in body

        # Should contain status event
        assert "event: status" in body
        assert "Processing..." in body

        # Should contain complete event
        assert "event: complete" in body
        assert '"success": true' in body

    @patch('autocode.interfaces.api.load_functions')
    def test_streaming_headers(self, mock_load):
        """The streaming response includes required SSE headers."""
        app = create_api_app()
        client = TestClient(app)

        response = client.post("/test_stream", json={"message": "hello"})
        assert response.headers.get("cache-control") == "no-cache"

    @patch('autocode.interfaces.api.load_functions')
    def test_non_streaming_endpoints_unchanged(self, mock_load):
        """Non-streaming endpoints continue to work as before."""
        app = create_api_app()
        client = TestClient(app)

        # GET should work
        response = client.get("/test_normal?x=5")
        assert response.status_code == 200
        data = response.json()
        assert data["result"] == 10
        assert data["success"] is True

        # POST should work
        response = client.post("/test_normal", json={"x": 7})
        assert response.status_code == 200
        data = response.json()
        assert data["result"] == 14

    @patch('autocode.interfaces.api.load_functions')
    def test_functions_details_includes_streaming_field(self, mock_load):
        """GET /functions/details includes streaming: true for streaming functions."""
        app = create_api_app()
        client = TestClient(app)

        response = client.get("/functions/details")
        assert response.status_code == 200
        data = response.json()

        # Streaming function should have streaming: true
        assert "test_stream" in data["functions"]
        assert data["functions"]["test_stream"]["streaming"] is True

        # Normal function should have streaming: false
        assert "test_normal" in data["functions"]
        assert data["functions"]["test_normal"]["streaming"] is False

    def test_get_stream_func_returns_callable_for_streaming(self):
        """get_stream_func returns the stream function for streaming functions."""
        stream_func = get_stream_func("test_stream")
        assert stream_func is not None
        assert callable(stream_func)

    def test_get_stream_func_returns_none_for_non_streaming(self):
        """get_stream_func returns None for non-streaming functions."""
        stream_func = get_stream_func("test_normal")
        assert stream_func is None

    def test_get_stream_func_returns_none_for_unknown(self):
        """get_stream_func returns None for unknown function names."""
        stream_func = get_stream_func("nonexistent_function")
        assert stream_func is None

    def test_schemas_include_streaming_field(self):
        """get_all_schemas includes streaming field in serialized schemas."""
        schemas = get_all_schemas()
        stream_schema = next((s for s in schemas if s.name == "test_stream"), None)
        normal_schema = next((s for s in schemas if s.name == "test_normal"), None)

        assert stream_schema is not None
        assert stream_schema.streaming is True

        assert normal_schema is not None
        assert normal_schema.streaming is False

    @patch('autocode.interfaces.api.load_functions')
    def test_streaming_and_normal_coexist(self, mock_load):
        """Streaming and non-streaming functions coexist on the same app."""
        app = create_api_app()
        client = TestClient(app)

        # Both should respond
        stream_resp = client.post("/test_stream", json={"message": "hi"})
        normal_resp = client.get("/test_normal?x=3")

        assert stream_resp.status_code == 200
        assert normal_resp.status_code == 200

        # Stream should be SSE
        assert "text/event-stream" in stream_resp.headers.get("content-type", "")

        # Normal should be JSON
        assert "application/json" in normal_resp.headers.get("content-type", "")


class TestStreamingWithRealRegistry:
    """Tests that use the real registry load to verify chat_stream registration.
    
    These tests need the real module imports to fire @register_function decorators.
    We override the autouse cleanup_registry fixture because once Python caches
    imported modules, re-calling load_functions() won't re-fire decorators.
    Instead, we reload the pipelines module to force re-registration.
    """

    @pytest.fixture(autouse=True)
    def cleanup_registry(self):
        """Override global autouse fixture: clear + force reload of pipelines."""
        clear_registry()
        yield
        clear_registry()

    def _force_load(self):
        """Force reload of pipelines module to re-fire @register_function decorators."""
        import importlib
        import autocode.core.ai.pipelines
        clear_registry()
        importlib.reload(autocode.core.ai.pipelines)

    def test_chat_stream_is_registered(self):
        """chat_stream is registered after load_functions()."""
        self._force_load()
        func_info = get_function_by_name("chat_stream")
        assert func_info is not None
        assert func_info.streaming is True
        assert func_info.name == "chat_stream"

    def test_chat_stream_has_stream_func(self):
        """chat_stream has a corresponding stream_func in the stream registry."""
        self._force_load()
        stream_func = get_stream_func("chat_stream")
        assert stream_func is not None
        assert callable(stream_func)

    def test_chat_stream_stream_func_is_stream_chat(self):
        """chat_stream's stream_func is the stream_chat function."""
        from autocode.core.ai.streaming import stream_chat
        self._force_load()
        stream_func = get_stream_func("chat_stream")
        assert stream_func is stream_chat

    def test_chat_has_no_stream_func(self):
        """Regular chat() function has no stream_func."""
        self._force_load()
        stream_func = get_stream_func("chat")
        assert stream_func is None

    def test_chat_is_not_streaming(self):
        """Regular chat() function has streaming=False."""
        self._force_load()
        func_info = get_function_by_name("chat")
        assert func_info is not None
        assert func_info.streaming is False

    def test_chat_stream_schema_in_functions_details(self):
        """chat_stream appears in schemas with streaming=True."""
        self._force_load()
        schemas = get_all_schemas()
        stream_schema = next((s for s in schemas if s.name == "chat_stream"), None)
        assert stream_schema is not None
        assert stream_schema.streaming is True

    def test_chat_stream_only_exposes_api_interface(self):
        """chat_stream is only exposed on the API interface (not CLI/MCP)."""
        self._force_load()
        func_info = get_function_by_name("chat_stream")
        assert func_info is not None
        assert "api" in func_info.interfaces
        assert "cli" not in func_info.interfaces
        assert "mcp" not in func_info.interfaces
