"""
CLI interface using Click with dynamic commands from registry.

This module provides a command-line interface for the Autocode framework,
automatically generating CLI commands from registered functions. It supports
dynamic parameter inference, multiple server modes, and function listing.

Example:
    # List available functions
    $ python -m autocode.interfaces.cli list
    
    # Execute a registered function
    $ python -m autocode.interfaces.cli hello_world --name "World"
    
    # Start API server
    $ python -m autocode.interfaces.cli serve-api --port 8000
"""
import click
import uvicorn
from typing import Dict, Any, Callable, Optional

from autocode.interfaces.registry import (
    get_all_functions,
    load_functions,
    get_functions_for_interface
)
from autocode.interfaces.api import create_api_app
from autocode.interfaces.mcp import create_mcp_app
from autocode.interfaces.logging_config import configure_cli_logging


# ============================================================================
# CONFIGURATION
# ============================================================================

# Type mapping for Click options - maps Python types to Click parameter types
TYPE_MAP: Dict[type, Any] = {
    int: click.INT,
    float: click.FLOAT,
    bool: click.BOOL,
    str: click.STRING,
}


# ============================================================================
# MAIN CLI GROUP
# ============================================================================

@click.group(help="Autocode CLI - Minimalistic framework for code quality tools")
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose output (DEBUG level)')
@click.pass_context
def app(ctx, verbose):
    """Autocode CLI - Minimalistic framework for code quality tools.
    
    This CLI provides dynamic command generation from registered functions,
    allowing you to execute any registered function from the command line
    with automatically inferred parameters.
    """
    # Configure logging based on verbose flag
    configure_cli_logging(verbose=verbose)
    
    # Store verbose flag in context for subcommands
    ctx.ensure_object(dict)
    ctx.obj['verbose'] = verbose


# ============================================================================
# PUBLIC COMMANDS
# ============================================================================

@app.command("list")
def list_functions_cmd():
    """List all available functions in the registry.
    
    Displays comprehensive information about each registered function including:
    - Function name and description
    - Parameter names, types, defaults, and descriptions
    - Required vs optional parameters
    
    Example:
        $ python -m autocode.interfaces.cli list
    """
    click.echo("Available functions:")
    for func_info in get_all_functions():
        click.echo(f"  {func_info.name}: {func_info.description}")
        
        # Show inferred parameters with rich information
        schema = func_info.to_schema()
        params = schema.parameters
        
        if params:
            params_info = []
            for param in params:
                param_str = f"{param.name} ({param.type_str})"
                if not param.required:
                    param_str += f" = {param.default}"
                else:
                    param_str += " (required)"
                if param.description != f"Parameter {param.name}":
                    param_str += f" - {param.description}"
                params_info.append(param_str)
            
            click.echo(f"    Parameters:")
            for param_info in params_info:
                click.echo(f"      {param_info}")


@app.command("serve-api")
@click.option("--host", default="127.0.0.1", help="Host to bind to")
@click.option("--port", default=8000, type=int, help="Port to bind to")
@click.option("--reload", is_flag=True, help="Enable auto-reload for development")
def serve_api(host: str, port: int, reload: bool):
    """Start the API server (REST endpoints only).
    
    Launches a FastAPI server with dynamic endpoints for all registered functions.
    Each function is exposed as both GET and POST endpoints with automatic
    parameter validation.
    
    Args:
        host: Network interface to bind to (default: 127.0.0.1)
        port: Port number to listen on (default: 8000)
        reload: Enable auto-reload on code changes (development mode)
        
    Example:
        $ python -m autocode.interfaces.cli serve-api --port 8000 --reload
    """
    click.echo(f"Starting Autocode API server on {host}:{port}")
    
    if reload:
        # When reloading, we must pass the import string to uvicorn
        # factory=True allows passing a function that returns the app
        uvicorn.run(
            "autocode.interfaces.api:create_api_app", 
            host=host, 
            port=port, 
            reload=True,
            factory=True
        )
    else:
        # Without reload, we can pass the app instance directly
        api_app = create_api_app()
        uvicorn.run(api_app, host=host, port=port)


@app.command("serve-mcp")
@click.option("--host", default="127.0.0.1", help="Host to bind to")
@click.option("--port", default=8001, type=int, help="Port to bind to")
@click.option("--reload", is_flag=True, help="Enable auto-reload for development")
def serve_mcp(host: str, port: int, reload: bool):
    """Start server with API endpoints and MCP integration.
    
    Launches a unified server combining FastAPI REST endpoints with
    Model Context Protocol (MCP) capabilities for AI assistant integration.
    
    Args:
        host: Network interface to bind to (default: 127.0.0.1)
        port: Port number to listen on (default: 8001)
        reload: Enable auto-reload on code changes (development mode)
        
    Example:
        $ python -m autocode.interfaces.cli serve-mcp --port 8001
    """
    click.echo(f"Starting Autocode server (API + MCP) on {host}:{port}")
    
    if reload:
        uvicorn.run(
            "autocode.interfaces.mcp:create_mcp_app",
            host=host,
            port=port,
            reload=True,
            factory=True
        )
    else:
        mcp_app = create_mcp_app()
        uvicorn.run(mcp_app, host=host, port=port)


@app.command("serve")
@click.option("--host", default="0.0.0.0", help="Host to bind to")
@click.option("--port", default=8000, type=int, help="Port to bind to")
@click.option("--reload", is_flag=True, help="Enable auto-reload for development")
def serve(host: str, port: int, reload: bool):
    """Start the unified server with both API and MCP (recommended).
    
    This is the recommended way to start the Autocode server, providing
    both REST API endpoints and MCP integration in a single process.
    
    Args:
        host: Network interface to bind to (default: 127.0.0.1)
        port: Port number to listen on (default: 8000)
        reload: Enable auto-reload on code changes (development mode)
        
    Example:
        $ python -m autocode.interfaces.cli serve --port 8000 --reload
    """
    click.echo(f"Starting Autocode unified server (API + MCP) on {host}:{port}")
    
    if reload:
        # create_mcp_app returns an app with both API and MCP integrated
        uvicorn.run(
            "autocode.interfaces.mcp:create_mcp_app",
            host=host,
            port=port,
            reload=True,
            factory=True
        )
    else:
        unified_app = create_mcp_app()
        uvicorn.run(unified_app, host=host, port=port)


# ============================================================================
# HEALTH CHECK COMMAND
# ============================================================================

@app.command("health-check")
@click.option(
    "--format", "output_format",
    type=click.Choice(["table", "json"]),
    default="table",
    show_default=True,
    help="Output format: table (human-readable) or json (machine-readable).",
)
@click.option(
    "--strict",
    is_flag=True,
    default=False,
    help="Use strict default thresholds, ignoring any [tool.codehealth] in pyproject.toml.",
)
@click.option(
    "--project-root",
    type=click.Path(exists=True),
    default=".",
    show_default=True,
    help="Root directory of the project to analyze.",
)
def health_check(output_format: str, strict: bool, project_root: str):
    """Run code health quality gates against the current project.

    Analyzes all files tracked by git and checks them against quality thresholds
    defined in [tool.codehealth] of pyproject.toml (or strict defaults with --strict).

    Exit code 0 = all gates passed, 1 = critical violations found.

    \b
    Examples:
        autocode health-check
        autocode health-check --format json
        autocode health-check --strict
        autocode health-check --project-root /path/to/project
    """
    import sys
    from pathlib import Path

    from autocode.core.code.analyzer import analyze_file_metrics
    from autocode.core.code.coupling import analyze_coupling
    from autocode.core.code.health import HealthConfig, load_thresholds, run_health_check
    from autocode.core.vcs.git import get_tracked_files

    root = Path(project_root).resolve()
    config = HealthConfig() if strict else load_thresholds(root)

    _ALL_EXTENSIONS = (".py", ".js", ".mjs", ".jsx")
    files = get_tracked_files(*_ALL_EXTENSIONS, cwd=str(root))

    file_metrics = []
    for fpath in files:
        if any(Path(fpath).match(pattern) for pattern in config.exclude):
            continue
        try:
            content = (root / fpath).read_text(encoding="utf-8")
            file_metrics.append(analyze_file_metrics(fpath, content))
        except Exception:
            pass

    coupling = analyze_coupling(files)
    result = run_health_check(config, file_metrics, coupling_result=coupling)

    if output_format == "json":
        _print_health_json(result)
    else:
        _print_health_table(result)

    sys.exit(0 if result.passed else 1)


# ============================================================================
# PRIVATE HELPERS - HEALTH OUTPUT FORMATTERS
# ============================================================================

def _print_health_json(result) -> None:
    """Print HealthCheckResult as JSON to stdout.

    Args:
        result: HealthCheckResult from run_health_check()
    """
    import json

    data = {
        "passed": result.passed,
        "summary": result.summary,
        "violations": [
            {
                "rule": v.rule,
                "level": v.level,
                "path": v.path,
                "value": v.value,
                "threshold": v.threshold,
                "detail": v.detail,
            }
            for v in result.violations
        ],
    }
    click.echo(json.dumps(data, indent=2))


def _print_health_table(result) -> None:
    """Print HealthCheckResult as a human-readable Unicode box table.

    Args:
        result: HealthCheckResult from run_health_check()
    """
    width = 56
    sep = "═" * width
    status = "✅  ALL GATES PASSED" if result.passed else "❌  GATES FAILED"

    click.echo(f"\n╔{sep}╗")
    click.echo(f"║{'  CODE HEALTH QUALITY GATES':^{width}}║")
    click.echo(f"╠{sep}╣")

    for key, value in result.summary.items():
        content = f"  {key:<26} {value}"
        click.echo(f"║{content:<{width}}║")

    criticals = [v for v in result.violations if v.level == "critical"]
    warnings = [v for v in result.violations if v.level == "warning"]

    if criticals:
        click.echo(f"╠{sep}╣")
        click.echo(f"║  ❌ CRITICAL VIOLATIONS ({len(criticals)}){'':<{width - 30}}║")
        for v in criticals[:10]:  # cap at 10 to avoid flooding
            line = f"    [{v.rule}] {v.path}: {v.value:.1f} > {v.threshold:.1f}"
            click.echo(f"║{line:<{width}}║")
            if v.detail:
                detail_line = f"      → {v.detail}"
                # Truncate detail if too long
                if len(detail_line) > width:
                    detail_line = detail_line[: width - 3] + "..."
                click.echo(f"║{detail_line:<{width}}║")
        if len(criticals) > 10:
            more_line = f"    … and {len(criticals) - 10} more critical violations"
            click.echo(f"║{more_line:<{width}}║")

    if warnings:
        click.echo(f"╠{sep}╣")
        click.echo(f"║  ⚠️  WARNINGS ({len(warnings)}){'':<{width - 22}}║")

    click.echo(f"╠{sep}╣")
    click.echo(f"║{'  ' + status:<{width}}║")
    click.echo(f"╚{sep}╝\n")


# ============================================================================
# PRIVATE HELPERS - COMMAND GENERATION
# ============================================================================

def _get_click_type(param_type: type, choices: Optional[list] = None) -> Any:
    """Get appropriate Click type for parameter.
    
    Maps Python types to Click parameter types with support for choices.
    
    Args:
        param_type: Python type annotation from function signature
        choices: Optional list of valid choices (from Literal types)
        
    Returns:
        Click type object suitable for option/argument definition
        
    Example:
        >>> _get_click_type(int)
        <IntParamType>
        >>> _get_click_type(str, choices=["a", "b", "c"])
        <click.Choice(['a', 'b', 'c'])>
    """
    # Handle choices from Literal types
    if choices:
        return click.Choice(choices)
    
    # Map to Click types, default to STRING for unknown types
    return TYPE_MAP.get(param_type, click.STRING)


def _add_command_options(command_func: Callable, params: list) -> Callable:
    """Add Click options to command function from parameter definitions.
    
    Iterates through function parameters and adds corresponding Click options
    in reverse order (Click requirement for proper option handling).
    
    Args:
        command_func: Function to decorate with Click options
        params: List of ParamSchema objects from function registry
        
    Returns:
        Decorated function with Click options attached
        
    Example:
        >>> def my_func(**kwargs): pass
        >>> decorated = _add_command_options(my_func, params)
        # decorated now has @click.option decorators for each param
    """
    # Add options in reverse order (Click requirement)
    for param in reversed(params):
        # Get Click type with choices support
        click_type = _get_click_type(param.type, param.choices)
        
        # Create option name (convert underscores to hyphens for CLI)
        option_name = f"--{param.name.replace('_', '-')}"
        
        # Prepare option arguments
        option_kwargs = {
            "type": click_type,
            "required": param.required,
            "help": param.description
        }
        
        # Only set default if not required (otherwise Click won't enforce requirement)
        if not param.required:
            option_kwargs["default"] = param.default
            
        # Add the option to the command function
        command_func = click.option(
            option_name,
            **option_kwargs
        )(command_func)
    
    return command_func


def _prepare_function_params(func_info, kwargs: Dict[str, Any]) -> Dict[str, Any]:
    """Prepare function parameters from CLI arguments.
    
    Filters and processes CLI arguments to match function signature,
    handling defaults and required parameters appropriately.
    
    Args:
        func_info: FunctionInfo object with parameter metadata
        kwargs: Dictionary of arguments from Click command
        
    Returns:
        Dictionary of parameters ready for function execution
        
    Example:
        >>> params = _prepare_function_params(func_info, {"x": 5, "y": None})
        {"x": 5, "y": 1}  # y uses default from func_info
    """
    func_params = {}
    for param in func_info.params:
        if param.name in kwargs and kwargs[param.name] is not None:
            # Parameter was provided and is not None
            func_params[param.name] = kwargs[param.name]
        elif not param.required and param.default is not None:
            # Parameter not provided or is None, use default if available
            func_params[param.name] = param.default
        elif param.required:
            # Required parameter - let Click handle the error if missing
            func_params[param.name] = kwargs.get(param.name)
    
    return func_params


def _create_handler(func_name: str, func_info) -> Callable:
    """Create a command handler for a specific function.
    
    Generates a Click-compatible command function that executes a registered
    function with proper parameter handling and error management.
    
    Args:
        func_name: Name of the function (for logging/errors)
        func_info: FunctionInfo object with function and metadata
        
    Returns:
        Command function ready to be registered with Click
        
    Example:
        >>> handler = _create_handler("my_func", func_info)
        >>> app.command()(handler)  # Registers command
    """
    def command_func(**kwargs):
        """Execute the registered function with provided arguments."""
        try:
            # Prepare function parameters from CLI arguments
            func_params = _prepare_function_params(func_info, kwargs)
            
            # Execute function with parameters
            result = func_info.func(**func_params)
            click.echo(result)
            
        except Exception as e:
            click.echo(f"Error executing {func_name}: {str(e)}", err=True)
            raise click.Abort()
    
    # Set function attributes for Click
    command_func.__name__ = f"{func_name}_command"
    command_func.__doc__ = func_info.description
    
    return command_func


def _register_commands() -> None:
    """Register all functions from registry as CLI commands.
    
    Uses get_functions_for_interface to get only functions that should be
    exposed in CLI, then creates Click commands for each with dynamically
    generated parameters.
    
    Should be called after load_functions() to ensure all functions
    are registered before CLI command generation.
    """
    # Use centralized filtering - only get functions exposed in CLI
    cli_functions = get_functions_for_interface("cli")
    
    for func_info in cli_functions:
        # Create the command handler
        command_func = _create_handler(func_info.name, func_info)
        
        # Add Click options from explicit params
        command_func = _add_command_options(command_func, func_info.params)
        
        # Register the command with the app
        app.command(name=func_info.name, help=func_info.description)(command_func)


# ============================================================================
# INITIALIZATION
# ============================================================================

def _initialize_cli():
    """Initialize CLI by loading functions and registering commands.
    
    This function is called automatically when the module is imported,
    but kept separate for testability and explicit flow control.
    
    Note: We configure logging at INFO level by default during initialization.
    The --verbose flag in app() will reconfigure it to DEBUG when requested.
    """
    # Configure logging BEFORE loading functions to reduce noise
    # Default to INFO level (quiet), verbose flag will change to DEBUG
    configure_cli_logging(verbose=False)
    
    # Load core functions
    load_functions()
    
    # Then register all commands from registry
    _register_commands()


# Initialize CLI on module import
_initialize_cli()


# ============================================================================
# ENTRY POINT
# ============================================================================

if __name__ == "__main__":
    app()
