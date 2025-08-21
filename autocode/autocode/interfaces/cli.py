"""
CLI interface using Click with dynamic commands from registry.
"""
import click
import uvicorn
from typing import Dict, Any, Callable

from autocode.autocode.interfaces.registry import (
    FUNCTION_REGISTRY, 
    get_parameters
)
from autocode.autocode.interfaces.api import create_api_app
from autocode.autocode.interfaces.mcp import create_mcp_app


@click.group(help="Autocode CLI - Minimalistic framework for code quality tools")
def app():
    """Autocode CLI - Minimalistic framework for code quality tools"""
    pass


# Type mapping for Click options
TYPE_MAP: Dict[type, Any] = {
    int: click.INT,
    float: click.FLOAT,
    bool: click.BOOL,
    str: click.STRING,
}


def add_command_options(command_func: Callable, params) -> Callable:
    """Helper to add Click options from explicit params."""
    # Add options in reverse order (Click requirement)
    for param in reversed(params):
        # Map Python types to Click types
        click_type = TYPE_MAP.get(param.type, click.STRING)
        
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


def create_handler(func_name: str, func_info) -> Callable:
    """Create a command handler for a specific function."""
    def command_func(**kwargs):
        """Execute the registered function with provided arguments."""
        try:
            # Filter and prepare function parameters
            func_params = {
                param.name: kwargs.get(
                    param.name, 
                    param.default if not param.required and param.default is not None else None
                )
                for param in func_info.params
                if param.name in kwargs
            }
            
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


def register_commands() -> None:
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
def serve_api(host: str, port: int, reload: bool):
    """Start only the API server."""
    click.echo(f"Starting Autocode API server on {host}:{port}")
    api_app = create_api_app()
    uvicorn.run(api_app, host=host, port=port, reload=reload)


@app.command("serve-mcp")
@click.option("--host", default="127.0.0.1", help="Host to bind to")
@click.option("--port", default=8001, type=int, help="Port to bind to")
@click.option("--reload", is_flag=True, help="Enable auto-reload")
def serve_mcp(host: str, port: int, reload: bool):
    """Start server with API endpoints and MCP integration."""
    click.echo(f"Starting Autocode server (API + MCP) on {host}:{port}")
    mcp_app = create_mcp_app()
    uvicorn.run(mcp_app, host=host, port=port, reload=reload)


@app.command("serve")
@click.option("--host", default="127.0.0.1", help="Host to bind to")
@click.option("--port", default=8000, type=int, help="Port to bind to")
@click.option("--reload", is_flag=True, help="Enable auto-reload")
def serve(host: str, port: int, reload: bool):
    """Start the unified server with both API and MCP in a single process."""
    click.echo(f"Starting Autocode unified server (API + MCP) on {host}:{port}")
    
    # create_mcp_app() now returns an app with both API and MCP integrated
    unified_app = create_mcp_app()
    
    # Start the unified server
    uvicorn.run(unified_app, host=host, port=port, reload=reload)


if __name__ == "__main__":
    app()
