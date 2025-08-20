"""
Simple calculator functions for mathematical operations.
"""


def add(a: int, b: int) -> int:
    """Add two numbers.
    
    Args:
        a: First number
        b: Second number
        
    Returns:
        Sum of a and b
    """
    return a + b


def multiply(x: int, y: int = 1) -> int:
    """Multiply two numbers.
    
    Args:
        x: First number
        y: Second number (optional, defaults to 1)
        
    Returns:
        Product of x and y
    """
    return x * y
