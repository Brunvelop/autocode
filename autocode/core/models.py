"""
Autocode domain models.

Framework models (ParamSchema, FunctionInfo, FunctionSchema, etc.) are provided by refract
and re-exported here for backward compatibility.
GenericOutput is autocode's own domain model.
"""
from pydantic import BaseModel, Field
from typing import Any

# Re-export framework models from refract (backward compatibility)
from refract import ParamSchema, FunctionInfo, FunctionSchema
from refract.models import HttpMethod, Interface, DEFAULT_HTTP_METHODS, DEFAULT_INTERFACES

__all__ = [
    "ParamSchema",
    "FunctionInfo",
    "FunctionSchema",
    "HttpMethod",
    "Interface",
    "DEFAULT_HTTP_METHODS",
    "DEFAULT_INTERFACES",
    "GenericOutput",
]


# --- Autocode domain model ---

class GenericOutput(BaseModel):
    """Generic output model for simple functions."""
    result: Any = Field(description="Function result")
    success: bool = Field(default=True, description="Whether the operation was successful")
    message: str | None = Field(default=None, description="Optional message")
