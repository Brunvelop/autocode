"""FastAPI server with dynamic endpoints from registry and static file serving."""
import logging
import os
import re
from typing import Any, Dict, Type

from fastapi import Depends, FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, create_model

from autocode.interfaces.models import FunctionInfo, GenericOutput, FunctionSchema
from autocode.interfaces.registry import (
    load_functions,
    get_all_schemas,
    get_functions_for_interface,
    function_count
)
from autocode.interfaces.logging_config import configure_api_logging

configure_api_logging()
logger = logging.getLogger(__name__)


# --- Public API ---

def create_api_app() -> FastAPI:
    """
    Create and configure FastAPI application.
    
    Entry point for creating the complete API with dynamic endpoints,
    standard endpoints (health, functions list), and web UI.
    """
    app = FastAPI(
        title="Autocode API",
        description="Minimalistic framework for autocode",
        version="1.0.0"
    )

    _load_and_validate_functions()
    _register_dynamic_endpoints(app)
    _register_standard_endpoints(app)
    _register_static_files(app)

    return app


def create_handler(func_info: FunctionInfo, method: str):
    """
    Create endpoint handler for registered function.
    
    Used by both api.py and mcp.py to create FastAPI handlers.
    Returns tuple of (handler_function, pydantic_model).
    """
    is_post = method.upper() == "POST"
    DynamicModel = _create_dynamic_model(func_info, for_post=is_post)

    if is_post:
        async def handler(request: DynamicModel):
            return _execute_function(func_info, request.model_dump(), method)
    else:
        async def handler(query_params: DynamicModel = Depends()):
            return _execute_function(func_info, query_params.model_dump(), method)

    return handler, DynamicModel


# --- Setup Helpers ---

def _load_and_validate_functions():
    """Load core functions and log registry state."""
    logger.info("Loading core functions for API...")
    try:
        load_functions()
        count = function_count()
        if count == 0:
            logger.warning("No functions loaded in registry")
        else:
            api_funcs = [f.name for f in get_functions_for_interface("api")]
            mcp_funcs = [f.name for f in get_functions_for_interface("mcp")]
            logger.info(f"Loaded {count} functions: API={api_funcs}, MCP={mcp_funcs}")
    except Exception as e:
        logger.error(f"Failed to load core functions: {e}")
        raise


def _register_dynamic_endpoints(app: FastAPI):
    """Register all API-exposed functions as endpoints."""
    api_functions = get_functions_for_interface("api")

    for func_info in api_functions:
        for method in func_info.http_methods:
            handler, _ = create_handler(func_info, method)
            response_model = func_info.return_type or GenericOutput
            app.add_api_route(
                f"/{func_info.name}",
                handler,
                methods=[method.upper()],
                response_model=response_model,
                operation_id=f"{func_info.name}_{method.lower()}",
                summary=func_info.description
            )

    logger.info(f"Registered {len(api_functions)} dynamic endpoints")


def _register_standard_endpoints(app: FastAPI):
    """Register standard API endpoints (root, health, functions, tests)."""
    current_dir = os.path.dirname(__file__)
    views_dir = os.path.join(current_dir, "..", "web", "views")
    tests_dir = os.path.join(current_dir, "..", "web", "tests")

    @app.get("/")
    async def root():
        return FileResponse(os.path.join(views_dir, "index.html"))

    @app.get("/functions")
    async def functions_ui():
        return FileResponse(os.path.join(views_dir, "functions.html"))

    @app.get("/demo")
    async def demo_ui():
        return FileResponse(os.path.join(views_dir, "demo.html"))

    @app.get("/tests")
    async def tests_dashboard():
        return FileResponse(os.path.join(tests_dir, "index.html"))

    @app.get("/functions/details")
    async def list_functions_details() -> dict[str, dict[str, FunctionSchema]]:
        schemas = get_all_schemas()
        return {"functions": {s.name: s for s in schemas}}

    @app.get("/health")
    async def health_check():
        return {"status": "healthy", "functions": function_count()}

    @app.get("/api/tests/discover")
    async def discover_tests():
        return _discover_test_files(tests_dir)


def _register_static_files(app: FastAPI):
    """Mount static files directories for web UI."""
    current_dir = os.path.dirname(__file__)
    web_dir = os.path.join(current_dir, "..", "web")

    mounts = [
        ("/elements", "elements"),
        ("/tests", "tests"),
        ("/static", "static")
    ]

    for route, subdir in mounts:
        path = os.path.join(web_dir, subdir)
        if os.path.exists(path):
            html_mode = subdir == "tests"
            app.mount(route, StaticFiles(directory=path, html=html_mode), name=subdir)


# --- Model Generation ---

def _create_dynamic_model(func_info: FunctionInfo, for_post: bool = True) -> Type[BaseModel]:
    """Create Pydantic model from function parameters."""
    fields = {}

    for param in func_info.params:
        if param.required:
            fields[param.name] = (param.type, Field(description=param.description))
        else:
            default = param.default if param.default is not None else None
            fields[param.name] = (param.type, Field(default=default, description=param.description))

    suffix = "Input" if for_post else "QueryParams"
    return create_model(f"{func_info.name.title()}{suffix}", **fields)


# --- Function Execution ---

def _execute_function(
    func_info: FunctionInfo,
    request_params: Dict[str, Any],
    method: str
) -> Dict[str, Any]:
    """Execute function with parameters and handle errors."""
    try:
        func_params = _extract_params(func_info, request_params)
        logger.debug(f"{method} {func_info.name}: params={func_params}")
        result = func_info.func(**func_params)
        return _format_response(result)
    except (ValueError, TypeError) as e:
        logger.warning(f"{method} {func_info.name} param error: {e}")
        raise HTTPException(status_code=400, detail=f"Parameter error: {e}")
    except Exception as e:
        logger.error(f"{method} {func_info.name} error: {e}")
        raise HTTPException(status_code=500, detail=f"Internal error: {e}")


def _extract_params(func_info: FunctionInfo, request_params: Dict[str, Any]) -> Dict[str, Any]:
    """Extract function parameters from request data."""
    params = {}
    for param in func_info.params:
        if param.name in request_params:
            params[param.name] = request_params[param.name]
        elif not param.required and param.default is not None:
            params[param.name] = param.default
    return params


def _format_response(result: Any) -> Dict[str, Any]:
    """Format function result into API response."""
    if isinstance(result, GenericOutput):
        return result.model_dump()
    if isinstance(result, dict):
        return result
    return GenericOutput(
        success=False,
        result=str(result),
        message="Warning: Function returned non-GenericOutput type"
    ).model_dump()


# --- Test Discovery ---

def _discover_test_files(tests_root: str) -> dict:
    """Discover test files in tests directory."""
    discovered = {}

    for root, dirs, files in os.walk(tests_root):
        dirs[:] = [d for d in dirs if not d.startswith(('_', '.'))]
        rel_path = os.path.relpath(root, tests_root)
        category = 'General' if rel_path == '.' else rel_path.replace(os.sep, ' ').title()

        for file in files:
            if not file.endswith('.test.html'):
                continue

            file_path = os.path.join(root, file)
            web_path = f"/tests/{os.path.relpath(file_path, tests_root).replace(os.sep, '/')}"
            title, description = _extract_test_metadata(file_path, file)

            if category not in discovered:
                discovered[category] = []
            discovered[category].append({
                "name": title,
                "description": description,
                "path": web_path,
                "filename": file
            })

    return discovered


def _extract_test_metadata(file_path: str, default_name: str) -> tuple[str, str]:
    """Extract title and description from test HTML file."""
    title, description = default_name, "Test suite"
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        title_match = re.search(r'<title>(.*?)</title>', content)
        if title_match:
            title = title_match.group(1).replace(' - Unit Tests', '').replace(' - Integration Tests', '').strip()
        desc_match = re.search(r'<p class=".*?text-gray-600.*?">(.*?)</p>', content)
        if desc_match:
            description = desc_match.group(1).strip()
    except Exception:
        pass
    return title, description
