"""
DSPy utilities for AI operations.

This module provides reusable utilities for working with DSPy,
including setup functions and generic generators.
"""
import os
from typing import Any, Dict, Literal, Type

import dspy
from autocode.autocode.core.ai.models import DspyOutput


# Available models for inference
ModelType = Literal[
    'openrouter/openai/gpt-4o',
    'openrouter/x-ai/grok-4',
    'openrouter/x-ai/grok-code-fast-1',
    'openrouter/x-ai/grok-4-fast',
    'openrouter/anthropic/claude-sonnet-4.5',
    'openrouter/openai/gpt-oss-20b',
    'openrouter/openai/gpt-5',
    'openrouter/openai/gpt-5-codex'
]


# Available DSPy modules
ModuleType = Literal[
    'Predict',
    'ChainOfThought',
    'ProgramOfThought',
    'ReAct',
    'MultiChainComparison'
]


# Mapping from module type strings to DSPy module classes
MODULE_MAP = {
    'Predict': dspy.Predict,
    'ChainOfThought': dspy.ChainOfThought,
    'ProgramOfThought': dspy.ProgramOfThought,
    'ReAct': dspy.ReAct,
    'MultiChainComparison': dspy.MultiChainComparison
}


def generate_with_dspy(
    signature_class: Type[dspy.Signature],
    inputs: Dict[str, Any],
    model: ModelType = 'openrouter/openai/gpt-4o',
    module_type: ModuleType = 'ChainOfThought',
    module_kwargs: Dict[str, Any] = None,
    max_tokens: int = 16000,
    temperature: float = 0.7,
    **lm_kwargs
) -> DspyOutput:
    """
    Generador genérico que ejecuta cualquier signature de DSPy con el módulo seleccionado.
    
    Esta función proporciona una interfaz unificada para ejecutar cualquier
    signature de DSPy con diferentes módulos (Predict, ChainOfThought, ReAct, etc.).
    Retorna siempre un DspyOutput con los campos principales y metadata DSPy.
    
    Args:
        signature_class: La clase de signature de DSPy a utilizar
        inputs: Diccionario con los parámetros de entrada para la signature
        model: Modelo de inferencia a utilizar
        module_type: Tipo de módulo DSPy a usar (Predict, ChainOfThought, etc.)
        module_kwargs: Parámetros adicionales específicos del módulo 
            (ej: tools para ReAct)
        max_tokens: Número máximo de tokens a generar (default: 16000)
        temperature: Temperature para la generación (default: 0.7)
        **lm_kwargs: Parámetros adicionales para dspy.LM (stop, cache, etc.)
        
    Returns:
        DspyOutput con todos los campos de output de la signature, más metadata DSPy
        (reasoning, completions, observations cuando apliquen).
        
    Raises:
        ValueError: Si la API key no está configurada o module_type es inválido
        
    Examples:
        >>> # Ejemplo básico con un solo output
        >>> result = generate_with_dspy(
        ...     CodeGenerationSignature,
        ...     {"design_text": "Create a hello world function"}
        ... )
        >>> print(result.result['python_code'])
        >>> print(result.success)  # True
        
        >>> # Ejemplo con ChainOfThought (incluye reasoning)
        >>> result = generate_with_dspy(
        ...     QASignature,
        ...     {"question": "What is Python?"},
        ...     module_type='ChainOfThought'
        ... )
        >>> print(result.result['answer'])
        >>> print(result.reasoning)  # Razonamiento paso a paso
    """
    # Inicializar module_kwargs si no se proporciona
    if module_kwargs is None:
        module_kwargs = {}
    
    # Validar module_type antes de configurar el LM
    if module_type not in MODULE_MAP:
        valid_options = list(MODULE_MAP.keys())
        return DspyOutput(
            success=False,
            result={},
            message=f"Invalid module_type '{module_type}'. Valid options: {valid_options}"
        )
    
    # Configurar el Language Model
    try:
        lm = get_dspy_lm(
            model, 
            max_tokens=max_tokens, 
            temperature=temperature, 
            **lm_kwargs
        )
    except ValueError as e:
        return DspyOutput(
            success=False,
            result={},
            message=f"Error configurando LM: {str(e)}"
        )
    
    # Usar context en lugar de configure para evitar conflictos en async tasks
    try:
        with dspy.context(lm=lm):
            # Crear el generador con el módulo seleccionado
            module_class = MODULE_MAP[module_type]
            generator = module_class(signature_class, **module_kwargs)
            
            # Ejecutar la generación con los inputs proporcionados
            response = generator(**inputs)
    except Exception as e:
        return DspyOutput(
            success=False,
            result={},
            message=f"Error en generación DSPy: {str(e)}"
        )
    
    # Extraer output fields de la signature
    output_fields = [
        name for name, field in signature_class.model_fields.items()
        if field.json_schema_extra.get('__dspy_field_type') == 'output'
    ]
    
    # Construir dict con outputs principales
    dspy_fields = {field: getattr(response, field, None) for field in output_fields}
    
    # Fallback si no hay outputs explícitos
    if not dspy_fields:
        dspy_fields = {
            attr: getattr(response, attr) 
            for attr in dir(response)
            if not attr.startswith('_') and not callable(getattr(response, attr))
        }
    
    # Verificar si se generó algo
    if not dspy_fields:
        return DspyOutput(
            success=False,
            result={},
            message="No se encontraron campos de output en la response de DSPy"
        )
    
    # Extraer y procesar campos DSPy comunes (si existen)
    # Convertir objetos Prediction a strings para evitar errores de validación Pydantic
    reasoning = getattr(response, 'reasoning', None)
    completions_raw = getattr(response, 'completions', None)
    observations_raw = getattr(response, 'observations', None)
    
    # Procesar completions: convertir Prediction objects a strings
    completions = None
    if completions_raw is not None:
        if isinstance(completions_raw, list):
            completions = [
                str(comp) if hasattr(comp, '__dict__') else comp 
                for comp in completions_raw
            ]
        else:
            completions = [str(completions_raw)]
    
    # Procesar observations: convertir a strings si es necesario
    observations = None
    if observations_raw is not None:
        if isinstance(observations_raw, list):
            observations = [
                str(obs) if hasattr(obs, '__dict__') else obs 
                for obs in observations_raw
            ]
        else:
            observations = [str(observations_raw)]
    
    # Capturar historial del LM para metadata adicional
    history = None
    if hasattr(lm, 'history') and lm.history:
        history = []
        for entry in lm.history:
            # Convertir cada entrada del historial a un dict serializable
            history_entry = {}
            for key, value in entry.items():
                # Convertir objetos complejos a strings/dicts serializables
                if hasattr(value, '__dict__'):
                    history_entry[key] = str(value)
                elif isinstance(value, (str, int, float, bool, type(None))):
                    history_entry[key] = value
                elif isinstance(value, (list, dict)):
                    history_entry[key] = value
                else:
                    history_entry[key] = str(value)
            history.append(history_entry)
    
    return DspyOutput(
        success=True,
        result=dspy_fields,
        message="Generación exitosa",
        reasoning=reasoning,
        completions=completions,
        observations=observations,
        history=history
    )


def get_dspy_lm(
    model: ModelType,
    max_tokens: int = 16000,
    temperature: float = 0.7,
    api_key: str = None,
    **kwargs
) -> dspy.LM:
    """
    Configura y retorna un Language Model de DSPy.
    
    Args:
        model: El modelo de inferencia a utilizar
        max_tokens: Número máximo de tokens a generar (default: 16000)
        temperature: Temperature para la generación (default: 0.7)
        api_key: API key de OpenRouter. Si no se proporciona, se obtiene de
            la variable de entorno OPENROUTER_API_KEY
        **kwargs: Parámetros adicionales para dspy.LM (stop, cache, etc.)
        
    Returns:
        Instancia configurada de dspy.LM
        
    Raises:
        ValueError: Si la API key no está configurada ni en parámetros 
            ni en variables de entorno
        
    Examples:
        >>> # Usando variable de entorno
        >>> lm = get_dspy_lm(
        ...     'openrouter/openai/gpt-4o', 
        ...     max_tokens=8000, 
        ...     temperature=0.9
        ... )
        
        >>> # Proporcionando API key directamente
        >>> lm = get_dspy_lm(
        ...     'openrouter/openai/gpt-4o', 
        ...     api_key='your-key-here',
        ...     max_tokens=20000, 
        ...     cache=False
        ... )
    """
    # Obtener API key de parámetro o variable de entorno
    if api_key is None:
        api_key = os.getenv('OPENROUTER_API_KEY')
    
    if not api_key:
        raise ValueError(
            "OPENROUTER_API_KEY no está configurada. "
            "Proporciónala como parámetro o variable de entorno"
        )
    
    return dspy.LM(
        model, 
        api_key=api_key,
        max_tokens=max_tokens,
        temperature=temperature,
        **kwargs
    )
