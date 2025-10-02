# AI Module - Code ↔ Design Generation

Este módulo proporciona funcionalidades bidireccionales de generación usando DSPy (Declarative Self-improving Python):
- **Text to Code**: Genera código Python a partir de documentos de diseño
- **Code to Design**: Genera documentos de diseño Markdown a partir de código Python

## Funciones Disponibles

### Generación de Código (Text to Code)

### 1. `generate_python_code(design_text: str, model: str = 'openrouter/openai/gpt-4o') -> str`

Genera código Python a partir de un texto de diseño.

**Características:**
- Usa DSPy con ChainOfThought para razonamiento
- Modelo de inferencia configurable
- Extensible con few-shot learning
- Registrada en el registry (accesible vía API/CLI/MCP)

**Modelos disponibles:**
- `openrouter/openai/gpt-4o` (default)
- `openrouter/x-ai/grok-4`
- `openrouter/anthropic/claude-sonnet-4.5`
- `openrouter/openai/gpt-5`
- `openrouter/openai/gpt-5-codex`

**Uso:**
```python
from autocode.autocode.core.ai.ai_functions import generate_python_code

design = """
Crear una función que calcule el factorial de un número.
- Nombre: factorial
- Parámetro: n (int)
- Retorna: int
"""

# Usar modelo por defecto
code = generate_python_code(design)
print(code)

# Usar modelo específico
code = generate_python_code(design, model='openrouter/anthropic/claude-sonnet-4.5')
print(code)
```

**Vía CLI:**
```bash
autocode generate-python-code --design-text "Crear una función que sume dos números"
autocode generate-python-code --design-text "Crear una función que sume dos números" --model "openrouter/x-ai/grok-4"
```

**Vía API:**
```bash
curl -X POST http://localhost:8000/generate_python_code \
  -H "Content-Type: application/json" \
  -d '{"design_text": "Crear una función que sume dos números"}'
  
curl -X POST http://localhost:8000/generate_python_code \
  -H "Content-Type: application/json" \
  -d '{"design_text": "Crear una función que sume dos números", "model": "openrouter/anthropic/claude-sonnet-4.5"}'
```

### 2. `text_to_code(input_path: str, output_path: str, model: str = 'openrouter/openai/gpt-4o') -> str`

Convierte un archivo de diseño en un archivo .py.

**Características:**
- Lee documentos Markdown u otros formatos de texto
- Genera y guarda el código automáticamente
- Modelo de inferencia configurable
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

# Con modelo específico
result = text_to_code(
    input_path="design.md",
    output_path="generated.py",
    model="openrouter/x-ai/grok-4"
)
print(result)
```

**Vía CLI:**
```bash
autocode text-to-code --input-path design.md --output-path generated.py
autocode text-to-code --input-path design.md --output-path generated.py --model "openrouter/anthropic/claude-sonnet-4.5"
```

**Vía API:**
```bash
curl -X POST http://localhost:8000/text_to_code \
  -H "Content-Type: application/json" \
  -d '{"input_path": "design.md", "output_path": "generated.py"}'
  
curl -X POST http://localhost:8000/text_to_code \
  -H "Content-Type: application/json" \
  -d '{"input_path": "design.md", "output_path": "generated.py", "model": "openrouter/openai/gpt-5"}'
```

### Generación de Documentación (Code to Design)

### 3. `generate_design_document(python_code: str, include_diagrams: bool = True, model: str = 'openrouter/openai/gpt-4o') -> str`

Genera un documento de diseño Markdown a partir de código Python.

**Características:**
- Usa DSPy con ChainOfThought para análisis profundo del código
- Genera documentación estructurada siguiendo el formato de los ejemplos proporcionados
- Incluye secciones como: Resumen Ejecutivo, Componentes, Flujos, Dependencias, Diagramas Mermaid, Ejemplos, Testing, etc.
- Modelo de inferencia configurable
- Extensible con few-shot learning
- Registrada en el registry (accesible vía API/CLI/MCP)

**Uso:**
```python
from autocode.autocode.core.ai.ai_functions import generate_design_document

python_code = """
def calculate_factorial(n: int) -> int:
    '''Calcula el factorial de un número.'''
    if n <= 1:
        return 1
    return n * calculate_factorial(n - 1)
"""

design_doc = generate_design_document(python_code, include_diagrams=True)
print(design_doc)

# Con modelo específico
design_doc = generate_design_document(
    python_code, 
    include_diagrams=True,
    model='openrouter/anthropic/claude-sonnet-4.5'
)
print(design_doc)
```

**Vía CLI:**
```bash
autocode generate-design-document --python-code "def suma(a, b): return a + b" --include-diagrams true
autocode generate-design-document --python-code "def suma(a, b): return a + b" --include-diagrams true --model "openrouter/x-ai/grok-4"
```

**Vía API:**
```bash
curl -X POST http://localhost:8000/generate_design_document \
  -H "Content-Type: application/json" \
  -d '{"python_code": "def suma(a, b): return a + b", "include_diagrams": true}'
  
curl -X POST http://localhost:8000/generate_design_document \
  -H "Content-Type: application/json" \
  -d '{"python_code": "def suma(a, b): return a + b", "include_diagrams": true, "model": "openrouter/openai/gpt-5-codex"}'
```

### 4. `code_to_design(input_path: str, output_path: str, include_diagrams: bool = True, model: str = 'openrouter/openai/gpt-4o') -> str`

Convierte un archivo .py en un documento de diseño .md.

**Características:**
- Lee archivos de código Python
- Genera documentación Markdown estructurada automáticamente
- Control opcional sobre inclusión de diagramas Mermaid
- Modelo de inferencia configurable
- Manejo de errores integrado
- Registrada en el registry (accesible vía API/CLI/MCP)

**Uso:**
```python
from autocode.autocode.core.ai.ai_functions import code_to_design

result = code_to_design(
    input_path="my_module.py",
    output_path="my_module_design.md",
    include_diagrams=True
)
print(result)

# Con modelo específico
result = code_to_design(
    input_path="my_module.py",
    output_path="my_module_design.md",
    include_diagrams=True,
    model="openrouter/anthropic/claude-sonnet-4.5"
)
print(result)
```

**Vía CLI:**
```bash
autocode code-to-design --input-path my_module.py --output-path design.md --include-diagrams true
autocode code-to-design --input-path my_module.py --output-path design.md --include-diagrams true --model "openrouter/openai/gpt-5"
```

**Vía API:**
```bash
curl -X POST http://localhost:8000/code_to_design \
  -H "Content-Type: application/json" \
  -d '{"input_path": "my_module.py", "output_path": "design.md", "include_diagrams": true}'
  
curl -X POST http://localhost:8000/code_to_design \
  -H "Content-Type: application/json" \
  -d '{"input_path": "my_module.py", "output_path": "design.md", "include_diagrams": true, "model": "openrouter/x-ai/grok-4"}'
```

### 5. Funciones de I/O (Módulo separado)

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

### Signature Refinada para Documentación Limpia

De manera similar, el módulo incluye una **class-based signature** para la generación inversa (código a diseño):

```python
class DesignDocumentSignature(dspy.Signature):
    """
    Genera un documento de diseño completo en formato Markdown a partir de código Python.
    
    IMPORTANTE: El documento generado debe ser Markdown puro y bien estructurado,
    sin bloques de código extra, sin comillas triple adicionales alrededor del documento,
    y sin texto explicativo adicional fuera del documento. Solo el Markdown válido.
    
    El documento debe seguir una estructura similar a:
    - Resumen Ejecutivo
    - Componentes Principales por Archivo/Directorio
    - Flujos y Procesos Clave
    - Dependencias y Relaciones
    - Diagramas Mermaid (flowcharts, secuencias, estados, etc.)
    - Ejemplos de Uso
    - Manejo de Errores y Casos Límite
    - Consideraciones de Rendimiento y Escalabilidad
    - Suposiciones y Limitaciones
    - Estrategia de Testing
    - Inventario de Tests
    """
    
    python_code: str = dspy.InputField(desc="Código Python fuente a analizar")
    include_diagrams: bool = dspy.InputField(desc="Si incluir diagramas Mermaid")
    design_document: str = dspy.OutputField(
        desc="Documento de diseño completo en Markdown puro. Sin bloques ```markdown."
    )
```

**Ventajas del enfoque bidireccional:**
- ✅ **Consistencia**: Ambas direcciones usan el mismo patrón de DSPy signatures
- ✅ **Documentación automática**: Genera docs estructuradas siguiendo convenciones establecidas
- ✅ **Extensible**: Preparado para few-shot learning con ejemplos de código ↔ diseño
- ✅ **Control granular**: Parámetro `include_diagrams` para ajustar nivel de detalle

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

El módulo sigue SRP con funciones especializadas:

**Generación de Código:**
- `generate_python_code`: Solo genera código (lógica DSPy)
- `text_to_code`: Orquesta lectura, generación y escritura de código

**Generación de Documentación:**
- `generate_design_document`: Solo genera documentación (lógica DSPy)
- `code_to_design`: Orquesta lectura, generación y escritura de documentos

**I/O (en file_utils):**
- `read_file` / `read_design_document`: Solo lectura de archivos
- `write_file` / `write_python_file`: Solo escritura de archivos

Esta separación permite reutilizar las funciones individuales en otros contextos y facilita el testing unitario.

## Roadmap

**Mejoras Generales:**
- [ ] Agregar soporte para múltiples modelos LM
- [ ] Implementar cache de generaciones
- [ ] Implementar few-shot learning con ejemplos de código ↔ diseño
- [ ] Agregar métricas de calidad para ambas direcciones

**Code to Design:**
- [ ] Validación automática de diagramas Mermaid generados
- [ ] Soporte para análisis multi-archivo (proyectos completos)
- [ ] Generación de diagramas de arquitectura automáticos
- [ ] Detección automática de patrones de diseño en código

**Text to Code:**
- [ ] Validación de código generado con linters (ruff, black)
- [ ] Soporte para lenguajes adicionales (JavaScript, TypeScript, Go, etc.)
- [ ] Generación de tests automáticos a partir del diseño

**Optimización:**
- [ ] Compilar modelos con ejemplos de design_examples/
- [ ] Implementar métricas de similitud para documentación
- [ ] A/B testing de diferentes estrategias de prompting

## Referencias

- [DSPy Documentation](https://dspy.ai)
- [DSPy ChainOfThought](https://dspy.ai/api/modules/ChainOfThought)
- [DSPy Optimizers](https://dspy.ai/learn/optimization/optimizers)
- [Bootstrap Few-Shot](https://dspy.ai/api/optimizers/BootstrapFewShot)
