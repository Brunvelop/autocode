"""
Modelos específicos para el módulo AI.

Este módulo contiene modelos Pydantic especializados para operaciones de AI,
extendiendo los modelos genéricos de interfaces para añadir campos específicos
de DSPy y otras funcionalidades de AI.
"""

from pydantic import Field
from typing import Any, Dict, List, Optional
from autocode.autocode.interfaces.models import GenericOutput


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
