"""
Central registry for all functions exposed via interfaces (CLI, API, MCP).
Uses automatic parameter inference from function signatures and docstrings.

Example:
    @register_function(http_methods=["GET", "POST"])
    def my_function(x: int, y: str = "default") -> GenericOutput:
        '''Adds two numbers together.
        
        Args:
            x: First number
            y: Second number or string
        '''
        return GenericOutput(result=x + y, success=True)
"""
from typing import Dict, Any, Callable, get_origin, get_args, Union, Literal
import ast
import importlib
import importlib.util
import inspect
import logging
import pkgutil
from docstring_parser import parse

from autocode.interfaces.models import (
    FunctionInfo, ExplicitParam, GenericOutput, FunctionSchema,
    HttpMethod, Interface, DEFAULT_HTTP_METHODS, DEFAULT_INTERFACES
)

logger = logging.getLogger(__name__)

# --- GLOBALS ---

FUNCTION_REGISTRY: Dict[str, FunctionInfo] = {}
_functions_loaded = False


class RegistryError(Exception):
    """Custom exception for registry-related errors."""
    pass


# --- PUBLIC API ---

def register_function(
    http_methods: list[HttpMethod] | None = None,
    interfaces: list[Interface] | None = None
) -> Callable[[Callable], Callable]:
    """Decorator to expose a function via CLI, API, and/or MCP."""
    def decorator(func: Callable) -> Callable:
        try:
            info = _generate_function_info(func, http_methods, interfaces)
            FUNCTION_REGISTRY[info.name] = info
            logger.debug(f"Registered '{info.name}' with methods {info.http_methods}")
        except Exception as e:
            raise RegistryError(f"Failed to register function '{func.__name__}': {e}") from e
        return func
    return decorator


def get_functions_for_interface(interface: Interface) -> Dict[str, FunctionInfo]:
    """Filter registered functions by interface ("api", "cli", or "mcp").
    
    Raises:
        RegistryError: If FUNCTION_REGISTRY is empty (load_core_functions not called).
    """
    if not FUNCTION_REGISTRY:
        raise RegistryError(
            "FUNCTION_REGISTRY is empty. "
            "Call load_core_functions() at application startup."
        )
    return {name: info for name, info in FUNCTION_REGISTRY.items() if interface in info.interfaces}


def get_all_function_schemas() -> Dict[str, FunctionSchema]:
    """Get serializable schemas for all registered functions."""
    _ensure_functions_loaded()
    return {name: info.to_schema() for name, info in FUNCTION_REGISTRY.items()}


def load_core_functions(strict: bool = False):
    """Autodiscover and import modules with @register_function in autocode/core/.
    
    Called automatically on first registry access. Safe to call multiple times.
    If strict=True, raises RegistryError on any import failure.
    """
    global _functions_loaded
    if _functions_loaded:
        return
    
    try:
        import autocode.core
    except ImportError as e:
        raise RegistryError(f"Failed to import autocode.core: {e}") from e
    
    discovered, failed = [], []
    modules = sorted(pkgutil.walk_packages(autocode.core.__path__, autocode.core.__name__ + "."), key=lambda x: x[1])
    
    for _, module_name, is_pkg in modules:
        if is_pkg:
            continue
        module_path = _get_module_file_path(module_name)
        if not _has_register_decorator(module_path):
            continue
        try:
            importlib.import_module(module_name)
            discovered.append(module_name)
        except Exception as e:
            failed.append((module_name, str(e)))
            logger.warning(f"Could not import {module_name}: {e}")
    
    _functions_loaded = True
    
    if failed and strict:
        raise RegistryError(f"Failed to load modules in strict mode: {[m[0] for m in failed]}")
    
    logger.debug(f"Loaded {len(FUNCTION_REGISTRY)} functions from {len(discovered)} modules")


def clear_registry():
    """Clear registry and reset loaded flag. Used for testing."""
    global _functions_loaded
    FUNCTION_REGISTRY.clear()
    _functions_loaded = False


# --- PRIVATE IMPLEMENTATION ---

def _ensure_functions_loaded():
    """Lazy-load functions on first registry access."""
    if not _functions_loaded:
        load_core_functions()


def _generate_function_info(
    func: Callable,
    http_methods: list[HttpMethod] | None = None,
    interfaces: list[Interface] | None = None
) -> FunctionInfo:
    """Generate FunctionInfo from function signature and docstring."""
    http_methods = http_methods or list(DEFAULT_HTTP_METHODS)
    interfaces = interfaces or list(DEFAULT_INTERFACES)
    
    # Validate HTTP methods
    valid_methods = {"GET", "POST", "PUT", "DELETE", "PATCH"}
    if not all(m.upper() in valid_methods for m in http_methods):
        raise ValueError(f"Invalid HTTP methods. Must be one of: {valid_methods}")
    
    # Validate return type
    sig = inspect.signature(func)
    return_annotation = sig.return_annotation
    
    if return_annotation == inspect.Parameter.empty:
        raise RegistryError(f"Function '{func.__name__}' must have a return type annotation of GenericOutput")
    
    # Resolve Optional/Union to inner type
    return_type = return_annotation
    if get_origin(return_annotation) is Union:
        non_none = [a for a in get_args(return_annotation) if a is not type(None)]
        if non_none:
            return_type = non_none[0]
    
    if not (isinstance(return_type, type) and issubclass(return_type, GenericOutput)):
        raise RegistryError(f"Function '{func.__name__}' must return GenericOutput, got {return_type}")
    
    # Parse docstring for parameter descriptions
    doc = parse(inspect.getdoc(func) or "")
    param_docs = {p.arg_name: p.description for p in doc.params}
    
    # Extract parameters
    params = []
    for name, param in sig.parameters.items():
        if param.kind in (inspect.Parameter.VAR_POSITIONAL, inspect.Parameter.VAR_KEYWORD):
            continue
        params.append(_extract_param_info(param, name, param_docs))
    
    return FunctionInfo(
        name=func.__name__,
        func=func,
        description=doc.short_description or f"Execute {func.__name__}",
        params=params,
        http_methods=http_methods,
        interfaces=interfaces,
        return_type=return_type
    )


def _extract_param_info(param: inspect.Parameter, name: str, param_docs: dict[str, str]) -> ExplicitParam:
    """Extract ExplicitParam from inspect.Parameter."""
    param_type = param.annotation if param.annotation != inspect.Parameter.empty else Any
    choices = list(get_args(param_type)) if get_origin(param_type) is Literal else None
    
    return ExplicitParam(
        name=name,
        type=param_type,
        default=param.default if param.default != inspect.Parameter.empty else None,
        required=param.default == inspect.Parameter.empty,
        description=param_docs.get(name, f"Parameter {name}"),
        choices=choices
    )


def _get_module_file_path(module_name: str) -> str | None:
    """Return file path for a module, or None if not found."""
    try:
        spec = importlib.util.find_spec(module_name)
        return spec.origin if spec else None
    except Exception:
        return None


def _has_register_decorator(module_path: str | None) -> bool:
    """Check if module contains @register_function decorator using AST."""
    if not module_path:
        return False
    try:
        with open(module_path, 'r', encoding='utf-8') as f:
            tree = ast.parse(f.read(), filename=module_path)
        
        for node in ast.walk(tree):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            for dec in node.decorator_list:
                if isinstance(dec, ast.Name) and dec.id == 'register_function':
                    return True
                if isinstance(dec, ast.Call):
                    func = dec.func
                    if isinstance(func, ast.Name) and func.id == 'register_function':
                        return True
                    if isinstance(func, ast.Attribute) and func.attr == 'register_function':
                        return True
                if isinstance(dec, ast.Attribute) and dec.attr == 'register_function':
                    return True
        return False
    except Exception:
        return False
