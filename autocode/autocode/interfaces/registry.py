"""
Central registry for all functions exposed via interfaces.
This registry enables automatic generation of CLI commands, API endpoints, and MCP tools.
Uses automatic parameter inference from function signatures and docstrings.
"""
from typing import Dict, Any, List, Callable, get_origin, get_args
import inspect
import logging
from docstring_parser import parse

from autocode.autocode.interfaces.models import FunctionInfo, ExplicitParam

# Configure logging
logger = logging.getLogger(__name__)

# Global registry - populated dynamically by decorator
FUNCTION_REGISTRY: Dict[str, FunctionInfo] = {}


class RegistryError(Exception):
    """Custom exception for registry-related errors."""
    pass


def _generate_function_info(func: Callable, http_methods: List[str] = None) -> FunctionInfo:
    """Generate FunctionInfo from function signature and docstring.
    
    Args:
        func: The function to analyze
        http_methods: List of HTTP methods to support (default: ["GET", "POST"])
        
    Returns:
        FunctionInfo instance with inferred parameters and description
        
    Raises:
        ValueError: If http_methods contains invalid values
    """
    if http_methods is None:
        http_methods = ["GET", "POST"]
    
    # Validate http_methods
    valid_methods = {"GET", "POST", "PUT", "DELETE", "PATCH"}
    if not all(method.upper() in valid_methods for method in http_methods):
        raise ValueError(f"Invalid HTTP methods. Must be one of: {valid_methods}")
    
    sig = inspect.signature(func)
    doc = parse(inspect.getdoc(func) or "")
    param_docs = {p.arg_name: p.description for p in doc.params}
    
    params = []
    for name, param in sig.parameters.items():
        # Skip *args and **kwargs parameters
        if param.kind in (inspect.Parameter.VAR_POSITIONAL, inspect.Parameter.VAR_KEYWORD):
            continue
            
        param_type = param.annotation if param.annotation != inspect.Parameter.empty else Any
        default = param.default if param.default != inspect.Parameter.empty else None
        required = default is None
        description = param_docs.get(name, f"Parameter {name}")
        
        # Extract choices from Literal type
        choices = None
        origin = get_origin(param_type)
        if origin is not None:
            # Check if it's a Literal type
            try:
                from typing import Literal
                if origin is Literal:
                    choices = list(get_args(param_type))
            except ImportError:
                pass
        
        params.append(ExplicitParam(
            name=name,
            type=param_type,
            default=default,
            required=required,
            description=description,
            choices=choices
        ))
    
    return FunctionInfo(
        name=func.__name__,
        func=func,
        description=doc.short_description or f"Execute {func.__name__}",
        params=params,
        http_methods=http_methods
    )


def register_function(http_methods: List[str] = None):
    """Decorator to automatically register a function in the global registry.
    
    Args:
        http_methods: List of HTTP methods to support for this function
        
    Returns:
        Decorator function
        
    Example:
        @register_function(http_methods=["GET", "POST"])
        def my_function(param1: str) -> str:
            '''My function description.'''
            return f"Result: {param1}"
    """
    def decorator(func: Callable) -> Callable:
        try:
            info = _generate_function_info(func, http_methods)
            FUNCTION_REGISTRY[info.name] = info
            logger.debug(f"Registered function '{info.name}' with methods {info.http_methods}")
        except Exception as e:
            logger.error(f"Failed to register function '{func.__name__}': {e}")
            raise RegistryError(f"Failed to register function '{func.__name__}': {e}") from e
        return func
    return decorator


_functions_loaded = False

def load_core_functions():
    """Load all core functions into the registry.
    
    This function imports all modules containing registered functions,
    which triggers the decorator registration process.
    """
    global _functions_loaded
    if _functions_loaded:
        return
        
    try:
        # Import modules to trigger decorator registration
        # The decorators will automatically register the functions
        import autocode.autocode.core.hello.hello_world
        import autocode.autocode.core.math.calculator
        import autocode.autocode.core.ai.ai_functions
        
        _functions_loaded = True
        logger.info(f"Loaded {len(FUNCTION_REGISTRY)} functions into registry")
        
    except ImportError as e:
        logger.error(f"Failed to load core functions: {e}")
        raise RegistryError(f"Failed to load core functions: {e}") from e

def _ensure_functions_loaded():
    """Ensure functions are loaded before accessing the registry."""
    if not _functions_loaded:
        load_core_functions()


# Public API functions
def get_function(name: str) -> Callable:
    """Get a function from the registry by name.
    
    Args:
        name: The name of the function to retrieve
        
    Returns:
        The function object
        
    Raises:
        RegistryError: If the function is not found
    """
    _ensure_functions_loaded()
    if name not in FUNCTION_REGISTRY:
        available = ", ".join(list_functions())
        raise RegistryError(f"Function '{name}' not found. Available functions: {available}")
    return FUNCTION_REGISTRY[name].func


def get_function_info(name: str) -> FunctionInfo:
    """Get complete function information from the registry.
    
    Args:
        name: The name of the function
        
    Returns:
        FunctionInfo instance with complete metadata
        
    Raises:
        RegistryError: If the function is not found
    """
    _ensure_functions_loaded()
    if name not in FUNCTION_REGISTRY:
        available = ", ".join(list_functions())
        raise RegistryError(f"Function '{name}' not found. Available functions: {available}")
    return FUNCTION_REGISTRY[name]


def get_parameters(name: str) -> List[Dict[str, Any]]:
    """Get explicit parameters for a function.
    
    Args:
        name: The name of the function
        
    Returns:
        List of parameter dictionaries with metadata
        
    Raises:
        RegistryError: If the function is not found
    """
    func_info = get_function_info(name)
    return [
        {
            "name": param.name,
            "type": param.type.__name__,
            "default": param.default,
            "required": param.required,
            "description": param.description
        }
        for param in func_info.params
    ]


def list_functions() -> List[str]:
    """Get list of all registered function names.
    
    Returns:
        Sorted list of function names
    """
    _ensure_functions_loaded()
    return sorted(FUNCTION_REGISTRY.keys())


def clear_registry():
    """Clear all functions from the registry. Useful for testing."""
    global FUNCTION_REGISTRY
    FUNCTION_REGISTRY.clear()
    logger.debug("Registry cleared")


def get_registry_stats() -> Dict[str, Any]:
    """Get statistics about the current registry state.
    
    Returns:
        Dictionary with registry statistics
    """
    _ensure_functions_loaded()
    return {
        "total_functions": len(FUNCTION_REGISTRY),
        "function_names": list_functions(),
        "http_methods_distribution": {
            method: sum(1 for info in FUNCTION_REGISTRY.values() 
                       if method in info.http_methods)
            for method in ["GET", "POST", "PUT", "DELETE", "PATCH"]
        }
    }
