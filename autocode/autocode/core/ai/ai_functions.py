"""
AI functions using DSPy for intelligent operations.
"""
import dspy
from autocode.autocode.interfaces.registry import register_function
import os


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
    dspy.settings.configure(lm=lm)
    
    # Crear y ejecutar el módulo de QA
    qa = dspy.ChainOfThought('question -> answer')
    response = qa(question=question)
    
    return response.answer
