"""
High-level pipelines for AI operations.

This module contains orchestration functions that combine file I/O
with DSPy generation for complete workflows.
"""
from typing import Dict, Any, Optional, List, get_args
import os
import litellm
from fastapi import HTTPException
from refract import register_function, Refract
from autocode.core.ai.models import ChatResult, ContextUsage, ChatConfig
from autocode.core.utils.openrouter import fetch_models_info
from autocode.core.ai.providers import ModelType
from autocode.core.ai.dspy_utils import (
    generate_with_dspy, 
    ModuleType,
    get_all_module_kwargs_schemas,
    get_available_tools_info,
    prepare_chat_tools
)
from autocode.core.ai.signatures import ChatSignature
from autocode.core.ai.streaming import stream_chat


def _read_path_content(path: str) -> str:
    """
    Lee recursivamente todos los archivos de texto de un directorio (o un único archivo).
    
    Ignora silenciosamente archivos binarios o con errores de lectura.
    
    Args:
        path: Ruta a un directorio o archivo
        
    Returns:
        Contenido concatenado de todos los archivos de texto encontrados
    """
    if os.path.isfile(path):
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception:
            return ""

    contents = []
    for root, _, files in os.walk(path):
        for filename in sorted(files):
            filepath = os.path.join(root, filename)
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    contents.append(f.read())
            except Exception:
                # Ignorar archivos binarios, sin permisos, etc.
                continue

    return "\n".join(contents)


@register_function(http_methods=["POST"], interfaces=["api"])
def calculate_context_usage(
    model: ModelType,
    messages: Optional[List[Dict[str, str]]] = None,
    path: Optional[str] = None,
) -> ContextUsage:
    """
    Calcula el uso actual y máximo de la ventana de contexto para un modelo.
    
    Acepta mensajes, un path a un directorio/archivo, o ambos combinados.
    Usa litellm para contar tokens y obtener el tamaño máximo de contexto.
    
    Args:
        model: Modelo de inferencia a utilizar
        messages: Lista de mensajes en formato OpenAI [{"role": "user"|"assistant", "content": "..."}].
                  Opcional si se proporciona `path`.
        path: Ruta a un directorio o archivo. Si se proporciona, lee recursivamente todos
              los archivos de texto y los contabiliza como un mensaje user adicional.
              Opcional si se proporcionan `messages`.
        
    Returns:
        ContextUsage con current, max y percentage
    """
    all_messages: List[Dict[str, str]] = list(messages) if messages else []

    # Si se proporciona path, añadir su contenido como mensaje user sintético
    if path is not None:
        if not os.path.exists(path):
            raise HTTPException(status_code=404, detail=f"Path no encontrado: {path}")
        path_content = _read_path_content(path)
        if path_content:
            all_messages.append({"role": "user", "content": path_content})

    try:
        # Calcular tokens actuales usando litellm.token_counter
        current_tokens = litellm.token_counter(model=model, messages=all_messages)
        
        # Obtener tamaño máximo de ventana de contexto
        max_tokens = litellm.get_max_tokens(model)
        
        # Calcular porcentaje de uso
        percentage = (current_tokens / max_tokens * 100) if max_tokens > 0 else 0
        
        return ContextUsage(
            current=current_tokens,
            max=max_tokens,
            percentage=round(percentage, 2)
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error calculando uso de contexto: {str(e)}")


@register_function(http_methods=["POST"], interfaces=["api"])
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
) -> ChatResult:
    """
    Chat conversacional con acceso a herramientas MCP.

    Este endpoint usa DSPy con el módulo configurado para:
    - Usar las funciones MCP registradas como herramientas con schemas completos
    - Razonar sobre qué herramientas usar para responder (con ReAct)
    - Retornar un ChatResult con response, trajectory, reasoning, history, etc.

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
        ChatResult con:
        - response: Respuesta principal del asistente
        - history: Historial completo de llamadas al LM con metadata
        - trajectory: Trayectoria de ReAct (thoughts, tool_names, tool_args, observations)
        - reasoning: Razonamiento paso a paso
        - completions: Múltiples completions si aplica

    Raises:
        HTTPException: Si ocurre algún error durante la ejecución
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

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error en chat: {str(e)}")


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
) -> ChatResult:
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
        ChatResult (en modo síncrono, delega a chat())
    """
    return chat(
        message=message, conversation_history=conversation_history,
        model=model, max_tokens=max_tokens, temperature=temperature,
        module_type=module_type, module_kwargs=module_kwargs,
        enabled_tools=enabled_tools, lm_kwargs=lm_kwargs,
        enable_prompt_cache=enable_prompt_cache
    )


@register_function(http_methods=["GET"], interfaces=["api"])
def get_chat_config() -> ChatConfig:
    """
    Obtiene la configuración disponible para el chat.
    
    Retorna información sobre:
    - module_kwargs_schemas: Parámetros disponibles por cada module_type
    - available_tools: Lista de tools MCP disponibles con nombre y descripción
    - models: Lista de modelos disponibles con metadata de OpenRouter
    
    Esta información permite a la UI renderizar controles dinámicos
    según el module_type seleccionado y el modelo.
    
    Returns:
        ChatConfig con module_kwargs_schemas, available_tools y models
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

        mcp_functions = Refract.current().get_functions_for_interface("mcp")

        return ChatConfig(
            module_kwargs_schemas=get_all_module_kwargs_schemas(),
            available_tools=get_available_tools_info(mcp_functions),
            models=models_data
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error obteniendo configuración: {str(e)}")
