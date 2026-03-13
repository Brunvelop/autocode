"""
High-level pipelines for AI operations.

This module contains orchestration functions that combine file I/O
with DSPy generation for complete workflows.
"""
from typing import Dict, Any, Optional, List, get_args
import litellm
from autocode.core.registry import register_function, get_functions_for_interface
from autocode.core.models import GenericOutput
from autocode.core.ai.models import DspyOutput
from autocode.core.utils.openrouter import fetch_models_info
from autocode.core.ai.dspy_utils import (
    generate_with_dspy, 
    ModelType, 
    ModuleType,
    get_all_module_kwargs_schemas,
    get_available_tools_info,
    prepare_chat_tools
)
from autocode.core.ai.signatures import ChatSignature
from autocode.core.ai.streaming import stream_chat


@register_function(http_methods=["POST"], interfaces=["api", "cli"])
def calculate_context_usage(
    model: ModelType,
    messages: List[Dict[str, str]]
) -> GenericOutput:
    """
    Calcula el uso actual y máximo de la ventana de contexto para un modelo y mensajes dados.
    
    Usa litellm para:
    - Contar tokens del mensaje actual usando token_counter
    - Obtener el tamaño máximo de ventana de contexto usando get_max_tokens
    
    Args:
        model: Modelo de inferencia a utilizar
        messages: Lista de mensajes en formato OpenAI [{"role": "user"|"assistant", "content": "..."}]
        
    Returns:
        GenericOutput con result={"current": int, "max": int, "percentage": float}
    """
    try:
        # Calcular tokens actuales usando litellm.token_counter
        current_tokens = litellm.token_counter(model=model, messages=messages)
        
        # Obtener tamaño máximo de ventana de contexto
        max_tokens = litellm.get_max_tokens(model)
        
        # Calcular porcentaje de uso
        percentage = (current_tokens / max_tokens * 100) if max_tokens > 0 else 0
        
        return GenericOutput(
            success=True,
            result={
                "current": current_tokens,
                "max": max_tokens,
                "percentage": round(percentage, 2)
            },
            message=f"Context usage: {current_tokens}/{max_tokens} tokens ({percentage:.1f}%)"
        )
        
    except Exception as e:
        return GenericOutput(
            success=False,
            result={"current": 0, "max": 0, "percentage": 0},
            message=f"Error calculando uso de contexto: {str(e)}"
        )


@register_function(http_methods=["POST"], interfaces=["api", "cli"])
def chat(
    message: str,
    conversation_history: str = "",
    model: ModelType = 'openrouter/z-ai/glm-5',
    max_tokens: int = 16000,
    temperature: float = 0.7,
    module_type: ModuleType = 'ReAct',
    module_kwargs: Optional[Dict[str, Any]] = None,
    enabled_tools: Optional[List[str]] = None,
    lm_kwargs: Optional[Dict[str, Any]] = None,
    enable_prompt_cache: bool = True
) -> DspyOutput:
    """
    Chat conversacional con acceso a herramientas MCP.
    
    Este endpoint usa DSPy con el módulo configurado para:
    - Usar las funciones MCP registradas como herramientas con schemas completos
    - Razonar sobre qué herramientas usar para responder (con ReAct)
    - Retornar un DspyOutput completo con trajectory, reasoning, history, etc.
    
    Args:
        message: Mensaje actual del usuario
        conversation_history: Historial de conversación en formato texto (opcional)
        model: Modelo de inferencia a utilizar
        max_tokens: Número máximo de tokens (default: 16000)
        temperature: Temperature para generación (default: 0.7)
        module_type: Tipo de módulo DSPy (Predict, ChainOfThought, ReAct, etc.) (default: ReAct)
        module_kwargs: Parámetros adicionales del módulo (ej: max_iters para ReAct)
        enabled_tools: Lista de nombres de funciones a habilitar como tools (si None, usa todas)
        lm_kwargs: Parámetros avanzados adicionales para el LLM (top_p, etc.)
        enable_prompt_cache: Activa cache de prompts del proveedor (Anthropic/OpenAI) para reducir costos y latencia (default: True)
        
    Returns:
        DspyOutput con:
        - result: Dict con 'response', 'trajectory' (si ReAct), 'reasoning', etc.
        - history: Historial completo de llamadas al LM con metadata
        - trajectory: Trayectoria de ReAct (thoughts, tool_names, tool_args, observations)
        - reasoning: Razonamiento paso a paso
        - completions: Múltiples completions si aplica
    """
    try:
        # Preparar tools usando helper compartido
        tools = prepare_chat_tools(enabled_tools)
        
        # Preparar module_kwargs con tools para ReAct
        if module_kwargs is None:
            module_kwargs = {}
        
        # Si es ReAct, asegurar que tenga tools y max_iters
        if module_type == 'ReAct':
            if 'tools' not in module_kwargs:
                module_kwargs['tools'] = tools
            if 'max_iters' not in module_kwargs:
                module_kwargs['max_iters'] = 5
        
        # Generar respuesta usando el módulo configurado
        kwargs = lm_kwargs or {}
        
        # Inyectar cache_control_injection_points para cache del proveedor (Anthropic/OpenAI)
        # Esto reduce costos y latencia cacheando prefijos de prompts en el servidor del proveedor
        if enable_prompt_cache and 'cache_control_injection_points' not in kwargs:
            kwargs['cache_control_injection_points'] = [
                {"location": "message", "role": "system"}
            ]
        
        return generate_with_dspy(
            signature_class=ChatSignature,
            inputs={
                'message': message,
                'conversation_history': conversation_history
            },
            model=model,
            module_type=module_type,
            module_kwargs=module_kwargs,
            max_tokens=max_tokens,
            temperature=temperature,
            **kwargs
        )
        
    except Exception as e:
        # Retornar error en formato DspyOutput
        return DspyOutput(
            success=False,
            result={"error": f"Error en chat: {str(e)}"},
            message=f"Error en chat: {str(e)}"
        )


@register_function(
    http_methods=["POST"],
    interfaces=["api"],
    streaming=True,
    stream_func=stream_chat
)
def chat_stream(
    message: str,
    conversation_history: str = "",
    model: ModelType = 'openrouter/openai/gpt-4o',
    max_tokens: int = 16000,
    temperature: float = 0.7,
    module_type: ModuleType = 'ReAct',
    module_kwargs: Optional[Dict[str, Any]] = None,
    enabled_tools: Optional[List[str]] = None,
    lm_kwargs: Optional[Dict[str, Any]] = None,
    enable_prompt_cache: bool = True
) -> DspyOutput:
    """Chat con streaming en tiempo real vía SSE.
    
    Misma funcionalidad que chat() pero con streaming de tokens.
    Esta función existe como definición de schema para el registry.
    La ejecución real se hace vía stream_func (stream_chat).
    Si se invoca síncronamente (ej: desde CLI), delega a chat().
    
    Args:
        message: Mensaje actual del usuario
        conversation_history: Historial de conversación en formato texto (opcional)
        model: Modelo de inferencia a utilizar
        max_tokens: Número máximo de tokens (default: 16000)
        temperature: Temperature para generación (default: 0.7)
        module_type: Tipo de módulo DSPy (Predict, ChainOfThought, ReAct, etc.) (default: ReAct)
        module_kwargs: Parámetros adicionales del módulo (ej: max_iters para ReAct)
        enabled_tools: Lista de nombres de funciones a habilitar como tools (si None, usa todas)
        lm_kwargs: Parámetros avanzados adicionales para el LLM (top_p, etc.)
        enable_prompt_cache: Activa cache de prompts del proveedor (default: True)
        
    Returns:
        DspyOutput (en modo síncrono, delega a chat())
    """
    return chat(
        message=message, conversation_history=conversation_history,
        model=model, max_tokens=max_tokens, temperature=temperature,
        module_type=module_type, module_kwargs=module_kwargs,
        enabled_tools=enabled_tools, lm_kwargs=lm_kwargs,
        enable_prompt_cache=enable_prompt_cache
    )


@register_function(http_methods=["GET"], interfaces=["api"])
def get_chat_config() -> GenericOutput:
    """
    Obtiene la configuración disponible para el chat.
    
    Retorna información sobre:
    - module_kwargs_schemas: Parámetros disponibles por cada module_type
    - available_tools: Lista de tools MCP disponibles con nombre y descripción
    - models: Lista de modelos disponibles con metadata de OpenRouter
    
    Esta información permite a la UI renderizar controles dinámicos
    según el module_type seleccionado y el modelo.
    
    Returns:
        GenericOutput con:
        - result.module_kwargs_schemas: Dict[module_type, {params, supports_tools}]
        - result.available_tools: List[{name, description, enabled_by_default}]
        - result.models: List[Dict] con info de cada modelo
    """
    try:
        # Obtener lista base de modelos definidos en el sistema
        base_models = list(get_args(ModelType))
        
        # Enriquecer con metadata de OpenRouter (sync)
        openrouter_info = fetch_models_info(base_models)
        
        models_data = []
        for model_id in base_models:
            info = openrouter_info.get(model_id, {})
            # Fusionar ID con la info obtenida (o defaults si falla fetch)
            models_data.append({
                "id": model_id,
                "name": info.get("name", model_id.split("/")[-1]),
                "context_length": info.get("context_length"),
                "top_provider": info.get("top_provider", {}),
                "pricing": info.get("pricing"),
                "supported_parameters": info.get("supported_parameters", [])
            })

        # Obtener funciones MCP del registry
        mcp_functions = get_functions_for_interface("mcp")

        return GenericOutput(
            success=True,
            result={
                "module_kwargs_schemas": get_all_module_kwargs_schemas(),
                "available_tools": get_available_tools_info(mcp_functions),
                "models": models_data
            },
            message="Configuración de chat obtenida exitosamente"
        )
    except Exception as e:
        return GenericOutput(
            success=False,
            result={},
            message=f"Error obteniendo configuración: {str(e)}"
        )
