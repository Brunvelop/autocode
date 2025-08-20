"""
CLI interface using Click with dynamic commands from registry.
"""
import click
import uvicorn
from typing import Optional, List
import inspect

from autocode.autocode.interfaces.registry import (
    FUNCTION_REGISTRY, 
    get_function, 
    get_function_info,
    get_parameters
)
from autocode.autocode.interfaces.api import create_api_app
from autocode.autocode.interfaces.mcp import create_mcp_app

@click.group(help="Autocode CLI - Minimalistic framework for code quality tools")
def app():
    """Autocode CLI - Minimalistic framework for code quality tools"""
    pass


def add_command_options(command_func, params):
    """Helper to add Click options from explicit params."""
    # Add options in reverse order (Click requirement)
    for param in reversed(params):
        # Map Python types to Click types
        click_type = str  # default
        if param.type == int:
            click_type = int
        elif param.type == float:
            click_type = float
        elif param.type == bool:
            click_type = bool
        
        # Create click option
        option_name = f"--{param.name.replace('_', '-')}"
        
        # Add the option to the command function
        command_func = click.option(
            option_name,
            type=click_type,
            default=param.default if not param.required else None,
            required=param.required,
            help=param.description
        )(command_func)
    
    return command_func


def create_handler(func_name, func_info):
    """Create a command handler for a specific function."""
    def command_func(**kwargs):
        """Execute the registered function with provided arguments."""
        try:
            # Filter kwargs to only include expected parameters
            func_params = {}
            for param in func_info.params:
                if param.name in kwargs:
                    value = kwargs[param.name]
                    # Use default if value is None and default exists
                    if value is None and not param.required and param.default is not None:
                        value = param.default
                    func_params[param.name] = value
            
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


def register_commands():
    """Register all commands from the function registry using explicit params."""
    for func_name, func_info in FUNCTION_REGISTRY.items():
        # Create the command handler
        command_func = create_handler(func_name, func_info)
        
        # Add Click options from explicit params
        command_func = add_command_options(command_func, func_info.params)
        
        # Register the command with the app
        app.command(name=func_name, help=func_info.description)(command_func)

# Register all commands
register_commands()


@app.command("list")
def list_functions():
    """List all available functions in the registry."""
    click.echo("Available functions:")
    for func_name, func_info in FUNCTION_REGISTRY.items():
        click.echo(f"  {func_name}: {func_info.description}")
        
        # Show inferred parameters with richer information
        params = get_parameters(func_name)
        if params:
            params_info = []
            for param in params:
                param_str = f"{param['name']} ({param['type']})"
                if not param['required']:
                    param_str += f" = {param['default']}"
                else:
                    param_str += " (required)"
                if param['description'] != f"Parameter {param['name']}":
                    param_str += f" - {param['description']}"
                params_info.append(param_str)
            
            click.echo(f"    Parameters:")
            for param_info in params_info:
                click.echo(f"      {param_info}")


@app.command("serve-api")
@click.option("--host", default="127.0.0.1", help="Host to bind to")
@click.option("--port", default=8000, type=int, help="Port to bind to")
@click.option("--reload", is_flag=True, help="Enable auto-reload")
def serve_api(host, port, reload):
    """Start only the API server."""
    click.echo(f"Starting Autocode API server on {host}:{port}")
    api_app = create_api_app()
    uvicorn.run(api_app, host=host, port=port, reload=reload)


@app.command("serve-mcp")
@click.option("--host", default="127.0.0.1", help="Host to bind to")
@click.option("--port", default=8001, type=int, help="Port to bind to")
@click.option("--reload", is_flag=True, help="Enable auto-reload")
def serve_mcp(host, port, reload):
    """Start server with API endpoints and MCP integration."""
    click.echo(f"Starting Autocode server (API + MCP) on {host}:{port}")
    mcp_app = create_mcp_app()
    uvicorn.run(mcp_app, host=host, port=port, reload=reload)


@app.command("serve")
@click.option("--host", default="127.0.0.1", help="Host to bind to")
@click.option("--port", default=8000, type=int, help="Port to bind to")
@click.option("--reload", is_flag=True, help="Enable auto-reload")
def serve(host, port, reload):
    """Start the unified server with both API and MCP in a single process."""
    click.echo(f"Starting Autocode unified server (API + MCP) on {host}:{port}")
    
    # create_mcp_app() now returns an app with both API and MCP integrated
    unified_app = create_mcp_app()
    
    # Start the unified server
    uvicorn.run(unified_app, host=host, port=port, reload=reload)


# Note: Individual commands removed in favor of the universal 'run' command
# This eliminates hardcoding and makes the CLI truly dynamic


if __name__ == "__main__":
    app()
