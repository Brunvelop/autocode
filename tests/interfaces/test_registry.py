"""
Tests for the registry module.
"""
import pytest
from autocode.autocode.interfaces.registry import (
    FUNCTION_REGISTRY,
    get_function,
    get_function_info,
    get_parameters,
    list_functions
)
from autocode.autocode.interfaces.models import FunctionInfo, ExplicitParam
from autocode.autocode.core.hello.hello_world import hello_world
from autocode.autocode.core.math.calculator import add, multiply


class TestRegistry:
    """Test registry functionality."""
    
    def test_function_registry_structure(self):
        """Test that the registry has the expected structure."""
        assert isinstance(FUNCTION_REGISTRY, dict)
        assert len(FUNCTION_REGISTRY) >= 3  # hello, add, multiply
        
        # Check specific functions exist
        assert "hello" in FUNCTION_REGISTRY
        assert "add" in FUNCTION_REGISTRY
        assert "multiply" in FUNCTION_REGISTRY
        
        # Check each entry is a FunctionInfo
        for func_info in FUNCTION_REGISTRY.values():
            assert isinstance(func_info, FunctionInfo)
            assert hasattr(func_info, 'name')
            assert hasattr(func_info, 'func')
            assert hasattr(func_info, 'description')
            assert hasattr(func_info, 'http_methods')
    
    def test_get_function(self):
        """Test getting functions from registry."""
        # Test valid function
        hello_func = get_function("hello")
        assert hello_func == hello_world
        
        add_func = get_function("add")
        assert add_func == add
        
        multiply_func = get_function("multiply")
        assert multiply_func == multiply
        
        # Test invalid function
        with pytest.raises(KeyError):
            get_function("nonexistent")
    
    def test_get_function_info(self):
        """Test getting function info from registry."""
        hello_info = get_function_info("hello")
        assert isinstance(hello_info, FunctionInfo)
        assert hello_info.name == "hello"
        assert hello_info.func == hello_world
        assert "greeting" in hello_info.description.lower()
        assert "GET" in hello_info.http_methods
        assert "POST" in hello_info.http_methods
        
        # Test invalid function
        with pytest.raises(KeyError):
            get_function_info("nonexistent")
    
    def test_get_parameters(self):
        """Test explicit parameters via registry."""
        # Test hello function parameters
        hello_params = get_parameters("hello")
        assert len(hello_params) == 1
        param = hello_params[0]
        assert param["name"] == "name"
        assert param["type"] == "str"
        assert param["required"] == False
        assert param["default"] == "World"
        
        # Test add function parameters
        add_params = get_parameters("add")
        assert len(add_params) == 2
        
        param_a = add_params[0]
        assert param_a["name"] == "a"
        assert param_a["type"] == "int"
        assert param_a["required"] == True
        
        param_b = add_params[1]
        assert param_b["name"] == "b"
        assert param_b["type"] == "int"
        assert param_b["required"] == True
        
        # Test multiply function parameters
        multiply_params = get_parameters("multiply")
        assert len(multiply_params) == 2
        
        param_x = multiply_params[0]
        assert param_x["name"] == "x"
        assert param_x["type"] == "int"
        assert param_x["required"] == True
        
        param_y = multiply_params[1]
        assert param_y["name"] == "y"
        assert param_y["type"] == "int"
        assert param_y["required"] == False
        assert param_y["default"] == 1
    
    def test_explicit_params_structure(self):
        """Test explicit parameter structure in registry."""
        hello_info = get_function_info("hello")
        assert len(hello_info.params) == 1
        
        param = hello_info.params[0]
        assert isinstance(param, ExplicitParam)
        assert param.name == "name"
        assert param.type == str
        assert param.default == "World"
        assert param.required == False
        assert "name to greet" in param.description.lower()
    
    def test_list_functions(self):
        """Test listing all functions."""
        functions = list_functions()
        assert isinstance(functions, list)
        assert "hello" in functions
        assert "add" in functions
        assert "multiply" in functions
        assert len(functions) >= 3
    
    def test_invalid_function_access(self):
        """Test error handling for invalid functions."""
        with pytest.raises(KeyError):
            get_parameters("nonexistent")
        
        with pytest.raises(KeyError):
            get_function("nonexistent")
        
        with pytest.raises(KeyError):
            get_function_info("nonexistent")


class TestRegistryIntegration:
    """Test registry integration with actual core functions."""
    
    def test_hello_function_integration(self):
        """Test that hello function works correctly through registry."""
        func = get_function("hello")
        result = func()
        assert result == "Hello, World!"
        
        result_with_name = func("Alice")
        assert result_with_name == "Hello, Alice!"
    
    def test_add_function_integration(self):
        """Test that add function works correctly through registry."""
        func = get_function("add")
        result = func(5, 3)
        assert result == 8
        
        result2 = func(10, 20)
        assert result2 == 30
    
    def test_multiply_function_integration(self):
        """Test that multiply function works correctly through registry."""
        func = get_function("multiply")
        result = func(5, 3)
        assert result == 15
        
        # Test with default y=1
        result_default = func(5)
        assert result_default == 5


# Integration test to ensure the refactored system works end-to-end
class TestEndToEndIntegration:
    """Test the complete system integration."""
    
    def test_complete_workflow(self):
        """Test a complete workflow from registry to execution."""
        # Get function info
        func_info = get_function_info("hello")
        assert func_info.name == "hello"
        
        # Get explicit parameters
        params = get_parameters("hello")
        assert len(params) == 1
        assert params[0]["name"] == "name"
        assert params[0]["default"] == "World"
        
        # Execute function with explicit parameters
        func = get_function("hello")
        result = func("Integration Test")
        
        # Verify the entire pipeline works
        assert result == "Hello, Integration Test!"
        
    def test_explicit_param_workflow(self):
        """Test workflow using explicit params from registry."""
        # Get add function info and params
        add_info = get_function_info("add")
        add_params = get_parameters("add")
        
        assert len(add_params) == 2
        assert all(param["required"] for param in add_params)
        
        # Execute with explicit values
        add_func = get_function("add")
        result = add_func(10, 5)
        assert result == 15
