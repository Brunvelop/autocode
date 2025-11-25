"""
Tests for autocode.interfaces.cli module.

Tests the Click-based CLI interface including dynamic command generation,
built-in commands, and integration with the function registry.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock, call
from click.testing import CliRunner
import click

from autocode.interfaces.cli import (
    app, _add_command_options, _create_handler, _register_commands,
    list_functions, serve_api, serve_mcp, serve, TYPE_MAP
)
from autocode.interfaces.registry import FUNCTION_REGISTRY
from autocode.interfaces.models import ExplicitParam, FunctionInfo


class TestTypeMappingAndUtils:
    """Tests for CLI utility functions and type mapping."""
    
    def test_type_map_completeness(self):
        """Test that TYPE_MAP covers expected Python types."""
        expected_mappings = {
            int: click.INT,
            float: click.FLOAT,
            bool: click.BOOL,
            str: click.STRING,
        }
        
        for python_type, click_type in expected_mappings.items():
            assert TYPE_MAP[python_type] == click_type
    
    def test_add_command_options_basic(self):
        """Test adding basic Click options to a command function."""
        @click.command()
        def test_command():
            pass
        
        params = [
            ExplicitParam(name="count", type=int, default=1, required=False, description="Number of items"),
            ExplicitParam(name="name", type=str, required=True, description="Name parameter")
        ]
        
        decorated_func = _add_command_options(test_command, params)
        
        # Verify function is still callable
        assert callable(decorated_func)
        
        # Test that options were added (indirectly through Click's mechanism)
        runner = CliRunner()
        result = runner.invoke(decorated_func, ['--help'])
        assert "--count" in result.output
        assert "--name" in result.output
        assert "Number of items" in result.output
        assert "Name parameter" in result.output
    
    def test_add_command_options_with_required(self):
        """Test adding required options."""
        @click.command()
        def test_command(**kwargs):
            # Accept kwargs like real CLI handlers do
            pass
        
        params = [
            ExplicitParam(name="required_param", type=str, required=True, description="Required parameter")
        ]
        
        decorated_func = _add_command_options(test_command, params)
        
        runner = CliRunner()
        
        # Test that required parameter is enforced
        result = runner.invoke(decorated_func, [])
        assert result.exit_code != 0  # Should fail without required param
        
        # Test with required parameter
        result = runner.invoke(decorated_func, ['--required-param', 'value'])
        assert result.exit_code == 0
    
    def test_add_command_options_type_mapping(self):
        """Test that different parameter types are mapped correctly."""
        @click.command()
        def test_command():
            pass
        
        params = [
            ExplicitParam(name="int_param", type=int, default=42, required=False, description="Integer param"),
            ExplicitParam(name="float_param", type=float, default=3.14, required=False, description="Float param"),
            ExplicitParam(name="bool_param", type=bool, default=True, required=False, description="Boolean param"),
        ]
        
        decorated_func = _add_command_options(test_command, params)
        
        runner = CliRunner()
        result = runner.invoke(decorated_func, ['--help'])
        
        # Check that all parameters appear in help
        assert "--int-param" in result.output
        assert "--float-param" in result.output
        assert "--bool-param" in result.output


class TestCreateHandler:
    """Tests for create_handler - CLI command handler creation."""
    
    def test_create_handler_basic(self, sample_function_info):
        """Test creating a basic command handler."""
        handler = _create_handler("test_add", sample_function_info)
        
        assert callable(handler)
        assert handler.__name__ == "test_add_command"
        assert handler.__doc__ == sample_function_info.description
    
    def test_create_handler_execution_success(self, sample_function_info):
        """Test successful handler execution."""
        handler = _create_handler("test_add", sample_function_info)
        
        # Mock click.echo to capture output
        with patch('click.echo') as mock_echo:
            # Call handler with keyword arguments (as Click would)
            handler(x=5, y=3)
            
            # Should have echoed the result
            mock_echo.assert_called_once_with(8)
    
    def test_create_handler_execution_with_defaults(self, sample_function_info):
        """Test handler execution using default parameter values."""
        handler = _create_handler("test_add", sample_function_info)
        
        with patch('click.echo') as mock_echo:
            # Call with only required parameter
            handler(x=10, y=None)  # y should use default
            
            # Should use default value for y (1)
            mock_echo.assert_called_once_with(11)
    
    def test_create_handler_execution_error(self, sample_function_info):
        """Test handler execution with function error."""
        # Create function that raises an error
        def error_func(x: int, y: int = 1) -> int:
            raise ValueError("Test error")
        
        func_info = FunctionInfo(
            name="error_func",
            func=error_func,
            description="Function that errors",
            params=sample_function_info.params
        )
        
        handler = _create_handler("error_func", func_info)
        
        with patch('click.echo') as mock_echo, \
             pytest.raises(click.Abort):
            handler(x=5, y=3)
            
            # Should echo error message
            mock_echo.assert_called_with("Error executing error_func: Test error", err=True)


class TestRegisterCommands:
    """Tests for register_commands - dynamic command registration."""
    
    @patch('autocode.interfaces.cli.load_core_functions')
    def test_register_commands_with_populated_registry(self, mock_load, populated_registry):
        """Test command registration with functions in registry."""
        # Clear existing commands from app first
        original_commands = app.commands.copy()
        app.commands.clear()
        
        try:
            _register_commands()
            
            # Should have registered commands for functions in registry
            assert "test_add" in app.commands
            
            # Test the registered command
            runner = CliRunner()
            result = runner.invoke(app, ['test_add', '--help'])
            assert result.exit_code == 0
            assert "Add two numbers together" in result.output
            assert "--x" in result.output
            assert "--y" in result.output
            
        finally:
            # Restore original commands
            app.commands = original_commands
    
    @patch('autocode.interfaces.cli.load_core_functions')
    def test_register_commands_empty_registry(self, mock_load):
        """Test command registration with empty registry."""
        # Clear registry and commands
        original_commands = app.commands.copy()
        original_registry = FUNCTION_REGISTRY.copy()
        FUNCTION_REGISTRY.clear()
        app.commands.clear()
        
        try:
            _register_commands()
            
            # Should not have registered any new commands (only built-in ones)
            # Note: This test depends on the order of operations in the module
            
        finally:
            # Restore
            app.commands = original_commands
            FUNCTION_REGISTRY.update(original_registry)


class TestBuiltInCommands:
    """Tests for built-in CLI commands."""
    
    def test_list_functions_command(self, populated_registry):
        """Test the list command."""
        runner = CliRunner()
        result = runner.invoke(app, ['list'])
        
        assert result.exit_code == 0
        assert "Available functions:" in result.output
        assert "test_add" in result.output
        assert "Add two numbers together" in result.output
        
        # Should show parameter information
        assert "Parameters:" in result.output
        assert "x (int)" in result.output
        assert "y (int)" in result.output
    
    def test_list_functions_empty_registry(self):
        """Test list command with empty registry."""
        runner = CliRunner()
        result = runner.invoke(app, ['list'])
        
        assert result.exit_code == 0
        assert "Available functions:" in result.output
    
    @patch('uvicorn.run')
    def test_serve_api_command_defaults(self, mock_uvicorn_run):
        """Test serve-api command with default parameters."""
        runner = CliRunner()
        result = runner.invoke(app, ['serve-api'])
        
        assert result.exit_code == 0
        
        # Should have called uvicorn.run with defaults
        mock_uvicorn_run.assert_called_once()
        call_args = mock_uvicorn_run.call_args
        
        # Check the arguments passed to uvicorn.run
        assert call_args[1]['host'] == "127.0.0.1"
        assert call_args[1]['port'] == 8000
        assert call_args[1]['reload'] is False
    
    @patch('uvicorn.run')
    def test_serve_api_command_custom_params(self, mock_uvicorn_run):
        """Test serve-api command with custom parameters."""
        runner = CliRunner()
        result = runner.invoke(app, [
            'serve-api',
            '--host', '0.0.0.0',
            '--port', '3000',
            '--reload'
        ])
        
        assert result.exit_code == 0
        
        # Should have called uvicorn.run with custom params
        mock_uvicorn_run.assert_called_once()
        call_args = mock_uvicorn_run.call_args
        
        assert call_args[1]['host'] == "0.0.0.0"
        assert call_args[1]['port'] == 3000
        assert call_args[1]['reload'] is True
    
    @patch('uvicorn.run')
    @patch('autocode.interfaces.cli.create_mcp_app')
    def test_serve_mcp_command(self, mock_create_mcp_app, mock_uvicorn_run):
        """Test serve-mcp command."""
        mock_app = Mock()
        mock_create_mcp_app.return_value = mock_app
        
        runner = CliRunner()
        result = runner.invoke(app, ['serve-mcp', '--port', '8001'])
        
        assert result.exit_code == 0
        
        # Should have created MCP app and started uvicorn
        mock_create_mcp_app.assert_called_once()
        mock_uvicorn_run.assert_called_once_with(
            mock_app, host="127.0.0.1", port=8001, reload=False
        )
    
    @patch('uvicorn.run')
    @patch('autocode.interfaces.cli.create_mcp_app')
    def test_serve_command_unified(self, mock_create_mcp_app, mock_uvicorn_run):
        """Test unified serve command."""
        mock_app = Mock()
        mock_create_mcp_app.return_value = mock_app
        
        runner = CliRunner()
        result = runner.invoke(app, ['serve', '--reload'])
        
        assert result.exit_code == 0
        
        # Should have created unified MCP app
        mock_create_mcp_app.assert_called_once()
        mock_uvicorn_run.assert_called_once_with(
            mock_app, host="127.0.0.1", port=8000, reload=True
        )


class TestCLIIntegration:
    """Integration tests for CLI functionality."""
    
    def test_full_cli_integration_with_dynamic_command(self, populated_registry):
        """Test full CLI integration with dynamically registered command."""
        # Clear existing commands and re-register with populated registry
        original_commands = app.commands.copy()
        app.commands.clear()
        
        try:
            _register_commands()
            
            runner = CliRunner()
            
            # Test executing the dynamic command
            result = runner.invoke(app, ['test_add', '--x', '10', '--y', '5'])
            
            assert result.exit_code == 0
            assert "15" in result.output  # 10 + 5 = 15
            
        finally:
            # Restore original commands
            app.commands = original_commands
    
    def test_cli_error_handling_missing_required_param(self, populated_registry):
        """Test CLI error handling with missing required parameter."""
        runner = CliRunner()
        
        # Try to execute command without required parameter
        result = runner.invoke(app, ['test_add', '--y', '5'])  # Missing --x
        
        assert result.exit_code != 0  # Should fail
        # Click should show error about missing option
    
    def test_cli_help_system(self, populated_registry):
        """Test CLI help system."""
        # Clear existing commands and re-register with populated registry
        original_commands = app.commands.copy()
        app.commands.clear()
        
        try:
            _register_commands()
            
            runner = CliRunner()
            
            # Test main help
            result = runner.invoke(app, ['--help'])
            assert result.exit_code == 0
            assert "Autocode CLI" in result.output
            
            # Test command-specific help
            result = runner.invoke(app, ['test_add', '--help'])
            assert result.exit_code == 0
            assert "Add two numbers together" in result.output
            assert "--x" in result.output
            assert "--y" in result.output
            
        finally:
            # Restore original commands
            app.commands = original_commands
    
    def test_cli_version_and_basic_functionality(self):
        """Test basic CLI functionality and structure."""
        runner = CliRunner()
        
        # Test that the app is a Click group
        assert isinstance(app, click.Group)
        
        # Test basic invocation
        result = runner.invoke(app, ['--help'])
        assert result.exit_code == 0
        
        # Check that built-in commands are present
        assert any('list' in cmd for cmd in result.output.split())
        assert any('serve' in cmd for cmd in result.output.split())


class TestCLIErrorScenarios:
    """Tests for various CLI error scenarios."""
    
    @patch('uvicorn.run')
    def test_serve_command_with_uvicorn_error(self, mock_uvicorn_run):
        """Test serve command when uvicorn raises an error."""
        mock_uvicorn_run.side_effect = Exception("Uvicorn failed to start")
        
        runner = CliRunner()
        result = runner.invoke(app, ['serve-api'])
        
        # Command should fail gracefully
        assert result.exit_code != 0
    
    def test_dynamic_command_with_function_error(self, populated_registry):
        """Test dynamic command when underlying function raises error."""
        # Create a function that always errors
        def always_fails(x: int) -> int:
            raise RuntimeError("This function always fails")
        
        error_func_info = FunctionInfo(
            name="always_fails",
            func=always_fails,
            description="Function that always fails",
            params=[ExplicitParam(name="x", type=int, required=True, description="Input")]
        )
        
        # Temporarily add to registry
        original_registry = FUNCTION_REGISTRY.copy()
        FUNCTION_REGISTRY["always_fails"] = error_func_info
        
        # Register commands again to pick up the new function
        original_commands = app.commands.copy()
        
        try:
            # Add the new command manually for testing
            handler = _create_handler("always_fails", error_func_info)
            decorated_handler = _add_command_options(handler, error_func_info.params)
            command = app.command(name="always_fails", help=error_func_info.description)(decorated_handler)
            
            runner = CliRunner()
            result = runner.invoke(app, ['always_fails', '--x', '5'])
            
            # Should fail with Abort
            assert result.exit_code != 0
            
        finally:
            # Restore original state
            FUNCTION_REGISTRY.clear()
            FUNCTION_REGISTRY.update(original_registry)
            app.commands = original_commands
    
    def test_parameter_type_validation(self, populated_registry):
        """Test parameter type validation in CLI."""
        runner = CliRunner()
        
        # Try to pass non-integer value to integer parameter
        result = runner.invoke(app, ['test_add', '--x', 'not_a_number', '--y', '5'])
        
        # Click should handle type validation
        assert result.exit_code != 0


class TestCLICommandRegistrationEdgeCases:
    """Tests for edge cases in command registration."""
    
    def test_command_with_underscores_to_hyphens(self):
        """Test that parameter names with underscores become hyphenated options."""
        def func_with_underscore(param_name: str) -> str:
            return param_name
        
        func_info = FunctionInfo(
            name="underscore_func",
            func=func_with_underscore,
            description="Function with underscore param",
            params=[ExplicitParam(name="param_name", type=str, required=True, description="Param with underscore")]
        )
        
        @click.command()
        def test_command():
            pass
        
        decorated_func = _add_command_options(test_command, func_info.params)
        
        runner = CliRunner()
        result = runner.invoke(decorated_func, ['--help'])
        
        # Should show hyphenated option name
        assert "--param-name" in result.output
    
    def test_command_with_complex_parameter_types(self):
        """Test commands with various parameter types and defaults."""
        from typing import Optional
        
        params = [
            ExplicitParam(name="string_param", type=str, required=True, description="String parameter"),
            ExplicitParam(name="optional_int", type=int, default=42, required=False, description="Optional integer"),
            ExplicitParam(name="boolean_flag", type=bool, default=False, required=False, description="Boolean flag"),
        ]
        
        @click.command()
        def complex_command():
            pass
        
        decorated_func = _add_command_options(complex_command, params)
        
        runner = CliRunner()
        result = runner.invoke(decorated_func, ['--help'])
        
        # All parameters should appear in help
        assert "--string-param" in result.output
        assert "--optional-int" in result.output
        assert "--boolean-flag" in result.output
        
        # Descriptions should appear
        assert "String parameter" in result.output
        assert "Optional integer" in result.output
        assert "Boolean flag" in result.output
