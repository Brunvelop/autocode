"""
Integration tests for autocode's chat_stream registration with refract.

Verifies that autocode's specific streaming functions (chat_stream) are
correctly registered with the Refract instance: streaming flag, stream_func
assignment, interface exposure, and schema representation.

These are autocode-domain tests — they test that autocode's configuration
of refract is correct, not the refract framework itself.
"""
import pytest

from refract.registry import _clear_pending
from autocode.app import app


class TestChatStreamRegistration:
    """Tests that use real module imports to verify chat_stream registration.

    These tests need the real module imports to fire @register_function decorators.
    We override the autouse cleanup_registry fixture because once Python caches
    imported modules, re-calling load_functions() won't re-fire decorators.
    Instead, we reload the pipelines module to force re-registration.
    """

    @pytest.fixture(autouse=True)
    def cleanup_registry(self):
        """Override global autouse fixture: clear + force reload of pipelines."""
        app.clear()
        _clear_pending()
        yield
        app.clear()
        _clear_pending()

    def _force_load(self):
        """Force reload of pipelines module to re-fire @register_function decorators."""
        import importlib
        import autocode.core.ai.pipelines
        app.clear()
        _clear_pending()
        importlib.reload(autocode.core.ai.pipelines)
        app._drain_pending()

    def test_chat_stream_is_registered(self):
        """chat_stream is registered after forcing reload of pipelines."""
        self._force_load()
        func_info = app.get_function_by_name("chat_stream")
        assert func_info is not None
        assert func_info.streaming is True
        assert func_info.name == "chat_stream"

    def test_chat_stream_has_stream_func(self):
        """chat_stream has a corresponding stream_func in the stream registry."""
        self._force_load()
        stream_func = app.get_stream_func("chat_stream")
        assert stream_func is not None
        assert callable(stream_func)

    def test_chat_stream_stream_func_is_stream_chat(self):
        """chat_stream's stream_func is the stream_chat function."""
        from autocode.core.ai.streaming import stream_chat
        self._force_load()
        stream_func = app.get_stream_func("chat_stream")
        assert stream_func is stream_chat

    def test_chat_has_no_stream_func(self):
        """Regular chat() function has no stream_func."""
        self._force_load()
        stream_func = app.get_stream_func("chat")
        assert stream_func is None

    def test_chat_is_not_streaming(self):
        """Regular chat() function has streaming=False."""
        self._force_load()
        func_info = app.get_function_by_name("chat")
        assert func_info is not None
        assert func_info.streaming is False

    def test_chat_stream_schema_in_functions_details(self):
        """chat_stream appears in schemas with streaming=True."""
        self._force_load()
        schemas = app.get_all_schemas()
        stream_schema = next((s for s in schemas if s.name == "chat_stream"), None)
        assert stream_schema is not None
        assert stream_schema.streaming is True

    def test_chat_stream_only_exposes_api_interface(self):
        """chat_stream is only exposed on the API interface (not CLI/MCP)."""
        self._force_load()
        func_info = app.get_function_by_name("chat_stream")
        assert func_info is not None
        assert "api" in func_info.interfaces
        assert "cli" not in func_info.interfaces
        assert "mcp" not in func_info.interfaces
