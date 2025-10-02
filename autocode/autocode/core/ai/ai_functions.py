"""
AI functions using DSPy for intelligent operations.
"""
import dspy
from typing import Literal
from autocode.autocode.interfaces.registry import register_function
from autocode.autocode.core.utils.file_utils import read_design_document, write_python_file, read_file, write_file
import os

# Available models for inference
ModelType = Literal[
    'openrouter/openai/gpt-4o',
    'openrouter/x-ai/grok-4',
    'openrouter/anthropic/claude-sonnet-4.5',
    'openrouter/openai/gpt-5',
    'openrouter/openai/gpt-5-codex'
]


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


@register_function(http_methods=["GET", "POST"])
def simple_qa(question: str, model: ModelType = 'openrouter/openai/gpt-4o') -> str:
    """
    Responde una pregunta simple usando DSPy ChainOfThought.
    
    Args:
        question: La pregunta a responder
        model: Modelo de inferencia a utilizar
        
    Returns:
        La respuesta a la pregunta
    """
    # Configuración de DSPy con OpenRouter
    api_key = os.getenv('OPENROUTER_API_KEY')
    if not api_key:
        return "Error: OPENROUTER_API_KEY no está configurada en las variables de entorno"
    
    lm = dspy.LM(model, api_key=api_key)
    
    # Usar context en lugar de configure para evitar conflictos en async tasks
    with dspy.context(lm=lm):
        # Crear y ejecutar el módulo de QA
        qa = dspy.ChainOfThought('question -> answer')
        response = qa(question=question)
    
    return response.answer


@register_function(http_methods=["GET", "POST"])
def generate_python_code(design_text: str, model: ModelType = 'openrouter/openai/gpt-4o') -> str:
    """
    Genera código Python a partir de un documento de diseño usando DSPy.
    
    Esta función usa DSPy con una signature refinada para generar código Python
    limpio, sin bloques markdown ni formato adicional. Solo código ejecutable.
    Diseñada para ser extensible con few-shot learning en el futuro.
    
    Args:
        design_text: El texto del documento de diseño que describe el código a generar
        model: Modelo de inferencia a utilizar
        
    Returns:
        El código Python generado como string limpio (sin markdown)
    """
    # Configuración de DSPy con OpenRouter
    api_key = os.getenv('OPENROUTER_API_KEY')
    if not api_key:
        return "Error: OPENROUTER_API_KEY no está configurada en las variables de entorno"
    
    lm = dspy.LM(model, api_key=api_key)
    
    # Usar context en lugar de configure para evitar conflictos en async tasks
    with dspy.context(lm=lm):
        # Usar signature class-based para mayor control sobre el output
        # La signature incluye instrucciones explícitas para generar código limpio
        code_generator = dspy.ChainOfThought(CodeGenerationSignature)
        
        # Generar el código
        response = code_generator(design_text=design_text)
    
    return response.python_code


@register_function(http_methods=["GET", "POST"])
def text_to_code(input_path: str, output_path: str, model: ModelType = 'openrouter/openai/gpt-4o') -> str:
    """
    Convierte un documento de diseño en código Python.
    
    Lee un documento de diseño (Markdown u otro formato de texto),
    genera código Python usando DSPy, y guarda el resultado en un archivo .py.
    
    Args:
        input_path: Ruta al archivo de documento de diseño
        output_path: Ruta donde guardar el archivo .py generado
        model: Modelo de inferencia a utilizar
        
    Returns:
        Mensaje de éxito con las rutas procesadas
        
    Raises:
        FileNotFoundError: Si el archivo de entrada no existe
        IOError: Si hay error al leer o escribir archivos
    """
    try:
        # Leer el documento de diseño
        design_text = read_design_document(input_path)
        
        # Generar el código Python
        python_code = generate_python_code(design_text, model)
        
        # Verificar que se generó código válido
        if python_code.startswith("Error:"):
            return python_code
        
        # Escribir el código en el archivo de salida
        write_python_file(python_code, output_path)
        
        return f"Código generado exitosamente:\n- Input: {input_path}\n- Output: {output_path}\n- Líneas: {len(python_code.splitlines())}"
        
    except (FileNotFoundError, IOError) as e:
        return f"Error: {str(e)}"
    except Exception as e:
        return f"Error inesperado: {str(e)}"


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
    - Gestión de Estado y Recursos
    - Artefactos de Entrada y Salida
    - Diagramas Mermaid (flowcharts, secuencias, estados, modelos de clases, etc.)
    - Ejemplos de Uso
    - Manejo de Errores y Casos Límite
    - Consideraciones de Rendimiento y Escalabilidad
    - Suposiciones y Limitaciones
    - Estrategia de Testing
    - Inventario de Tests
    
    Los diagramas Mermaid deben ser válidos y representar flujos, arquitectura,
    secuencias de interacción, estados, entrada/salida y modelos de clases relevantes.
    """
    
    python_code: str = dspy.InputField(
        desc="Código Python fuente a analizar y documentar"
    )
    include_diagrams: bool = dspy.InputField(
        desc="Si se deben incluir diagramas Mermaid en el documento"
    )
    design_document: str = dspy.OutputField(
        desc="Documento de diseño completo en Markdown puro. Sin bloques ```markdown, sin explicaciones adicionales. Solo el Markdown válido con todas las secciones estructuradas."
    )


@register_function(http_methods=["GET", "POST"])
def generate_design_document(python_code: str, include_diagrams: bool = True, model: ModelType = 'openrouter/openai/gpt-4o') -> str:
    """
    Genera un documento de diseño en Markdown a partir de código Python usando DSPy.
    
    Esta función usa DSPy con una signature refinada para generar documentación
    estructurada en Markdown, sin bloques adicionales ni formato extra. Solo Markdown válido.
    Diseñada para ser extensible con few-shot learning en el futuro.
    
    Args:
        python_code: El código Python fuente a analizar y documentar
        include_diagrams: Si se deben incluir diagramas Mermaid (default: True)
        model: Modelo de inferencia a utilizar
        
    Returns:
        El documento de diseño generado como string Markdown limpio
    """
    # Configuración de DSPy con OpenRouter
    api_key = os.getenv('OPENROUTER_API_KEY')
    if not api_key:
        return "Error: OPENROUTER_API_KEY no está configurada en las variables de entorno"
    
    lm = dspy.LM(model, api_key=api_key)
    
    # Usar context en lugar de configure para evitar conflictos en async tasks
    with dspy.context(lm=lm):
        # Usar signature class-based para mayor control sobre el output
        # La signature incluye instrucciones explícitas para generar Markdown limpio
        design_generator = dspy.ChainOfThought(DesignDocumentSignature)
        
        # Generar el documento
        response = design_generator(
            python_code=python_code,
            include_diagrams=include_diagrams
        )
    
    return response.design_document


@register_function(http_methods=["GET", "POST"])
def code_to_design(input_path: str, output_path: str, include_diagrams: bool = True, model: ModelType = 'openrouter/openai/gpt-4o') -> str:
    """
    Convierte código Python en un documento de diseño Markdown.
    
    Lee un archivo de código Python, genera un documento de diseño usando DSPy,
    y guarda el resultado en un archivo .md.
    
    Args:
        input_path: Ruta al archivo .py de código fuente
        output_path: Ruta donde guardar el archivo .md generado
        include_diagrams: Si se deben incluir diagramas Mermaid (default: True)
        model: Modelo de inferencia a utilizar
        
    Returns:
        Mensaje de éxito con las rutas procesadas
        
    Raises:
        FileNotFoundError: Si el archivo de entrada no existe
        IOError: Si hay error al leer o escribir archivos
    """
    try:
        # Leer el código Python
        python_code = read_file(input_path)
        
        # Generar el documento de diseño
        design_document = generate_design_document(python_code, include_diagrams, model)
        
        # Verificar que se generó un documento válido
        if design_document.startswith("Error:"):
            return design_document
        
        # Escribir el documento en el archivo de salida
        write_file(design_document, output_path, file_type='markdown')
        
        return f"Documento de diseño generado exitosamente:\n- Input: {input_path}\n- Output: {output_path}\n- Líneas: {len(design_document.splitlines())}\n- Diagramas: {'Sí' if include_diagrams else 'No'}"
        
    except (FileNotFoundError, IOError) as e:
        return f"Error: {str(e)}"
    except Exception as e:
        return f"Error inesperado: {str(e)}"
