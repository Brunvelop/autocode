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

from .models import CheckExecutionResponse, AutocodeConfig
# Import CLI functions for thin wrapper implementation
from ..cli import check_docs, check_tests, git_changes, code_to_design, load_config

# Initialize FastAPI app
app = FastAPI(
    title="Autocode Thin Layer API",
    description="Simplified API that provides CLI wrappers and web interface",
    version="1.0.0"
)

# Setup templates and static files
templates = Jinja2Templates(directory=Path(__file__).parent.parent / "web" / "templates")
app.mount("/static", StaticFiles(directory=Path(__file__).parent.parent / "web" / "static"), name="static")
# Mount design directory to serve documentation files
app.mount("/design", StaticFiles(directory=Path(__file__).parent.parent.parent / "design"), name="design")

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
async def root(request: Request):
    """Redirect to dashboard."""
    return RedirectResponse(url="/dashboard", status_code=302)


@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request):
    """Serve the dashboard page."""
    return templates.TemplateResponse("pages/dashboard.html", {"request": request})


@app.get("/design", response_class=HTMLResponse)
async def design(request: Request):
    """Serve the design page."""
    return templates.TemplateResponse("pages/design.html", {"request": request})


@app.get("/config", response_class=HTMLResponse)
async def config_page(request: Request):
    """Serve the configuration page."""
    return templates.TemplateResponse("pages/config.html", {"request": request})


@app.get("/index", response_class=HTMLResponse)
async def index(request: Request):
    """Serve the old index page (backward compatibility)."""
    return templates.TemplateResponse("index.html", {"request": request})


# CLI Wrapper Endpoints

@app.post("/api/generate-docs", response_model=CheckExecutionResponse)
async def generate_docs(background_tasks: BackgroundTasks):
    """Generate/check documentation using CLI function."""
    try:
        def run_docs_task():
            """Background task to run docs check."""
            return check_docs()
        
        background_tasks.add_task(run_docs_task)
        
        return CheckExecutionResponse(
            success=True,
            result=None,
            error=None
        )
    except Exception as e:
        return handle_cli_error("check_docs", e)


@app.post("/api/generate-design", response_model=CheckExecutionResponse)
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


@app.post("/api/analyze-git", response_model=CheckExecutionResponse)
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


@app.get("/api/config/load", response_model=Dict[str, Any])
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


@app.post("/api/docs/check-sync")
async def check_docs_sync():
    """Synchronously check documentation status."""
    try:
        exit_code = check_docs()
        return {
            "success": exit_code == 0,
            "exit_code": exit_code,
            "message": "Documentation is up to date" if exit_code == 0 else "Documentation issues found"
        }
    except Exception as e:
        logger.error(f"Error checking docs: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Health check endpoint
@app.get("/health")
async def health_check():
    """Simple health check."""
    return {"status": "healthy"}


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
