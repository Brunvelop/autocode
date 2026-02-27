"""
Tests for autocode.interfaces.mcp module.

Tests the MCP (Model Context Protocol) integration including FastAPI app creation
with MCP server capabilities and error handling.
"""
import pytest
from unittest.mock import Mock, patch
from fastapi import FastAPI

from autocode.interfaces.mcp import create_mcp_app


@pytest.fixture
def mock_api_app():
    """Create a mock FastAPI app with common properties."""
    mock_app = Mock(spec=FastAPI)
    mock_app.title = "Autocode API"
    mock_app.description = "Original description"
    mock_app.version = "1.0.0"
    mock_app.routes = []
    mock_app.middleware = []
    return mock_app


@pytest.fixture
def mock_mcp_instance():
    """Create a mock MCP instance with common methods."""
    mock_instance = Mock()
    mock_instance.mount_http = Mock()
    return mock_instance


@pytest.fixture
def patched_dependencies():
    """Patch common MCP dependencies and return the patchers."""
    with patch('autocode.interfaces.mcp.create_api_app') as mock_create_api_app, \
         patch('autocode.interfaces.mcp.FastApiMCP') as mock_fastapi_mcp, \
         patch('autocode.interfaces.mcp._register_mcp_endpoints') as mock_register_mcp, \
         patch('autocode.interfaces.mcp.logger') as mock_logger:
        yield {
            'create_api_app': mock_create_api_app,
            'fastapi_mcp': mock_fastapi_mcp,
            'register_mcp_endpoints': mock_register_mcp,
            'logger': mock_logger
        }


class TestCreateMcpApp:
    """Tests for create_mcp_app - MCP-enabled FastAPI app creation."""
    
    @patch('autocode.interfaces.mcp._register_mcp_endpoints')
    @patch('autocode.interfaces.mcp.FastApiMCP')
    @patch('autocode.interfaces.mcp.create_api_app')
    def test_create_mcp_app_success(self, mock_create_api_app, mock_fastapi_mcp, mock_register_mcp):
        """Test successful MCP app creation."""
        # Mock the API app with additional properties
        mock_api_app = Mock(spec=FastAPI)
        mock_api_app.title = "Autocode API"
        mock_api_app.description = "Original description"
        mock_api_app.version = "1.0.0"
        mock_api_app.routes = ["existing_route"]
        mock_create_api_app.return_value = mock_api_app
        
        # Mock the MCP server
        mock_mcp_instance = Mock()
        mock_mcp_instance.mount_http = Mock()
        mock_fastapi_mcp.return_value = mock_mcp_instance
        
        # Call create_mcp_app
        result_app = create_mcp_app()
        
        # Verify API app was created with no arguments
        mock_create_api_app.assert_called_once_with()
        
        # Verify MCP endpoints were registered
        mock_register_mcp.assert_called_once_with(mock_api_app)
        
        # Verify app metadata was updated correctly
        assert mock_api_app.title == "Autocode API + MCP Server"
        assert mock_api_app.description == "Minimalistic framework for code quality tools with MCP integration"
        
        # Verify other properties were preserved
        assert mock_api_app.version == "1.0.0"  # Should not change
        assert mock_api_app.routes == ["existing_route"]  # Should not change
        
        # Verify MCP was initialized with exact parameters (including include_tags)
        mock_fastapi_mcp.assert_called_once_with(
            mock_api_app,
            name="Autocode MCP Server",
            description="MCP server for autocode functions and API endpoints",
            include_tags=["mcp-tools"]
        )
        
        # Verify MCP was mounted with Streamable HTTP transport
        mock_mcp_instance.mount_http.assert_called_once_with()
        
        # Verify the exact same app instance is returned
        assert result_app is mock_api_app
    
    @patch('autocode.interfaces.mcp._register_mcp_endpoints')
    @patch('autocode.interfaces.mcp.FastApiMCP')
    @patch('autocode.interfaces.mcp.create_api_app')
    def test_create_mcp_app_preserves_api_functionality(self, mock_create_api_app, mock_fastapi_mcp, mock_register):
        """Test that MCP app preserves original API functionality."""
        # Create a more realistic mock API app
        mock_api_app = Mock(spec=FastAPI)
        mock_api_app.title = "Autocode API"
        mock_api_app.description = "Original description"
        mock_api_app.routes = ["route1", "route2"]  # Simulate existing routes
        mock_create_api_app.return_value = mock_api_app
        
        # Mock MCP
        mock_mcp_instance = Mock()
        mock_fastapi_mcp.return_value = mock_mcp_instance
        
        result_app = create_mcp_app()
        
        # Verify original app structure is preserved
        assert result_app.routes == ["route1", "route2"]
        assert result_app == mock_api_app
        
        # Verify only title and description were modified
        assert result_app.title == "Autocode API + MCP Server"
        assert result_app.description == "Minimalistic framework for code quality tools with MCP integration"
    
    @patch('autocode.interfaces.mcp._register_mcp_endpoints')
    @patch('autocode.interfaces.mcp.FastApiMCP')
    @patch('autocode.interfaces.mcp.create_api_app')
    @patch('autocode.interfaces.mcp.logger')
    def test_create_mcp_app_logs_success(self, mock_logger, mock_create_api_app, mock_fastapi_mcp, mock_register):
        """Test that successful MCP app creation is logged."""
        # Setup mocks
        mock_api_app = Mock(spec=FastAPI)
        mock_create_api_app.return_value = mock_api_app
        mock_mcp_instance = Mock()
        mock_fastapi_mcp.return_value = mock_mcp_instance
        
        create_mcp_app()
        
        # Verify success was logged
        mock_logger.info.assert_called_with("Successfully created MCP app with API integration")
    
    @patch('autocode.interfaces.mcp.create_api_app')
    def test_create_mcp_app_api_creation_error(self, mock_create_api_app):
        """Test MCP app creation when API app creation fails."""
        mock_create_api_app.side_effect = Exception("API creation failed")
        
        with pytest.raises(RuntimeError, match="MCP server initialization failed: API creation failed"):
            create_mcp_app()
    
    @patch('autocode.interfaces.mcp._register_mcp_endpoints')
    @patch('autocode.interfaces.mcp.FastApiMCP')
    @patch('autocode.interfaces.mcp.create_api_app')
    def test_create_mcp_app_mcp_initialization_error(self, mock_create_api_app, mock_fastapi_mcp, mock_register):
        """Test MCP app creation when MCP initialization fails."""
        # API app creation succeeds
        mock_api_app = Mock(spec=FastAPI)
        mock_create_api_app.return_value = mock_api_app
        
        # MCP initialization fails
        mock_fastapi_mcp.side_effect = Exception("MCP initialization failed")
        
        with pytest.raises(RuntimeError, match="MCP server initialization failed: MCP initialization failed"):
            create_mcp_app()
    
    @patch('autocode.interfaces.mcp._register_mcp_endpoints')
    @patch('autocode.interfaces.mcp.FastApiMCP')
    @patch('autocode.interfaces.mcp.create_api_app')
    def test_create_mcp_app_mount_error(self, mock_create_api_app, mock_fastapi_mcp, mock_register):
        """Test MCP app creation when MCP mount fails."""
        # API app and MCP instance creation succeed
        mock_api_app = Mock(spec=FastAPI)
        mock_create_api_app.return_value = mock_api_app
        
        mock_mcp_instance = Mock()
        mock_mcp_instance.mount_http.side_effect = Exception("Mount failed")
        mock_fastapi_mcp.return_value = mock_mcp_instance
        
        with pytest.raises(RuntimeError, match="MCP server initialization failed: Mount failed"):
            create_mcp_app()
    
    @patch('autocode.interfaces.mcp._register_mcp_endpoints')
    @patch('autocode.interfaces.mcp.FastApiMCP')
    @patch('autocode.interfaces.mcp.create_api_app')
    @patch('autocode.interfaces.mcp.logger')
    def test_create_mcp_app_error_logging(self, mock_logger, mock_create_api_app, mock_fastapi_mcp, mock_register):
        """Test that errors are properly logged."""
        # Setup to cause an error in MCP initialization
        mock_api_app = Mock(spec=FastAPI)
        mock_create_api_app.return_value = mock_api_app
        mock_fastapi_mcp.side_effect = Exception("Test error")
        
        with pytest.raises(RuntimeError):
            create_mcp_app()
        
        # Verify error was logged
        mock_logger.error.assert_called_with("Failed to create MCP app: Test error")
    


class TestMcpIntegration:
    """Integration tests for MCP functionality."""
    
    @patch('autocode.interfaces.mcp._register_mcp_endpoints')
    @patch('autocode.interfaces.mcp.FastApiMCP')
    @patch('autocode.interfaces.mcp.create_api_app')
    def test_mcp_app_integration_with_real_api_structure(self, mock_create_api_app, mock_fastapi_mcp, mock_register):
        """Test MCP app creation with realistic API app structure."""
        # Create a more realistic mock that mimics actual FastAPI app
        mock_api_app = Mock(spec=FastAPI)
        mock_api_app.title = "Autocode API"
        mock_api_app.description = "Minimalistic framework for code quality tools"
        mock_api_app.version = "1.0.0"
        mock_api_app.routes = []
        mock_api_app.middleware = []
        
        mock_create_api_app.return_value = mock_api_app
        
        # Mock MCP with realistic behavior
        mock_mcp_instance = Mock()
        mock_mcp_instance.mount_http = Mock(return_value=None)
        mock_fastapi_mcp.return_value = mock_mcp_instance
        
        result_app = create_mcp_app()
        
        # Verify the integration preserves important app properties
        assert result_app.version == "1.0.0"  # Should preserve version
        assert hasattr(result_app, 'routes')  # Should preserve routes
        assert hasattr(result_app, 'middleware')  # Should preserve middleware
        
        # Verify MCP-specific changes
        assert result_app.title == "Autocode API + MCP Server"
        assert "MCP integration" in result_app.description
    
    @patch('autocode.interfaces.mcp._register_mcp_endpoints')
    @patch('autocode.interfaces.mcp.FastApiMCP')
    @patch('autocode.interfaces.mcp.create_api_app')
    def test_mcp_server_configuration(self, mock_create_api_app, mock_fastapi_mcp, mock_register_mcp):
        """Test that MCP server is configured with correct parameters."""
        mock_api_app = Mock(spec=FastAPI)
        mock_create_api_app.return_value = mock_api_app
        
        mock_mcp_instance = Mock()
        mock_fastapi_mcp.return_value = mock_mcp_instance
        
        create_mcp_app()
        
        # Verify MCP endpoints were registered
        mock_register_mcp.assert_called_once_with(mock_api_app)
        
        # Verify MCP was configured with correct parameters (including include_tags)
        mock_fastapi_mcp.assert_called_once_with(
            mock_api_app,
            name="Autocode MCP Server",
            description="MCP server for autocode functions and API endpoints",
            include_tags=["mcp-tools"]
        )
        
        # Verify mount_http was called
        mock_mcp_instance.mount_http.assert_called_once()
    
    def test_mcp_app_return_type(self, patched_dependencies, mock_api_app, mock_mcp_instance):
        """Test that create_mcp_app returns a FastAPI instance."""
        # Setup using fixtures
        patched_dependencies['create_api_app'].return_value = mock_api_app
        patched_dependencies['fastapi_mcp'].return_value = mock_mcp_instance
        
        result = create_mcp_app()
        
        # Should return the same FastAPI instance
        assert result is mock_api_app


class TestMcpErrorHandling:
    """Tests for MCP error handling scenarios."""
    
    @patch('autocode.interfaces.mcp.create_api_app')
    def test_chained_exception_preservation(self, mock_create_api_app):
        """Test that original exceptions are preserved in the chain."""
        original_error = ValueError("Original error")
        mock_create_api_app.side_effect = original_error
        
        with pytest.raises(RuntimeError) as exc_info:
            create_mcp_app()
        
        # Verify the original exception is preserved
        assert exc_info.value.__cause__ is original_error
        assert "MCP server initialization failed: Original error" in str(exc_info.value)
    
    @patch('autocode.interfaces.mcp._register_mcp_endpoints')
    @patch('autocode.interfaces.mcp.FastApiMCP')
    @patch('autocode.interfaces.mcp.create_api_app')
    def test_multiple_error_scenarios(self, mock_create_api_app, mock_fastapi_mcp, mock_register):
        """Test various error scenarios that could occur during MCP app creation."""
        
        # Test 1: API app creation error
        mock_create_api_app.side_effect = ImportError("Cannot import FastAPI")
        
        with pytest.raises(RuntimeError, match="Cannot import FastAPI"):
            create_mcp_app()
        
        # Reset for next test
        mock_create_api_app.side_effect = None
        mock_api_app = Mock(spec=FastAPI)
        mock_create_api_app.return_value = mock_api_app
        
        # Test 2: FastApiMCP import/initialization error
        mock_fastapi_mcp.side_effect = ImportError("Cannot import fastapi_mcp")
        
        with pytest.raises(RuntimeError, match="Cannot import fastapi_mcp"):
            create_mcp_app()
        
        # Reset for next test
        mock_fastapi_mcp.side_effect = None
        mock_mcp_instance = Mock()
        mock_fastapi_mcp.return_value = mock_mcp_instance
        
        # Test 3: Mount operation error
        mock_mcp_instance.mount_http.side_effect = RuntimeError("Cannot mount MCP server")
        
        with pytest.raises(RuntimeError, match="Cannot mount MCP server"):
            create_mcp_app()
    
    @pytest.mark.parametrize("error,expected_message", [
        (ValueError("Value error"), "Value error"),
        (ImportError("Import error"), "Import error"),
        (RuntimeError("Runtime error"), "Runtime error"),
        (Exception("Generic exception"), "Generic exception"),
        (TypeError("Type error"), "Type error"),
        (AttributeError("Attribute error"), "Attribute error"),
    ])
    @patch('autocode.interfaces.mcp._register_mcp_endpoints')
    @patch('autocode.interfaces.mcp.FastApiMCP')
    @patch('autocode.interfaces.mcp.create_api_app')
    @patch('autocode.interfaces.mcp.logger')
    def test_error_logging_with_different_error_types(self, mock_logger, mock_create_api_app, mock_fastapi_mcp, mock_register, error, expected_message):
        """Test that different types of errors are logged appropriately."""
        mock_api_app = Mock(spec=FastAPI)
        mock_create_api_app.return_value = mock_api_app
        mock_fastapi_mcp.side_effect = error
        
        with pytest.raises(RuntimeError):
            create_mcp_app()
        
        # Verify appropriate error logging
        mock_logger.error.assert_called_with(f"Failed to create MCP app: {expected_message}")


class TestMcpModuleConstants:
    """Tests for module-level constants and imports."""
    
    def test_module_imports(self):
        """Test that all required modules are imported correctly."""
        import autocode.interfaces.mcp as mcp_module
        
        # Verify key imports exist
        assert hasattr(mcp_module, 'create_mcp_app')
        assert hasattr(mcp_module, 'FastAPI')
        assert hasattr(mcp_module, 'FastApiMCP')
        assert hasattr(mcp_module, 'create_api_app')
        assert hasattr(mcp_module, 'logging')
        assert hasattr(mcp_module, 'logger')
    
    def test_logger_configuration(self):
        """Test that logger is configured correctly."""
        from autocode.interfaces.mcp import logger
        
        assert logger.name == 'autocode.interfaces.mcp'
    
    def test_module_docstring(self):
        """Test that module has appropriate documentation."""
        import autocode.interfaces.mcp as mcp_module
        
        assert mcp_module.__doc__ is not None
        assert "MCP" in mcp_module.__doc__
        assert "Model Context Protocol" in mcp_module.__doc__


class TestMcpAppBehavior:
    """Tests for expected MCP app behavior and characteristics."""
    
    @patch('autocode.interfaces.mcp._register_mcp_endpoints')
    @patch('autocode.interfaces.mcp.FastApiMCP')
    @patch('autocode.interfaces.mcp.create_api_app')
    def test_app_modification_sequence(self, mock_create_api_app, mock_fastapi_mcp, mock_register):
        """Test the sequence of modifications made to the app."""
        # Create a mock that tracks changes
        mock_api_app = Mock(spec=FastAPI)
        mock_api_app.title = "Original Title"
        mock_api_app.description = "Original Description"
        mock_create_api_app.return_value = mock_api_app
        
        mock_mcp_instance = Mock()
        mock_fastapi_mcp.return_value = mock_mcp_instance
        
        # Track the sequence of operations
        modifications = []
        
        def track_title_change(value):
            modifications.append(("title", value))
            
        def track_description_change(value):
            modifications.append(("description", value))
        
        # Use property to track changes
        type(mock_api_app).title = property(lambda self: self._title, 
                                          lambda self, val: track_title_change(val) or setattr(self, '_title', val))
        type(mock_api_app).description = property(lambda self: self._description, 
                                                lambda self, val: track_description_change(val) or setattr(self, '_description', val))
        
        mock_api_app._title = "Original Title"
        mock_api_app._description = "Original Description"
        
        result = create_mcp_app()
        
        # Verify modifications were made
        assert ("title", "Autocode API + MCP Server") in modifications
        assert ("description", "Minimalistic framework for code quality tools with MCP integration") in modifications
        
        # Verify final state
        assert result._title == "Autocode API + MCP Server"
        assert result._description == "Minimalistic framework for code quality tools with MCP integration"
