"""
High-level pipelines for AI operations.

This module contains orchestration functions that combine file I/O
with DSPy generation for complete workflows.
"""
from typing import Literal, Dict, Any, Optional, List, get_args
import litellm
from autocode.interfaces.registry import register_function, get_functions_for_interface
from autocode.interfaces.models import GenericOutput
from autocode.core.ai.models import DspyOutput
from autocode.core.utils.file_utils import (
    read_design_document,
    write_python_file,
    read_file,
    write_file
)
from autocode.core.utils.openrouter import fetch_models_info
from autocode.core.ai.dspy_utils import (
    generate_with_dspy, 
    ModelType, 
    ModuleType,
    get_all_module_kwargs_schemas,
    get_available_tools_info
)
from autocode.core.ai.signatures import (
    CodeGenerationSignature,
    DesignDocumentSignature,
    QASignature,
    ChatSignature
)
from autocode.interfaces.models import FunctionInfo


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
) -> GenericOutput:
    """
    Convierte un documento de diseño en código Python.
    
    Lee un documento de diseño (Markdown u otro formato de texto),
    genera código Python usando DSPy, y guarda el resultado en un archivo .py.
    
    Args:
        input_path: Ruta al archivo de documento de diseño
        output_path: Ruta donde guardar el archivo .py generado
        model: Modelo de inferencia a utilizar
        
    Returns:
        GenericOutput con información sobre el proceso de generación
    """
    try:
        # Leer el documento de diseño
        design_text = read_design_document(input_path)
        
        # Generar código usando generate_with_dspy (retorna DspyOutput)
        output = generate_with_dspy(
            signature_class=CodeGenerationSignature,
            inputs={'design_text': design_text},
            model=model
        )
        
        # Verificar éxito
        if not output.success:
            return GenericOutput(
                success=False,
                result={},
                message=f"Error: {output.message}"
            )
        
        # Extraer el campo python_code del result
        python_code = output.result.get('python_code', '')
        if not python_code:
            return GenericOutput(
                success=False,
                result={},
                message="Error: No se generó código Python"
            )
        
        # Escribir el código en el archivo de salida
        write_python_file(python_code, output_path)
        
        lines_count = len(python_code.splitlines())
        return GenericOutput(
            success=True,
            result={
                "input_path": input_path,
                "output_path": output_path,
                "lines_count": lines_count,
                "code_preview": python_code[:200] + "..." if len(python_code) > 200 else python_code
            },
            message=f"Código generado exitosamente: {lines_count} líneas escritas en {output_path}"
        )
        
    except ValueError as e:
        return GenericOutput(success=False, result={}, message=f"Error: {str(e)}")
    except (FileNotFoundError, IOError) as e:
        return GenericOutput(success=False, result={}, message=f"Error: {str(e)}")
    except Exception as e:
        return GenericOutput(success=False, result={}, message=f"Error inesperado: {str(e)}")


@register_function(http_methods=["GET", "POST"])
def code_to_design(
    input_path: str,
    output_path: str,
    include_diagrams: bool = True,
    model: ModelType = 'openrouter/openai/gpt-4o'
) -> GenericOutput:
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
        GenericOutput con información sobre el proceso de generación
    """
    try:
        # Leer el código Python
        python_code = read_file(input_path)
        
        # Generar documento usando generate_with_dspy (retorna DspyOutput)
        output = generate_with_dspy(
            signature_class=DesignDocumentSignature,
            inputs={'python_code': python_code, 'include_diagrams': include_diagrams},
            model=model
        )
        
        # Verificar éxito
        if not output.success:
            return GenericOutput(
                success=False,
                result={},
                message=f"Error: {output.message}"
            )
        
        # Extraer el campo design_document del result
        design_document = output.result.get('design_document', '')
        if not design_document:
            return GenericOutput(
                success=False,
                result={},
                message="Error: No se generó documento de diseño"
            )
        
        # Escribir el documento en el archivo de salida
        write_file(design_document, output_path, file_type='markdown')
        
        lines_count = len(design_document.splitlines())
        return GenericOutput(
            success=True,
            result={
                "input_path": input_path,
                "output_path": output_path,
                "lines_count": lines_count,
                "includes_diagrams": include_diagrams,
                "document_preview": design_document[:200] + "..." if len(design_document) > 200 else design_document
            },
            message=f"Documento de diseño generado exitosamente: {lines_count} líneas escritas en {output_path}"
        )
        
    except ValueError as e:
        return GenericOutput(success=False, result={}, message=f"Error: {str(e)}")
    except (FileNotFoundError, IOError) as e:
        return GenericOutput(success=False, result={}, message=f"Error: {str(e)}")
    except Exception as e:
        return GenericOutput(success=False, result={}, message=f"Error inesperado: {str(e)}")


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
) -> DspyOutput:
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
        DspyOutput con todos los outputs de la signature y metadata DSPy
        
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
        return DspyOutput(
            success=False,
            result={},
            message=f"Signature type '{signature_type}' no válido. Opciones: {list(SIGNATURE_MAP.keys())}"
        )
    
    # Retorna DspyOutput completo (útil para funciones genéricas con múltiples outputs)
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
) -> GenericOutput:
    """
    Genera código Python a partir de un texto de diseño.
    
    Args:
        design_text: Descripción del código a generar
        model: Modelo de inferencia a utilizar
        
    Returns:
        GenericOutput con el código Python generado en el campo result
    """
    try:
        output = generate_with_dspy(
            signature_class=CodeGenerationSignature,
            inputs={'design_text': design_text},
            model=model
        )
        
        # Verificar éxito
        if not output.success:
            return GenericOutput(
                success=False,
                result="",
                message=output.message
            )
        
        # Extraer el campo python_code
        python_code = output.result.get('python_code', '')
        if not python_code:
            return GenericOutput(
                success=False,
                result="",
                message="No se generó código Python"
            )
        
        return GenericOutput(
            success=True,
            result=python_code,
            message="Código generado exitosamente"
        )
        
    except Exception as e:
        return GenericOutput(
            success=False,
            result="",
            message=f"Error generando código: {str(e)}"
        )


@register_function(http_methods=["GET", "POST"])
def generate_design(
    python_code: str,
    include_diagrams: bool = True,
    model: ModelType = 'openrouter/openai/gpt-4o'
) -> GenericOutput:
    """
    Genera un documento de diseño Markdown a partir de código Python.
    
    Args:
        python_code: Código Python a documentar
        include_diagrams: Si se deben incluir diagramas Mermaid
        model: Modelo de inferencia a utilizar
        
    Returns:
        GenericOutput con el documento de diseño en el campo result
    """
    try:
        output = generate_with_dspy(
            signature_class=DesignDocumentSignature,
            inputs={'python_code': python_code, 'include_diagrams': include_diagrams},
            model=model
        )
        
        # Verificar éxito
        if not output.success:
            return GenericOutput(
                success=False,
                result="",
                message=output.message
            )
        
        # Extraer el campo design_document
        design_document = output.result.get('design_document', '')
        if not design_document:
            return GenericOutput(
                success=False,
                result="",
                message="No se generó documento de diseño"
            )
        
        return GenericOutput(
            success=True,
            result=design_document,
            message="Documento de diseño generado exitosamente"
        )
        
    except Exception as e:
        return GenericOutput(
            success=False,
            result="",
            message=f"Error generando documento: {str(e)}"
        )


@register_function(http_methods=["GET", "POST"])
def generate_answer(
    question: str,
    model: ModelType = 'openrouter/openai/gpt-4o'
) -> GenericOutput:
    """
    Responde una pregunta usando razonamiento.
    
    Args:
        question: Pregunta a responder
        model: Modelo de inferencia a utilizar
        
    Returns:
        GenericOutput con la respuesta en el campo result
    """
    try:
        output = generate_with_dspy(
            signature_class=QASignature,
            inputs={'question': question},
            model=model
        )
        
        # Verificar éxito
        if not output.success:
            return GenericOutput(
                success=False,
                result="",
                message=output.message
            )
        
        # Extraer el campo answer
        answer = output.result.get('answer', '')
        if not answer:
            return GenericOutput(
                success=False,
                result="",
                message="No se generó respuesta"
            )
        
        return GenericOutput(
            success=True,
            result=answer,
            message="Respuesta generada exitosamente"
        )
        
    except Exception as e:
        return GenericOutput(
            success=False,
            result="",
            message=f"Error generando respuesta: {str(e)}"
        )


@register_function(http_methods=["POST"])
def calculate_context_usage(
    model: ModelType,
    messages: List[Dict[str, str]]
) -> GenericOutput:
    """
    Calcula el uso actual y máximo de la ventana de contexto para un modelo y mensajes dados.
    
    Usa litellm para:
    - Contar tokens del mensaje actual usando token_counter
    - Obtener el tamaño máximo de ventana de contexto usando get_max_tokens
    
    Args:
        model: Modelo de inferencia a utilizar
        messages: Lista de mensajes en formato OpenAI [{"role": "user"|"assistant", "content": "..."}]
        
    Returns:
        GenericOutput con result={"current": int, "max": int, "percentage": float}
    """
    try:
        # Calcular tokens actuales usando litellm.token_counter
        current_tokens = litellm.token_counter(model=model, messages=messages)
        
        # Obtener tamaño máximo de ventana de contexto
        max_tokens = litellm.get_max_tokens(model)
        
        # Calcular porcentaje de uso
        percentage = (current_tokens / max_tokens * 100) if max_tokens > 0 else 0
        
        return GenericOutput(
            success=True,
            result={
                "current": current_tokens,
                "max": max_tokens,
                "percentage": round(percentage, 2)
            },
            message=f"Context usage: {current_tokens}/{max_tokens} tokens ({percentage:.1f}%)"
        )
        
    except Exception as e:
        return GenericOutput(
            success=False,
            result={"current": 0, "max": 0, "percentage": 0},
            message=f"Error calculando uso de contexto: {str(e)}"
        )


@register_function(http_methods=["POST"], interfaces=["api", "cli"])
def chat(
    message: str,
    conversation_history: str = "",
    model: ModelType = 'openrouter/openai/gpt-4o',
    max_tokens: int = 16000,
    temperature: float = 0.7,
    module_type: ModuleType = 'ReAct',
    module_kwargs: Optional[Dict[str, Any]] = None,
    enabled_tools: Optional[List[str]] = None,
    lm_kwargs: Optional[Dict[str, Any]] = None
) -> DspyOutput:
    """
    Chat conversacional con acceso a herramientas MCP.
    
    Este endpoint usa DSPy con el módulo configurado para:
    - Usar las funciones MCP registradas como herramientas con schemas completos
    - Razonar sobre qué herramientas usar para responder (con ReAct)
    - Retornar un DspyOutput completo con trajectory, reasoning, history, etc.
    
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
        
    Returns:
        DspyOutput con:
        - result: Dict con 'response', 'trajectory' (si ReAct), 'reasoning', etc.
        - history: Historial completo de llamadas al LM con metadata
        - trajectory: Trayectoria de ReAct (thoughts, tool_names, tool_args, observations)
        - reasoning: Razonamiento paso a paso
        - completions: Múltiples completions si aplica
    """
    import dspy
    
    try:
        # Obtener funciones MCP del registry
        mcp_functions = get_functions_for_interface("mcp")
        functions_to_use = mcp_functions  # Ya es una lista de FunctionInfo
        
        tools = []
        for func_info in functions_to_use:
            # Filtrar por enabled_tools si se especificó
            if enabled_tools is not None and func_info.name not in enabled_tools:
                continue
            
            # Crear wrapper de tool con schema enriquecido
            def create_tool_wrapper(fi: FunctionInfo):
                def tool_func(**kwargs):
                    """Tool wrapper que ejecuta funciones inyectadas."""
                    try:
                        # DSPy ReAct puede pasar los params dentro de un argumento 'kwargs'
                        # Si recibimos kwargs={'name': 'value'} en lugar de name='value'
                        if 'kwargs' in kwargs and isinstance(kwargs['kwargs'], dict):
                            actual_kwargs = kwargs['kwargs']
                        else:
                            actual_kwargs = kwargs
                        
                        return fi.func(**actual_kwargs)
                    except Exception as e:
                        return f"Error ejecutando {fi.name}: {str(e)}"
                
                # Configurar metadata del tool con schema detallado
                tool_func.__name__ = fi.name
                
                # Construir docstring enriquecida con información de parámetros
                doc_parts = [fi.description, "\n\nArgs:"]
                for param in fi.params:
                    # Formato: nombre (tipo, required/optional, default): descripción
                    param_type = param.type.__name__ if hasattr(param.type, '__name__') else str(param.type)
                    required_str = "required" if param.required else f"optional, default={param.default}"
                    
                    # Agregar choices si existen (para Literal types)
                    choices_str = ""
                    if param.choices:
                        choices_str = f" [choices: {', '.join(map(str, param.choices))}]"
                    
                    doc_parts.append(f"    {param.name} ({param_type}, {required_str}){choices_str}: {param.description}")
                
                tool_func.__doc__ = "\n".join(doc_parts)
                
                return tool_func
            
            tools.append(create_tool_wrapper(func_info))
        
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
        
    except Exception as e:
        # Retornar error en formato DspyOutput
        return DspyOutput(
            success=False,
            result={"error": f"Error en chat: {str(e)}"},
            message=f"Error en chat: {str(e)}"
        )


@register_function(http_methods=["GET"])
def get_chat_config() -> GenericOutput:
    """
    Obtiene la configuración disponible para el chat.
    
    Retorna información sobre:
    - module_kwargs_schemas: Parámetros disponibles por cada module_type
    - available_tools: Lista de tools MCP disponibles con nombre y descripción
    - models: Lista de modelos disponibles con metadata de OpenRouter
    
    Esta información permite a la UI renderizar controles dinámicos
    según el module_type seleccionado y el modelo.
    
    Returns:
        GenericOutput con:
        - result.module_kwargs_schemas: Dict[module_type, {params, supports_tools}]
        - result.available_tools: List[{name, description, enabled_by_default}]
        - result.models: List[Dict] con info de cada modelo
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

        # Obtener funciones MCP del registry
        mcp_functions = get_functions_for_interface("mcp")

        return GenericOutput(
            success=True,
            result={
                "module_kwargs_schemas": get_all_module_kwargs_schemas(),
                "available_tools": get_available_tools_info(mcp_functions),
                "models": models_data
            },
            message="Configuración de chat obtenida exitosamente"
        )
    except Exception as e:
        return GenericOutput(
            success=False,
            result={},
            message=f"Error obteniendo configuración: {str(e)}"
        )
