"""
Shared Pydantic models for all interfaces (CLI, API, MCP).
These models define the input/output contracts for functions registered in the registry.

Example usage:
    param = ExplicitParam(name="x", type=int, required=True, description="An integer input")
    func_info = FunctionInfo(name="add", func=my_func, description="Adds two numbers")
"""

from pydantic import BaseModel, Field, ConfigDict
from typing import Any, Callable, Dict, List, Optional, Type


# Base models (atomic components)
class ExplicitParam(BaseModel):
    """Model for explicit parameter definitions in the registry."""
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    name: str = Field(description="Parameter name")
    type: Any = Field(description="Parameter type (accepts types and generic types)")
    default: Optional[Any] = Field(default=None, description="Default value")
    required: bool = Field(description="Whether the parameter is required")
    description: str = Field(description="Parameter description")
    choices: Optional[List[Any]] = Field(default=None, description="Available choices for Literal types")


# Composite models (depend on base models)
class FunctionInfo(BaseModel):
    """Function information for the registry with explicit parameters."""
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    name: str
    func: Callable
    description: str
    params: List[ExplicitParam] = Field(default_factory=list, description="Explicit parameter definitions")
    http_methods: List[str] = Field(default_factory=lambda: ["GET", "POST"])


# Generic models (fallback for functions without specific models)
class ExplicitInput(BaseModel):
    """Generic input model with explicit parameter handling."""
    params: Dict[str, Any] = Field(default_factory=dict, description="Function parameters")


class GenericOutput(BaseModel):
    """Generic output model for simple functions."""
    result: Any = Field(description="Function result")
    success: bool = Field(default=True, description="Whether the operation was successful")
    message: Optional[str] = Field(default=None, description="Optional message")


class DspyOutput(GenericOutput):
    """
    Output extendido para generaciones DSPy con campos específicos.
    
    Hereda de GenericOutput para mantener compatibilidad con el resto del código,
    añadiendo campos específicos de DSPy como reasoning, completions y observations.
    """
    result: Dict[str, Any] = Field(
        description="Outputs principales de DSPy (e.g., {'python_code': '...', 'reasoning': '...'})"
    )
    reasoning: Optional[str] = Field(
        default=None, 
        description="Razonamiento paso a paso (de ChainOfThought/ReAct)"
    )
    completions: Optional[List[str]] = Field(
        default=None, 
        description="Múltiples completions si aplica (e.g., de Predict con n>1)"
    )
    observations: Optional[List[str]] = Field(
        default=None, 
        description="Observaciones de tools en ReAct"
    )
    history: Optional[List[Dict[str, Any]]] = Field(
        default=None,
        description="Historial completo de llamadas al LM con metadata (prompt, response, usage, cost, etc.)"
    )
