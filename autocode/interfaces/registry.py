"""
Central registry for all functions exposed via interfaces.
This registry enables automatic generation of CLI commands, API endpoints, and MCP tools.
Uses automatic parameter inference from function signatures and docstrings.

Example:
    @register_function(http_methods=["GET", "POST"])
    def my_function(x: int, y: str = "default") -> GenericOutput:
        '''Adds two numbers together.
        
        Args:
            x: First number
            y: Second number or string
            
        Returns:
            Result of the operation
        '''
        return GenericOutput(result=x + y, success=True)
"""
from typing import Dict, Any, List, Callable, get_origin, get_args, Union, Literal, TypeAlias
import inspect
import logging
from docstring_parser import parse

from autocode.interfaces.models import FunctionInfo, ExplicitParam, GenericOutput, FunctionSchema

# Configure logging
logger = logging.getLogger(__name__)

# Global registry - populated dynamically by decorator
FUNCTION_REGISTRY: Dict[str, FunctionInfo] = {}
_functions_loaded = False

# Type aliases for better type hints
HttpMethod = Literal["GET", "POST", "PUT", "DELETE", "PATCH"]
Interface = Literal["api", "cli", "mcp"]

# Default values as constants (explicit and reusable)
DEFAULT_HTTP_METHODS: list[HttpMethod] = ["GET", "POST"]
DEFAULT_INTERFACES: list[Interface] = ["api", "cli", "mcp"]


# ============================================================================
# EXCEPTIONS
# ============================================================================

class RegistryError(Exception):
    """Custom exception for registry-related errors."""
    pass


# ============================================================================
# PUBLIC API - REGISTRATION
# ============================================================================

def register_function(
    http_methods: list[HttpMethod] | None = None,
    interfaces: list[Interface] | None = None
) -> Callable[[Callable], Callable]:
    """Decorator to expose a function via CLI, API, and/or MCP.
    
    Raises RegistryError if registration fails (e.g., invalid return type).
    """
    def decorator(func: Callable) -> Callable:
        try:
            info = _generate_function_info(func, http_methods, interfaces)
            FUNCTION_REGISTRY[info.name] = info
            # Only log at DEBUG level, not INFO (reduces CLI noise)
            logger.debug(f"Registered function '{info.name}' with methods {info.http_methods} and interfaces {info.interfaces}")
        except Exception as e:
            logger.error(f"Failed to register function '{func.__name__}': {e}")
            raise RegistryError(f"Failed to register function '{func.__name__}': {e}") from e
        return func
    return decorator


# ============================================================================
# PUBLIC API - REGISTRY ACCESS
# ============================================================================

def get_functions_for_interface(interface: Interface) -> Dict[str, FunctionInfo]:
    """Filter registered functions by interface ("api", "cli", or "mcp")."""
    _ensure_functions_loaded()
    return {
        name: info 
        for name, info in FUNCTION_REGISTRY.items() 
        if interface in info.interfaces
    }


def get_function_info(name: str) -> FunctionInfo:
    """Get FunctionInfo by name. Raises RegistryError if not found."""
    _ensure_functions_loaded()
    if name not in FUNCTION_REGISTRY:
        available = ", ".join(list_functions())
        raise RegistryError(f"Function '{name}' not found. Available functions: {available}")
    return FUNCTION_REGISTRY[name]


def get_all_function_schemas() -> Dict[str, FunctionSchema]:
    """Get serializable schemas for all registered functions."""
    _ensure_functions_loaded()
    return {
        name: info.to_schema()
        for name, info in FUNCTION_REGISTRY.items()
    }


def list_functions() -> List[str]:
    """Return sorted list of all registered function names."""
    _ensure_functions_loaded()
    return sorted(FUNCTION_REGISTRY.keys())


def clear_registry():
    """Clear registry and reset loaded flag. Used for testing."""
    global _functions_loaded
    FUNCTION_REGISTRY.clear()
    _functions_loaded = False


def get_function(name: str) -> Callable:
    """Get callable function by name. Raises RegistryError if not found."""
    func_info = get_function_info(name)
    return func_info.func


def get_registry_stats() -> Dict[str, Any]:
    """Return stats: total_functions, function_names, http_methods_distribution."""
    _ensure_functions_loaded()
    
    # Count HTTP methods distribution
    methods_count = {"GET": 0, "POST": 0, "PUT": 0, "DELETE": 0, "PATCH": 0}
    for func_info in FUNCTION_REGISTRY.values():
        for method in func_info.http_methods:
            if method in methods_count:
                methods_count[method] += 1
    
    return {
        "total_functions": len(FUNCTION_REGISTRY),
        "function_names": sorted(FUNCTION_REGISTRY.keys()),
        "http_methods_distribution": methods_count
    }


# ============================================================================
# LOADING AND INITIALIZATION
# ============================================================================

def _get_module_file_path(module_name: str) -> str | None:
    """Return file path for a module, or None if not found."""
    import importlib.util
    try:
        spec = importlib.util.find_spec(module_name)
        if spec and spec.origin:
            return spec.origin
    except Exception:
        pass
    return None


def _has_register_decorator(module_path: str) -> bool:
    """Check if module contains @register_function decorator using AST parsing."""
    import ast
    
    if not module_path:
        return False
    try:
        with open(module_path, 'r', encoding='utf-8') as f:
            source = f.read()
        
        tree = ast.parse(source, filename=module_path)
        
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                for decorator in node.decorator_list:
                    # Handle @register_function (Name node)
                    if isinstance(decorator, ast.Name) and decorator.id == 'register_function':
                        return True
                    # Handle @register_function() (Call node)
                    if isinstance(decorator, ast.Call):
                        func = decorator.func
                        if isinstance(func, ast.Name) and func.id == 'register_function':
                            return True
                        # Handle module.register_function() (Attribute node)
                        if isinstance(func, ast.Attribute) and func.attr == 'register_function':
                            return True
                    # Handle module.register_function (Attribute without call)
                    if isinstance(decorator, ast.Attribute) and decorator.attr == 'register_function':
                        return True
        return False
    except Exception:
        return False


def load_core_functions(strict: bool = False):
    """Autodiscover and import modules with @register_function in autocode/core/.
    
    Called automatically on first registry access. Safe to call multiple times.
    If strict=True, raises RegistryError on any import failure.
    """
    global _functions_loaded
    if _functions_loaded:
        return
    
    import pkgutil
    import importlib
    
    try:
        import autocode.core
    except ImportError as e:
        logger.error(f"Failed to import autocode.core package: {e}", exc_info=True)
        raise RegistryError(f"Failed to import autocode.core package: {e}") from e
    
    package_path = autocode.core.__path__
    prefix = autocode.core.__name__ + "."
    
    discovered_modules = []
    skipped_modules = []
    failed_modules = []
    
    # Sort modules for deterministic order (reproducibility)
    modules = sorted(
        pkgutil.walk_packages(package_path, prefix),
        key=lambda x: x[1]  # Sort by module_name
    )
    
    for importer, module_name, is_pkg in modules:
        # Skip package __init__ files (is_pkg=True means it's a package)
        if is_pkg:
            continue
        
        # Get module file path for decorator detection
        module_path = _get_module_file_path(module_name)
        
        # Only import modules that have @register_function decorator
        if not _has_register_decorator(module_path):
            skipped_modules.append(module_name)
            # Don't log skipped modules at all - reduces noise significantly
            continue
        
        try:
            importlib.import_module(module_name)
            discovered_modules.append(module_name)
            # Only log at DEBUG level
            logger.debug(f"Autodiscovered module: {module_name}")
        except ImportError as e:
            failed_modules.append((module_name, str(e)))
            logger.warning(f"Could not import {module_name}: {e}", exc_info=True)
        except Exception as e:
            failed_modules.append((module_name, str(e)))
            logger.error(f"Error loading {module_name}: {e}", exc_info=True)
    
    _functions_loaded = True
    
    if failed_modules:
        logger.warning(f"Some modules failed to load: {failed_modules}")
        if strict:
            raise RegistryError(
                f"Failed to load modules in strict mode: {[m[0] for m in failed_modules]}"
            )
    
    # Only log summary at DEBUG level to reduce CLI noise
    logger.debug(
        f"Autodiscovered {len(FUNCTION_REGISTRY)} functions from "
        f"{len(discovered_modules)} modules in autocode.core "
        f"(skipped {len(skipped_modules)} modules without @register_function)"
    )


def _ensure_functions_loaded():
    """Lazy-load functions on first registry access."""
    if not _functions_loaded:
        load_core_functions()


# ============================================================================
# PRIVATE HELPERS - FUNCTION INTROSPECTION
# ============================================================================

def _generate_function_info(
    func: Callable,
    http_methods: list[HttpMethod] | None = None,
    interfaces: list[Interface] | None = None
) -> FunctionInfo:
    """Generate FunctionInfo from function signature and docstring."""
    if http_methods is None:
        http_methods = list(DEFAULT_HTTP_METHODS)
        
    if interfaces is None:
        interfaces = list(DEFAULT_INTERFACES)
    
    http_methods = _validate_http_methods(http_methods)
    return_type = _get_return_type(func)
    _validate_return_type(func)
    
    # Parse docstring for parameter descriptions
    doc = parse(inspect.getdoc(func) or "")
    param_docs = {p.arg_name: p.description for p in doc.params}
    
    # Extract parameters from function signature
    sig = inspect.signature(func)
    params = []
    for name, param in sig.parameters.items():
        # Skip *args and **kwargs parameters
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


def _get_return_type(func: Callable):
    """Get declared return type, resolving Optional/Union to the inner type."""
    sig = inspect.signature(func)
    return_annotation = sig.return_annotation

    if return_annotation == inspect.Parameter.empty:
        return None

    origin = get_origin(return_annotation)
    if origin is Union:
        args = get_args(return_annotation)
        non_none = [a for a in args if a is not type(None)]
        if len(non_none) == 1:
            return_annotation = non_none[0]

    return return_annotation


def _validate_http_methods(http_methods: list[str]) -> list[str]:
    """Validate HTTP methods. Raises ValueError if invalid."""
    valid_methods = {"GET", "POST", "PUT", "DELETE", "PATCH"}
    if not all(method.upper() in valid_methods for method in http_methods):
        raise ValueError(f"Invalid HTTP methods. Must be one of: {valid_methods}")
    return http_methods


def _validate_return_type(func: Callable) -> None:
    """Validate return type is GenericOutput or subclass. Raises RegistryError if invalid."""
    sig = inspect.signature(func)
    return_annotation = sig.return_annotation
    
    if return_annotation == inspect.Parameter.empty:
        raise RegistryError(
            f"Function '{func.__name__}' must have a return type annotation of GenericOutput or a subclass. "
            f"Example: def {func.__name__}(...) -> GenericOutput:"
        )
    
    try:
        # Handle Union types (e.g., GenericOutput | None)
        origin = get_origin(return_annotation)
        if origin is Union:
            args = get_args(return_annotation)
            valid_types = [arg for arg in args if arg is not type(None)]
            if valid_types:
                return_annotation = valid_types[0]
        
        # Verify it's GenericOutput or subclass
        if not (isinstance(return_annotation, type) and issubclass(return_annotation, GenericOutput)):
            raise RegistryError(
                f"Function '{func.__name__}' must return GenericOutput or a subclass. "
                f"Found: {return_annotation}. "
                f"Please update the function to return GenericOutput(result=..., success=True/False, message=...)"
            )
    except TypeError:
        raise RegistryError(
            f"Function '{func.__name__}' has invalid return type annotation: {return_annotation}. "
            f"Must be GenericOutput or a subclass."
        )


def _extract_param_info(param: inspect.Parameter, param_name: str, param_docs: dict[str, str]) -> ExplicitParam:
    """Extract ExplicitParam from inspect.Parameter (type, default, description, choices)."""
    param_type = param.annotation if param.annotation != inspect.Parameter.empty else Any
    default = param.default if param.default != inspect.Parameter.empty else None
    required = param.default == inspect.Parameter.empty
    description = param_docs.get(param_name, f"Parameter {param_name}")
    
    # Extract choices from Literal type
    choices = None
    origin = get_origin(param_type)
    if origin is Literal:
        choices = list(get_args(param_type))
    
    return ExplicitParam(
        name=param_name,
        type=param_type,
        default=default,
        required=required,
        description=description,
        choices=choices
    )
