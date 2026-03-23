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
from autocode.core.registry import get_functions_for_interface
from autocode.core.models import GenericOutput

# Setup logging
logger = logging.getLogger(__name__)


# --- REFRACT INSTANCE API ---

def _register_mcp_endpoints_for_refract(app: FastAPI, refract) -> None:
    """Register MCP endpoints from a Refract instance's registry.

    Instance-level counterpart of ``_register_mcp_endpoints``.  Reads
    functions from *refract* instead of the global registry.

    Args:
        app: FastAPI application to register endpoints on.
        refract: A ``Refract`` instance whose ``"mcp"``-interface functions
            are exposed as MCP tool endpoints.
    """
    mcp_functions = refract.get_functions_for_interface("mcp")

    for func_info in mcp_functions:
        for method in func_info.http_methods:
            handler, input_model = create_handler(func_info, method)
            response_model = func_info.return_type or GenericOutput

            app.add_api_route(
                f"/{func_info.name}",
                handler,
                methods=[method.upper()],
                response_model=response_model,
                operation_id=f"mcp_{func_info.name}_{method.lower()}",
                summary=func_info.description,
                tags=["mcp-tools"]
            )

    logger.info(f"[Refract:{refract._name}] Registered {len(mcp_functions)} MCP endpoints")


def create_mcp_app_for_refract(refract) -> FastAPI:
    """Create a FastAPI application with API + MCP integration for a Refract instance.

    Instance-level counterpart of ``create_mcp_app()``.  Uses *refract*'s
    registry for both the base API app and the MCP-specific endpoints.

    Steps:
        1. Build the base FastAPI app via ``refract.api()``.
        2. Update app metadata to reflect MCP integration.
        3. Register MCP-specific endpoints from the instance registry.
        4. Initialise and mount the FastApiMCP server.

    Args:
        refract: A ``Refract`` instance whose registry drives both the API
            and the MCP tool endpoints.

    Returns:
        A configured ``FastAPI`` application with MCP support.

    Raises:
        RuntimeError: If MCP server initialisation fails.
    """
    try:
        # Step 1: Create base API application from the instance registry
        app = refract.api()

        # Step 2: Update app metadata to reflect MCP integration
        app.title = f"{refract._name} API + MCP Server"
        app.description = f"API and MCP server for {refract._name}"

        # Step 3: Register MCP-specific endpoints (only functions with "mcp" interface)
        _register_mcp_endpoints_for_refract(app, refract)

        # Step 4: Initialise MCP server — include only mcp-tools tagged endpoints
        mcp = FastApiMCP(
            app,
            name=f"{refract._name} MCP Server",
            description=f"MCP server for {refract._name} functions and API endpoints",
            include_tags=["mcp-tools"]
        )

        # Step 5: Mount MCP server with Streamable HTTP transport (modern)
        mcp.mount_http()

        logger.info(f"[Refract:{refract._name}] Successfully created MCP app with API integration")
        return app

    except Exception as e:
        logger.error(f"[Refract:{refract._name}] Failed to create MCP app: {str(e)}")
        raise RuntimeError(f"MCP server initialization failed: {str(e)}") from e


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
    
    for func_info in mcp_functions:
        for method in func_info.http_methods:
            handler, input_model = create_handler(func_info, method)
            response_model = func_info.return_type or GenericOutput
            
            app.add_api_route(
                f"/{func_info.name}",
                handler,
                methods=[method.upper()],
                response_model=response_model,
                operation_id=f"mcp_{func_info.name}_{method.lower()}",
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
        
        # Step 5: Mount MCP server with Streamable HTTP transport (modern)
        mcp.mount_http()
        
        logger.info("Successfully created MCP app with API integration")
        return app
        
    except Exception as e:
        logger.error(f"Failed to create MCP app: {str(e)}")
        raise RuntimeError(f"MCP server initialization failed: {str(e)}") from e
