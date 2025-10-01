# AI Module - Text to Code Generation

Este módulo proporciona funcionalidades de generación de código Python usando DSPy (Declarative Self-improving Python).

## Funciones Disponibles

### 1. `generate_python_code(design_text: str) -> str`

Genera código Python a partir de un texto de diseño.

**Características:**
- Usa DSPy con ChainOfThought para razonamiento
- Extensible con few-shot learning
- Registrada en el registry (accesible vía API/CLI/MCP)

**Uso:**
```python
from autocode.autocode.core.ai.ai_functions import generate_python_code

design = """
Crear una función que calcule el factorial de un número.
- Nombre: factorial
- Parámetro: n (int)
- Retorna: int
"""

code = generate_python_code(design)
print(code)
```

**Vía CLI:**
```bash
autocode generate-python-code --design-text "Crear una función que sume dos números"
```

**Vía API:**
```bash
curl -X POST http://localhost:8000/generate_python_code \
  -H "Content-Type: application/json" \
  -d '{"design_text": "Crear una función que sume dos números"}'
```

### 2. `text_to_code(input_path: str, output_path: str) -> str`

Convierte un archivo de diseño en un archivo .py.

**Características:**
- Lee documentos Markdown u otros formatos de texto
- Genera y guarda el código automáticamente
- Manejo de errores integrado
- Registrada en el registry (accesible vía API/CLI/MCP)

**Uso:**
```python
from autocode.autocode.core.ai.ai_functions import text_to_code

result = text_to_code(
    input_path="design.md",
    output_path="generated.py"
)
print(result)
```

**Vía CLI:**
```bash
autocode text-to-code --input-path design.md --output-path generated.py
```

**Vía API:**
```bash
curl -X POST http://localhost:8000/text_to_code \
  -H "Content-Type: application/json" \
  -d '{"input_path": "design.md", "output_path": "generated.py"}'
```

### 3. Funciones de I/O (Módulo separado)

Las funciones de lectura/escritura de archivos ahora están en `autocode.autocode.core.utils.file_utils`:

#### `read_design_document(path: str) -> str`
Lee un archivo de diseño y retorna su contenido.

#### `write_python_file(code: str, path: str) -> None`
Escribe código Python en un archivo (crea directorios si es necesario).

#### `write_file(content: str, path: str, file_type: str = None) -> None`
Función genérica extensible para escribir diferentes tipos de archivos.

#### `read_file(path: str) -> str`
Lee cualquier archivo de texto.

**Ventaja**: Separación de responsabilidades (SRP). El módulo AI se enfoca en generación, mientras que file_utils maneja I/O.

## Configuración

### Requisitos
- Variable de entorno `OPENROUTER_API_KEY` configurada
- DSPy instalado (`dspy-ai` en pyproject.toml)

### Configurar API Key
```bash
export OPENROUTER_API_KEY="tu_api_key_aqui"
```

## Arquitectura DSPy

### Signature Refinada para Código Limpio

El módulo usa una **class-based signature** con instrucciones explícitas para evitar que las LLMs generen código envuelto en bloques Markdown:

```python
class CodeGenerationSignature(dspy.Signature):
    """
    Genera código Python completo y funcional a partir de un documento de diseño.
    
    IMPORTANTE: El código generado debe ser código Python puro y ejecutable, 
    sin bloques markdown (```python), sin comillas triple alrededor del código, 
    y sin texto explicativo adicional. Solo el código Python válido.
    """
    
    design_text: str = dspy.InputField(
        desc="Documento de diseño que describe el código a generar"
    )
    python_code: str = dspy.OutputField(
        desc="Código Python puro, completo y ejecutable. Sin markdown, sin bloques ```python, sin explicaciones. Solo código válido."
    )
```

**Por qué esto funciona:**
- ✅ **Docstring de la signature**: Establece el comportamiento esperado del módulo
- ✅ **OutputField desc**: Guía explícita sobre el formato del output
- ✅ **Sin regex**: Solución puramente DSPy, no post-procesamiento
- ✅ **Optimizable**: Compatible con few-shot learning para reforzar el comportamiento

### Modelo LM
Por defecto usa: `openrouter/openai/gpt-4o`

### Problema Común y Solución

**Problema**: Las LLMs tienden a envolver código en bloques Markdown:
```
\```python
def fibonacci(n):
    return n
\```
```

**Solución DSPy**: La signature refinada instruye explícitamente al modelo para generar solo código puro. DSPy traduce estas instrucciones en prompts optimizados que guían el comportamiento del LM sin necesidad de regex o post-procesamiento.

### Context Manager (Thread-safe y Async-safe)
Las funciones usan `dspy.context(lm=lm)` en lugar de `dspy.settings.configure()` para garantizar compatibilidad con FastAPI (async) y evitar conflictos entre múltiples requests concurrentes:

```python
lm = dspy.LM('openrouter/openai/gpt-4o', api_key=api_key)
with dspy.context(lm=lm):
    code_generator = dspy.ChainOfThought('design_text -> python_code')
    response = code_generator(design_text=design_text)
```

**Ventajas de usar `dspy.context()`:**
- ✅ Async-safe: Funciona correctamente en FastAPI y otros frameworks async
- ✅ Thread-safe: Permite múltiples llamadas concurrentes sin conflictos
- ✅ Aislamiento: Cada request tiene su propio contexto DSPy
- ✅ Sin side effects: No modifica configuración global

## Extensibilidad con Few-Shot Learning

El diseño actual está preparado para optimización futura con ejemplos.

### Cómo agregar Few-Shot Learning

1. **Crear un dataset de ejemplos:**
```python
import dspy

# Ejemplos de diseño -> código
trainset = [
    dspy.Example(
        design_text="Función que suma dos números",
        python_code="def suma(a: int, b: int) -> int:\n    return a + b"
    ).with_inputs("design_text"),
    dspy.Example(
        design_text="Función que calcula el factorial",
        python_code="def factorial(n: int) -> int:\n    if n <= 1:\n        return 1\n    return n * factorial(n-1)"
    ).with_inputs("design_text"),
    # Más ejemplos...
]
```

2. **Compilar con BootstrapFewShot:**
```python
from dspy.teleprompt import BootstrapFewShot

# Definir métrica de calidad (opcional pero recomendado)
def code_quality_metric(example, pred, trace=None):
    # Verificar que el código sea válido Python
    try:
        compile(pred.python_code, '<string>', 'exec')
        return 1.0
    except:
        return 0.0

# Crear el optimizador
optimizer = BootstrapFewShot(
    metric=code_quality_metric,
    max_bootstrapped_demos=4,
    max_labeled_demos=2
)

# Compilar el generador
code_generator = dspy.ChainOfThought('design_text -> python_code')
compiled_generator = optimizer.compile(
    student=code_generator,
    trainset=trainset
)

# Guardar el modelo optimizado
compiled_generator.save('text_to_code_optimized.json')
```

3. **Usar el modelo optimizado:**
```python
# Cargar en la función generate_python_code
compiled_generator = dspy.ChainOfThought('design_text -> python_code')
compiled_generator.load('text_to_code_optimized.json')

response = compiled_generator(design_text=design_text)
```

### Otros Optimizadores Disponibles

**MIPROv2** (Recomendado para mejores resultados):
```python
from dspy.teleprompt import MIPROv2

teleprompter = MIPROv2(
    metric=code_quality_metric,
    auto="light"  # o "medium", "heavy"
)

optimized = teleprompter.compile(
    program=code_generator,
    trainset=trainset,
    max_bootstrapped_demos=3,
    max_labeled_demos=4
)
```

**KNNFewShot** (Para selección dinámica de ejemplos):
```python
from dspy.teleprompt import KNNFewShot
from sentence_transformers import SentenceTransformer
from dspy import Embedder

knn_optimizer = KNNFewShot(
    k=3,
    trainset=trainset,
    vectorizer=Embedder(SentenceTransformer("all-MiniLM-L6-v2").encode)
)

compiled_knn = knn_optimizer.compile(
    student=dspy.ChainOfThought("design_text -> python_code")
)
```

## Ejemplos de Uso

Consulta los archivos en `examples/`:
- `design_example.md` - Ejemplo de documento de diseño
- `test_text_to_code.py` - Script de prueba completo

## Testing

Ejecutar pruebas:
```bash
cd examples
python test_text_to_code.py
```

## Single Responsibility Principle

El módulo sigue SRP:
- `generate_python_code`: Solo genera código (lógica DSPy)
- `read_design_document`: Solo lee archivos
- `write_python_file`: Solo escribe archivos
- `text_to_code`: Orquesta las operaciones (wrapper)

Esto permite reutilizar las funciones individuales en otros contextos.

## Roadmap

- [ ] Agregar soporte para múltiples modelos LM
- [ ] Implementar cache de generaciones
- [ ] Agregar validación de código generado
- [ ] Implementar few-shot learning con ejemplos
- [ ] Agregar métricas de calidad
- [ ] Soporte para lenguajes adicionales
- [ ] Integración con linters (ruff, black)

## Referencias

- [DSPy Documentation](https://dspy.ai)
- [DSPy ChainOfThought](https://dspy.ai/api/modules/ChainOfThought)
- [DSPy Optimizers](https://dspy.ai/learn/optimization/optimizers)
- [Bootstrap Few-Shot](https://dspy.ai/api/optimizers/BootstrapFewShot)
