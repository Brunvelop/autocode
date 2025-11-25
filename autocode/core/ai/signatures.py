"""
DSPy Signatures for AI operations.

This module contains all the signature definitions used for structured
AI generation tasks with DSPy.
"""
import dspy


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


class QASignature(dspy.Signature):
    """
    Responde preguntas usando razonamiento paso a paso.
    """
    
    question: str = dspy.InputField(
        desc="La pregunta a responder"
    )
    answer: str = dspy.OutputField(
        desc="La respuesta a la pregunta"
    )


class ChatSignature(dspy.Signature):
    """
    Chat conversacional con memoria y capacidad de usar herramientas (tools).
    
    Este signature está diseñado para trabajar con ReAct, permitiendo al modelo:
    - Mantener contexto de la conversación anterior
    - Razonar sobre qué herramientas usar
    - Generar respuestas coherentes y contextualmente apropiadas
    """
    
    message: str = dspy.InputField(
        desc="Mensaje actual del usuario"
    )
    conversation_history: str = dspy.InputField(
        desc="Historial de la conversación en formato 'User: ... | Assistant: ...'"
    )
    response: str = dspy.OutputField(
        desc="Respuesta del asistente al mensaje del usuario, considerando el contexto"
    )
