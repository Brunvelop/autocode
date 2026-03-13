# AI Module - Chat & Task Execution

Este módulo proporciona funcionalidades de IA conversacional y ejecución de tareas usando DSPy (Declarative Self-improving Python).

## Funciones Disponibles

**Modelos disponibles:**
- `openrouter/openai/gpt-4o`
- `openrouter/x-ai/grok-4`
- `openrouter/anthropic/claude-sonnet-4.5`
- `openrouter/openai/gpt-5`
- `openrouter/openai/gpt-5-codex`
- `openrouter/z-ai/glm-5` (default para chat)

Todas las funciones están registradas en el registry (accesibles vía API/CLI/MCP).

---

### `chat(message, conversation_history, model, ...) -> DspyOutput`
Chat conversacional con acceso a herramientas MCP.

```python
from autocode.core.ai.pipelines import chat

result = chat(
    message="¿Qué archivos hay en el proyecto?",
    conversation_history=""
)
print(result.result['response'])
```

### `chat_stream(message, conversation_history, model, ...) -> DspyOutput`
Chat con streaming en tiempo real vía SSE. Misma interfaz que `chat()`, pero emite tokens progresivamente cuando se invoca desde la API.

### `calculate_context_usage(model, messages) -> GenericOutput`
Calcula el uso de la ventana de contexto para un modelo y mensajes dados.

```python
from autocode.core.ai.pipelines import calculate_context_usage

result = calculate_context_usage(
    model='openrouter/openai/gpt-4o',
    messages=[{"role": "user", "content": "Hola"}]
)
print(result.result)  # {"current": 10, "max": 128000, "percentage": 0.01}
```

### `get_chat_config() -> GenericOutput`
Obtiene la configuración disponible para el chat: modelos, tools MCP y schemas de módulos DSPy.

---

## Configuración

**Requisitos:** Variable de entorno `OPENROUTER_API_KEY` configurada y `dspy-ai` instalado.

```bash
export OPENROUTER_API_KEY="tu_api_key_aqui"
```

---

## Arquitectura DSPy

### Signatures disponibles (`signatures.py`)

| Signature | Inputs | Output | Usada por |
|-----------|--------|--------|-----------|
| `ChatSignature` | `message`, `conversation_history` | `response` | `chat()`, `chat_stream()`, `stream_chat()` |
| `TaskExecutionSignature` | `task_instruction`, `file_path` | `completion_summary` | `executor.py` (ReAct executor) |

### Selección de Módulo DSPy
El parámetro `module_type` en `generate_with_dspy()` permite elegir el módulo:

| Módulo | Descripción |
|--------|-------------|
| `dspy.Predict` | Predictor básico |
| `dspy.ChainOfThought` | Razonamiento paso a paso |
| `dspy.ProgramOfThought` | Genera y ejecuta código para responder |
| `dspy.ReAct` | Agente que usa herramientas (default para chat) |
| `dspy.MultiChainComparison` | Compara múltiples outputs |

### Parámetros Extra por Módulo (`module_kwargs`)
```python
# ReAct: tools y max_iters
module_kwargs={'tools': [tool1, tool2], 'max_iters': 10}

# Predict/ChainOfThought: número de completions
module_kwargs={'n': 5}
```

### Uso directo de `generate_with_dspy`
`generate_with_dspy` acepta cualquier signature directamente — no necesitas un dispatcher:

```python
from autocode.core.ai.dspy_utils import generate_with_dspy
from autocode.core.ai.signatures import ChatSignature

result = generate_with_dspy(
    signature_class=ChatSignature,
    inputs={"message": "Hola", "conversation_history": ""},
    module_type='ChainOfThought'
)
print(result.result['response'])
print(result.reasoning)  # Razonamiento paso a paso
```

### Context Manager (Thread-safe y Async-safe)
Usa `dspy.context(lm=lm)` en lugar de `dspy.settings.configure()` para garantizar compatibilidad con FastAPI y evitar conflictos entre requests concurrentes:

```python
lm = dspy.LM('openrouter/openai/gpt-4o', api_key=api_key)
with dspy.context(lm=lm):
    response = module(...)
```

---

## Single Responsibility Principle

| Responsabilidad | Módulo |
|----------------|--------|
| Signatures declarativas | `signatures.py` |
| Generación DSPy (low-level) | `dspy_utils.py` → `generate_with_dspy` |
| Pipelines registradas | `pipelines.py` → `chat`, `chat_stream`, etc. |
| Streaming SSE | `streaming.py` → `stream_chat` |
| Lectura/escritura de archivos | `utils/file_utils.py` |
