"""
Autocode domain models.
"""
from pydantic import BaseModel, Field
from typing import Any

__all__ = [
    "GenericOutput",
]


# --- Autocode domain model ---

class GenericOutput(BaseModel):
    """Generic output model for simple functions."""
    result: Any = Field(description="Function result")
    success: bool = Field(default=True, description="Whether the operation was successful")
    message: str | None = Field(default=None, description="Optional message")
