"""
Modelos específicos para el módulo AI.

Este módulo contiene modelos Pydantic especializados para operaciones de AI,
extendiendo los modelos genéricos de interfaces para añadir campos específicos
de DSPy y otras funcionalidades de AI.
"""

import json
from pydantic import BaseModel, Field
from typing import Any, Dict, List, Optional, Union
from autocode.core.models import GenericOutput


class DspyOutput(GenericOutput):
    """
    Output extendido para generaciones DSPy con campos específicos.
    
    Hereda de GenericOutput para mantener compatibilidad con el resto del código,
    añadiendo campos específicos de DSPy como reasoning, completions y observations.
    """
    result: Any = Field(
        description="Outputs principales de DSPy (puede ser dict con múltiples campos, str para outputs simples, u otros tipos según la signature)"
    )
    reasoning: Optional[str] = Field(
        default=None, 
        description="Razonamiento paso a paso (de ChainOfThought/ReAct)"
    )
    completions: Optional[List[str]] = Field(
        default=None, 
        description="Múltiples completions si aplica (e.g., de Predict con n>1)"
    )
    trajectory: Optional[Union[Dict[str, Any], List[Dict[str, Any]]]] = Field(
        default=None,
        description="Trayectoria completa de ReAct u otros módulos similares (thoughts, tool_names, tool_args, observations)"
    )
    history: Optional[List[Dict[str, Any]]] = Field(
        default=None,
        description="Historial completo de llamadas al LM con metadata (prompt, response, usage, cost, etc.)"
    )
    
    def model_dump(self, **kwargs) -> Dict[str, Any]:
        """
        Custom model_dump que serializa recursivamente campos complejos.
        
        Maneja objetos que pueden no ser directamente serializables por Pydantic,
        como ModelResponse con mocks de cache, objetos con __dict__, etc.
        Convierte todo a tipos básicos de Python (dict, list, str, int, etc.).
        
        Returns:
            Dict con todos los campos serializados de forma segura para JSON
        """
        # Normalizar trayectoria si es necesario (limpieza de formato plano de DSPy)
        normalized_trajectory = DspyOutput.normalize_trajectory(self.trajectory)

        # Construir el dict manualmente para evitar problemas con super().model_dump()
        # cuando hay objetos no serializables
        data = {
            'success': self.success,
            'result': DspyOutput.serialize_value(self.result),
            'message': self.message,
            'reasoning': self.reasoning,
            'completions': DspyOutput.serialize_value(self.completions),
            'trajectory': DspyOutput.serialize_value(normalized_trajectory),
            'history': DspyOutput.serialize_value(self.history)
        }
        
        return data
    
    @staticmethod
    def normalize_trajectory(trajectory: Any) -> Any:
        """
        Detecta y normaliza trayectorias planas de DSPy (thought_0, tool_0...) 
        a una lista estructurada de pasos.
        """
        if not isinstance(trajectory, dict):
            return trajectory

        # Detectar claves con sufijo numérico (ej: thought_0)
        import re
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
                
                # Normalizar nombres de campos
                if field_name == 'tool_args':
                    # A veces args vienen como string JSON, otras como dict
                    steps[step_idx]['tool_args'] = value
                elif field_name in ['tool', 'tool_name']:
                    steps[step_idx]['tool_name'] = value
                else:
                    steps[step_idx][field_name] = value

        if not has_indexed_keys:
            return trajectory

        # Convertir mapa de pasos a lista ordenada
        ordered_steps = []
        for idx in sorted(steps.keys()):
            ordered_steps.append(steps[idx])
            
        return ordered_steps

    @staticmethod
    def _serialize_complex_object(value: Any) -> Any:
        """
        Serializa un objeto complejo (Pydantic, __dict__, o fallback JSON/str).
        
        Gestiona la cascada de intentos para objetos que no son tipos básicos,
        listas ni dicts: model_dump → __dict__ → json → str.
        
        Args:
            value: Objeto complejo a serializar
            
        Returns:
            Valor serializado a tipos básicos
        """
        # Si tiene método model_dump (Pydantic), usarlo
        if hasattr(value, 'model_dump') and callable(getattr(value, 'model_dump')):
            try:
                return DspyOutput.serialize_value(value.model_dump())
            except Exception:
                pass

        # Si tiene __dict__, convertir a dict saltando atributos privados
        if hasattr(value, '__dict__'):
            try:
                obj_dict = {}
                for key, val in value.__dict__.items():
                    if not key.startswith('_'):
                        obj_dict[key] = DspyOutput.serialize_value(val)
                return obj_dict
            except Exception:
                pass

        # Como último recurso, usar json.dumps/loads para forzar serialización
        try:
            return json.loads(json.dumps(value, default=str))
        except (TypeError, ValueError):
            return str(value)

    @staticmethod
    def serialize_value(value: Any) -> Any:
        """
        Serializa recursivamente un valor a tipos básicos de Python.
        
        Actúa como dispatcher limpio: delega casos complejos a
        _serialize_complex_object().
        
        Args:
            value: Valor a serializar (puede ser dict, list, object, etc.)
            
        Returns:
            Valor serializado a tipos básicos (dict, list, str, int, float, bool, None)
        """
        if value is None:
            return None
        if isinstance(value, (str, int, float, bool)):
            return value
        if isinstance(value, list):
            return [DspyOutput.serialize_value(item) for item in value]
        if isinstance(value, dict):
            return {key: DspyOutput.serialize_value(val) for key, val in value.items()}
        return DspyOutput._serialize_complex_object(value)


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
    Resultado directo de chat sin envelope GenericOutput.

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
