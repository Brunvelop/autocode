"""
Shared Pydantic models for all interfaces (CLI, API, MCP).
These models define the input/output contracts for functions registered in the registry.
"""
from pydantic import BaseModel, Field
from typing import Any, Dict, List, Optional, Type, Callable
from abc import ABC


class BaseFunctionInput(BaseModel, ABC):
    """Base class for all function input models."""
    pass


class BaseFunctionOutput(BaseModel, ABC):
    """Base class for all function output models."""
    pass


class FunctionInfo(BaseModel):
    """Simplified function information for the registry with inference support."""
    name: str
    func: Callable
    description: str
    http_methods: List[str] = Field(default_factory=lambda: ["GET", "POST"])
    
    class Config:
        arbitrary_types_allowed = True  # Allow Callable type


# Generic models for functions without specific models
class GenericInput(BaseFunctionInput):
    """Generic input model for simple functions."""
    data: Dict[str, Any] = Field(default_factory=dict, description="Generic input data")


class GenericOutput(BaseFunctionOutput):
    """Generic output model for simple functions."""
    result: Any = Field(description="Function result")
    success: bool = Field(default=True, description="Whether the operation was successful")
    message: Optional[str] = Field(default=None, description="Optional message")
