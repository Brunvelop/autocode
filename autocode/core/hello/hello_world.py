"""
Core hello_world function - pure function for greeting functionality.
"""
from autocode.interfaces.registry import register_function
from autocode.interfaces.models import GenericOutput


@register_function(http_methods=["GET", "POST"])
def hello_world(name: str = "World") -> GenericOutput:
    """
    Generate a hello greeting for the given name.
    
    Args:
        name: The name to greet (default: "World")
        
    Returns:
        GenericOutput with greeting string in result field
    """
    try:
        greeting = f"Hello, {name}!"
        return GenericOutput(
            success=True,
            result=greeting,
            message="Greeting generated successfully"
        )
    except Exception as e:
        return GenericOutput(
            success=False,
            result="",
            message=f"Error generating greeting: {str(e)}"
        )
