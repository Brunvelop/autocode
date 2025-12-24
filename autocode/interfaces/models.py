"""
Shared Pydantic models for all interfaces (CLI, API, MCP).
These models define the input/output contracts for functions registered in the registry.

Example usage:
    param = ExplicitParam(name="x", type=int, required=True, description="An integer input")
    func_info = FunctionInfo(name="add", func=my_func, description="Adds two numbers")
"""

from pydantic import BaseModel, Field, ConfigDict
from typing import Any, Callable, Dict, List, Literal, Optional, Type, Union, get_origin, get_args


# ============================================================================
# SERIALIZATION SCHEMAS (API Contract)
# ============================================================================

class ParamSchema(BaseModel):
    """Schema serializable para un parámetro (API contract)."""
    name: str = Field(description="Parameter name")
    type: str = Field(description="Parameter type name")
    default: Optional[Any] = Field(default=None, description="Default value")
    required: bool = Field(description="Whether the parameter is required")
    description: str = Field(description="Parameter description")
    choices: Optional[List[Any]] = Field(default=None, description="Available choices")


class FunctionSchema(BaseModel):
    """Schema serializable para una función (API contract)."""
    name: str = Field(description="Function name")
    description: str = Field(description="Function description")
    http_methods: List[str] = Field(description="Supported HTTP methods")
    parameters: List[ParamSchema] = Field(description="Function parameters")


class FunctionDetailsResponse(BaseModel):
    """Respuesta del endpoint /functions/details."""
    functions: Dict[str, FunctionSchema] = Field(description="Map of function names to schemas")


# ============================================================================
# RUNTIME MODELS (Internal Registry)
# ============================================================================

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

    def to_schema(self) -> ParamSchema:
        """Convierte a schema serializable."""
        return ParamSchema(
            name=self.name,
            type=self._serialize_type(self.type),
            default=self.default,
            required=self.required,
            description=self.description,
            choices=self.choices
        )

    def _serialize_type(self, t: Any) -> str:
        """Serializa tipo Python a string, incluyendo genéricos.
        
        Soporta:
        - Tipos básicos: int, str, float, bool, list, dict, tuple
        - Tipos genéricos: List[str], Dict[str, int], Tuple[int, str]
        - Optional: Optional[str] -> "str?"
        - Union: Union[str, int] -> "str | int"
        - Literal: Literal["a", "b"] -> "Literal['a', 'b']"
        - Tipos anidados: List[Dict[str, int]] -> "list[dict[str, int]]"
        """
        # Mapping de tipos comunes a nombres amigables para frontend
        TYPE_MAP = {
            int: "int",
            float: "float",
            str: "str",
            bool: "bool",
            list: "list",
            dict: "dict",
            tuple: "tuple",
        }
        
        # Si es uno de los tipos básicos mapeados
        if t in TYPE_MAP:
            return TYPE_MAP[t]
        
        # Tipos genéricos (List[str], Dict[str, int], Optional[str], etc.)
        origin = get_origin(t)
        if origin is not None:
            args = get_args(t)
            
            # Optional[X] es Union[X, None] - detectar y convertir a "X?"
            if origin is Union:
                non_none_args = [a for a in args if a is not type(None)]
                # Si es Optional (Union con un solo tipo + None)
                if len(non_none_args) == 1 and type(None) in args:
                    return f"{self._serialize_type(non_none_args[0])}?"
                # Union normal: "str | int | float"
                return " | ".join(self._serialize_type(a) for a in args)
            
            # Literal['a', 'b'] -> "Literal['a', 'b']"
            if origin is Literal:
                args_str = ", ".join(repr(a) for a in args)
                return f"Literal[{args_str}]"
            
            # List[X], Dict[K, V], Tuple[X, Y], etc.
            origin_name = TYPE_MAP.get(origin, getattr(origin, '__name__', str(origin)).lower())
            if args:
                args_str = ", ".join(self._serialize_type(a) for a in args)
                return f"{origin_name}[{args_str}]"
            return origin_name
            
        # Si tiene __name__ (clases, tipos nativos)
        if hasattr(t, '__name__'):
            return TYPE_MAP.get(t, t.__name__)
            
        # Fallback a string representation
        return str(t)


# Composite models (depend on base models)
class FunctionInfo(BaseModel):
    """Function information for the registry with explicit parameters."""
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    name: str
    func: Callable
    description: str
    params: List[ExplicitParam] = Field(default_factory=list, description="Explicit parameter definitions")
    http_methods: List[str] = Field(default_factory=lambda: ["GET", "POST"])
    # Return type annotation (GenericOutput o subclase). Útil para tipar el response_model en FastAPI.
    return_type: Optional[Type[BaseModel]] = Field(default=None, description="Declared return type annotation")

    def to_schema(self) -> FunctionSchema:
        """Convierte a schema serializable."""
        return FunctionSchema(
            name=self.name,
            description=self.description,
            http_methods=self.http_methods,
            parameters=[p.to_schema() for p in self.params]
        )


# Generic models (fallback for functions without specific models)
class ExplicitInput(BaseModel):
    """Generic input model with explicit parameter handling."""
    params: Dict[str, Any] = Field(default_factory=dict, description="Function parameters")


class GenericOutput(BaseModel):
    """Generic output model for simple functions."""
    result: Any = Field(description="Function result")
    success: bool = Field(default=True, description="Whether the operation was successful")
    message: Optional[str] = Field(default=None, description="Optional message")
