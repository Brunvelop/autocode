"""
MCP (Model Context Protocol) integration using fastapi_mcp.

This module provides integration between the Autocode API and the Model Context Protocol,
allowing the API endpoints to be exposed as MCP tools for use with AI assistants and
other MCP-compatible clients.
"""
import logging
from fastapi import FastAPI
from fastapi_mcp import FastApiMCP
from autocode.interfaces.api import create_api_app, create_handler
from autocode.interfaces.registry import get_functions_for_interface
from autocode.interfaces.models import GenericOutput

# Setup logging
logger = logging.getLogger(__name__)


def _register_mcp_endpoints(app: FastAPI) -> None:
    """
    Register endpoints specifically for MCP tools.
    
    Uses get_functions_for_interface to get only functions that should be
    exposed via MCP, then creates endpoints for them.
    
    Args:
        app: FastAPI application to register endpoints on
    """
    # Get functions that should be exposed in MCP
    mcp_functions = get_functions_for_interface("mcp")
    
    for func_name, func_info in mcp_functions.items():
        for method in func_info.http_methods:
            handler, input_model = create_handler(func_info, method)
            response_model = func_info.return_type or GenericOutput
            
            app.add_api_route(
                f"/{func_name}",
                handler,
                methods=[method.upper()],
                response_model=response_model,
                operation_id=f"mcp_{func_name}_{method.lower()}",
                summary=func_info.description,
                tags=["mcp-tools"]  # Tag for MCP-specific endpoints
            )
    
    logger.info(f"Registered {len(mcp_functions)} MCP endpoints")


def create_mcp_app() -> FastAPI:
    """
    Create a FastAPI app with both API endpoints and MCP server integration.
    
    This function creates a unified FastAPI application that serves both:
    - Standard REST API endpoints (from create_api_app)
    - MCP (Model Context Protocol) server capabilities
    
    The MCP server exposes only functions with "mcp" in their interfaces list,
    using the centralized get_functions_for_interface() filtering.
    
    Returns:
        FastAPI: Configured application with API endpoints and MCP integration
        
    Raises:
        RuntimeError: If MCP server initialization fails
        
    Example:
        >>> app = create_mcp_app()
        >>> # App now serves both REST API and MCP endpoints
    """
    try:
        # Step 1: Create base API application with all API endpoints
        app = create_api_app()
        
        # Step 2: Update app metadata to reflect MCP integration
        app.title = "Autocode API + MCP Server"
        app.description = "Minimalistic framework for code quality tools with MCP integration"
        
        # Step 3: Register MCP-specific endpoints (only functions with "mcp" interface)
        _register_mcp_endpoints(app)
        
        # Step 4: Initialize MCP server - include only mcp-tools tagged endpoints
        mcp = FastApiMCP(
            app,
            name="Autocode MCP Server",
            description="MCP server for autocode functions and API endpoints",
            include_tags=["mcp-tools"]  # Only include MCP-specific endpoints
        )
        
        # Step 5: Mount MCP server to enable MCP functionality
        mcp.mount()
        
        logger.info("Successfully created MCP app with API integration")
        return app
        
    except Exception as e:
        logger.error(f"Failed to create MCP app: {str(e)}")
        raise RuntimeError(f"MCP server initialization failed: {str(e)}") from e
