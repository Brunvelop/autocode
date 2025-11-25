"""
Tests for autocode.interfaces.registry module.

Tests the central registry system that enables automatic generation of CLI commands,
API endpoints, and MCP tools through function registration and parameter inference.
"""
import pytest
import inspect
from typing import Any
from unittest.mock import patch, Mock

from autocode.interfaces.registry import (
    FUNCTION_REGISTRY, _generate_function_info, register_function,
    get_function, get_function_info, get_parameters, list_functions,
    clear_registry, get_registry_stats, load_core_functions,
    RegistryError, _functions_loaded
)
from autocode.interfaces.models import FunctionInfo, ExplicitParam


class TestGenerateFunctionInfo:
    """Tests for _generate_function_info - automatic parameter inference."""
    
    def test_generate_function_info_simple(self):
        """Test function info generation from simple function."""
        def simple_func(x: int, y: str = "default") -> str:
            """Simple function for testing.
            
            Args:
                x: An integer parameter
                y: A string parameter with default
                
            Returns:
                A formatted string
            """
            return f"{x}: {y}"
        
        info = _generate_function_info(simple_func)
        
        assert info.name == "simple_func"
        assert info.func == simple_func
        assert info.description == "Simple function for testing."
        assert info.http_methods == ["GET", "POST"]  # Default
        assert len(info.params) == 2
        
        # Check parameters
        x_param = info.params[0]
        assert x_param.name == "x"
        assert x_param.type == int
        assert x_param.required is True
        assert x_param.default is None
        assert x_param.description == "An integer parameter"
        
        y_param = info.params[1]
        assert y_param.name == "y"
        assert y_param.type == str
        assert y_param.required is False
        assert y_param.default == "default"
        assert y_param.description == "A string parameter with default"
    
    def test_generate_function_info_no_annotations(self):
        """Test function info generation without type annotations."""
        def no_annotations_func(x, y=42):
            """Function without type annotations."""
            return x + y
        
        info = _generate_function_info(no_annotations_func)
        
        assert info.name == "no_annotations_func"
        assert len(info.params) == 2
        
        # Parameters should use Any type when no annotation
        x_param = info.params[0]
        assert x_param.name == "x"
        assert x_param.type == Any
        assert x_param.required is True
        
        y_param = info.params[1]
        assert y_param.name == "y"
        assert y_param.type == Any
        assert y_param.required is False
        assert y_param.default == 42
    
    def test_generate_function_info_no_docstring(self):
        """Test function info generation without docstring."""
        def no_doc_func(x: int) -> int:
            return x * 2
        
        info = _generate_function_info(no_doc_func)
        
        assert info.name == "no_doc_func"
        assert info.description == "Execute no_doc_func"  # Default description
        assert len(info.params) == 1
        
        # Parameter should have generic description
        param = info.params[0]
        assert param.description == "Parameter x"
    
    def test_generate_function_info_custom_http_methods(self):
        """Test function info generation with custom HTTP methods."""
        def custom_func(x: int) -> int:
            """Custom function."""
            return x
        
        info = _generate_function_info(custom_func, http_methods=["POST", "PUT"])
        
        assert info.http_methods == ["POST", "PUT"]
    
    def test_generate_function_info_invalid_http_methods(self):
        """Test function info generation with invalid HTTP methods."""
        def test_func(x: int) -> int:
            return x
        
        with pytest.raises(ValueError, match="Invalid HTTP methods"):
            _generate_function_info(test_func, http_methods=["INVALID"])
    
    def test_generate_function_info_complex_signature(self):
        """Test function info generation with complex signature."""
        def complex_func(
            required_param: str,
            optional_param: int = 10,
            *args,
            **kwargs
        ) -> dict:
            """Complex function with various parameter types.
            
            Args:
                required_param: A required string parameter
                optional_param: An optional integer parameter
            """
            return {"result": "complex"}
        
        info = _generate_function_info(complex_func)
        
        # Should only process regular parameters, not *args/**kwargs
        assert len(info.params) == 2
        
        required = info.params[0]
        assert required.name == "required_param"
        assert required.type == str
        assert required.required is True
        
        optional = info.params[1]
        assert optional.name == "optional_param"
        assert optional.type == int
        assert optional.required is False
        assert optional.default == 10


class TestRegisterFunctionDecorator:
    """Tests for register_function decorator."""
    
    def test_register_function_basic(self):
        """Test basic function registration."""
        @register_function()
        def test_basic_func(x: int) -> int:
            """Basic test function."""
            return x * 2
        
        assert "test_basic_func" in FUNCTION_REGISTRY
        func_info = FUNCTION_REGISTRY["test_basic_func"]
        
        assert func_info.name == "test_basic_func"
        assert func_info.func == test_basic_func
        assert func_info.description == "Basic test function."
        assert len(func_info.params) == 1
        assert func_info.params[0].name == "x"
        
        # Test that function still works normally
        assert test_basic_func(5) == 10
    
    def test_register_function_custom_methods(self):
        """Test function registration with custom HTTP methods."""
        @register_function(http_methods=["GET"])
        def get_only_func(x: str) -> str:
            """GET-only function."""
            return f"GET: {x}"
        
        assert "get_only_func" in FUNCTION_REGISTRY
        func_info = FUNCTION_REGISTRY["get_only_func"]
        assert func_info.http_methods == ["GET"]
    
    def test_register_function_error_handling(self):
        """Test error handling in function registration."""
        with patch('autocode.interfaces.registry._generate_function_info') as mock_generate:
            mock_generate.side_effect = Exception("Generation error")
            
            with pytest.raises(RegistryError, match="Failed to register function"):
                @register_function()
                def failing_func():
                    pass


class TestRegistryPublicAPI:
    """Tests for public registry API functions."""
    
    def test_get_function_success(self, populated_registry):
        """Test successful function retrieval."""
        func = get_function("test_add")
        
        assert callable(func)
        # Test that we got the right function
        result = func(3, 4)
        assert result == 7
    
    def test_get_function_not_found(self):
        """Test function retrieval with non-existent function."""
        with pytest.raises(RegistryError, match="Function 'nonexistent' not found"):
            get_function("nonexistent")
    
    def test_get_function_info_success(self, populated_registry):
        """Test successful function info retrieval."""
        func_info = get_function_info("test_add")
        
        assert isinstance(func_info, FunctionInfo)
        assert func_info.name == "test_add"
        assert func_info.description == "Add two numbers together"
        assert len(func_info.params) == 2
    
    def test_get_function_info_not_found(self):
        """Test function info retrieval with non-existent function."""
        with pytest.raises(RegistryError, match="Function 'nonexistent' not found"):
            get_function_info("nonexistent")
    
    def test_get_parameters(self, populated_registry):
        """Test parameter information retrieval."""
        params = get_parameters("test_add")
        
        assert len(params) == 2
        
        x_param = params[0]
        assert x_param["name"] == "x"
        assert x_param["type"] == "int"
        assert x_param["required"] is True
        assert x_param["description"] == "First number"
        
        y_param = params[1]
        assert y_param["name"] == "y"
        assert y_param["type"] == "int"
        assert y_param["required"] is False
        assert y_param["default"] == 1
        assert y_param["description"] == "Second number"
    
    def test_list_functions_empty(self):
        """Test listing functions with empty registry."""
        functions = list_functions()
        assert functions == []
    
    def test_list_functions_populated(self, populated_registry):
        """Test listing functions with populated registry."""
        functions = list_functions()
        
        assert functions == ["test_add"]  # Should be sorted
        
        # Add another function and test sorting
        @register_function()
        def another_func():
            pass
        
        functions = list_functions()
        assert functions == ["another_func", "test_add"]
    
    def test_clear_registry(self, populated_registry):
        """Test registry clearing."""
        # Verify registry is populated
        assert len(FUNCTION_REGISTRY) > 0
        
        clear_registry()
        
        # Verify registry is empty
        assert len(FUNCTION_REGISTRY) == 0
        assert list_functions() == []
    
    def test_get_registry_stats_empty(self):
        """Test registry statistics with empty registry."""
        stats = get_registry_stats()
        
        assert stats["total_functions"] == 0
        assert stats["function_names"] == []
        assert stats["http_methods_distribution"]["GET"] == 0
        assert stats["http_methods_distribution"]["POST"] == 0
    
    def test_get_registry_stats_populated(self, populated_registry):
        """Test registry statistics with populated registry."""
        # Add another function with different methods
        @register_function(http_methods=["GET", "PUT"])
        def put_func():
            pass
        
        stats = get_registry_stats()
        
        assert stats["total_functions"] == 2
        assert set(stats["function_names"]) == {"test_add", "put_func"}
        assert stats["http_methods_distribution"]["GET"] == 2
        assert stats["http_methods_distribution"]["POST"] == 1
        assert stats["http_methods_distribution"]["PUT"] == 1
        assert stats["http_methods_distribution"]["DELETE"] == 0


class TestLoadCoreFunctions:
    """Tests for core function loading."""
    
    def test_load_core_functions_success(self, mock_core_functions):
        """Test successful loading of core functions."""
        # Import the module's _functions_loaded to manipulate it
        from autocode.interfaces import registry
        original_loaded = registry._functions_loaded
        
        try:
            # Clear registry and reset flag
            clear_registry()
            registry._functions_loaded = False
            
            load_core_functions()
            
            # Should have loaded successfully (mocked imports)
            assert registry._functions_loaded is True
            
        finally:
            registry._functions_loaded = original_loaded
    
    def test_load_core_functions_already_loaded(self, mock_core_functions):
        """Test that load_core_functions doesn't reload if already loaded."""
        from autocode.interfaces import registry
        original_loaded = registry._functions_loaded
        
        try:
            registry._functions_loaded = True
            registry_size = len(FUNCTION_REGISTRY)
            
            load_core_functions()
            
            # Should not have changed registry size
            assert len(FUNCTION_REGISTRY) == registry_size
            
        finally:
            registry._functions_loaded = original_loaded
    
    def test_load_core_functions_import_error(self):
        """Test handling of import errors during loading."""
        from autocode.interfaces import registry
        original_loaded = registry._functions_loaded
        
        try:
            registry._functions_loaded = False
            
            # Mock the import by patching __import__ to simulate ImportError
            def mock_import(name, *args, **kwargs):
                if 'hello_world' in name:
                    raise ImportError("Mock import error")
                return __import__(name, *args, **kwargs)
            
            with patch('builtins.__import__', side_effect=mock_import):
                with pytest.raises(RegistryError, match="Failed to load core functions"):
                    load_core_functions()
            
        finally:
            registry._functions_loaded = original_loaded


class TestRegistryIntegration:
    """Integration tests for registry functionality."""
    
    def test_end_to_end_function_registration_and_usage(self):
        """Test complete flow from registration to usage."""
        # Register a function
        @register_function(http_methods=["GET", "POST"])
        def integration_test_func(name: str, count: int = 1) -> str:
            """Integration test function.
            
            Args:
                name: The name to repeat
                count: How many times to repeat it
            """
            return " ".join([name] * count)
        
        # Verify registration
        assert "integration_test_func" in FUNCTION_REGISTRY
        
        # Test function retrieval and execution
        func = get_function("integration_test_func")
        result = func("test", 3)
        assert result == "test test test"
        
        # Test parameter information
        params = get_parameters("integration_test_func")
        assert len(params) == 2
        
        name_param = next(p for p in params if p["name"] == "name")
        count_param = next(p for p in params if p["name"] == "count")
        
        assert name_param["required"] is True
        assert count_param["required"] is False
        assert count_param["default"] == 1
        
        # Test stats
        stats = get_registry_stats()
        assert "integration_test_func" in stats["function_names"]
        assert stats["http_methods_distribution"]["GET"] >= 1
        assert stats["http_methods_distribution"]["POST"] >= 1
    
    def test_registry_error_propagation(self):
        """Test that registry errors are properly propagated."""
        # Test with non-existent function
        with pytest.raises(RegistryError):
            get_function("does_not_exist")
        
        with pytest.raises(RegistryError):
            get_function_info("does_not_exist")
        
        with pytest.raises(RegistryError):
            get_parameters("does_not_exist")
