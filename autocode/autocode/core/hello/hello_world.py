"""
Core hello_world function - pure function for greeting functionality.
"""
from autocode.autocode.interfaces.registry import register_function


@register_function(http_methods=["GET", "POST"])
def hello_world(name: str = "World") -> str:
    """
    Generate a hello greeting for the given name.
    
    Args:
        name: The name to greet (default: "World")
        
    Returns:
        A greeting string
    """
    return f"Hello, {name}!"
