"""
DSPy utilities for AI operations.

This module provides reusable utilities for working with DSPy,
including setup functions and generic generators.
"""
import inspect
import json
import logging
import os
from typing import Any, Dict, List, Literal, Optional, Type, Union

import dspy
from autocode.core.ai.models import DspyOutput


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
    
    # Extracción simplificada con getattr
    result = getattr(response, 'response', {})
    reasoning = getattr(response, 'reasoning', None)
    completions = getattr(response, 'completions', None)
    trajectory = getattr(response, 'trajectory', None)
    history = getattr(lm, 'history', None)

    # Normalización de tipos para DSPy (que a veces devuelve objetos complejos)
    if reasoning is not None and not isinstance(reasoning, str):
        reasoning = str(reasoning)

    if completions is not None:
        normalized_completions = []
        for c in completions:
            if isinstance(c, str):
                normalized_completions.append(c)
            elif hasattr(c, 'response'): # dspy.Prediction
                normalized_completions.append(str(c.response))
            else:
                normalized_completions.append(str(c))
        completions = normalized_completions
    
    if not result:
        error_msg = "No se encontraron campos de output en la response de DSPy"
        logger.warning(error_msg)
        return DspyOutput(success=False, result={}, message=error_msg)
    
    # Convertir campos complejos a formatos serializables para API
    # History: Convertir ModelResponse y otros objetos a dicts
    if history:
        serialized_history = []
        for item in history:
            if hasattr(item, 'model_dump'):
                serialized_history.append(item.model_dump())
            elif hasattr(item, '__dict__'):
                serialized_history.append(vars(item))
            else:
                serialized_history.append(item)
        history = serialized_history
    
    # Trajectory: Convertir objetos anidados (como GenericOutput) a dicts
    if isinstance(trajectory, dict):
        serialized_trajectory = {}
        for key, value in trajectory.items():
            if hasattr(value, 'model_dump'):
                serialized_trajectory[key] = value.model_dump()
            elif hasattr(value, '__dict__'):
                serialized_trajectory[key] = vars(value)
            else:
                serialized_trajectory[key] = value
        trajectory = serialized_trajectory
    elif isinstance(trajectory, list):
        # Si es lista (ya normalizada o lista de pasos), intentar serializar items internos si son objetos
        serialized_trajectory = []
        for item in trajectory:
            if hasattr(item, 'model_dump'):
                serialized_trajectory.append(item.model_dump())
            elif hasattr(item, '__dict__'):
                serialized_trajectory.append(vars(item))
            else:
                serialized_trajectory.append(item)
        trajectory = serialized_trajectory
    else:
        # Si no es dict ni lista (ej: Mock, objeto extraño), forzar a None para evitar error de validación
        trajectory = None
    
    logger.info(f"Generación exitosa con {len(result)} campos de output")
    return DspyOutput(
        success=True,
        result=result,
        message="Generación exitosa",
        reasoning=reasoning,
        completions=completions,
        trajectory=trajectory,
        history=history
    )


# ============================================================================
# MODULE INTROSPECTION FUNCTIONS
# ============================================================================

# Parámetros a excluir de la introspección (internos de DSPy)
_EXCLUDED_MODULE_PARAMS = {'self', 'signature', 'tools'}

# Descripciones amigables para parámetros conocidos
_PARAM_DESCRIPTIONS = {
    'n': 'Número de completions a generar',
    'max_iters': 'Máximo de iteraciones del agente',
    'num_comparisons': 'Número de cadenas a comparar',
    'tools': 'Herramientas disponibles para el agente',
    'temperature': 'Creatividad de la generación (0=determinista, 1=creativo)',
    'max_tokens': 'Máximo de tokens a generar',
}


def _get_type_name(annotation: Any) -> str:
    """
    Obtiene el nombre legible del tipo de una anotación.
    
    Args:
        annotation: Anotación de tipo de Python
        
    Returns:
        String con el nombre del tipo
    """
    if annotation == inspect.Parameter.empty:
        return 'any'
    if hasattr(annotation, '__name__'):
        return annotation.__name__
    return str(annotation).replace('typing.', '')


def get_module_kwargs_schema(module_type: ModuleType) -> Dict[str, Any]:
    """
    Inspecciona la clase DSPy del módulo y extrae sus parámetros del __init__.
    
    Esta función usa introspección en runtime para descubrir automáticamente
    qué kwargs acepta cada módulo DSPy, sin necesidad de hardcodear schemas.
    
    Args:
        module_type: Tipo de módulo DSPy a inspeccionar
        
    Returns:
        Diccionario con:
        - params: Lista de definiciones de parámetros
        - supports_tools: Booleano indicando si el módulo acepta 'tools'
        
    Example:
        >>> schema = get_module_kwargs_schema('ReAct')
        >>> print(schema['supports_tools'])
        True
    """
    if module_type not in MODULE_MAP:
        logger.warning(f"Module type '{module_type}' not found in MODULE_MAP")
        return {'params': [], 'supports_tools': False}
    
    module_class = MODULE_MAP[module_type]
    
    try:
        sig = inspect.signature(module_class.__init__)
    except (ValueError, TypeError) as e:
        logger.warning(f"Could not inspect {module_type}.__init__: {e}")
        return {'params': [], 'supports_tools': False}
    
    params = []
    
    # Detect if 'tools' is in signature (before excluding it from params list)
    supports_tools = 'tools' in sig.parameters
    
    for name, param in sig.parameters.items():
        # Excluir parámetros internos
        if name in _EXCLUDED_MODULE_PARAMS:
            continue
        # Excluir *args y **kwargs
        if param.kind in (inspect.Parameter.VAR_POSITIONAL, inspect.Parameter.VAR_KEYWORD):
            continue
        
        param_type = _get_type_name(param.annotation)
        has_default = param.default != inspect.Parameter.empty
        default_value = param.default if has_default else None
        
        # Sanitize default value for JSON serialization
        if has_default:
            try:
                json.dumps(default_value)
            except (TypeError, OverflowError):
                # If not serializable (e.g. type, function, complex object), convert to string representation
                if hasattr(default_value, '__name__'):
                    default_value = default_value.__name__
                else:
                    default_value = str(default_value)
        
        # Obtener descripción amigable
        description = _PARAM_DESCRIPTIONS.get(
            name, 
            f"Parámetro {name} del módulo {module_type}"
        )
        
        params.append({
            'name': name,
            'type': param_type,
            'default': default_value,
            'required': not has_default,
            'description': description
        })
    
    return {
        'params': params,
        'supports_tools': supports_tools
    }


def get_all_module_kwargs_schemas() -> Dict[str, Dict[str, Any]]:
    """
    Obtiene los schemas de kwargs para todos los módulos DSPy disponibles.
    
    Returns:
        Diccionario mapeando module_type a su configuración (params, supports_tools)
        
    Example:
        >>> schemas = get_all_module_kwargs_schemas()
        >>> print(schemas['ReAct']['supports_tools'])
        True
    """
    return {
        module_type: get_module_kwargs_schema(module_type)
        for module_type in MODULE_MAP.keys()
    }


def get_available_tools_info() -> List[Dict[str, Any]]:
    """
    Obtiene información de las funciones del registry que pueden usarse como tools.
    
    Excluye automáticamente la función 'chat' para evitar recursión.
    
    Returns:
        Lista de diccionarios con información de cada tool:
        - name: Nombre de la función
        - description: Descripción de la función
        - enabled_by_default: Si está habilitada por defecto
        
    Example:
        >>> tools = get_available_tools_info()
        >>> print([t['name'] for t in tools])
        ['generate_code', 'generate_design', 'generate_answer', ...]
    """
    # Import aquí para evitar importación circular
    from autocode.interfaces.registry import FUNCTION_REGISTRY, _ensure_functions_loaded
    
    _ensure_functions_loaded()
    
    # Funciones a excluir de tools (evitar recursión y funciones no útiles como tools)
    excluded_functions = {'chat'}
    
    tools = []
    for func_name, func_info in FUNCTION_REGISTRY.items():
        if func_name in excluded_functions:
            continue
        
        tools.append({
            'name': func_name,
            'description': func_info.description,
            'enabled_by_default': True  # Por defecto todas habilitadas
        })
    
    return sorted(tools, key=lambda t: t['name'])
