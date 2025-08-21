"""
FastAPI server with dynamic endpoints from registry and static file serving.
"""
import os
import logging
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from autocode.autocode.interfaces.registry import FUNCTION_REGISTRY
from autocode.autocode.interfaces.models import ExplicitInput, GenericOutput

# Setup logging
logger = logging.getLogger(__name__)


def create_result_response(result):
    """
    Format function results into consistent API response format.
    
    Returns dict as-is, wraps other types in GenericOutput model.
    """
    if isinstance(result, dict):
        return result
    return GenericOutput(result=result)


def extract_function_params(func_info, request_params):
    """
    Extract and prepare function parameters from request data.
    
    Handles both explicit parameters and default values.
    """
    func_params = {}
    for param in func_info.params:
        if param.name in request_params:
            func_params[param.name] = request_params[param.name]
        elif not param.required and param.default is not None:
            func_params[param.name] = param.default
    return func_params


def execute_function_with_params(func_info, request_params, method, extra_debug_info=""):
    """
    Execute registered function with extracted parameters and handle common logic.
    
    Handles parameter extraction, logging, function execution, and error management.
    """
    try:
        func_params = extract_function_params(func_info, request_params)
        debug_msg = f"{method} {func_info.name}: params={func_params}"
        if extra_debug_info:
            debug_msg += f", {extra_debug_info}"
        logger.debug(debug_msg)
        result = func_info.func(**func_params)
        return create_result_response(result)
    except Exception as e:
        logger.error(f"{method} {func_info.name} error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


def create_post_handler(func_info):
    """Create POST endpoint handler for registered function."""
    async def handler(request: ExplicitInput):
        return execute_function_with_params(func_info, request.params, "POST")
    return handler


def create_get_handler(func_info):
    """Create GET endpoint handler with dynamic query parameters."""
    from fastapi import Request
    
    async def handler(request: Request):
        query_params = dict(request.query_params)
        return execute_function_with_params(
            func_info, query_params, "GET", f"query={query_params}"
        )
    
    return handler


def register_dynamic_endpoints(app: FastAPI):
    """
    Register all functions from registry as API endpoints.
    
    Creates both GET and POST handlers based on function metadata.
    """
    for func_name, func_info in FUNCTION_REGISTRY.items():
        for method in func_info.http_methods:
            if method.upper() == "POST":
                app.add_api_route(
                    f"/{func_name}",
                    create_post_handler(func_info),
                    methods=["POST"],
                    response_model=GenericOutput,
                    operation_id=f"{func_name}_post",
                    summary=func_info.description
                )
            elif method.upper() == "GET":
                app.add_api_route(
                    f"/{func_name}",
                    create_get_handler(func_info),
                    methods=["GET"],
                    response_model=GenericOutput,
                    operation_id=f"{func_name}_get",
                    summary=func_info.description
                )


def create_api_app() -> FastAPI:
    """
    Create and configure FastAPI application.
    
    Sets up dynamic endpoints from registry, static file serving,
    and standard API endpoints (health, functions list, root).
    """
    app = FastAPI(
        title="Autocode API",
        description="Minimalistic framework for code quality tools",
        version="1.0.0"
    )

    # Register dynamic endpoints from function registry
    register_dynamic_endpoints(app)

    # Standard API endpoints
    @app.get("/")
    async def root():
        """Root endpoint - serve the web UI."""
        current_dir = os.path.dirname(__file__)
        index_path = os.path.join(current_dir, "..", "web", "index.html")
        return FileResponse(index_path)

    @app.get("/functions")
    async def list_functions():
        """List all available registered functions."""
        return {"functions": list(FUNCTION_REGISTRY.keys())}

    @app.get("/health")
    async def health_check():
        """Health check endpoint with function count."""
        return {"status": "healthy", "functions": len(FUNCTION_REGISTRY)}

    # Mount static files for web UI
    current_dir = os.path.dirname(__file__)
    web_dir = os.path.join(current_dir, "..", "web")
    if os.path.exists(web_dir):
        app.mount("/static", StaticFiles(directory=web_dir), name="static")

    return app
