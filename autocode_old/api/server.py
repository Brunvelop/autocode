"""
FastAPI thin layer application for autocode.
Simplified API that only provides CLI wrappers and serves web pages.
"""

import logging
from pathlib import Path
from typing import Dict, Any

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi import Request
from fastapi_mcp import FastApiMCP

from .models import CheckExecutionResponse
# Import CLI functions for thin wrapper implementation
from ..cli import check_tests, git_changes, code_to_design, opencode, count_tokens
# Import core functionality for docs check
from ..core.config import load_config
from ..core.docs import check_documentation
from ..core.docs.formatters import format_json_output, format_summary_only

# Initialize FastAPI app
app = FastAPI(
    title="Autocode Thin Layer API",
    description="Simplified API that provides CLI wrappers and web interface",
    version="1.0.0"
)

# Initialize MCP server
mcp = FastApiMCP(
    app,
    name="Autocode MCP Server",
    description="MCP server for autocode CLI tools and API endpoints"
)

# Setup templates and static files
templates = Jinja2Templates(directory=Path(__file__).parent.parent / "web" / "templates")
app.mount("/static", StaticFiles(directory=Path(__file__).parent.parent / "web" / "static"), name="static")
# Mount design directory to serve documentation files
app.mount("/design", StaticFiles(directory=Path(__file__).parent.parent.parent / "design"), name="design")
# Mount docs directory to serve markdown files
app.mount("/documentation", StaticFiles(directory=Path(__file__).parent.parent.parent / "docs"), name="documentation")

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def handle_cli_error(func_name: str, error: Exception) -> CheckExecutionResponse:
    """Standard error handling for CLI function calls."""
    logger.error(f"Error in CLI function '{func_name}': {error}")
    return CheckExecutionResponse(
        success=False,
        result=None,
        error=f"CLI function '{func_name}' failed: {str(error)}"
    )


# Page Routes

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Serve the home page."""
    return templates.TemplateResponse("pages/home.html", {"request": request})


@app.get("/documentation", response_class=HTMLResponse)
async def documentation_page(request: Request):
    """Serve the documentation page."""
    return templates.TemplateResponse("pages/docs.html", {"request": request})


# CLI Wrapper Endpoints

@app.post("/api/generate-design", response_model=CheckExecutionResponse, operation_id="generate_design")
async def generate_design(
    directory: str = None,
    output_dir: str = None,
    background_tasks: BackgroundTasks = None
):
    """Generate design diagrams using CLI function."""
    try:
        def run_design_task():
            """Background task to run design generation."""
            return code_to_design(
                directory=directory,
                output_dir=output_dir
            )
        
        background_tasks.add_task(run_design_task)
        
        return CheckExecutionResponse(
            success=True,
            result=None,
            error=None
        )
    except Exception as e:
        return handle_cli_error("code_to_design", e)


@app.post("/api/analyze-git", response_model=CheckExecutionResponse, operation_id="analyze_git")
async def analyze_git(
    output: str = None,
    verbose: bool = False,
    background_tasks: BackgroundTasks = None
):
    """Analyze git changes using CLI function."""
    try:
        def run_git_task():
            """Background task to run git analysis."""
            return git_changes(output=output, verbose=verbose)
        
        background_tasks.add_task(run_git_task)
        
        return CheckExecutionResponse(
            success=True,
            result=None,
            error=None
        )
    except Exception as e:
        return handle_cli_error("git_changes", e)


@app.get("/api/config/load", response_model=Dict[str, Any], operation_id="load_configuration")
async def load_configuration():
    """Load configuration using CLI function."""
    try:
        config = load_config()
        return {
            "success": True,
            "config": config.dict(),
            "error": None
        }
    except Exception as e:
        logger.error(f"Error loading config: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/check-tests", response_model=CheckExecutionResponse, operation_id="check_tests")
async def check_tests_wrapper(background_tasks: BackgroundTasks):
    """Check if tests exist and are passing using CLI function."""
    try:
        def run_tests_task():
            """Background task to run the CLI function."""
            return check_tests()
        
        background_tasks.add_task(run_tests_task)
        
        return CheckExecutionResponse(
            success=True,
            result=None,
            error=None
        )
    except Exception as e:
        return handle_cli_error("check_tests", e)


@app.post("/api/opencode", response_model=CheckExecutionResponse, operation_id="opencode_analysis")
async def opencode_wrapper(
    background_tasks: BackgroundTasks,
    prompt: str = None,
    prompt_file: str = None,
    list_prompts: bool = False,
    validate: bool = False,
    debug: bool = False,
    json_output: bool = False,
    quiet: bool = False,
    verbose: bool = False,
    cwd: str = None
):
    """Execute OpenCode AI analysis with prompts using CLI function."""
    try:
        def run_opencode_task():
            """Background task to run the CLI function."""
            return opencode(
                prompt=prompt,
                prompt_file=prompt_file,
                list_prompts=list_prompts,
                validate=validate,
                debug=debug,
                json_output=json_output,
                quiet=quiet,
                verbose=verbose,
                cwd=cwd
            )
        
        background_tasks.add_task(run_opencode_task)
        
        return CheckExecutionResponse(
            success=True,
            result=None,
            error=None
        )
    except Exception as e:
        return handle_cli_error("opencode", e)


@app.post("/api/count-tokens", response_model=CheckExecutionResponse, operation_id="count_tokens")
async def count_tokens_wrapper(
    background_tasks: BackgroundTasks,
    file: str = None,
    directory: str = None,
    pattern: str = "*",
    model: str = "gpt-4",
    threshold: int = None,
    verbose: bool = False
):
    """Count tokens in files for LLM analysis using CLI function."""
    try:
        def run_count_tokens_task():
            """Background task to run the CLI function."""
            return count_tokens(
                file=file,
                directory=directory,
                pattern=pattern,
                model=model,
                threshold=threshold,
                verbose=verbose
            )
        
        background_tasks.add_task(run_count_tokens_task)
        
        return CheckExecutionResponse(
            success=True,
            result=None,
            error=None
        )
    except Exception as e:
        return handle_cli_error("count_tokens", e)


@app.post("/api/docs/check", operation_id="check_documentation")
async def check_docs():
    """Check documentation status and return detailed results."""
    try:
        config = load_config()
        result = check_documentation(Path.cwd(), config.docs)
        
        return {
            "success": not result.has_issues,
            "data": format_json_output(result),
            "summary": format_summary_only(result)
        }
    except Exception as e:
        logger.error(f"Error checking docs: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Health check endpoint
@app.get("/health")
async def health_check():
    """Simple health check."""
    return {"status": "healthy"}


# Mount MCP server with both HTTP and SSE transports
mcp.mount_http()
mcp.mount_sse()
mcp.setup_server()


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    return app


if __name__ == "__main__":
    import uvicorn
    
    # Run the application
    uvicorn.run(
        "autocode.api.server:app",
        host="127.0.0.1",
        port=8080,
        reload=True,
        log_level="info"
    )
