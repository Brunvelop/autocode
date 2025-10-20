"""
DSPy utilities for AI operations.

This module provides reusable utilities for working with DSPy,
including setup functions and generic generators.
"""
import logging
import os
from typing import Any, Dict, List, Literal, Optional, Type

import dspy
from autocode.autocode.core.ai.models import DspyOutput


# Configure logging
logger = logging.getLogger(__name__)


# ============================================================================
# CONSTANTS AND TYPE DEFINITIONS
# ============================================================================

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


# ============================================================================
# PRIVATE HELPER FUNCTIONS
# ============================================================================

def _validate_module_type(module_type: ModuleType) -> Optional[str]:
    """
    Valida que el module_type sea válido.
    
    Args:
        module_type: Tipo de módulo DSPy a validar
        
    Returns:
        None si es válido, mensaje de error si no lo es
    """
    if module_type not in MODULE_MAP:
        valid_options = list(MODULE_MAP.keys())
        return f"Invalid module_type '{module_type}'. Valid options: {valid_options}"
    return None


def _create_and_execute_module(
    lm: dspy.LM,
    signature_class: Type[dspy.Signature],
    inputs: Dict[str, Any],
    module_type: ModuleType,
    module_kwargs: Dict[str, Any]
) -> Any:
    """
    Crea y ejecuta un módulo DSPy con la signature e inputs dados.
    
    Args:
        lm: Language Model configurado
        signature_class: La clase de signature de DSPy a utilizar
        inputs: Diccionario con los parámetros de entrada
        module_type: Tipo de módulo DSPy a usar
        module_kwargs: Parámetros adicionales del módulo
        
    Returns:
        Response del módulo DSPy
        
    Raises:
        Exception: Si hay error en la ejecución
    """
    with dspy.context(lm=lm):
        module_class = MODULE_MAP[module_type]
        generator = module_class(signature_class, **module_kwargs)
        return generator(**inputs)


def _extract_and_process_outputs(
    response: Any,
    signature_class: Type[dspy.Signature]
) -> Dict[str, Any]:
    """
    Extrae y procesa los campos de output de una response DSPy.
    
    Combina la extracción de campos y su procesamiento en una sola función
    para mayor simplicidad y eficiencia.
    
    Args:
        response: Response del módulo DSPy
        signature_class: La clase de signature utilizada
        
    Returns:
        Diccionario con los campos de output procesados
    """
    # Extraer output fields de la signature
    output_fields = [
        name for name, field in signature_class.model_fields.items()
        if field.json_schema_extra.get('__dspy_field_type') == 'output'
    ]
    
    # Construir dict con outputs principales
    result = {field: getattr(response, field, None) for field in output_fields}
    
    # Fallback si no hay outputs explícitos
    if not result:
        result = {
            attr: getattr(response, attr) 
            for attr in dir(response)
            if not attr.startswith('_') and not callable(getattr(response, attr))
        }
    
    return result


def _process_list_field(field_value: Any) -> Optional[List[str]]:
    """
    Procesa un campo DSPy convirtiéndolo a lista de strings si es necesario.
    
    Esta función maneja la conversión de objetos Prediction y otras
    estructuras complejas a strings serializables.
    
    Args:
        field_value: Valor del campo a procesar
        
    Returns:
        Lista de strings si el campo existe, None si no
    """
    if field_value is None:
        return None
    
    if isinstance(field_value, list):
        return [str(item) if hasattr(item, '__dict__') else item for item in field_value]
    
    return [str(field_value)]


def _extract_lm_history(lm: dspy.LM) -> Optional[List[Dict[str, Any]]]:
    """
    Extrae el historial del Language Model en formato serializable.
    
    Args:
        lm: Language Model de DSPy
        
    Returns:
        Lista de entradas del historial o None si no hay historial
    """
    if not hasattr(lm, 'history') or not lm.history:
        return None
    
    return [
        {
            k: str(v) if hasattr(v, '__dict__') else v 
            if isinstance(v, (str, int, float, bool, type(None), list, dict)) 
            else str(v)
            for k, v in entry.items()
        }
        for entry in lm.history
    ]


# ============================================================================
# PUBLIC API FUNCTIONS
# ============================================================================

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
        error_msg = (
            "OPENROUTER_API_KEY no está configurada. "
            "Proporciónala como parámetro o variable de entorno"
        )
        logger.error(error_msg)
        raise ValueError(error_msg)
    
    logger.debug(f"Configurando LM con modelo: {model}")
    return dspy.LM(
        model, 
        api_key=api_key,
        max_tokens=max_tokens,
        temperature=temperature,
        **kwargs
    )


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
    
    # Validar module_type
    error_msg = _validate_module_type(module_type)
    if error_msg:
        logger.error(error_msg)
        return DspyOutput(success=False, result={}, message=error_msg)
    
    # Configurar el Language Model
    try:
        lm = get_dspy_lm(
            model, 
            max_tokens=max_tokens, 
            temperature=temperature, 
            **lm_kwargs
        )
    except ValueError as e:
        error_msg = f"Error configurando LM: {str(e)}"
        logger.error(error_msg)
        return DspyOutput(success=False, result={}, message=error_msg)
    
    # Ejecutar el módulo DSPy
    try:
        logger.debug(f"Ejecutando módulo {module_type} con signature {signature_class.__name__}")
        response = _create_and_execute_module(
            lm, signature_class, inputs, module_type, module_kwargs
        )
    except Exception as e:
        error_msg = f"Error en generación DSPy: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return DspyOutput(success=False, result={}, message=error_msg)
    
    # Extraer y procesar outputs de la signature
    dspy_fields = _extract_and_process_outputs(response, signature_class)
    
    if not dspy_fields:
        error_msg = "No se encontraron campos de output en la response de DSPy"
        logger.warning(error_msg)
        return DspyOutput(success=False, result={}, message=error_msg)
    
    # Procesar campos DSPy especiales
    reasoning = getattr(response, 'reasoning', None)
    completions = _process_list_field(getattr(response, 'completions', None))
    observations = _process_list_field(getattr(response, 'observations', None))
    history = _extract_lm_history(lm)
    
    logger.info(f"Generación exitosa con {len(dspy_fields)} campos de output")
    return DspyOutput(
        success=True,
        result=dspy_fields,
        message="Generación exitosa",
        reasoning=reasoning,
        completions=completions,
        observations=observations,
        history=history
    )
