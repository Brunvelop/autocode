"""
Tests for autocode.interfaces.registry module.

Tests the central registry system that enables automatic generation of CLI commands,
API endpoints, and MCP tools through function registration and parameter inference.
"""
import pytest
import inspect
import importlib
from typing import Any
from unittest.mock import patch, Mock

from autocode.interfaces.registry import (
    FUNCTION_REGISTRY, _generate_function_info, register_function,
    get_function, get_function_info, get_all_function_schemas, list_functions,
    clear_registry, get_registry_stats, load_core_functions,
    RegistryError, _functions_loaded, _has_register_decorator
)
from autocode.interfaces.models import FunctionInfo, ExplicitParam, GenericOutput, FunctionSchema


class TestGenerateFunctionInfo:
    """Tests for _generate_function_info - automatic parameter inference."""
    
    def test_generate_function_info_simple(self):
        """Test function info generation from simple function."""
        def simple_func(x: int, y: str = "default") -> GenericOutput:
            """Simple function for testing.
            
            Args:
                x: An integer parameter
                y: A string parameter with default
                
            Returns:
                A formatted string
            """
            return GenericOutput(result=f"{x}: {y}", success=True)
        
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
        """Test function info generation without type annotations - should fail without return type."""
        def no_annotations_func(x, y=42):
            """Function without type annotations."""
            return x + y
        
        # Should raise RegistryError because no return type annotation
        with pytest.raises(RegistryError, match="must have a return type annotation"):
            _generate_function_info(no_annotations_func)
    
    def test_generate_function_info_with_any_params(self):
        """Test function info generation with Any type parameters but GenericOutput return."""
        def any_params_func(x, y=42) -> GenericOutput:
            """Function with Any type parameters."""
            return GenericOutput(result=x + y, success=True)
        
        info = _generate_function_info(any_params_func)
        
        assert info.name == "any_params_func"
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
        def no_doc_func(x: int) -> GenericOutput:
            return GenericOutput(result=x * 2, success=True)
        
        info = _generate_function_info(no_doc_func)
        
        assert info.name == "no_doc_func"
        assert info.description == "Execute no_doc_func"  # Default description
        assert len(info.params) == 1
        
        # Parameter should have generic description
        param = info.params[0]
        assert param.description == "Parameter x"
    
    def test_generate_function_info_custom_http_methods(self):
        """Test function info generation with custom HTTP methods."""
        def custom_func(x: int) -> GenericOutput:
            """Custom function."""
            return GenericOutput(result=x, success=True)
        
        info = _generate_function_info(custom_func, http_methods=["POST", "PUT"])
        
        assert info.http_methods == ["POST", "PUT"]
    
    def test_generate_function_info_invalid_http_methods(self):
        """Test function info generation with invalid HTTP methods."""
        def test_func(x: int) -> GenericOutput:
            return GenericOutput(result=x, success=True)
        
        with pytest.raises(ValueError, match="Invalid HTTP methods"):
            _generate_function_info(test_func, http_methods=["INVALID"])
    
    def test_generate_function_info_complex_signature(self):
        """Test function info generation with complex signature."""
        def complex_func(
            required_param: str,
            optional_param: int = 10,
            *args,
            **kwargs
        ) -> GenericOutput:
            """Complex function with various parameter types.
            
            Args:
                required_param: A required string parameter
                optional_param: An optional integer parameter
            """
            return GenericOutput(result={"result": "complex"}, success=True)
        
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
        def test_basic_func(x: int) -> GenericOutput:
            """Basic test function."""
            return GenericOutput(result=x * 2, success=True)
        
        assert "test_basic_func" in FUNCTION_REGISTRY
        func_info = FUNCTION_REGISTRY["test_basic_func"]
        
        assert func_info.name == "test_basic_func"
        assert func_info.func == test_basic_func
        assert func_info.description == "Basic test function."
        assert len(func_info.params) == 1
        assert func_info.params[0].name == "x"
        
        # Test that function still works normally
        result = test_basic_func(5)
        assert result.result == 10
    
    def test_register_function_custom_methods(self):
        """Test function registration with custom HTTP methods."""
        @register_function(http_methods=["GET"])
        def get_only_func(x: str) -> GenericOutput:
            """GET-only function."""
            return GenericOutput(result=f"GET: {x}", success=True)
        
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
        # Test that we got the right function - now returns GenericOutput
        result = func(3, 4)
        assert result.result == 7
    
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
    
    def test_get_all_function_schemas(self, populated_registry):
        """Test schemas retrieval."""
        schemas = get_all_function_schemas()
        
        assert "test_add" in schemas
        schema = schemas["test_add"]
        assert isinstance(schema, FunctionSchema)
        
        params = schema.parameters
        assert len(params) == 2
        
        x_param = params[0]
        assert x_param.name == "x"
        assert x_param.type == "int"
        assert x_param.required is True
        assert x_param.description == "First number"
        
        y_param = params[1]
        assert y_param.name == "y"
        assert y_param.type == "int"
        assert y_param.required is False
        assert y_param.default == 1
        assert y_param.description == "Second number"
    
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
        def another_func() -> GenericOutput:
            """Another function for testing."""
            return GenericOutput(result="done", success=True)
        
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
        def put_func() -> GenericOutput:
            """PUT function for testing."""
            return GenericOutput(result="put", success=True)
        
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
        """Test handling of import errors during autocode.core package import."""
        from autocode.interfaces import registry
        original_loaded = registry._functions_loaded
        
        try:
            registry._functions_loaded = False
            
            # Mock the autocode.core package import to fail
            # This tests the critical path where the core package itself fails to import
            with patch.dict('sys.modules', {'autocode.core': None}):
                with patch('importlib.import_module', side_effect=ImportError("Mock import error")):
                    with pytest.raises(RegistryError, match="Failed to import autocode.core"):
                        load_core_functions()
            
        finally:
            registry._functions_loaded = original_loaded

    def test_load_core_functions_partial_failure_continues(self):
        """Test that autodiscovery continues loading other modules when one fails.
        
        This test verifies that when a single module fails to import during autodiscovery,
        the system continues to load other modules and does NOT raise an exception.
        
        Note: Due to Python's module caching, we can't reliably test that specific functions
        are excluded. Instead, we verify that the registry still loads successfully even
        when some modules fail to import.
        """
        from autocode.interfaces import registry
        import sys
        original_loaded = registry._functions_loaded
        original_registry = dict(FUNCTION_REGISTRY)
        
        # Save original modules state to restore later
        modules_to_remove = [m for m in sys.modules if m.startswith('autocode.core.')]
        original_modules = {m: sys.modules[m] for m in modules_to_remove}
        
        try:
            registry._functions_loaded = False
            clear_registry()
            
            # Remove cached core modules to force re-import
            for m in modules_to_remove:
                del sys.modules[m]
            
            original_import = importlib.import_module
            import_failures = []
            
            def mock_import_with_partial_failure(name):
                """Mock that fails for vcs.tree module but succeeds for others."""
                if 'vcs.tree' in name:
                    import_failures.append(name)
                    raise ImportError("Mock vcs.tree import error")
                return original_import(name)
            
            # Patch importlib.import_module directly since it's imported inside load_core_functions
            with patch.object(importlib, 'import_module', 
                              side_effect=mock_import_with_partial_failure):
                # Should NOT raise an exception - partial failures are tolerated
                load_core_functions()
            
            # The registry should have been marked as loaded
            assert registry._functions_loaded is True
            
            # Verify that the mock actually triggered (import failure was attempted)
            assert len(import_failures) > 0, "Mock should have intercepted vcs.tree import"
            
            # Functions from other modules SHOULD be in registry
            # (pipelines, session, etc. - they all loaded successfully)
            function_names = list(FUNCTION_REGISTRY.keys())
            assert len(function_names) > 0, "At least some functions should have loaded"
            
            # Verify some specific functions that should have loaded (from pipelines.py)
            assert 'chat' in FUNCTION_REGISTRY, "chat should be registered"
            
        finally:
            # Restore original state
            registry._functions_loaded = original_loaded
            clear_registry()
            FUNCTION_REGISTRY.update(original_registry)
            # Restore original modules
            for m, mod in original_modules.items():
                sys.modules[m] = mod


class TestRegistryIntegration:
    """Integration tests for registry functionality."""
    
    def test_end_to_end_function_registration_and_usage(self):
        """Test complete flow from registration to usage."""
        # Register a function
        @register_function(http_methods=["GET", "POST"])
        def integration_test_func(name: str, count: int = 1) -> GenericOutput:
            """Integration test function.
            
            Args:
                name: The name to repeat
                count: How many times to repeat it
            """
            return GenericOutput(result=" ".join([name] * count), success=True)
        
        # Verify registration
        assert "integration_test_func" in FUNCTION_REGISTRY
        
        # Test function retrieval and execution
        func = get_function("integration_test_func")
        result = func("test", 3)
        assert result.result == "test test test"
        
        # Test parameter information
        schema = get_all_function_schemas()["integration_test_func"]
        params = schema.parameters
        assert len(params) == 2
        
        name_param = next(p for p in params if p.name == "name")
        count_param = next(p for p in params if p.name == "count")
        
        assert name_param.required is True
        assert count_param.required is False
        assert count_param.default == 1
        
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


class TestDecoratorDetection:
    """Tests for @register_function decorator detection in source files using AST."""
    
    def test_has_register_decorator_true(self, tmp_path):
        """Test detection of @register_function() in source file."""
        # Create a temporary file with the decorator
        module_file = tmp_path / "test_module.py"
        module_file.write_text('''
from autocode.interfaces.registry import register_function
from autocode.interfaces.models import GenericOutput

@register_function()
def my_func() -> GenericOutput:
    return GenericOutput(result="test", success=True)
''')
        
        assert _has_register_decorator(str(module_file)) is True
    
    def test_has_register_decorator_without_parens(self, tmp_path):
        """Test detection of @register_function without parentheses."""
        module_file = tmp_path / "test_module_no_parens.py"
        module_file.write_text('''
from autocode.interfaces.registry import register_function
from autocode.interfaces.models import GenericOutput

@register_function
def my_func() -> GenericOutput:
    return GenericOutput(result="test", success=True)
''')
        
        assert _has_register_decorator(str(module_file)) is True
    
    def test_has_register_decorator_with_module_prefix(self, tmp_path):
        """Test detection of @registry.register_function() with module prefix."""
        module_file = tmp_path / "test_module_prefix.py"
        module_file.write_text('''
from autocode.interfaces import registry
from autocode.interfaces.models import GenericOutput

@registry.register_function()
def my_func() -> GenericOutput:
    return GenericOutput(result="test", success=True)
''')
        
        assert _has_register_decorator(str(module_file)) is True
    
    def test_has_register_decorator_false(self, tmp_path):
        """Test that modules without decorator are correctly identified."""
        # Create a temporary file without the decorator
        module_file = tmp_path / "utility_module.py"
        module_file.write_text('''
def helper_function(x, y):
    """A utility function without registration."""
    return x + y

class UtilityClass:
    pass
''')
        
        assert _has_register_decorator(str(module_file)) is False
    
    def test_has_register_decorator_in_comment_false(self, tmp_path):
        """Test that @register_function in comments is NOT detected (AST ignores comments)."""
        module_file = tmp_path / "module_with_comment.py"
        module_file.write_text('''
# This file uses @register_function decorator for functions
# @register_function should be used like this:

def helper_function(x, y):
    """
    Example with @register_function decorator.
    """
    return x + y
''')
        
        assert _has_register_decorator(str(module_file)) is False
    
    def test_has_register_decorator_in_docstring_false(self, tmp_path):
        """Test that @register_function in docstrings is NOT detected (AST accuracy)."""
        module_file = tmp_path / "module_with_docstring.py"
        module_file.write_text('''
def helper_function(x, y):
    """
    This function shows how to use @register_function decorator.
    Use @register_function() to register functions in the registry.
    """
    return x + y
''')
        
        assert _has_register_decorator(str(module_file)) is False
    
    def test_has_register_decorator_invalid_path(self):
        """Test handling of invalid/non-existent file paths."""
        assert _has_register_decorator("/nonexistent/path/module.py") is False
        assert _has_register_decorator(None) is False
        assert _has_register_decorator("") is False
    
    def test_has_register_decorator_invalid_syntax(self, tmp_path):
        """Test handling of files with invalid Python syntax."""
        module_file = tmp_path / "invalid_syntax.py"
        module_file.write_text('''
def broken_function(
    # Missing closing parenthesis
''')
        
        # Should return False when AST parsing fails
        assert _has_register_decorator(str(module_file)) is False


class TestStrictMode:
    """Tests for strict mode in load_core_functions."""
    
    def test_load_core_functions_strict_raises_on_failure(self):
        """Test that strict=True raises RegistryError when modules fail to import."""
        from autocode.interfaces import registry
        import sys
        original_loaded = registry._functions_loaded
        original_registry = dict(FUNCTION_REGISTRY)
        
        # Save original modules state
        modules_to_remove = [m for m in sys.modules if m.startswith('autocode.core.')]
        original_modules = {m: sys.modules[m] for m in modules_to_remove}
        
        try:
            registry._functions_loaded = False
            clear_registry()
            
            # Remove cached core modules
            for m in modules_to_remove:
                del sys.modules[m]
            
            original_import = importlib.import_module
            
            def mock_import_with_failure(name):
                """Mock that fails for vcs.tree module."""
                if 'vcs.tree' in name:
                    raise ImportError("Mock vcs.tree import error")
                return original_import(name)
            
            with patch.object(importlib, 'import_module', 
                              side_effect=mock_import_with_failure):
                # With strict=True, should raise RegistryError
                with pytest.raises(RegistryError, match="Failed to load modules in strict mode"):
                    load_core_functions(strict=True)
            
        finally:
            registry._functions_loaded = original_loaded
            clear_registry()
            FUNCTION_REGISTRY.update(original_registry)
            for m, mod in original_modules.items():
                sys.modules[m] = mod
    
    def test_load_core_functions_strict_false_tolerates_failures(self):
        """Test that strict=False (default) tolerates import failures."""
        from autocode.interfaces import registry
        import sys
        original_loaded = registry._functions_loaded
        original_registry = dict(FUNCTION_REGISTRY)
        
        modules_to_remove = [m for m in sys.modules if m.startswith('autocode.core.')]
        original_modules = {m: sys.modules[m] for m in modules_to_remove}
        
        try:
            registry._functions_loaded = False
            clear_registry()
            
            for m in modules_to_remove:
                del sys.modules[m]
            
            original_import = importlib.import_module
            
            def mock_import_with_failure(name):
                if 'calculator' in name:
                    raise ImportError("Mock calculator import error")
                return original_import(name)
            
            with patch.object(importlib, 'import_module', 
                              side_effect=mock_import_with_failure):
                # With strict=False (default), should NOT raise
                load_core_functions(strict=False)
            
            # Should have completed loading
            assert registry._functions_loaded is True
            
        finally:
            registry._functions_loaded = original_loaded
            clear_registry()
            FUNCTION_REGISTRY.update(original_registry)
            for m, mod in original_modules.items():
                sys.modules[m] = mod
