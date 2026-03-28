"""
Modelos específicos para el módulo AI.

Este módulo contiene modelos Pydantic especializados para operaciones de AI,
más funciones de serialización standalone que antes vivían en DspyOutput.
"""

import json
import re
from pydantic import BaseModel, Field
from typing import Any, Dict, List, Optional, Union


# ============================================================================
# SERIALIZATION UTILITIES (standalone, previously DspyOutput static methods)
# ============================================================================


def normalize_trajectory(trajectory: Any) -> Any:
    """
    Detecta y normaliza trayectorias planas de DSPy (thought_0, tool_0...)
    a una lista estructurada de pasos.

    Args:
        trajectory: Trayectoria raw de DSPy (dict, list u otro tipo).

    Returns:
        Lista de pasos si era dict plano con índices, o el valor original en otro caso.
    """
    if not isinstance(trajectory, dict):
        return trajectory

    steps = {}
    has_indexed_keys = False

    for key, value in trajectory.items():
        match = re.search(r'^(.*)_(\d+)$', key)
        if match:
            has_indexed_keys = True
            field_name = match.group(1)
            step_idx = int(match.group(2))

            if step_idx not in steps:
                steps[step_idx] = {}

            if field_name in ['tool', 'tool_name']:
                steps[step_idx]['tool_name'] = value
            else:
                steps[step_idx][field_name] = value

    if not has_indexed_keys:
        return trajectory

    return [steps[idx] for idx in sorted(steps.keys())]


def _serialize_complex_object(value: Any) -> Any:
    """
    Serializa un objeto complejo (Pydantic, __dict__, o fallback JSON/str).

    Gestiona la cascada de intentos para objetos que no son tipos básicos,
    listas ni dicts: model_dump → __dict__ → json → str.

    Args:
        value: Objeto complejo a serializar.

    Returns:
        Valor serializado a tipos básicos.
    """
    if hasattr(value, 'model_dump') and callable(getattr(value, 'model_dump')):
        try:
            return serialize_value(value.model_dump())
        except Exception:
            pass

    if hasattr(value, '__dict__'):
        try:
            obj_dict = {}
            for key, val in value.__dict__.items():
                if not key.startswith('_'):
                    obj_dict[key] = serialize_value(val)
            return obj_dict
        except Exception:
            pass

    try:
        return json.loads(json.dumps(value, default=str))
    except (TypeError, ValueError):
        return str(value)


def serialize_value(value: Any) -> Any:
    """
    Serializa recursivamente un valor a tipos básicos de Python.

    Args:
        value: Valor a serializar (puede ser dict, list, object, etc.).

    Returns:
        Valor serializado a tipos básicos (dict, list, str, int, float, bool, None).
    """
    if value is None:
        return None
    if isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, list):
        return [serialize_value(item) for item in value]
    if isinstance(value, dict):
        return {key: serialize_value(val) for key, val in value.items()}
    return _serialize_complex_object(value)


# ============================================================================
# DOMAIN MODELS
# ============================================================================


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
