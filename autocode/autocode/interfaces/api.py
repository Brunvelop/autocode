"""
FastAPI server with dynamic endpoints from registry and static file serving.
"""
import logging
import os
from typing import Any, Dict, Type, Union

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field, create_model

from autocode.autocode.interfaces.models import FunctionInfo, GenericOutput
from autocode.autocode.core.ai.models import DspyOutput
from autocode.autocode.interfaces.registry import FUNCTION_REGISTRY, load_core_functions

# Setup logging with custom filter to exclude noisy third-party libraries
class AutocodeLogFilter(logging.Filter):
    """Filter to exclude logs from specified noisy third-party modules."""
    
    # List of module prefixes to exclude from logs
    EXCLUDED_MODULES = [
        'sse_starlette',
        'LiteLLM',
        'httpcore',
        'mcp',
        'fastapi_mcp',
    ]
    
    def filter(self, record):
        # Exclude logs from modules in the exclusion list
        for excluded in self.EXCLUDED_MODULES:
            if record.name.startswith(excluded):
                return False
        return True

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Add filter to root logger to exclude third-party library logs
root_logger = logging.getLogger()
root_logger.addFilter(AutocodeLogFilter())

# Silence specific noisy third-party loggers by setting their level to WARNING
# This is necessary because some libraries bypass filters with custom handlers
for noisy_logger in ['LiteLLM', 'httpcore', 'sse_starlette', 'mcp', 'fastapi_mcp']:
    logging.getLogger(noisy_logger).setLevel(logging.WARNING)
    # Also silence sub-loggers
    for sub in ['connection', 'http11', 'sse', 'server', 'lowlevel']:
        logging.getLogger(f'{noisy_logger}.{sub}').setLevel(logging.WARNING)
    # Silence nested sub-loggers (e.g., mcp.server.lowlevel.server)
    for nested in ['server.lowlevel.server', 'server.sse', 'server.lowlevel']:
        logging.getLogger(f'{noisy_logger}.{nested}').setLevel(logging.WARNING)

logger = logging.getLogger(__name__)


# ============================================================================
# MAIN APPLICATION FACTORY
# ============================================================================

def create_api_app() -> FastAPI:
    """
    Create and configure FastAPI application.
    
    Entry point for creating the complete API application with:
    - Dynamic endpoints from function registry
    - Standard API endpoints (health, functions list)
    - Web UI with templates and static files
    
    Returns:
        Configured FastAPI application ready to run
        
    Raises:
        Exception: If core functions fail to load
    """
    app = FastAPI(
        title="Autocode API",
        description="Minimalistic framework for code quality tools",
        version="1.0.0"
    )

    # Load and validate core functions
    _load_and_validate_functions()
    
    # Register dynamic endpoints from function registry
    logger.info("Registering dynamic endpoints...")
    register_dynamic_endpoints(app)
    _log_endpoint_count(app)
    
    # Setup templates and static files
    templates = _setup_templates()
    
    # Register standard API endpoints
    _register_standard_endpoints(app, templates)
    _register_static_files(app)

    return app


def _load_and_validate_functions():
    """Load core functions and validate registry state."""
    logger.info("Loading core functions for API...")
    try:
        load_core_functions()
        if not FUNCTION_REGISTRY:
            logger.warning("No functions loaded in registry")
        else:
            logger.info(
                f"Successfully loaded {len(FUNCTION_REGISTRY)} functions: "
                f"{list(FUNCTION_REGISTRY.keys())}"
            )
    except Exception as e:
        logger.error(f"Failed to load core functions: {e}")
        raise


def _log_endpoint_count(app: FastAPI):
    """Log the number of registered dynamic endpoints for debugging."""
    endpoint_count = len([
        route for route in app.routes 
        if hasattr(route, 'path') 
        and route.path.startswith('/') 
        and route.path not in ['/', '/functions', '/health', '/functions/details']
    ])
    logger.info(f"Registered {endpoint_count} dynamic endpoints")


def _setup_templates() -> Jinja2Templates:
    """Setup Jinja2 templates for web UI."""
    current_dir = os.path.dirname(__file__)
    web_dir = os.path.join(current_dir, "..", "web")
    return Jinja2Templates(directory=web_dir)


def _register_standard_endpoints(app: FastAPI, templates: Jinja2Templates):
    """Register standard API endpoints (root, health, functions)."""
    
    @app.get("/")
    async def root(request: Request):
        """Root endpoint - serve the web UI with chat widget."""
        return templates.TemplateResponse("templates/index.html", {"request": request})

    @app.get("/functions")
    async def functions_ui(request: Request):
        """Serve the dynamic functions UI page with chat widget."""
        return templates.TemplateResponse("templates/functions.html", {"request": request})

    @app.get("/demo")
    async def demo_ui(request: Request):
        """Serve the custom elements demo page."""
        return templates.TemplateResponse("templates/auto-elements-demo.html", {"request": request})

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
                        "description": param.description,
                        "choices": param.choices
                    }
                    for param in func_info.params
                ]
            }
        return {"functions": functions_details}

    @app.get("/health")
    async def health_check():
        """Health check endpoint with function count."""
        return {"status": "healthy", "functions": len(FUNCTION_REGISTRY)}


def _register_static_files(app: FastAPI):
    """Mount static files directory for web UI."""
    current_dir = os.path.dirname(__file__)
    web_dir = os.path.join(current_dir, "..", "web")
    if os.path.exists(web_dir):
        app.mount("/static", StaticFiles(directory=web_dir), name="static")


# ============================================================================
# DYNAMIC ENDPOINT REGISTRATION
# ============================================================================

def register_dynamic_endpoints(app: FastAPI):
    """
    Register all functions from registry as API endpoints.
    
    Creates both GET and POST handlers based on function metadata with dynamic models.
    Uses the unified create_handler function to avoid code duplication.
    
    Args:
        app: FastAPI application instance to register routes on
        
    Example:
        >>> app = FastAPI()
        >>> register_dynamic_endpoints(app)
    """
    for func_name, func_info in FUNCTION_REGISTRY.items():
        for method in func_info.http_methods:
            handler, input_model = create_handler(func_info, method)
            app.add_api_route(
                f"/{func_name}",
                handler,
                methods=[method.upper()],
                response_model=Union[GenericOutput, DspyOutput],
                operation_id=f"{func_name}_{method.lower()}",
                summary=func_info.description
            )


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
    """
    is_post = method.upper() == "POST"
    DynamicModel = create_dynamic_model(func_info, for_post=is_post)
    
    if is_post:
        async def handler(request: DynamicModel):
            request_params = request.model_dump()
            return execute_function_with_params(func_info, request_params, method)
    else:
        async def handler(query_params: DynamicModel = Depends()):
            request_params = query_params.model_dump()
            return execute_function_with_params(
                func_info, request_params, method, f"query={request_params}"
            )
    
    return handler, DynamicModel


# ============================================================================
# PYDANTIC MODEL GENERATION
# ============================================================================

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
        field_type = param.type
        
        # Handle default values and required fields
        if param.required:
            fields[param.name] = (field_type, Field(description=param.description))
        else:
            default_value = param.default if param.default is not None else None
            fields[param.name] = (field_type, Field(default=default_value, description=param.description))
    
    # Create model name
    suffix = "Input" if for_post else "QueryParams"
    model_name = f"{func_info.name.title()}{suffix}"
    
    return create_model(model_name, **fields)


# ============================================================================
# FUNCTION EXECUTION
# ============================================================================

def execute_function_with_params(
    func_info: FunctionInfo, 
    request_params: Dict[str, Any], 
    method: str, 
    extra_debug_info: str = ""
) -> Dict[str, Any]:
    """
    Execute registered function with extracted parameters and handle errors.
    
    Args:
        func_info: Function metadata and callable to execute
        request_params: Dictionary with parameters from API request
        method: HTTP method name for logging purposes
        extra_debug_info: Additional debug information to log
        
    Returns:
        Dict containing formatted function result
        
    Raises:
        HTTPException: 400 for parameter validation errors, 500 for runtime errors
    """
    try:
        func_params = extract_function_params(func_info, request_params)
        debug_msg = f"{method} {func_info.name}: params={func_params}"
        if extra_debug_info:
            debug_msg += f", {extra_debug_info}"
        logger.debug(debug_msg)
        result = func_info.func(**func_params)
        response = create_result_response(result)
        logger.debug(response)
        return response
    except (ValueError, TypeError) as e:
        logger.warning(f"{method} {func_info.name} parameter error: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Parameter error: {str(e)}")
    except Exception as e:
        logger.error(f"{method} {func_info.name} runtime error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")


def extract_function_params(func_info: FunctionInfo, request_params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract and prepare function parameters from request data.
    
    Args:
        func_info: Function information containing parameter definitions
        request_params: Dictionary with request parameters from API call
        
    Returns:
        Dict with extracted parameters ready for function execution
    """
    func_params = {}
    for param in func_info.params:
        if param.name in request_params:
            func_params[param.name] = request_params[param.name]
        elif not param.required and param.default is not None:
            func_params[param.name] = param.default
    return func_params


# ============================================================================
# RESPONSE FORMATTING
# ============================================================================

def create_result_response(result: Any) -> Dict[str, Any]:
    """
    Format function results into consistent API response format.
    
    Converts GenericOutput instances to dictionaries for JSON serialization.
    All registered functions must return GenericOutput or subclass (enforced by registry).
    
    Args:
        result: Function result (GenericOutput or subclass)
        
    Returns:
        Dict with GenericOutput fields (success, result, message, etc.)
    """
    if isinstance(result, GenericOutput):
        return result.model_dump()
    
    # Fallback for dict (temporary compatibility)
    if isinstance(result, dict):
        return result
    
    # Should never happen due to registry enforcement
    return GenericOutput(
        success=False,
        result=str(result),
        message="Warning: Function returned non-GenericOutput type"
    ).model_dump()
