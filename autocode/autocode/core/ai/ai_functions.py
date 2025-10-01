"""
AI functions using DSPy for intelligent operations.
"""
import dspy
from autocode.autocode.interfaces.registry import register_function
from autocode.autocode.core.utils.file_utils import read_design_document, write_python_file
import os


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
def simple_qa(question: str) -> str:
    """
    Responde una pregunta simple usando DSPy ChainOfThought.
    
    Args:
        question: La pregunta a responder
        
    Returns:
        La respuesta a la pregunta
    """
    # Configuración de DSPy con OpenRouter
    api_key = os.getenv('OPENROUTER_API_KEY')
    if not api_key:
        return "Error: OPENROUTER_API_KEY no está configurada en las variables de entorno"
    
    lm = dspy.LM('openrouter/openai/gpt-4o', api_key=api_key)
    
    # Usar context en lugar de configure para evitar conflictos en async tasks
    with dspy.context(lm=lm):
        # Crear y ejecutar el módulo de QA
        qa = dspy.ChainOfThought('question -> answer')
        response = qa(question=question)
    
    return response.answer


@register_function(http_methods=["GET", "POST"])
def generate_python_code(design_text: str) -> str:
    """
    Genera código Python a partir de un documento de diseño usando DSPy.
    
    Esta función usa DSPy con una signature refinada para generar código Python
    limpio, sin bloques markdown ni formato adicional. Solo código ejecutable.
    Diseñada para ser extensible con few-shot learning en el futuro.
    
    Args:
        design_text: El texto del documento de diseño que describe el código a generar
        
    Returns:
        El código Python generado como string limpio (sin markdown)
    """
    # Configuración de DSPy con OpenRouter
    api_key = os.getenv('OPENROUTER_API_KEY')
    if not api_key:
        return "Error: OPENROUTER_API_KEY no está configurada en las variables de entorno"
    
    lm = dspy.LM('openrouter/openai/gpt-4o', api_key=api_key)
    
    # Usar context en lugar de configure para evitar conflictos en async tasks
    with dspy.context(lm=lm):
        # Usar signature class-based para mayor control sobre el output
        # La signature incluye instrucciones explícitas para generar código limpio
        code_generator = dspy.ChainOfThought(CodeGenerationSignature)
        
        # Generar el código
        response = code_generator(design_text=design_text)
    
    return response.python_code


@register_function(http_methods=["GET", "POST"])
def text_to_code(input_path: str, output_path: str) -> str:
    """
    Convierte un documento de diseño en código Python.
    
    Lee un documento de diseño (Markdown u otro formato de texto),
    genera código Python usando DSPy, y guarda el resultado en un archivo .py.
    
    Args:
        input_path: Ruta al archivo de documento de diseño
        output_path: Ruta donde guardar el archivo .py generado
        
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
        python_code = generate_python_code(design_text)
        
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
