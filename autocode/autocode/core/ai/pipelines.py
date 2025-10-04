"""
High-level pipelines for AI operations.

This module contains orchestration functions that combine file I/O
with DSPy generation for complete workflows.
"""
from typing import Literal, Dict, Any, Optional
from autocode.autocode.interfaces.registry import register_function
from autocode.autocode.core.utils.file_utils import (
    read_design_document,
    write_python_file,
    read_file,
    write_file
)
from autocode.autocode.core.ai.dspy_utils import generate_with_dspy, ModelType, ModuleType
from autocode.autocode.core.ai.signatures import (
    CodeGenerationSignature,
    DesignDocumentSignature,
    QASignature
)


# Available signature types for UI selection
SignatureType = Literal['code_generation', 'design_document', 'qa']


# Mapping from signature type strings to signature classes
SIGNATURE_MAP = {
    'code_generation': CodeGenerationSignature,
    'design_document': DesignDocumentSignature,
    'qa': QASignature
}


@register_function(http_methods=["GET", "POST"])
def text_to_code(
    input_path: str,
    output_path: str,
    model: ModelType = 'openrouter/openai/gpt-4o'
) -> str:
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
        
        # Generar código usando generate_with_dspy (retorna dict)
        result = generate_with_dspy(
            signature_class=CodeGenerationSignature,
            inputs={'design_text': design_text},
            model=model
        )
        
        # Verificar errores
        if 'error' in result:
            return f"Error: {result['error']}"
        
        # Extraer el campo python_code del dict
        python_code = result.get('python_code', '')
        if not python_code:
            return "Error: No se generó código Python"
        
        # Escribir el código en el archivo de salida
        write_python_file(python_code, output_path)
        
        return f"Código generado exitosamente:\n- Input: {input_path}\n- Output: {output_path}\n- Líneas: {len(python_code.splitlines())}"
        
    except ValueError as e:
        return f"Error: {str(e)}"
    except (FileNotFoundError, IOError) as e:
        return f"Error: {str(e)}"
    except Exception as e:
        return f"Error inesperado: {str(e)}"


@register_function(http_methods=["GET", "POST"])
def code_to_design(
    input_path: str,
    output_path: str,
    include_diagrams: bool = True,
    model: ModelType = 'openrouter/openai/gpt-4o'
) -> str:
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
        
        # Generar documento usando generate_with_dspy (retorna dict)
        result = generate_with_dspy(
            signature_class=DesignDocumentSignature,
            inputs={'python_code': python_code, 'include_diagrams': include_diagrams},
            model=model
        )
        
        # Verificar errores
        if 'error' in result:
            return f"Error: {result['error']}"
        
        # Extraer el campo design_document del dict
        design_document = result.get('design_document', '')
        if not design_document:
            return "Error: No se generó documento de diseño"
        
        # Escribir el documento en el archivo de salida
        write_file(design_document, output_path, file_type='markdown')
        
        return f"Documento de diseño generado exitosamente:\n- Input: {input_path}\n- Output: {output_path}\n- Líneas: {len(design_document.splitlines())}\n- Diagramas: {'Sí' if include_diagrams else 'No'}"
        
    except ValueError as e:
        return f"Error: {str(e)}"
    except (FileNotFoundError, IOError) as e:
        return f"Error: {str(e)}"
    except Exception as e:
        return f"Error inesperado: {str(e)}"


# Generic wrapper functions with Literal for UI selection

@register_function(http_methods=["GET", "POST"])
def generate(
    signature_type: SignatureType,
    inputs: Dict[str, Any],
    model: ModelType = 'openrouter/openai/gpt-4o',
    module_type: ModuleType = 'ChainOfThought',
    module_kwargs: Optional[Dict[str, Any]] = None,
    max_tokens: int = 16000,
    temperature: float = 0.7
) -> Dict[str, Any]:
    """
    Generador genérico con selección de signature y módulo DSPy desde la UI.
    
    Ejecuta cualquier signature disponible con los inputs proporcionados,
    usando el módulo DSPy seleccionado (Predict, ChainOfThought, ReAct, etc.).
    
    Args:
        signature_type: Tipo de signature a utilizar (code_generation, design_document, qa)
        inputs: Diccionario con los parámetros de entrada para la signature seleccionada
        model: Modelo de inferencia a utilizar
        module_type: Tipo de módulo DSPy (Predict, ChainOfThought, ProgramOfThought, ReAct, MultiChainComparison)
        module_kwargs: Parámetros adicionales específicos del módulo (ej: tools para ReAct, n para Predict)
        max_tokens: Número máximo de tokens a generar (default: 16000). Aumentar si las respuestas se truncan
        temperature: Temperature para la generación (default: 0.7). Valores más altos = más creatividad
        
    Returns:
        Dict con todos los outputs de la signature (puede tener múltiples fields)
        
    Example inputs por signature_type:
        - code_generation: {"design_text": "Create a function that..."}
        - design_document: {"python_code": "def foo()...", "include_diagrams": true}
        - qa: {"question": "What is...?"}
    
    Example module_kwargs:
        - ReAct: {"tools": [function1, function2], "max_iters": 5}
        - Predict: {"n": 5}  # Para múltiples completions
    
    LM Parameters:
        - max_tokens: Controla la longitud máxima de la respuesta. Aumentar si ves warnings de truncamiento
        - temperature: Controla la aleatoriedad (0.0 = determinista, 1.0+ = más creativo)
    """
    signature_class = SIGNATURE_MAP.get(signature_type)
    if not signature_class:
        return {"error": f"Signature type '{signature_type}' no válido. Opciones: {list(SIGNATURE_MAP.keys())}"}
    
    # Retorna el dict completo (útil para funciones genéricas con múltiples outputs)
    return generate_with_dspy(
        signature_class=signature_class,
        inputs=inputs,
        model=model,
        module_type=module_type,
        module_kwargs=module_kwargs or {},
        max_tokens=max_tokens,
        temperature=temperature
    )


@register_function(http_methods=["GET", "POST"])
def generate_code(
    design_text: str,
    model: ModelType = 'openrouter/openai/gpt-4o'
) -> str:
    """
    Genera código Python a partir de un texto de diseño.
    
    Args:
        design_text: Descripción del código a generar
        model: Modelo de inferencia a utilizar
        
    Returns:
        Código Python generado
    """
    result = generate_with_dspy(
        signature_class=CodeGenerationSignature,
        inputs={'design_text': design_text},
        model=model
    )
    
    # Verificar errores
    if 'error' in result:
        return f"Error: {result['error']}"
    
    # Extraer el campo python_code
    return result.get('python_code', 'Error: No se generó código')


@register_function(http_methods=["GET", "POST"])
def generate_design(
    python_code: str,
    include_diagrams: bool = True,
    model: ModelType = 'openrouter/openai/gpt-4o'
) -> str:
    """
    Genera un documento de diseño Markdown a partir de código Python.
    
    Args:
        python_code: Código Python a documentar
        include_diagrams: Si se deben incluir diagramas Mermaid
        model: Modelo de inferencia a utilizar
        
    Returns:
        Documento de diseño en Markdown
    """
    result = generate_with_dspy(
        signature_class=DesignDocumentSignature,
        inputs={'python_code': python_code, 'include_diagrams': include_diagrams},
        model=model
    )
    
    # Verificar errores
    if 'error' in result:
        return f"Error: {result['error']}"
    
    # Extraer el campo design_document
    return result.get('design_document', 'Error: No se generó documento')


@register_function(http_methods=["GET", "POST"])
def generate_answer(
    question: str,
    model: ModelType = 'openrouter/openai/gpt-4o'
) -> str:
    """
    Responde una pregunta usando razonamiento.
    
    Args:
        question: Pregunta a responder
        model: Modelo de inferencia a utilizar
        
    Returns:
        Respuesta a la pregunta
    """
    result = generate_with_dspy(
        signature_class=QASignature,
        inputs={'question': question},
        model=model
    )
    
    # Verificar errores
    if 'error' in result:
        return f"Error: {result['error']}"
    
    # Extraer el campo answer
    return result.get('answer', 'Error: No se generó respuesta')
