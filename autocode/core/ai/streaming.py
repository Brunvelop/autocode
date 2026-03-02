"""
Streaming utilities for DSPy operations via SSE.

This module implements Server-Sent Events (SSE) streaming for chat operations,
allowing real-time token delivery to the frontend.
"""
import asyncio
import json
import logging
from typing import AsyncGenerator, Dict, Any, Optional, List

import dspy
from dspy.streaming import StreamResponse, StatusMessage

from autocode.core.ai.dspy_utils import (
    get_dspy_lm, MODULE_MAP, ModelType, ModuleType,
    prepare_chat_tools
)
from autocode.core.ai.models import DspyOutput
from autocode.core.ai.signatures import ChatSignature

logger = logging.getLogger(__name__)


class AutocodeStatusProvider(dspy.streaming.StatusMessageProvider):
    """Proveedor de mensajes de estado para streaming.
    
    Genera mensajes informativos durante el proceso de streaming
    para mantener al usuario informado del progreso.
    """
    
    def tool_start_status_message(self, instance, inputs):
        tool_name = getattr(instance, 'name', str(instance))
        return f"🛠️ Llamando herramienta: {tool_name}"
    
    def tool_end_status_message(self, outputs):
        return "✅ Herramienta completada"
    
    def module_start_status_message(self, instance, inputs):
        return f"🔄 Procesando {type(instance).__name__}..."
    
    def module_end_status_message(self, outputs):
        return ""  # String vacío — seguro para DSPy
    
    def lm_start_status_message(self, instance, inputs):
        return "🧠 Consultando al LLM..."
    
    def lm_end_status_message(self, outputs):
        return ""  # String vacío


async def stream_chat(
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
) -> AsyncGenerator[str, None]:
    """Generador async que produce eventos SSE para chat streaming.
    
    Solo emite tokens del campo 'response' de la signature.
    Otros campos (reasoning, trajectory) se incluyen en el evento 'complete' final.
    
    Args:
        message: Mensaje actual del usuario
        conversation_history: Historial de conversación en formato texto
        model: Modelo de inferencia a utilizar
        max_tokens: Número máximo de tokens a generar
        temperature: Temperature para la generación
        module_type: Tipo de módulo DSPy a usar
        module_kwargs: Parámetros adicionales del módulo
        enabled_tools: Lista de nombres de funciones a habilitar como tools
        lm_kwargs: Parámetros avanzados adicionales para el LLM
        enable_prompt_cache: Activa cache de prompts del proveedor
        
    Yields:
        Strings formateados como eventos SSE (event: type\\ndata: json\\n\\n)
    """
    try:
        # 1. Configurar LM
        kwargs = lm_kwargs or {}
        if enable_prompt_cache and 'cache_control_injection_points' not in kwargs:
            kwargs['cache_control_injection_points'] = [
                {"location": "message", "role": "system"}
            ]
        lm = get_dspy_lm(model, max_tokens=max_tokens, temperature=temperature, **kwargs)
        
        # 2. Preparar tools (reutiliza helper compartido)
        tools = prepare_chat_tools(enabled_tools)
        
        # 3. Preparar module_kwargs
        if module_kwargs is None:
            module_kwargs = {}
        if module_type == 'ReAct':
            module_kwargs.setdefault('tools', tools)
            module_kwargs.setdefault('max_iters', 5)
        
        # 4. Crear módulo DSPy
        module = MODULE_MAP[module_type](ChatSignature, **module_kwargs)
        
        # 5. Streamify con listeners y status provider
        stream_listeners = [
            dspy.streaming.StreamListener(
                signature_field_name="response",
                allow_reuse=True
            )
        ]
        stream_program = dspy.streamify(
            module,
            stream_listeners=stream_listeners,
            status_message_provider=AutocodeStatusProvider(),
        )
        
        # 6. Ejecutar y consumir stream
        prediction = None
        with dspy.context(lm=lm):
            output_stream = stream_program(
                message=message,
                conversation_history=conversation_history
            )
            async for chunk in output_stream:
                if isinstance(chunk, StreamResponse):
                    yield _format_sse("token", {
                        "chunk": chunk.chunk,
                        "field": chunk.signature_field_name,
                        "predict_name": chunk.predict_name,
                        "is_last_chunk": chunk.is_last_chunk
                    })
                elif isinstance(chunk, StatusMessage):
                    if chunk.message:  # Filtrar mensajes vacíos
                        yield _format_sse("status", {"message": chunk.message})
                elif isinstance(chunk, dspy.Prediction):
                    prediction = chunk
        
        # 7. Evento final — resultado ligero usando staticmethods de DspyOutput
        if prediction:
            result = {}
            for field_name in ChatSignature.output_fields:
                val = getattr(prediction, field_name, None)
                if val is not None:
                    result[field_name] = val
            
            reasoning = getattr(prediction, 'reasoning', None)
            trajectory = getattr(prediction, 'trajectory', None)
            
            # Usar staticmethods en vez de instancia dummy
            if isinstance(trajectory, (dict, list)):
                trajectory = DspyOutput.normalize_trajectory(trajectory)
                trajectory = DspyOutput.serialize_value(trajectory)
            
            yield _format_sse("complete", {
                "success": True,
                "result": result,
                "message": "Streaming completado",
                "reasoning": str(reasoning) if reasoning and not isinstance(reasoning, str) else reasoning,
                "trajectory": trajectory,
                "completions": None,
                "history": None  # No reconstruimos history en v1
            })
        else:
            yield _format_sse("complete", {
                "success": False,
                "result": {},
                "message": "No prediction received",
                "reasoning": None,
                "trajectory": None,
                "completions": None,
                "history": None
            })
            
    except (GeneratorExit, asyncio.CancelledError):
        logger.info("Client disconnected, stream cancelled")
    except Exception as e:
        logger.error(f"Streaming error: {e}", exc_info=True)
        yield _format_sse("error", {"message": str(e), "success": False})


def _format_sse(event: str, data: dict) -> str:
    """Formatea un evento como SSE.
    
    Args:
        event: Tipo de evento (token, status, complete, error)
        data: Datos del evento como diccionario
        
    Returns:
        String formateado como evento SSE
    """
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"
