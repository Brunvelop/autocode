"""
Core hello_world function - pure function for greeting functionality.
"""


def hello_world(name: str = "World") -> str:
    """
    Generate a hello greeting for the given name.
    
    Args:
        name: The name to greet (default: "World")
        
    Returns:
        A greeting string
    """
    return f"Hello, {name}!"
