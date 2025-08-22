"""
FastAPI server with dynamic endpoints from registry and static file serving.
"""
import os
import logging
from typing import Type, Dict, Any
from pydantic import BaseModel, create_model, Field
from fastapi import FastAPI, HTTPException, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from autocode.autocode.interfaces.registry import FUNCTION_REGISTRY, load_core_functions
from autocode.autocode.interfaces.models import GenericOutput, FunctionInfo

# Setup logging
logger = logging.getLogger(__name__)


def create_result_response(result: Any) -> Dict[str, Any]:
    """
    Format function results into consistent API response format.
    
    Args:
        result: Function result to format (any type)
        
    Returns:
        Dict containing formatted response - returns dict as-is, 
        wraps other types in GenericOutput model
        
    Example:
        >>> create_result_response({"key": "value"})
        {"key": "value"}
        >>> create_result_response("hello")
        {"result": "hello"}
    """
    if isinstance(result, dict):
        return result
    return GenericOutput(result=result).dict()


def create_dynamic_model(func_info: FunctionInfo, for_post: bool = True) -> Type[BaseModel]:
    """
    Create a dynamic Pydantic model based on function parameters.
    
    Args:
        func_info: Function information with parameters
        for_post: If True, creates model for POST body; if False, for GET query params
        
    Returns:
        Dynamically created Pydantic model class
    """
    fields = {}
    
    for param in func_info.params:
        # Convert type annotation
        field_type = param.type
        
        # Handle default values and required fields
        if param.required:
            # Required field without default
            fields[param.name] = (field_type, Field(description=param.description))
        else:
            # Optional field with default
            default_value = param.default if param.default is not None else None
            fields[param.name] = (field_type, Field(default=default_value, description=param.description))
    
    # Create model name
    suffix = "Input" if for_post else "QueryParams"
    model_name = f"{func_info.name.title()}{suffix}"
    
    # Create the dynamic model
    return create_model(model_name, **fields)


def extract_function_params(func_info: FunctionInfo, request_params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract and prepare function parameters from request data.
    
    Args:
        func_info: Function information containing parameter definitions
        request_params: Dictionary with request parameters from API call
        
    Returns:
        Dict with extracted parameters ready for function execution
        
    Handles both explicit parameters and default values.
    For required parameters missing from request, they are omitted 
    (validation should happen at Pydantic model level).
    
    Example:
        >>> func_info = FunctionInfo(params=[Param(name="x", required=True), 
        ...                                 Param(name="y", required=False, default=1)])
        >>> extract_function_params(func_info, {"x": 5})
        {"x": 5, "y": 1}
    """
    func_params = {}
    for param in func_info.params:
        if param.name in request_params:
            func_params[param.name] = request_params[param.name]
        elif not param.required and param.default is not None:
            func_params[param.name] = param.default
    return func_params


def execute_function_with_params(
    func_info: FunctionInfo, 
    request_params: Dict[str, Any], 
    method: str, 
    extra_debug_info: str = ""
) -> Dict[str, Any]:
    """
    Execute registered function with extracted parameters and handle common logic.
    
    Args:
        func_info: Function metadata and callable to execute
        request_params: Dictionary with parameters from API request
        method: HTTP method name for logging purposes
        extra_debug_info: Additional debug information to log
        
    Returns:
        Dict containing formatted function result
        
    Raises:
        HTTPException: 400 for parameter validation errors, 500 for runtime errors
        
    Handles parameter extraction, logging, function execution, and error management.
    Provides specific error codes for different types of failures.
    
    Example:
        >>> result = execute_function_with_params(func_info, {"x": 5}, "POST")
        {"result": 25}
    """
    try:
        func_params = extract_function_params(func_info, request_params)
        debug_msg = f"{method} {func_info.name}: params={func_params}"
        if extra_debug_info:
            debug_msg += f", {extra_debug_info}"
        logger.debug(debug_msg)
        result = func_info.func(**func_params)
        return create_result_response(result)
    except (ValueError, TypeError) as e:
        # Parameter validation or type errors
        logger.warning(f"{method} {func_info.name} parameter error: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Parameter error: {str(e)}")
    except Exception as e:
        # Runtime errors during function execution
        logger.error(f"{method} {func_info.name} runtime error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")


def create_handler(func_info: FunctionInfo, method: str):
    """
    Create endpoint handler for registered function with dynamic model.
    
    Args:
        func_info: Function information with parameters and metadata
        method: HTTP method ("GET" or "POST")
        
    Returns:
        Tuple of (handler_function, pydantic_model) ready for FastAPI registration
        
    Handles both GET (query parameters) and POST (request body) methods
    by creating appropriate Pydantic models and handler functions.
    
    Example:
        >>> handler, model = create_handler(func_info, "POST")
        >>> app.add_api_route("/endpoint", handler, methods=["POST"])
    """
    is_post = method.upper() == "POST"
    DynamicModel = create_dynamic_model(func_info, for_post=is_post)
    
    if is_post:
        async def handler(request: DynamicModel):
            # Convert Pydantic model to dict for processing
            request_params = request.dict()
            return execute_function_with_params(func_info, request_params, method)
    else:
        async def handler(query_params: DynamicModel = Depends()):
            # Convert Pydantic model to dict for processing
            request_params = query_params.dict()
            return execute_function_with_params(
                func_info, request_params, method, f"query={request_params}"
            )
    
    return handler, DynamicModel


def register_dynamic_endpoints(app: FastAPI):
    """
    Register all functions from registry as API endpoints.
    
    Creates both GET and POST handlers based on function metadata with dynamic models.
    Uses the unified create_handler function to avoid code duplication.
    
    Args:
        app: FastAPI application instance to register routes on
        
    Example:
        >>> app = FastAPI()
        >>> register_dynamic_endpoints(app)  # Registers all functions from FUNCTION_REGISTRY
    """
    for func_name, func_info in FUNCTION_REGISTRY.items():
        for method in func_info.http_methods:
            handler, input_model = create_handler(func_info, method)
            app.add_api_route(
                f"/{func_name}",
                handler,
                methods=[method.upper()],
                response_model=GenericOutput,
                operation_id=f"{func_name}_{method.lower()}",
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

    # Load core functions before registering endpoints
    logger.info("Loading core functions for API...")
    try:
        load_core_functions()
        logger.info(f"Successfully loaded {len(FUNCTION_REGISTRY)} functions: {list(FUNCTION_REGISTRY.keys())}")
    except Exception as e:
        logger.error(f"Failed to load core functions: {e}")
        raise

    # Register dynamic endpoints from function registry
    logger.info("Registering dynamic endpoints...")
    register_dynamic_endpoints(app)
    
    # Count registered endpoints for debugging
    endpoint_count = len([route for route in app.routes if hasattr(route, 'path') and route.path.startswith('/') and route.path not in ['/', '/functions', '/health']])
    logger.info(f"Registered {endpoint_count} dynamic endpoints")

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

    @app.get("/functions/details")
    async def list_functions_details():
        """Get detailed information about all registered functions."""
        functions_details = {}
        for func_name, func_info in FUNCTION_REGISTRY.items():
            functions_details[func_name] = {
                "name": func_info.name,
                "description": func_info.description,
                "http_methods": func_info.http_methods,
                "parameters": [
                    {
                        "name": param.name,
                        "type": param.type.__name__ if hasattr(param.type, '__name__') else str(param.type),
                        "default": param.default,
                        "required": param.required,
                        "description": param.description
                    }
                    for param in func_info.params
                ]
            }
        return {"functions": functions_details}

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
