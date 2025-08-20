"""
Central registry for all functions exposed via interfaces.
This registry enables automatic generation of CLI commands, API endpoints, and MCP tools.
Uses automatic parameter inference from function signatures and docstrings.
"""
from typing import Dict, Any, List, Callable
import inspect
from docstring_parser import parse
from autocode.autocode.core.hello.hello_world import hello_world
from autocode.autocode.core.math.calculator import add, multiply
from autocode.autocode.interfaces.models import FunctionInfo, ExplicitParam, ExplicitInput, GenericOutput


def generate_function_info(func: Callable, http_methods: List[str] = None) -> FunctionInfo:
    """
    Generate FunctionInfo automatically from function signature and docstring.
    
    Args:
        func: The function to analyze
        http_methods: List of HTTP methods to support (default: ["GET", "POST"])
        
    Returns:
        FunctionInfo instance with inferred parameters and description
    """
    if http_methods is None:
        http_methods = ["GET", "POST"]
    
    # Get function signature
    sig = inspect.signature(func)
    
    # Parse docstring
    doc = parse(inspect.getdoc(func) or "")
    param_docs = {p.arg_name: p.description for p in doc.params}
    
    # Generate parameters
    params = []
    for name, param in sig.parameters.items():
        # Get parameter type from annotation, default to Any if not specified
        param_type = param.annotation if param.annotation != inspect.Parameter.empty else Any
        
        # Get default value
        default = param.default if param.default != inspect.Parameter.empty else None
        
        # Determine if required (no default and not VAR_POSITIONAL/VAR_KEYWORD)
        required = (
            default is None and 
            param.kind not in (inspect.Parameter.VAR_POSITIONAL, inspect.Parameter.VAR_KEYWORD)
        )
        
        # Get description from docstring or use default
        description = param_docs.get(name, f"Parameter {name}")
        
        params.append(ExplicitParam(
            name=name,
            type=param_type,
            default=default,
            required=required,
            description=description
        ))
    
    return FunctionInfo(
        name=func.__name__,
        func=func,
        description=doc.short_description or f"Execute {func.__name__} function",
        params=params,
        http_methods=http_methods
    )


# Registry using automatic function inference
FUNCTION_REGISTRY: Dict[str, FunctionInfo] = {
    "hello": generate_function_info(hello_world),
    "add": generate_function_info(add),
    "multiply": generate_function_info(multiply),
}


def get_function(name: str) -> Callable:
    """Get a function from the registry by name."""
    if name not in FUNCTION_REGISTRY:
        raise KeyError(f"Function '{name}' not found in registry")
    return FUNCTION_REGISTRY[name].func


def get_function_info(name: str) -> FunctionInfo:
    """Get complete function information from the registry."""
    if name not in FUNCTION_REGISTRY:
        raise KeyError(f"Function '{name}' not found in registry")
    return FUNCTION_REGISTRY[name]


def get_parameters(name: str) -> List[Dict[str, Any]]:
    """Get explicit parameters for a function."""
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
    """Get list of all registered function names."""
    return list(FUNCTION_REGISTRY.keys())
