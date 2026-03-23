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
    list_functions_cmd, serve_api, serve_mcp, serve, TYPE_MAP
)
from autocode.core.registry import (
    RegistryError, function_count, get_all_functions, get_function_by_name, clear_registry
)
from autocode.core.models import ParamSchema, FunctionInfo, GenericOutput


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
        def test_command(**kwargs):
            pass
        
        params = [
            ParamSchema(name="count", type=int, default=1, required=False, description="Number of items"),
            ParamSchema(name="name", type=str, required=True, description="Name parameter")
        ]
        
        decorated_func = _add_command_options(test_command, params)
        command = click.command()(decorated_func)
        
        # Verify function is still callable
        assert callable(command)
        
        # Test that options were added (indirectly through Click's mechanism)
        runner = CliRunner()
        result = runner.invoke(command, ['--help'])
        assert "--count" in result.output
        assert "--name" in result.output
        assert "Number of items" in result.output
        assert "Name parameter" in result.output
    
    def test_add_command_options_with_required(self):
        """Test adding required options."""
        def test_command(**kwargs):
            # Accept kwargs like real CLI handlers do
            pass
        
        params = [
            ParamSchema(name="required_param", type=str, required=True, description="Required parameter")
        ]
        
        decorated_func = _add_command_options(test_command, params)
        command = click.command()(decorated_func)
        
        runner = CliRunner()
        
        # Test that required parameter is enforced
        result = runner.invoke(command, [])
        assert result.exit_code != 0  # Should fail without required param
        
        # Test with required parameter
        result = runner.invoke(command, ['--required-param', 'value'])
        assert result.exit_code == 0
    
    def test_add_command_options_type_mapping(self):
        """Test that different parameter types are mapped correctly."""
        def test_command(**kwargs):
            pass
        
        params = [
            ParamSchema(name="int_param", type=int, default=42, required=False, description="Integer param"),
            ParamSchema(name="float_param", type=float, default=3.14, required=False, description="Float param"),
            ParamSchema(name="bool_param", type=bool, default=True, required=False, description="Boolean param"),
        ]
        
        decorated_func = _add_command_options(test_command, params)
        command = click.command()(decorated_func)
        
        runner = CliRunner()
        result = runner.invoke(command, ['--help'])
        
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
        from autocode.core.models import GenericOutput
        handler = _create_handler("test_add", sample_function_info)
        
        # Mock click.echo to capture output
        with patch('click.echo') as mock_echo:
            # Call handler with keyword arguments (as Click would)
            handler(x=5, y=3)
            
            # Should have echoed the result wrapped in GenericOutput
            mock_echo.assert_called_once()
            call_args = mock_echo.call_args[0][0]
            assert isinstance(call_args, GenericOutput)
            assert call_args.result == 8
            assert call_args.success == True
    
    def test_create_handler_execution_with_defaults(self, sample_function_info):
        """Test handler execution using default parameter values."""
        from autocode.core.models import GenericOutput
        handler = _create_handler("test_add", sample_function_info)
        
        with patch('click.echo') as mock_echo:
            # Call with only required parameter
            handler(x=10, y=None)  # y should use default
            
            # Should use default value for y (1), result wrapped in GenericOutput
            mock_echo.assert_called_once()
            call_args = mock_echo.call_args[0][0]
            assert isinstance(call_args, GenericOutput)
            assert call_args.result == 11
            assert call_args.success == True
    
    def test_create_handler_execution_error(self, sample_function_info):
        """Test handler execution with function error."""
        # Create function that raises an error
        def error_func(x: int, y: int = 1) -> int:
            raise ValueError("Test error")

        func_info = FunctionInfo(
            name="error_func",
            func=error_func,
            description="Error function",
            params=sample_function_info.params,
            return_type=GenericOutput
        )
        
        handler = _create_handler("error_func", func_info)
        
        with patch('click.echo') as mock_echo, \
             pytest.raises(click.Abort):
            handler(x=5, y=3)
            
            # Should echo error message
            mock_echo.assert_called_with("Error executing error_func: Test error", err=True)


class TestRegisterCommands:
    """Tests for register_commands - dynamic command registration."""
    
    @patch('autocode.interfaces.cli.load_functions')
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
    
    @patch('autocode.interfaces.cli.load_functions')
    def test_register_commands_empty_registry(self, mock_load):
        """Test command registration with empty registry raises RegistryError."""
        # Clear registry and commands
        original_commands = app.commands.copy()
        original_functions = get_all_functions()
        clear_registry()
        app.commands.clear()
        
        try:
            # Should raise RegistryError when registry is empty
            with pytest.raises(RegistryError) as exc_info:
                _register_commands()
            
            assert "Registry is empty" in str(exc_info.value)
            
        finally:
            # Restore - need internal access for test cleanup
            from autocode.core.registry import _registry
            app.commands = original_commands
            _registry.extend(original_functions)


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
    def test_serve_api_command_defaults(self, mock_uvicorn_run, populated_registry):
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
        # reload parameter is not passed when False
        assert 'reload' not in call_args[1]
    
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
        
        assert call_args[0][0] == "autocode.interfaces.api:create_api_app"
        assert call_args[1]['host'] == "0.0.0.0"
        assert call_args[1]['port'] == 3000
        assert call_args[1]['reload'] is True
        assert call_args[1]['factory'] is True
    
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
            mock_app, host="127.0.0.1", port=8001
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
        
        # Should NOT have called create_mcp_app directly (uses factory string)
        mock_create_mcp_app.assert_not_called()
        
        # Should pass import string and factory=True
        mock_uvicorn_run.assert_called_once_with(
            "autocode.interfaces.mcp:create_mcp_app", 
            host="0.0.0.0", 
            port=8000, 
            reload=True,
            factory=True
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
            params=[ParamSchema(name="x", type=int, required=True, description="Param x")],
            return_type=GenericOutput
        )
        
        # Temporarily add to registry - need internal access for test setup
        from autocode.core.registry import _registry
        original_functions = get_all_functions()
        _registry.append(error_func_info)
        
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
            _registry.clear()
            _registry.extend(original_functions)
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
            params=[ParamSchema(name="param_name", type=str, required=True, description="Param with underscore")],
            return_type=GenericOutput
        )
        
        def test_command(**kwargs):
            pass
        
        decorated_func = _add_command_options(test_command, func_info.params)
        command = click.command()(decorated_func)
        
        runner = CliRunner()
        result = runner.invoke(command, ['--help'])
        
        # Should show hyphenated option name
        assert "--param-name" in result.output
    
    def test_command_with_complex_parameter_types(self):
        """Test commands with various parameter types and defaults."""
        from typing import Optional
        
        params = [
            ParamSchema(name="string_param", type=str, required=True, description="String parameter"),
            ParamSchema(name="optional_int", type=int, default=42, required=False, description="Optional integer"),
            ParamSchema(name="boolean_flag", type=bool, default=False, required=False, description="Boolean flag"),
        ]
        
        def complex_command(**kwargs):
            pass
        
        decorated_func = _add_command_options(complex_command, params)
        command = click.command()(decorated_func)
        
        runner = CliRunner()
        result = runner.invoke(command, ['--help'])
        
        # All parameters should appear in help
        assert "--string-param" in result.output
        assert "--optional-int" in result.output
        assert "--boolean-flag" in result.output
        
        # Descriptions should appear
        assert "String parameter" in result.output
        assert "Optional integer" in result.output
        assert "Boolean flag" in result.output


# ============================================================================
# Refract.cli() — Instance-level CLI
# ============================================================================

class TestRefractCli:
    """Tests for Refract.cli(), @refract.command(), and run_cli property."""

    def _make_refract_with_function(self, sample_function_info):
        """Helper: build a Refract instance with one pre-loaded function."""
        from autocode.core.registry import Refract
        r = Refract("test-project")
        r._registry.append(sample_function_info)
        return r

    # ------------------------------------------------------------------
    # Basic structure
    # ------------------------------------------------------------------

    def test_cli_returns_click_group(self, sample_function_info):
        """Refract.cli() returns a Click Group."""
        from autocode.core.registry import Refract
        r = Refract("test-project")
        group = r.cli()
        assert isinstance(group, click.Group)

    def test_cli_has_standard_commands(self, sample_function_info):
        """Click group includes list, serve, serve-api, serve-mcp."""
        from autocode.core.registry import Refract
        r = Refract("test-project")
        group = r.cli()
        assert "list" in group.commands
        assert "serve" in group.commands
        assert "serve-api" in group.commands
        assert "serve-mcp" in group.commands

    def test_cli_group_name_in_help(self, sample_function_info):
        """The CLI group help text includes the instance name."""
        from autocode.core.registry import Refract
        r = Refract("my-special-project")
        group = r.cli()
        runner = CliRunner()
        result = runner.invoke(group, ["--help"])
        assert result.exit_code == 0
        assert "my-special-project" in result.output

    def test_cli_has_verbose_flag(self):
        """The Click group exposes --verbose / -v flag."""
        from autocode.core.registry import Refract
        r = Refract("test-project")
        group = r.cli()
        runner = CliRunner()
        result = runner.invoke(group, ["--help"])
        assert result.exit_code == 0
        assert "--verbose" in result.output or "-v" in result.output

    # ------------------------------------------------------------------
    # list command
    # ------------------------------------------------------------------

    def test_cli_list_shows_registered_functions(self, sample_function_info):
        """list command shows functions from the Refract instance's registry."""
        from autocode.core.registry import Refract
        r = self._make_refract_with_function(sample_function_info)
        group = r.cli()
        runner = CliRunner()
        result = runner.invoke(group, ["list"])
        assert result.exit_code == 0
        assert "Available functions:" in result.output
        assert "test_add" in result.output
        assert "Add two numbers together" in result.output

    def test_cli_list_empty_registry(self):
        """list command with empty registry shows header but no functions."""
        from autocode.core.registry import Refract
        r = Refract("test-project")
        group = r.cli()
        runner = CliRunner()
        result = runner.invoke(group, ["list"])
        assert result.exit_code == 0
        assert "Available functions:" in result.output

    def test_cli_list_shows_parameters(self, sample_function_info):
        """list command shows parameter information for registered functions."""
        from autocode.core.registry import Refract
        r = self._make_refract_with_function(sample_function_info)
        group = r.cli()
        runner = CliRunner()
        result = runner.invoke(group, ["list"])
        assert result.exit_code == 0
        assert "Parameters:" in result.output
        assert "x (int)" in result.output
        assert "y (int)" in result.output

    # ------------------------------------------------------------------
    # Dynamic function commands
    # ------------------------------------------------------------------

    def test_cli_dynamic_commands_appear(self, sample_function_info):
        """Functions in the registry become CLI commands."""
        from autocode.core.registry import Refract
        r = self._make_refract_with_function(sample_function_info)
        group = r.cli()
        assert "test_add" in group.commands

    def test_cli_dynamic_command_executes(self, sample_function_info):
        """Dynamic CLI command executes the underlying function."""
        from autocode.core.registry import Refract
        r = self._make_refract_with_function(sample_function_info)
        group = r.cli()
        runner = CliRunner()
        result = runner.invoke(group, ["test_add", "--x", "7", "--y", "3"])
        assert result.exit_code == 0
        assert "10" in result.output  # 7 + 3 = 10

    def test_cli_dynamic_command_help(self, sample_function_info):
        """Dynamic command exposes its parameters in --help."""
        from autocode.core.registry import Refract
        r = self._make_refract_with_function(sample_function_info)
        group = r.cli()
        runner = CliRunner()
        result = runner.invoke(group, ["test_add", "--help"])
        assert result.exit_code == 0
        assert "--x" in result.output
        assert "--y" in result.output
        assert "Add two numbers together" in result.output

    def test_cli_only_includes_cli_interface_functions(self, sample_function_info):
        """Functions without 'cli' interface are not added as commands."""
        from autocode.core.registry import Refract
        api_only_func = FunctionInfo(
            name="api_only",
            func=lambda x: x,
            description="API only function",
            params=[],
            interfaces=["api"],
            return_type=GenericOutput
        )
        r = Refract("test-project")
        r._registry.append(sample_function_info)   # has 'cli' interface
        r._registry.append(api_only_func)          # no 'cli' interface
        group = r.cli()
        assert "test_add" in group.commands
        assert "api_only" not in group.commands

    # ------------------------------------------------------------------
    # @refract.command() — custom commands
    # ------------------------------------------------------------------

    def test_command_decorator_registers_custom_command(self):
        """@refract.command() stores the command in _custom_commands."""
        from autocode.core.registry import Refract
        r = Refract("test-project")

        @r.command()
        def my_task():
            """A custom task."""
            pass

        assert len(r._custom_commands) == 1
        cmd_name, cmd_func, cmd_kwargs = r._custom_commands[0]
        assert cmd_name == "my-task"
        assert cmd_func is my_task

    def test_command_decorator_default_name_uses_hyphens(self):
        """Function name underscores become hyphens in command name."""
        from autocode.core.registry import Refract
        r = Refract("test-project")

        @r.command()
        def health_check():
            pass

        cmd_name, _, _ = r._custom_commands[0]
        assert cmd_name == "health-check"

    def test_command_decorator_explicit_name(self):
        """Explicit name= overrides the function name."""
        from autocode.core.registry import Refract
        r = Refract("test-project")

        @r.command(name="custom-name")
        def whatever():
            pass

        cmd_name, _, _ = r._custom_commands[0]
        assert cmd_name == "custom-name"

    def test_command_decorator_preserves_original_function(self):
        """@refract.command() returns the original function unchanged."""
        from autocode.core.registry import Refract
        r = Refract("test-project")

        @r.command()
        def my_func():
            return "hello"

        assert my_func() == "hello"

    def test_custom_commands_appear_in_cli_group(self):
        """Custom commands added via @refract.command() appear in cli()."""
        from autocode.core.registry import Refract
        r = Refract("test-project")

        @r.command()
        def health_check():
            """Run health check."""
            click.echo("all good")

        group = r.cli()
        assert "health-check" in group.commands

    def test_custom_command_executes_in_cli_group(self):
        """Custom commands added via @refract.command() are executable."""
        from autocode.core.registry import Refract
        r = Refract("test-project")

        @r.command()
        def say_hello():
            """Greet."""
            click.echo("hello from custom command")

        group = r.cli()
        runner = CliRunner()
        result = runner.invoke(group, ["say-hello"])
        assert result.exit_code == 0
        assert "hello from custom command" in result.output

    def test_multiple_custom_commands(self):
        """Multiple @refract.command() decorators all appear in the group."""
        from autocode.core.registry import Refract
        r = Refract("test-project")

        @r.command()
        def cmd_one():
            pass

        @r.command()
        def cmd_two():
            pass

        @r.command(name="cmd-three")
        def cmd_three_func():
            pass

        group = r.cli()
        assert "cmd-one" in group.commands
        assert "cmd-two" in group.commands
        assert "cmd-three" in group.commands

    # ------------------------------------------------------------------
    # run_cli property
    # ------------------------------------------------------------------

    def test_run_cli_returns_click_group(self):
        """run_cli property returns a Click Group."""
        from autocode.core.registry import Refract
        r = Refract("test-project")
        assert isinstance(r.run_cli, click.Group)

    def test_run_cli_is_callable(self):
        """run_cli returns a callable (required for pyproject.toml entry points)."""
        from autocode.core.registry import Refract
        r = Refract("test-project")
        assert callable(r.run_cli)

    def test_run_cli_includes_standard_commands(self):
        """run_cli group has the same commands as cli()."""
        from autocode.core.registry import Refract
        r = Refract("test-project")
        group = r.run_cli
        assert "list" in group.commands
        assert "serve" in group.commands
        assert "serve-api" in group.commands
        assert "serve-mcp" in group.commands

    # ------------------------------------------------------------------
    # serve-api command
    # ------------------------------------------------------------------

    @patch('uvicorn.run')
    def test_serve_api_calls_uvicorn(self, mock_uvicorn):
        """serve-api command invokes uvicorn.run with correct parameters."""
        from autocode.core.registry import Refract
        from unittest.mock import MagicMock
        r = Refract("test-project")
        mock_api_app = MagicMock()
        r.api = MagicMock(return_value=mock_api_app)

        group = r.cli()
        runner = CliRunner()
        result = runner.invoke(group, ["serve-api", "--host", "0.0.0.0", "--port", "9000"])

        assert result.exit_code == 0
        r.api.assert_called_once()
        mock_uvicorn.assert_called_once_with(mock_api_app, host="0.0.0.0", port=9000)

    @patch('uvicorn.run')
    def test_serve_api_default_host_port(self, mock_uvicorn):
        """serve-api uses default host 127.0.0.1 and port 8000."""
        from autocode.core.registry import Refract
        from unittest.mock import MagicMock
        r = Refract("test-project")
        r.api = MagicMock(return_value=MagicMock())

        group = r.cli()
        runner = CliRunner()
        result = runner.invoke(group, ["serve-api"])

        assert result.exit_code == 0
        call_kwargs = mock_uvicorn.call_args[1]
        assert call_kwargs["host"] == "127.0.0.1"
        assert call_kwargs["port"] == 8000

    # ------------------------------------------------------------------
    # Isolation: multiple Refract instances
    # ------------------------------------------------------------------

    def test_two_refract_instances_have_independent_cli_groups(self, sample_function_info):
        """Each Refract instance gets its own isolated CLI group."""
        from autocode.core.registry import Refract
        r1 = Refract("project-a")
        r1._registry.append(sample_function_info)

        r2 = Refract("project-b")  # empty registry

        g1 = r1.cli()
        g2 = r2.cli()

        assert "test_add" in g1.commands
        assert "test_add" not in g2.commands
