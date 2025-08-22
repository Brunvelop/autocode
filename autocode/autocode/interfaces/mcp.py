"""
MCP (Model Context Protocol) integration using fastapi_mcp.

This module provides integration between the Autocode API and the Model Context Protocol,
allowing the API endpoints to be exposed as MCP tools for use with AI assistants and
other MCP-compatible clients.
"""
import logging
from fastapi import FastAPI
from fastapi_mcp import FastApiMCP
from autocode.autocode.interfaces.api import create_api_app

# Setup logging
logger = logging.getLogger(__name__)


def create_mcp_app() -> FastAPI:
    """
    Create a FastAPI app with both API endpoints and MCP server integration.
    
    This function creates a unified FastAPI application that serves both:
    - Standard REST API endpoints (from create_api_app)
    - MCP (Model Context Protocol) server capabilities
    
    Returns:
        FastAPI: Configured application with API endpoints and MCP integration
        
    Raises:
        RuntimeError: If MCP server initialization fails
        
    Example:
        >>> app = create_mcp_app()
        >>> # App now serves both REST API and MCP endpoints
    """
    try:
        # Step 1: Create base API application with all endpoints
        app = create_api_app()
        
        # Step 2: Update app metadata to reflect MCP integration
        app.title = "Autocode API + MCP Server"
        app.description = "Minimalistic framework for code quality tools with MCP integration"
        
        # Step 3: Initialize MCP server on the existing API app
        mcp = FastApiMCP(
            app,
            name="Autocode MCP Server",
            description="MCP server for autocode functions and API endpoints"
        )
        
        # Step 4: Mount MCP server to enable MCP functionality
        mcp.mount()
        
        logger.info("Successfully created MCP app with API integration")
        return app
        
    except Exception as e:
        logger.error(f"Failed to create MCP app: {str(e)}")
        raise RuntimeError(f"MCP server initialization failed: {str(e)}") from e
