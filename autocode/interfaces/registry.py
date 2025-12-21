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
from typing import Dict, Any, List, Callable, get_origin, get_args, Union, Literal
import inspect
import logging
from docstring_parser import parse

from autocode.interfaces.models import FunctionInfo, ExplicitParam, GenericOutput, FunctionSchema

# Configure logging
logger = logging.getLogger(__name__)

# Global registry - populated dynamically by decorator
FUNCTION_REGISTRY: Dict[str, FunctionInfo] = {}
_functions_loaded = False


# ============================================================================
# EXCEPTIONS
# ============================================================================

class RegistryError(Exception):
    """Custom exception for registry-related errors."""
    pass


# ============================================================================
# PUBLIC API - REGISTRATION
# ============================================================================

def register_function(http_methods: List[str] = None):
    """Decorator to automatically register a function in the global registry.
    
    This is the main entry point for registering functions. Simply decorate
    your function and it will be automatically available via CLI, API, and MCP.
    
    Args:
        http_methods: List of HTTP methods to support (default: ["GET", "POST"])
        
    Returns:
        Decorator function that registers the wrapped function
        
    Raises:
        RegistryError: If registration fails (e.g., invalid return type)
        
    Example:
        @register_function(http_methods=["GET", "POST"])
        def calculate(x: int, y: int, operation: str = "add") -> GenericOutput:
            '''Performs a mathematical operation.
            
            Args:
                x: First operand
                y: Second operand
                operation: Operation to perform (add, subtract, multiply, divide)
            '''
            result = x + y if operation == "add" else x - y
            return GenericOutput(result=result, success=True)
    """
    def decorator(func: Callable) -> Callable:
        try:
            info = _generate_function_info(func, http_methods)
            FUNCTION_REGISTRY[info.name] = info
            # Only log at DEBUG level, not INFO (reduces CLI noise)
            logger.debug(f"Registered function '{info.name}' with methods {info.http_methods}")
        except Exception as e:
            logger.error(f"Failed to register function '{func.__name__}': {e}")
            raise RegistryError(f"Failed to register function '{func.__name__}': {e}") from e
        return func
    return decorator


# ============================================================================
# PUBLIC API - REGISTRY ACCESS
# ============================================================================

def get_function_info(name: str) -> FunctionInfo:
    """Get complete function information from the registry.
    
    Args:
        name: The name of the function to retrieve
        
    Returns:
        FunctionInfo instance with complete metadata including parameters,
        description, and HTTP methods
        
    Raises:
        RegistryError: If the function is not found in the registry
        
    Example:
        >>> info = get_function_info("calculate")
        >>> print(info.description)
        'Performs a mathematical operation'
        >>> print([p.name for p in info.params])
        ['x', 'y', 'operation']
    """
    _ensure_functions_loaded()
    if name not in FUNCTION_REGISTRY:
        available = ", ".join(list_functions())
        raise RegistryError(f"Function '{name}' not found. Available functions: {available}")
    return FUNCTION_REGISTRY[name]


def get_all_function_schemas() -> Dict[str, FunctionSchema]:
    """Get serializable schemas for all registered functions.
    
    Returns:
        Dictionary mapping function names to their schemas.
    """
    _ensure_functions_loaded()
    return {
        name: info.to_schema()
        for name, info in FUNCTION_REGISTRY.items()
    }


def list_functions() -> List[str]:
    """Get list of all registered function names.
    
    Returns:
        Sorted list of function names available in the registry
        
    Example:
        >>> functions = list_functions()
        >>> print(functions)
        ['calculate', 'hello_world', 'process_text']
    """
    _ensure_functions_loaded()
    return sorted(FUNCTION_REGISTRY.keys())


def clear_registry():
    """Clear all registered functions from the registry.
    
    Primarily used for testing to ensure clean state between tests.
    Also resets the loaded flag to allow re-registration.
    
    Warning:
        This will remove all registered functions. Only use this in
        testing scenarios or when you need to completely reset the registry.
        
    Example:
        >>> clear_registry()
        >>> len(list_functions())
        0
    """
    global _functions_loaded
    FUNCTION_REGISTRY.clear()
    _functions_loaded = False


def get_function(name: str) -> Callable:
    """Get the actual callable function from the registry.
    
    Args:
        name: The name of the function to retrieve
        
    Returns:
        The callable function
        
    Raises:
        RegistryError: If the function is not found
        
    Example:
        >>> func = get_function("calculate")
        >>> result = func(x=5, y=3)
    """
    func_info = get_function_info(name)
    return func_info.func


def get_registry_stats() -> Dict[str, Any]:
    """Get statistical information about the registry.
    
    Provides insights into the current state of the registry including
    total functions, their names, and HTTP method distribution.
    
    Returns:
        Dictionary with statistics:
        - total_functions: Number of registered functions
        - function_names: List of all function names
        - http_methods_distribution: Count of functions by HTTP method
        
    Example:
        >>> stats = get_registry_stats()
        >>> print(f"Total functions: {stats['total_functions']}")
        >>> print(f"GET methods: {stats['http_methods_distribution']['GET']}")
    """
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
    """Get the file path for a module using importlib.util.find_spec.
    
    Uses the standard importlib.util approach with the full module name,
    which is more robust than using the importer's find_spec with short names.
    
    Args:
        module_name: Full module name (e.g., 'autocode.core.hello.hello_world')
        
    Returns:
        The file path to the module, or None if not found
    """
    import importlib.util
    try:
        spec = importlib.util.find_spec(module_name)
        if spec and spec.origin:
            return spec.origin
    except Exception:
        pass
    return None


def _has_register_decorator(module_path: str) -> bool:
    """Check if a module file contains the @register_function decorator using AST.
    
    Parses the module's source code with AST to accurately detect functions
    decorated with @register_function. This approach eliminates false positives
    (e.g., decorator mentioned in comments) and false negatives (e.g., unusual
    formatting or aliases).
    
    Args:
        module_path: Path to the Python module file
        
    Returns:
        True if the module contains a function with @register_function, False otherwise
    """
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
    """Autodiscover and load modules with @register_function decorator in autocode/core/.
    
    Automatically scans the autocode.core package and imports Python modules that
    contain the @register_function decorator, which populates the registry.
    
    Uses decorator detection instead of hardcoded exclusion patterns:
    - Only modules containing '@register_function' in source are imported
    - Avoids importing utility modules, models, etc. without explicit exclusions
    
    Called automatically by _ensure_functions_loaded() on first registry access.
    Safe to call multiple times (will only load once).
    
    Args:
        strict: If True, raises RegistryError when any module fails to import.
                Useful for CI/production environments. Default: False (tolerant mode).
    
    Raises:
        RegistryError: If autocode.core package cannot be imported, or if strict=True
                       and any module fails to import.
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
    """Ensure functions are loaded before accessing the registry.
    
    Internal helper that performs lazy loading of functions.
    Called by all public registry access methods.
    """
    if not _functions_loaded:
        load_core_functions()


# ============================================================================
# PRIVATE HELPERS - FUNCTION INTROSPECTION
# ============================================================================

def _generate_function_info(func: Callable, http_methods: List[str] = None) -> FunctionInfo:
    """Generate FunctionInfo from function signature and docstring.
    
    Main orchestrator that coordinates validation and extraction of function metadata.
    
    Args:
        func: The function to analyze
        http_methods: List of HTTP methods to support (default: ["GET", "POST"])
        
    Returns:
        FunctionInfo instance with inferred parameters and description
        
    Raises:
        ValueError: If http_methods contains invalid values
        RegistryError: If return type is not GenericOutput or a subclass
    """
    if http_methods is None:
        http_methods = ["GET", "POST"]
    
    http_methods = _validate_http_methods(http_methods)
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
        http_methods=http_methods
    )


def _validate_http_methods(http_methods: List[str]) -> List[str]:
    """Validate HTTP methods list.
    
    Args:
        http_methods: List of HTTP methods to validate
        
    Returns:
        Validated list of HTTP methods (unchanged if valid)
        
    Raises:
        ValueError: If any method is not in the valid set
    """
    valid_methods = {"GET", "POST", "PUT", "DELETE", "PATCH"}
    if not all(method.upper() in valid_methods for method in http_methods):
        raise ValueError(f"Invalid HTTP methods. Must be one of: {valid_methods}")
    return http_methods


def _validate_return_type(func: Callable) -> None:
    """Validate that function returns GenericOutput or a subclass.
    
    Ensures type safety for all registered functions by requiring a standardized
    output format. Handles Union types (e.g., GenericOutput | None).
    
    Args:
        func: The function to validate
        
    Raises:
        RegistryError: If return type is invalid or missing
    """
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


def _extract_param_info(param: inspect.Parameter, param_name: str, param_docs: Dict[str, str]) -> ExplicitParam:
    """Extract parameter information from function signature.
    
    Handles type inference, default values, and special types like Literal
    (which provides choices for parameters).
    
    Args:
        param: Parameter object from inspect.signature
        param_name: Name of the parameter
        param_docs: Dictionary mapping parameter names to descriptions from docstring
        
    Returns:
        ExplicitParam instance with complete parameter metadata
    """
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
