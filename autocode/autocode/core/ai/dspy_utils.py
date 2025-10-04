"""
DSPy utilities for AI operations.

This module provides reusable utilities for working with DSPy,
including setup functions and generic generators.
"""
import os
from typing import Any, Dict, Literal, Type

import dspy


# Available models for inference
ModelType = Literal[
    'openrouter/openai/gpt-4o',
    'openrouter/x-ai/grok-4',
    'openrouter/anthropic/claude-sonnet-4.5',
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
) -> Dict[str, Any]:
    """
    Generador genérico que ejecuta cualquier signature de DSPy con el módulo seleccionado.
    
    Esta función proporciona una interfaz unificada para ejecutar cualquier
    signature de DSPy con diferentes módulos (Predict, ChainOfThought, ReAct, etc.).
    Diseñada para ser extensible con few-shot learning en el futuro.
    
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
        Diccionario con todos los campos de output de la signature.
        Siempre retorna un dict, incluso para signatures con un solo output.
        Ejemplo: {'python_code': '...'} o {'answer': '...', 'reasoning': '...'}
        
    Raises:
        ValueError: Si la API key no está configurada o module_type es inválido
        
    Examples:
        >>> # Ejemplo básico con un solo output
        >>> result = generate_with_dspy(
        ...     CodeGenerationSignature,
        ...     {"design_text": "Create a hello world function"}
        ... )
        >>> print(result['python_code'])
        
        >>> # Ejemplo con parámetros de LM personalizados
        >>> result = generate_with_dspy(
        ...     CodeGenerationSignature,
        ...     {"design_text": "Create a complex class"},
        ...     max_tokens=20000,
        ...     temperature=0.9
        ... )
        >>> print(result['python_code'])
        
        >>> # Ejemplo con módulo específico y parámetros
        >>> def search_web(query: str) -> str:
        ...     return f"Results for {query}"
        >>> result = generate_with_dspy(
        ...     QASignature,
        ...     {"question": "What is Python?"},
        ...     module_type='ReAct',
        ...     module_kwargs={'tools': [search_web], 'max_iters': 5}
        ... )
        >>> print(result['answer'])
    """
    # Inicializar module_kwargs si no se proporciona
    if module_kwargs is None:
        module_kwargs = {}
    
    # Validar module_type antes de configurar el LM
    if module_type not in MODULE_MAP:
        valid_options = list(MODULE_MAP.keys())
        return {
            "error": f"Invalid module_type '{module_type}'. "
                    f"Valid options: {valid_options}"
        }
    
    # Configurar el Language Model
    try:
        lm = get_dspy_lm(
            model, 
            max_tokens=max_tokens, 
            temperature=temperature, 
            **lm_kwargs
        )
    except ValueError as e:
        return {"error": str(e)}
    
    # Usar context en lugar de configure para evitar conflictos en async tasks
    with dspy.context(lm=lm):
        # Crear el generador con el módulo seleccionado
        module_class = MODULE_MAP[module_type]
        generator = module_class(signature_class, **module_kwargs)
        
        # Ejecutar la generación con los inputs proporcionados
        response = generator(**inputs)
    
    # Extraer output fields de la signature
    output_fields = [
        name for name, field in signature_class.model_fields.items()
        if field.json_schema_extra.get('__dspy_field_type') == 'output'
    ]
    
    # Construir resultado accediendo directamente a la response
    result = {field: getattr(response, field, None) for field in output_fields}
    
    # Fallback si no hay outputs explícitos
    if not result:
        result = {
            attr: getattr(response, attr) 
            for attr in dir(response)
            if not attr.startswith('_') and not callable(getattr(response, attr))
        }
    
    return result if result else {"error": "No output fields found in response"}


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
