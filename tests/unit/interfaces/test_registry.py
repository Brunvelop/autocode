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
    _generate_function_info, register_function,
    get_all_schemas, get_all_functions, get_function_by_name, function_count,
    clear_registry, load_functions,
    RegistryError, _has_register_decorator
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
        
        func_info = get_function_by_name("test_basic_func")
        assert func_info is not None
        
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
        
        func_info = get_function_by_name("get_only_func")
        assert func_info is not None
        assert func_info.http_methods == ["GET"]
    
    def test_register_function_error_handling(self):
        """Test error handling in function registration."""
        with patch('autocode.interfaces.registry._generate_function_info') as mock_generate:
            mock_generate.side_effect = Exception("Generation error")
            
            with pytest.raises(RegistryError, match="Failed to register function"):
                @register_function()
                def failing_func():
                    pass
    
    def test_register_function_duplicate_raises_error(self):
        """Test that registering a function with the same name raises RegistryError."""
        @register_function()
        def duplicate_test_func(x: int) -> GenericOutput:
            """First registration."""
            return GenericOutput(result=x, success=True)
        
        # Second registration with same name should raise
        with pytest.raises(RegistryError, match="already registered"):
            @register_function()
            def duplicate_test_func(y: str) -> GenericOutput:
                """Second registration with same name."""
                return GenericOutput(result=y, success=True)


class TestRegistryPublicAPI:
    """Tests for public registry API functions."""
    
    def test_get_all_schemas(self, populated_registry):
        """Test schemas retrieval."""
        schemas = get_all_schemas()
        
        # Now returns list instead of dict
        assert len(schemas) > 0
        schema = next((s for s in schemas if s.name == "test_add"), None)
        assert schema is not None
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
    
    def test_clear_registry(self, populated_registry):
        """Test registry clearing."""
        # Verify registry is populated
        assert function_count() > 0
        
        clear_registry()
        
        # Verify registry is empty
        assert function_count() == 0
    
    def test_get_function_by_name(self, populated_registry):
        """Test retrieving function by name."""
        func_info = get_function_by_name("test_add")
        assert func_info is not None
        assert func_info.name == "test_add"
        
        # Non-existent function returns None
        assert get_function_by_name("nonexistent") is None
    
    def test_get_all_functions(self, populated_registry):
        """Test retrieving all functions."""
        functions = get_all_functions()
        assert len(functions) > 0
        assert any(f.name == "test_add" for f in functions)


class TestLoadFunctions:
    """Tests for function loading."""
    
    def test_load_functions_success(self, mock_core_functions):
        """Test successful loading of core functions."""
        # Import the module's _loaded to manipulate it
        from autocode.interfaces import registry
        original_loaded = registry._loaded
        
        try:
            # Clear registry and reset flag
            clear_registry()
            registry._loaded = False
            
            load_functions()
            
            # Should have loaded successfully (mocked imports)
            assert registry._loaded is True
            
        finally:
            registry._loaded = original_loaded
    
    def test_load_functions_already_loaded(self, mock_core_functions):
        """Test that load_functions doesn't reload if already loaded."""
        from autocode.interfaces import registry
        original_loaded = registry._loaded
        
        try:
            registry._loaded = True
            registry_size = function_count()
            
            load_functions()
            
            # Should not have changed registry size
            assert function_count() == registry_size
            
        finally:
            registry._loaded = original_loaded
    
    def test_load_functions_import_error(self):
        """Test handling of import errors during autocode.core package import."""
        from autocode.interfaces import registry
        original_loaded = registry._loaded
        
        try:
            registry._loaded = False
            
            # Mock the autocode.core package import to fail
            # This tests the critical path where the core package itself fails to import
            with patch.dict('sys.modules', {'autocode.core': None}):
                with patch('importlib.import_module', side_effect=ImportError("Mock import error")):
                    with pytest.raises(RegistryError, match="Failed to import autocode.core"):
                        load_functions()
            
        finally:
            registry._loaded = original_loaded

    def test_load_functions_partial_failure_continues(self):
        """Test that autodiscovery continues loading other modules when one fails.
        
        This test verifies that when a single module fails to import during autodiscovery,
        the system continues to load other modules and does NOT raise an exception.
        
        Note: Due to Python's module caching, we can't reliably test that specific functions
        are excluded. Instead, we verify that the registry still loads successfully even
        when some modules fail to import.
        """
        from autocode.interfaces import registry
        import sys
        original_loaded = registry._loaded
        original_functions = get_all_functions()
        
        # Save original modules state to restore later
        modules_to_remove = [m for m in sys.modules if m.startswith('autocode.core.')]
        original_modules = {m: sys.modules[m] for m in modules_to_remove}
        
        try:
            registry._loaded = False
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
            
            # Patch importlib.import_module directly since it's imported inside load_functions
            with patch.object(importlib, 'import_module', 
                              side_effect=mock_import_with_partial_failure):
                # Should NOT raise an exception - partial failures are tolerated
                load_functions()
            
            # The registry should have been marked as loaded
            assert registry._loaded is True
            
            # Verify that the mock actually triggered (import failure was attempted)
            assert len(import_failures) > 0, "Mock should have intercepted vcs.tree import"
            
            # Functions from other modules SHOULD be in registry
            # (pipelines, session, etc. - they all loaded successfully)
            functions = get_all_functions()
            assert len(functions) > 0, "At least some functions should have loaded"
            
            # Verify some specific functions that should have loaded (from pipelines.py)
            chat_func = get_function_by_name("chat")
            assert chat_func is not None, "chat should be registered"
            
        finally:
            # Restore original state
            registry._loaded = original_loaded
            clear_registry()
            # Re-add original functions using internal access (test cleanup only)
            from autocode.interfaces.registry import _registry
            _registry.extend(original_functions)
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
        
        # Verify registration using public API
        func_info = get_function_by_name("integration_test_func")
        assert func_info is not None
        
        # Test function retrieval and execution
        result = func_info.func("test", 3)
        assert result.result == "test test test"
        
        # Test parameter information
        schemas = get_all_schemas()
        schema = next((s for s in schemas if s.name == "integration_test_func"), None)
        assert schema is not None
        params = schema.parameters
        assert len(params) == 2
        
        name_param = next(p for p in params if p.name == "name")
        count_param = next(p for p in params if p.name == "count")
        
        assert name_param.required is True
        assert count_param.required is False
        assert count_param.default == 1
        
        # Verify HTTP methods are set correctly
        assert "GET" in func_info.http_methods
        assert "POST" in func_info.http_methods
    
    def test_registry_access_nonexistent_function(self):
        """Test that searching for non-existent function returns None."""
        result = get_function_by_name("does_not_exist")
        assert result is None


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
    """Tests for strict mode in load_functions."""
    
    def test_load_functions_strict_raises_on_failure(self):
        """Test that strict=True raises RegistryError when modules fail to import."""
        from autocode.interfaces import registry
        import sys
        original_loaded = registry._loaded
        original_functions = get_all_functions()
        
        # Save original modules state
        modules_to_remove = [m for m in sys.modules if m.startswith('autocode.core.')]
        original_modules = {m: sys.modules[m] for m in modules_to_remove}
        
        try:
            registry._loaded = False
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
                    load_functions(strict=True)
            
        finally:
            registry._loaded = original_loaded
            clear_registry()
            # Re-add original functions using internal access (test cleanup only)
            from autocode.interfaces.registry import _registry
            _registry.extend(original_functions)
            for m, mod in original_modules.items():
                sys.modules[m] = mod
    
    def test_load_functions_strict_false_tolerates_failures(self):
        """Test that strict=False (default) tolerates import failures."""
        from autocode.interfaces import registry
        import sys
        original_loaded = registry._loaded
        original_functions = get_all_functions()
        
        modules_to_remove = [m for m in sys.modules if m.startswith('autocode.core.')]
        original_modules = {m: sys.modules[m] for m in modules_to_remove}
        
        try:
            registry._loaded = False
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
                load_functions(strict=False)
            
            # Should have completed loading
            assert registry._loaded is True
            
        finally:
            registry._loaded = original_loaded
            clear_registry()
            # Re-add original functions using internal access (test cleanup only)
            from autocode.interfaces.registry import _registry
            _registry.extend(original_functions)
            for m, mod in original_modules.items():
                sys.modules[m] = mod
