"""
Modelos específicos para el módulo AI.

Este módulo contiene modelos Pydantic especializados para operaciones de AI.
"""

from pydantic import BaseModel, Field
from typing import Any, Dict, List, Optional, Union


class ContextUsage(BaseModel):
    """Domain model for context window usage."""
    current: int = Field(0, description="Tokens actuales en el contexto")
    max: int = Field(0, description="Tokens máximos del modelo")
    percentage: float = Field(0.0, description="Porcentaje de uso del contexto")


class ChatConfig(BaseModel):
    """Domain model for chat configuration."""
    module_kwargs_schemas: dict = Field(default_factory=dict, description="Esquemas de parámetros por tipo de módulo")
    available_tools: list = Field(default_factory=list, description="Herramientas MCP disponibles")
    models: list = Field(default_factory=list, description="Modelos disponibles con metadata")


class ChatResult(BaseModel):
    """
    Resultado directo de chat sin envelope.

    Retorno directo del dominio: cada campo es un campo real del resultado,
    sin wrappers success/result/message. Los errores se comunican via
    HTTPException → HTTP 4xx/5xx.
    """
    response: str = Field("", description="Respuesta principal del asistente")
    reasoning: Optional[str] = Field(
        default=None,
        description="Razonamiento paso a paso (de ChainOfThought/ReAct)"
    )
    trajectory: Optional[Union[Dict[str, Any], List[Dict[str, Any]]]] = Field(
        default=None,
        description="Trayectoria completa de ReAct (thoughts, tool_names, tool_args, observations)"
    )
    history: Optional[List[Dict[str, Any]]] = Field(
        default=None,
        description="Historial completo de llamadas al LM con metadata"
    )
    completions: Optional[List[str]] = Field(
        default=None,
        description="Múltiples completions si aplica (e.g., de Predict con n>1)"
    )
