"""
Modelos específicos para el módulo AI.

Este módulo contiene modelos Pydantic especializados para operaciones de AI,
extendiendo los modelos genéricos de interfaces para añadir campos específicos
de DSPy y otras funcionalidades de AI.
"""

import json
from pydantic import Field
from typing import Any, Dict, List, Optional
from autocode.interfaces.models import GenericOutput


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
    trajectory: Optional[Dict[str, Any]] = Field(
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
        # Construir el dict manualmente para evitar problemas con super().model_dump()
        # cuando hay objetos no serializables
        data = {
            'success': self.success,
            'result': self._serialize_value(self.result),
            'message': self.message,
            'reasoning': self.reasoning,
            'completions': self._serialize_value(self.completions),
            'trajectory': self._serialize_value(self.trajectory),
            'history': self._serialize_value(self.history)
        }
        
        return data
    
    def _serialize_value(self, value: Any) -> Any:
        """
        Serializa recursivamente un valor a tipos básicos de Python.
        
        Args:
            value: Valor a serializar (puede ser dict, list, object, etc.)
            
        Returns:
            Valor serializado a tipos básicos (dict, list, str, int, float, bool, None)
        """
        if value is None:
            return None
        
        # Si ya es un tipo básico, retornar directamente
        if isinstance(value, (str, int, float, bool)):
            return value
        
        # Si es una lista, serializar cada elemento
        if isinstance(value, list):
            return [self._serialize_value(item) for item in value]
        
        # Si es un dict, serializar cada valor
        if isinstance(value, dict):
            return {key: self._serialize_value(val) for key, val in value.items()}
        
        # Si tiene método model_dump (Pydantic), usarlo
        if hasattr(value, 'model_dump') and callable(getattr(value, 'model_dump')):
            try:
                return self._serialize_value(value.model_dump())
            except Exception:
                # Si falla model_dump, intentar con __dict__
                pass
        
        # Si tiene __dict__, convertir a dict
        if hasattr(value, '__dict__'):
            try:
                obj_dict = {}
                for key, val in value.__dict__.items():
                    # Saltar atributos privados
                    if not key.startswith('_'):
                        obj_dict[key] = self._serialize_value(val)
                return obj_dict
            except Exception:
                # Si falla, intentar convertir a string
                pass
        
        # Como último recurso, usar json.dumps/loads para forzar serialización
        try:
            # Esto fallará si el objeto no es serializable, en cuyo caso retornamos str
            return json.loads(json.dumps(value, default=str))
        except (TypeError, ValueError):
            # Si todo falla, convertir a string
            return str(value)
