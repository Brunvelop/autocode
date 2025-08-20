"""
Shared Pydantic models for all interfaces (CLI, API, MCP).
These models define the input/output contracts for functions registered in the registry.
"""
from pydantic import BaseModel, Field
from typing import Any, Dict, List, Optional, Type, Callable, Union


class ExplicitParam(BaseModel):
    """Model for explicit parameter definitions in the registry."""
    name: str = Field(description="Parameter name")
    type: Type = Field(description="Parameter type")
    default: Optional[Any] = Field(default=None, description="Default value")
    required: bool = Field(description="Whether the parameter is required")
    description: str = Field(description="Parameter description")
    
    class Config:
        arbitrary_types_allowed = True  # Allow Type type


class FunctionInfo(BaseModel):
    """Function information for the registry with explicit parameters."""
    name: str
    func: Callable
    description: str
    params: List[ExplicitParam] = Field(default_factory=list, description="Explicit parameter definitions")
    http_methods: List[str] = Field(default_factory=lambda: ["GET", "POST"])
    
    class Config:
        arbitrary_types_allowed = True  # Allow Callable type


# Generic models for functions without specific models
class ExplicitInput(BaseModel):
    """Generic input model with explicit parameter handling."""
    params: Dict[str, Any] = Field(default_factory=dict, description="Function parameters")


class GenericOutput(BaseModel):
    """Generic output model for simple functions."""
    result: Any = Field(description="Function result")
    success: bool = Field(default=True, description="Whether the operation was successful")
    message: Optional[str] = Field(default=None, description="Optional message")
