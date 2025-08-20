"""
Tests for the inference utilities module.
"""
import pytest
from typing import Optional
from autocode.autocode.interfaces.utils import InferenceUtils
from autocode.autocode.interfaces.models import BaseFunctionInput, BaseFunctionOutput


def sample_function_simple(name: str = "World") -> str:
    """
    A simple test function.
    
    Args:
        name: The name to greet
        
    Returns:
        A greeting message
    """
    return f"Hello, {name}!"


def sample_function_complex(a: int, b: int = 10, c: Optional[str] = None) -> int:
    """
    A complex test function.
    
    Args:
        a: First number (required)
        b: Second number (optional, default 10)
        c: Optional string parameter
        
    Returns:
        Sum of a and b
    """
    return a + b


def sample_function_no_types(x, y=5):
    """Function without type hints."""
    return x + y


def sample_function_no_params() -> str:
    """Function with no parameters."""
    return "No params"


class TestInferParameters:
    """Test parameter inference functionality."""
    
    def test_simple_function_parameters(self):
        """Test inference for a simple function."""
        params = InferenceUtils.infer_parameters(sample_function_simple)
        
        assert len(params) == 1
        param = params[0]
        
        assert param["name"] == "name"
        assert param["type"] == "str"
        assert param["required"] == False
        assert param["default"] == "World"
        assert "name to greet" in param["description"].lower()
    
    def test_complex_function_parameters(self):
        """Test inference for a function with multiple parameter types."""
        params = InferenceUtils.infer_parameters(sample_function_complex)
        
        assert len(params) == 3
        
        # Check first parameter (required int)
        param_a = params[0]
        assert param_a["name"] == "a"
        assert param_a["type"] == "int"
        assert param_a["required"] == True
        assert param_a["default"] is None
        
        # Check second parameter (optional int with default)
        param_b = params[1]
        assert param_b["name"] == "b"
        assert param_b["type"] == "int" 
        assert param_b["required"] == False
        assert param_b["default"] == 10
        
        # Check third parameter (optional string)
        param_c = params[2]
        assert param_c["name"] == "c"
        assert param_c["type"] == "str"
        assert param_c["required"] == False
        assert param_c["default"] is None
    
    def test_function_no_types(self):
        """Test inference for function without type hints."""
        params = InferenceUtils.infer_parameters(sample_function_no_types)
        
        assert len(params) == 2
        
        param_x = params[0]
        assert param_x["name"] == "x"
        assert param_x["type"] == "str"  # Default fallback
        assert param_x["required"] == True
        
        param_y = params[1]
        assert param_y["name"] == "y"
        assert param_y["type"] == "str"  # Default fallback
        assert param_y["required"] == False
        assert param_y["default"] == 5
    
    def test_function_no_params(self):
        """Test inference for function with no parameters."""
        params = InferenceUtils.infer_parameters(sample_function_no_params)
        assert len(params) == 0


class TestInferInputModel:
    """Test input model inference functionality."""
    
    def test_simple_function_input_model(self):
        """Test input model creation for simple function."""
        model_class = InferenceUtils.infer_input_model(sample_function_simple)
        
        # Create an instance
        instance = model_class(name="Alice")
        assert instance.name == "Alice"
        
        # Test with default
        default_instance = model_class()
        assert default_instance.name == "World"
        
        # Check inheritance
        assert issubclass(model_class, BaseFunctionInput)
    
    def test_complex_function_input_model(self):
        """Test input model creation for complex function."""
        model_class = InferenceUtils.infer_input_model(sample_function_complex)
        
        # Create instance with required param
        instance = model_class(a=5)
        assert instance.a == 5
        assert instance.b == 10  # Default value
        assert instance.c is None  # Optional default
        
        # Create instance with all params
        full_instance = model_class(a=1, b=2, c="test")
        assert full_instance.a == 1
        assert full_instance.b == 2
        assert full_instance.c == "test"
    
    def test_function_no_params_input_model(self):
        """Test input model for function with no parameters."""
        from autocode.autocode.interfaces.models import GenericInput
        
        model_class = InferenceUtils.infer_input_model(sample_function_no_params)
        
        # Should return GenericInput for functions without parameters
        assert model_class == GenericInput


class TestInferOutputModel:
    """Test output model inference functionality."""
    
    def test_string_return_output_model(self):
        """Test output model creation for string return type."""
        model_class = InferenceUtils.infer_output_model(sample_function_simple)
        
        # Create instance
        instance = model_class(message="Hello, test!")
        assert instance.message == "Hello, test!"
        
        # Check inheritance
        assert issubclass(model_class, BaseFunctionOutput)
    
    def test_int_return_output_model(self):
        """Test output model creation for int return type."""
        model_class = InferenceUtils.infer_output_model(sample_function_complex)
        
        # Create instance
        instance = model_class(result=42)
        assert instance.result == 42
    
    def test_no_annotation_output_model(self):
        """Test output model for function without return annotation."""
        from autocode.autocode.interfaces.models import GenericOutput
        
        model_class = InferenceUtils.infer_output_model(sample_function_no_types)
        
        # Should return GenericOutput for functions without return annotation
        assert model_class == GenericOutput


class TestTypeToString:
    """Test type hint to string conversion."""
    
    def test_basic_types(self):
        """Test conversion of basic Python types."""
        assert InferenceUtils._type_to_string(str) == "str"
        assert InferenceUtils._type_to_string(int) == "int"
        assert InferenceUtils._type_to_string(float) == "float"
        assert InferenceUtils._type_to_string(bool) == "bool"
        assert InferenceUtils._type_to_string(list) == "list"
        assert InferenceUtils._type_to_string(dict) == "dict"
    
    def test_complex_type(self):
        """Test conversion of complex types (fallback to str representation)."""
        from typing import List
        result = InferenceUtils._type_to_string(List[str])
        assert "typing.List" in result or "list" in result


class TestDocstringParsing:
    """Test docstring parameter parsing."""
    
    def test_parse_docstring_with_args(self):
        """Test parsing docstring with Args section."""
        params = InferenceUtils._parse_docstring_params(sample_function_complex)
        
        assert "a" in params
        assert "first number" in params["a"].lower()
        assert "b" in params 
        assert "second number" in params["b"].lower()
        assert "c" in params
        assert "optional string" in params["c"].lower()
    
    def test_parse_docstring_no_args(self):
        """Test parsing docstring without Args section."""
        def func_no_args():
            """Function without Args section."""
            pass
        
        params = InferenceUtils._parse_docstring_params(func_no_args)
        assert len(params) == 0
    
    def test_parse_no_docstring(self):
        """Test parsing function without docstring."""
        def func_no_doc():
            pass
        
        params = InferenceUtils._parse_docstring_params(func_no_doc)
        assert len(params) == 0
