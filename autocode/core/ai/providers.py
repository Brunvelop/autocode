"""
Catálogo de modelos AI disponibles.

Para añadir un nuevo modelo:
  1. Añade una entrada al Literal ModelType, en la sección del proveedor correspondiente.
  2. Formato: 'openrouter/{provider}/{model-name}'
  3. Eso es todo — el registry, la UI y get_chat_config() lo detectan automáticamente.

Todos los modelos usan el prefijo 'openrouter/' porque se acceden vía OpenRouter.
Ver: https://openrouter.ai/models
"""
from typing import Literal


# ============================================================================
# CATÁLOGO DE MODELOS
# ============================================================================

ModelType = Literal[
    # --- Anthropic ---
    'openrouter/anthropic/claude-sonnet-4.5',
    'openrouter/anthropic/claude-sonnet-4.6',
    'openrouter/anthropic/claude-opus-4.6',

    # --- NVIDIA ---
    'openrouter/nvidia/nemotron-3-nano-30b-a3b:free',

    # --- OpenAI ---
    'openrouter/openai/gpt-4o',
    'openrouter/openai/gpt-oss-20b',
    'openrouter/openai/gpt-5',
    'openrouter/openai/gpt-5-codex',

    # --- Qwen ---
    'openrouter/qwen/qwen3.5-9b',

    # --- xAI ---
    'openrouter/x-ai/grok-4',
    'openrouter/x-ai/grok-4-fast',
    'openrouter/x-ai/grok-code-fast-1',

    # --- Z-AI (Zhipu) ---
    'openrouter/z-ai/glm-5',
    'openrouter/z-ai/glm-5-turbo',
]
