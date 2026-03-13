"""
DSPy Signatures for AI operations.

This module contains all the signature definitions used for structured
AI generation tasks with DSPy.
"""
import dspy


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


class TaskExecutionSignature(dspy.Signature):
    """You are a precise code executor. Complete the assigned programming task
    using the available file tools. Read files you need for context, then
    create or modify files as instructed. Be thorough and precise.
    Only modify what is necessary. Verify your changes by reading the file after writing."""

    task_instruction: str = dspy.InputField(
        desc="Complete task description including what to do, implementation details, and acceptance criteria"
    )
    file_path: str = dspy.InputField(
        desc="Primary target file path for this task"
    )
    completion_summary: str = dspy.OutputField(
        desc="Brief summary of all changes made, files created/modified, and any issues encountered"
    )
