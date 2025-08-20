"""
MCP (Model Context Protocol) integration using fastapi_mcp.
"""
from fastapi import FastAPI
from fastapi_mcp import FastApiMCP
from autocode.autocode.interfaces.registry import FUNCTION_REGISTRY
from autocode.autocode.interfaces.api import create_api_app


def create_mcp_app() -> FastAPI:
    """Create a FastAPI app with both API endpoints and MCP server integration."""
    # Get the configured API app instead of creating a blank one
    app = create_api_app()
    
    # Update app metadata to reflect MCP integration
    app.title = "Autocode API + MCP Server"
    app.description = "Minimalistic framework for code quality tools with MCP integration"
    
    # Initialize MCP server on the existing API app
    mcp = FastApiMCP(
        app,
        name="Autocode MCP Server",
        description="MCP server for autocode functions and API endpoints"
    )
    
    # Mount MCP server
    mcp.mount()
    
    return app
