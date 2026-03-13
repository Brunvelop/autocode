# AI Module - Code ↔ Design Generation

Este módulo proporciona funcionalidades bidireccionales de generación usando DSPy (Declarative Self-improving Python):
- **Text to Code**: Genera código Python a partir de documentos de diseño
- **Code to Design**: Genera documentos de diseño Markdown a partir de código Python

## Funciones Disponibles

**Modelos disponibles:**
- `openrouter/openai/gpt-4o` (default)
- `openrouter/x-ai/grok-4`
- `openrouter/anthropic/claude-sonnet-4.5`
- `openrouter/openai/gpt-5`
- `openrouter/openai/gpt-5-codex`

Todas las funciones están registradas en el registry (accesibles vía API/CLI/MCP).

---

### `generate_code(design_text, model) -> str`
Genera código Python a partir de un texto de diseño.

```python
from autocode.core.ai.pipelines import generate_code

code = generate_code("Crear una función que calcule el factorial de un número.")
```

### `text_to_code(input_path, output_path, model) -> str`
Convierte un archivo de diseño en un archivo `.py`.

```python
from autocode.core.ai.pipelines import text_to_code

result = text_to_code(input_path="design.md", output_path="generated.py")
```

### `generate_design(python_code, include_diagrams, model) -> str`
Genera un documento de diseño Markdown a partir de código Python.

```python
from autocode.core.ai.pipelines import generate_design

design_doc = generate_design(python_code, include_diagrams=True)
```

### `code_to_design(input_path, output_path, include_diagrams, model) -> str`
Convierte un archivo `.py` en un documento de diseño `.md`.

```python
from autocode.core.ai.pipelines import code_to_design

result = code_to_design(input_path="my_module.py", output_path="my_module_design.md")
```

### `generate_answer(question, model) -> str`
Responde una pregunta usando razonamiento.

```python
from autocode.core.ai.pipelines import generate_answer

answer = generate_answer("¿Qué es DSPy?")
```

### `generate(signature_type, inputs, model) -> str`
Generador genérico con selección de signature. Valores válidos para `signature_type`: `'code_generation'`, `'design_document'`, `'qa'`.

```python
from autocode.core.ai.pipelines import generate

result = generate(
    signature_type='code_generation',
    inputs={'design_text': 'Create a hello world function'}
)
```

### Funciones de I/O (`autocode.core.utils.file_utils`)

Las funciones de lectura/escritura están en un módulo separado (SRP):
- `read_file(path)` / `read_design_document(path)` — lectura de archivos
- `write_file(content, path)` / `write_python_file(code, path)` — escritura de archivos

---

## Configuración

**Requisitos:** Variable de entorno `OPENROUTER_API_KEY` configurada y `dspy-ai` instalado.

```bash
export OPENROUTER_API_KEY="tu_api_key_aqui"
```

---

## Arquitectura DSPy

### Selección de Módulo DSPy
El parámetro `module_type` en `generate_with_dspy()` permite elegir el módulo:

| Módulo | Descripción |
|--------|-------------|
| `dspy.Predict` | Predictor básico |
| `dspy.ChainOfThought` | Razonamiento paso a paso (default) |
| `dspy.ProgramOfThought` | Genera y ejecuta código para responder |
| `dspy.ReAct` | Agente que usa herramientas |
| `dspy.MultiChainComparison` | Compara múltiples outputs |

### Parámetros Extra por Módulo (`module_kwargs`)
```python
# ReAct: tools y max_iters
module_kwargs={'tools': [tool1, tool2], 'max_iters': 10}

# Predict/ChainOfThought: número de completions
module_kwargs={'n': 5}
```

### Outputs como Dict
`generate_with_dspy` siempre retorna un `dict` con todos los campos de output de la signature:

```python
result = generate_with_dspy(CodeGenerationSignature, {'design_text': '...'})
python_code = result['python_code']  # extraer campo específico
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

| Responsabilidad | Función |
|----------------|---------|
| Generación de código (DSPy) | `generate_python_code` |
| Orquestación text→code | `text_to_code` |
| Generación de docs (DSPy) | `generate_design_document` |
| Orquestación code→design | `code_to_design` |
| Lectura de archivos | `file_utils.read_file` |
| Escritura de archivos | `file_utils.write_file` |
