"""
Simple calculator functions for mathematical operations.
"""
from autocode.interfaces.registry import register_function
from autocode.interfaces.models import GenericOutput


@register_function(http_methods=["GET", "POST"])
def add(a: int, b: int) -> GenericOutput:
    """Add two numbers.
    
    Args:
        a: First number
        b: Second number
        
    Returns:
        GenericOutput with sum of a and b in result field
    """
    try:
        result = a + b
        return GenericOutput(
            success=True,
            result=result,
            message=f"Successfully added {a} + {b} = {result}"
        )
    except Exception as e:
        return GenericOutput(
            success=False,
            result=0,
            message=f"Error adding numbers: {str(e)}"
        )


@register_function(http_methods=["GET", "POST"])
def multiply(x: int, y: int = 1) -> GenericOutput:
    """Multiply two numbers.
    
    Args:
        x: First number
        y: Second number (optional, defaults to 1)
        
    Returns:
        GenericOutput with product of x and y in result field
    """
    try:
        result = x * y
        return GenericOutput(
            success=True,
            result=result,
            message=f"Successfully multiplied {x} * {y} = {result}"
        )
    except Exception as e:
        return GenericOutput(
            success=False,
            result=0,
            message=f"Error multiplying numbers: {str(e)}"
        )
