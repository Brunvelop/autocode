"""
Simple calculator functions for mathematical operations.
"""
from autocode.autocode.interfaces.registry import register_function


@register_function(http_methods=["GET", "POST"])
def add(a: int, b: int) -> int:
    """Add two numbers.
    
    Args:
        a: First number
        b: Second number
        
    Returns:
        Sum of a and b
    """
    return a + b


@register_function(http_methods=["GET", "POST"])
def multiply(x: int, y: int = 1) -> int:
    """Multiply two numbers.
    
    Args:
        x: First number
        y: Second number (optional, defaults to 1)
        
    Returns:
        Product of x and y
    """
    return x * y
