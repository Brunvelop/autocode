"""FastAPI server with dynamic endpoints from registry and static file serving."""
import logging
import os
import re
from importlib.metadata import version as pkg_version
from typing import Any, Callable, Dict, Type

from fastapi import Depends, FastAPI, HTTPException
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, create_model

from autocode.core.models import FunctionInfo, GenericOutput, FunctionSchema
from autocode.core.registry import (
    load_functions,
    get_all_schemas,
    get_functions_for_interface,
    get_stream_func,
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
    try:
        _version = pkg_version("autocode")
    except Exception:
        _version = "unknown"

    app = FastAPI(
        title="Autocode API",
        description="Minimalistic framework for autocode",
        version=_version
    )

    _load_and_validate_functions()
    _register_dynamic_endpoints(app)
    _register_standard_endpoints(app)
    _register_static_files(app)

    return app


def create_router_for_refract(refract) -> "APIRouter":
    """Create an ``APIRouter`` with only the dynamic endpoints from a Refract instance.

    This is the *router mode* — suitable for mounting on a user-supplied
    ``FastAPI`` app (``my_app.include_router(refract.router())``).

    Includes:
        - Dynamic function endpoints for all functions with ``"api"`` interface.
        - ``GET /functions/details`` — schema discovery for the frontend.
        - ``GET /health`` — basic health check.

    Excludes:
        - Static file mounts.
        - Root / demo / tests HTML pages.

    Args:
        refract: A ``Refract`` instance whose registry will be used.

    Returns:
        An ``APIRouter`` ready to be included in any FastAPI application.
    """
    from fastapi.routing import APIRouter

    router = APIRouter()
    functions = refract.get_all_functions()
    _add_function_endpoints(router, functions, refract.get_stream_func)

    # Capture schemas at router-creation time so the closure doesn't hold a
    # live reference to the Refract instance longer than needed.
    def _make_details_handler(refract_ref):
        async def list_functions_details() -> dict:
            schemas = refract_ref.get_all_schemas()
            return {"functions": {s.name: s for s in schemas}}
        return list_functions_details

    def _make_health_handler(refract_ref):
        async def health_check() -> dict:
            return {"status": "healthy", "functions": refract_ref.function_count()}
        return health_check

    router.add_api_route(
        "/functions/details",
        _make_details_handler(refract),
        methods=["GET"],
        operation_id="refract_list_functions_details",
        summary="List all registered function schemas",
    )
    router.add_api_route(
        "/health",
        _make_health_handler(refract),
        methods=["GET"],
        operation_id="refract_health_check",
        summary="Health check",
    )

    return router


def create_api_app_for_refract(refract) -> FastAPI:
    """Create a complete ``FastAPI`` application for a ``Refract`` instance.

    Equivalent to ``create_api_app()`` but uses the *instance* registry
    instead of the global registry.  Suitable for the *app mode*:

        app = Refract("my-project", discover=["my_project.core"])
        fastapi_app = app.api()  # Ready to serve

    Includes everything ``create_router_for_refract`` produces, plus:
        - Standard HTML pages (root, ``/functions``, ``/demo``, ``/tests``).
        - Static file mounts (``/elements``, ``/tests``, ``/static``).

    Args:
        refract: A ``Refract`` instance whose registry will be used.

    Returns:
        A configured ``FastAPI`` application.
    """
    try:
        from importlib.metadata import version as pkg_version
        _version = pkg_version("autocode")
    except Exception:
        _version = "unknown"

    app = FastAPI(
        title=f"{refract._name} API",
        description=f"API for {refract._name}",
        version=_version,
    )

    functions = refract.get_all_functions()
    _add_function_endpoints(app, functions, refract.get_stream_func)
    _register_standard_endpoints_for_refract(app, refract)
    _register_static_files(app)

    return app


def _register_standard_endpoints_for_refract(app: FastAPI, refract) -> None:
    """Register standard endpoints bound to a Refract instance's registry.

    Parameterized version of ``_register_standard_endpoints`` — reads schemas
    and function counts from *refract* rather than the global registry.

    Args:
        app: FastAPI application to register endpoints on.
        refract: Refract instance whose registry is used for data endpoints.
    """
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
        schemas = refract.get_all_schemas()
        return {"functions": {s.name: s for s in schemas}}

    @app.get("/health")
    async def health_check():
        return {"status": "healthy", "functions": refract.function_count()}

    @app.get("/api/tests/discover")
    async def discover_tests():
        return _discover_test_files(tests_dir)


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


def _add_function_endpoints(
    app_or_router,
    functions: list,
    stream_getter: Callable,
) -> None:
    """Register dynamic endpoints from a given list of FunctionInfo objects.

    This is the parameterized core — it does not touch the global registry.
    Both the global ``_register_dynamic_endpoints`` and the instance-level
    ``create_router_for_refract`` / ``create_api_app_for_refract`` delegate here.

    Args:
        app_or_router: A ``FastAPI`` app or ``APIRouter`` to add routes to.
        functions: List of ``FunctionInfo`` objects whose ``"api"`` interface is set.
        stream_getter: Callable ``(name: str) -> Callable | None`` that returns the
            async generator for streaming functions.
    """
    api_functions = [f for f in functions if "api" in f.interfaces]

    for func_info in api_functions:
        if func_info.streaming:
            stream_func = stream_getter(func_info.name)
            if stream_func is None:
                logger.error(f"Streaming function '{func_info.name}' has no stream_func registered")
                continue
            handler = _create_stream_handler(func_info, stream_func)
            app_or_router.add_api_route(
                f"/{func_info.name}",
                handler,
                methods=["POST"],
                operation_id=f"{func_info.name}_stream",
                summary=f"[SSE Stream] {func_info.description}"
            )
        else:
            for method in func_info.http_methods:
                handler, _ = create_handler(func_info, method)
                response_model = func_info.return_type or GenericOutput
                app_or_router.add_api_route(
                    f"/{func_info.name}",
                    handler,
                    methods=[method.upper()],
                    response_model=response_model,
                    operation_id=f"{func_info.name}_{method.lower()}",
                    summary=func_info.description
                )

    logger.info(f"Registered {len(api_functions)} dynamic endpoints")


def _register_dynamic_endpoints(app: FastAPI):
    """Register all API-exposed functions as endpoints (reads global registry).

    Delegates to ``_add_function_endpoints`` with global-registry data.

    Streaming functions get a dedicated SSE endpoint via _create_stream_handler.
    Non-streaming functions use the standard handler as before.
    """
    all_functions = get_functions_for_interface("api")
    # get_functions_for_interface already filters by "api", pass full list
    # _add_function_endpoints re-filters, which is harmless.
    _add_function_endpoints(app, all_functions, get_stream_func)


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


# --- Streaming Handler ---

def _create_stream_handler(func_info: FunctionInfo, stream_func: Callable):
    """Create SSE streaming handler for a registered function.
    
    Args:
        func_info: Function metadata from registry.
        stream_func: Async generator function that produces SSE events.
        
    Returns:
        FastAPI handler that returns StreamingResponse.
    """
    DynamicModel = _create_dynamic_model(func_info, for_post=True)
    
    async def handler(request: DynamicModel):
        params = request.model_dump()
        return StreamingResponse(
            stream_func(**params),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no"
            }
        )
    return handler


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
    if isinstance(result, BaseModel):
        return result.model_dump()
    if isinstance(result, dict):
        return result
    logger.warning(f"Function returned non-BaseModel type: {type(result).__name__}. Converting to string.")
    return GenericOutput(
        success=False,
        result=str(result),
        message=f"Warning: Function returned non-BaseModel type ({type(result).__name__})"
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
