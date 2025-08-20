"""
Central registry for all functions exposed via interfaces.
This registry enables automatic generation of CLI commands, API endpoints, and MCP tools.
Uses inference to automatically derive parameters and models from function signatures.
"""
from typing import Dict, Any, List, Callable, Type
from autocode.autocode.core.hello.hello_world import hello_world
from autocode.autocode.core.math.calculator import add, multiply
from autocode.autocode.interfaces.models import FunctionInfo
from autocode.autocode.interfaces.utils import InferenceUtils
from pydantic import BaseModel


# Simplified registry - only essential information
FUNCTION_REGISTRY: Dict[str, FunctionInfo] = {
    "hello": FunctionInfo(
        name="hello",
        func=hello_world,
        description="Generate a hello greeting for the given name",
        http_methods=["GET", "POST"]
    ),
    "add": FunctionInfo(
        name="add",
        func=add,
        description="Add two numbers and return the sum",
        http_methods=["GET", "POST"]
    ),
    "multiply": FunctionInfo(
        name="multiply",
        func=multiply,
        description="Multiply two numbers and return the product",
        http_methods=["GET", "POST"]
    )
}


# Cache for inferred data to avoid recomputing
_parameter_cache: Dict[str, List[Dict[str, Any]]] = {}
_input_model_cache: Dict[str, Type[BaseModel]] = {}
_output_model_cache: Dict[str, Type[BaseModel]] = {}


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
    """Get inferred parameters for a function."""
    if name not in _parameter_cache:
        func_info = get_function_info(name)
        _parameter_cache[name] = InferenceUtils.infer_parameters(func_info.func)
    return _parameter_cache[name]


def get_input_model(name: str) -> Type[BaseModel]:
    """Get inferred input model for a function."""
    if name not in _input_model_cache:
        func_info = get_function_info(name)
        _input_model_cache[name] = InferenceUtils.infer_input_model(func_info.func)
    return _input_model_cache[name]


def get_output_model(name: str) -> Type[BaseModel]:
    """Get inferred output model for a function."""
    if name not in _output_model_cache:
        func_info = get_function_info(name)
        _output_model_cache[name] = InferenceUtils.infer_output_model(func_info.func)
    return _output_model_cache[name]


def list_functions() -> List[str]:
    """Get list of all registered function names."""
    return list(FUNCTION_REGISTRY.keys())


def clear_cache():
    """Clear all inference caches. Useful for testing or dynamic updates."""
    _parameter_cache.clear()
    _input_model_cache.clear()
    _output_model_cache.clear()
