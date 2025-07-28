"""
FastAPI application for autocode daemon.
"""

import asyncio
import logging
from pathlib import Path
from typing import Dict, Any, List

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from fastapi import Request

from ..orchestration.daemon import AutocodeDaemon
from .models import (
    StatusResponse,
    CheckExecutionRequest,
    CheckExecutionResponse,
    AutocodeConfig,
    CheckResult,
    DaemonStatus
)
# Import CLI functions for thin wrapper implementation
from ..cli import check_docs, check_tests, git_changes, code_to_design, load_config

# Initialize FastAPI app
app = FastAPI(
    title="Autocode Monitoring API",
    description="API for autocode daemon monitoring and management",
    version="1.0.0"
)

# Global daemon instance
daemon: AutocodeDaemon = None
daemon_task: asyncio.Task = None

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


@app.on_event("startup")
async def startup_event():
    """Initialize daemon on startup."""
    global daemon, daemon_task
    
    logger.info("Starting autocode daemon")
    daemon = AutocodeDaemon()
    
    # Start daemon in background
    daemon_task = asyncio.create_task(daemon.start())
    
    logger.info("Autocode daemon started")


@app.on_event("shutdown")
async def shutdown_event():
    """Clean shutdown of daemon."""
    global daemon, daemon_task
    
    if daemon:
        logger.info("Shutting down autocode daemon")
        daemon.stop()
        
        if daemon_task:
            daemon_task.cancel()
            try:
                await daemon_task
            except asyncio.CancelledError:
                pass
        
        logger.info("Autocode daemon stopped")


# API Routes

@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    """Redirect to dashboard."""
    from fastapi.responses import RedirectResponse
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


# Keep the old route for backward compatibility
@app.get("/index", response_class=HTMLResponse)
async def index(request: Request):
    """Serve the old index page (backward compatibility)."""
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/api/status", response_model=StatusResponse)
async def get_status():
    """Get current status of daemon and all checks."""
    if not daemon:
        raise HTTPException(status_code=503, detail="Daemon not initialized")
    
    daemon_status = daemon.get_daemon_status()
    check_results = daemon.get_all_results()
    
    return StatusResponse(
        daemon=daemon_status,
        checks=check_results,
        config=daemon.config
    )


@app.get("/api/daemon/status", response_model=DaemonStatus)
async def get_daemon_status():
    """Get daemon status."""
    if not daemon:
        raise HTTPException(status_code=503, detail="Daemon not initialized")
    
    return daemon.get_daemon_status()


@app.get("/api/checks", response_model=Dict[str, CheckResult])
async def get_all_checks():
    """Get results of all checks."""
    if not daemon:
        raise HTTPException(status_code=503, detail="Daemon not initialized")
    
    return daemon.get_all_results()


@app.get("/api/checks/{check_name}", response_model=CheckResult)
async def get_check_result(check_name: str):
    """Get result of a specific check."""
    if not daemon:
        raise HTTPException(status_code=503, detail="Daemon not initialized")
    
    results = daemon.get_all_results()
    if check_name not in results:
        raise HTTPException(status_code=404, detail=f"Check '{check_name}' not found")
    
    return results[check_name]


@app.post("/api/checks/{check_name}/run", response_model=CheckExecutionResponse)
async def run_check(check_name: str, background_tasks: BackgroundTasks):
    """Run a specific check manually using CLI functions."""
    if not daemon:
        raise HTTPException(status_code=503, detail="Daemon not initialized")
    
    # Map check names to CLI functions
    cli_function_map = {
        "doc_check": check_docs,
        "test_check": check_tests,
        "git_check": lambda: git_changes()
    }
    
    if check_name not in cli_function_map:
        raise HTTPException(status_code=400, detail=f"Unknown check: {check_name}")
    
    try:
        def run_check_task():
            """Background task to run the CLI function."""
            cli_function = cli_function_map[check_name]
            exit_code = cli_function()
            return exit_code
        
        background_tasks.add_task(run_check_task)
        
        return CheckExecutionResponse(
            success=True,
            result=None,
            error=None
        )
    except Exception as e:
        return handle_cli_error(check_name, e)


@app.get("/api/config", response_model=AutocodeConfig)
async def get_config():
    """Get current configuration."""
    if not daemon:
        raise HTTPException(status_code=503, detail="Daemon not initialized")
    
    return daemon.config


@app.get("/api/tokens/count")
async def count_tokens(file_path: str = "git_changes.json"):
    """Count tokens in a file.
    
    Args:
        file_path: Path to the file (relative to project root)
        
    Returns:
        Token statistics for the file
    """
    if not daemon:
        raise HTTPException(status_code=503, detail="Daemon not initialized")
    
    try:
        from ..core.token_counter import TokenCounter
        
        # Use token configuration from daemon
        token_counter = TokenCounter(daemon.config.daemon.token_alerts.model)
        
        # Resolve file path relative to project root
        file_path_obj = daemon.project_root / file_path
        
        if not file_path_obj.exists():
            raise HTTPException(status_code=404, detail=f"File not found: {file_path}")
        
        # Get token statistics
        token_stats = token_counter.get_token_statistics(file_path_obj)
        
        # Add threshold check
        threshold_check = token_counter.check_threshold(
            token_stats["token_count"], 
            daemon.config.daemon.token_alerts.threshold
        )
        
        # Combine results
        result = {
            **token_stats,
            "threshold_check": threshold_check,
            "config": {
                "threshold": daemon.config.daemon.token_alerts.threshold,
                "model": daemon.config.daemon.token_alerts.model,
                "alerts_enabled": daemon.config.daemon.token_alerts.enabled
            }
        }
        
        return result
        
    except ImportError:
        raise HTTPException(status_code=500, detail="Token counting not available (tiktoken not installed)")
    except Exception as e:
        logger.error(f"Error counting tokens: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/tokens/count-multiple")
async def count_tokens_multiple(file_paths: List[str]):
    """Count tokens in multiple files.
    
    Args:
        file_paths: List of file paths (relative to project root)
        
    Returns:
        Aggregated token statistics
    """
    if not daemon:
        raise HTTPException(status_code=503, detail="Daemon not initialized")
    
    try:
        from ..core.token_counter import count_tokens_in_multiple_files
        
        # Resolve file paths
        resolved_paths = []
        for file_path in file_paths:
            file_path_obj = daemon.project_root / file_path
            if file_path_obj.exists():
                resolved_paths.append(file_path_obj)
        
        if not resolved_paths:
            raise HTTPException(status_code=404, detail="No valid files found")
        
        # Count tokens
        result = count_tokens_in_multiple_files(
            resolved_paths, 
            daemon.config.daemon.token_alerts.model
        )
        
        # Add threshold check for total
        from ..core.token_counter import TokenCounter
        token_counter = TokenCounter(daemon.config.daemon.token_alerts.model)
        threshold_check = token_counter.check_threshold(
            result["total_tokens"],
            daemon.config.daemon.token_alerts.threshold
        )
        
        result["threshold_check"] = threshold_check
        result["config"] = {
            "threshold": daemon.config.daemon.token_alerts.threshold,
            "model": daemon.config.daemon.token_alerts.model,
            "alerts_enabled": daemon.config.daemon.token_alerts.enabled
        }
        
        return result
        
    except ImportError:
        raise HTTPException(status_code=500, detail="Token counting not available (tiktoken not installed)")
    except Exception as e:
        logger.error(f"Error counting tokens: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.put("/api/config")
async def update_config(config: AutocodeConfig):
    """Update configuration."""
    if not daemon:
        raise HTTPException(status_code=503, detail="Daemon not initialized")
    
    try:
        daemon.update_config(config)
        return {"message": "Configuration updated successfully"}
    except Exception as e:
        logger.error(f"Error updating configuration: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/scheduler/tasks")
async def get_scheduler_tasks():
    """Get scheduler tasks status."""
    if not daemon:
        raise HTTPException(status_code=503, detail="Daemon not initialized")
    
    return daemon.scheduler.get_all_tasks_status()


@app.get("/api/scheduler/tasks/{task_name}")
async def get_scheduler_task(task_name: str):
    """Get specific scheduler task status."""
    if not daemon:
        raise HTTPException(status_code=503, detail="Daemon not initialized")
    
    task_status = daemon.scheduler.get_task_status(task_name)
    if not task_status:
        raise HTTPException(status_code=404, detail=f"Task '{task_name}' not found")
    
    return task_status


@app.get("/api/architecture/diagram")
async def get_architecture_diagram():
    """Get the architecture diagram content from design/_index.md."""
    if not daemon:
        raise HTTPException(status_code=503, detail="Daemon not initialized")
    
    try:
        # Read the design index file
        design_index_path = daemon.project_root / "design" / "_index.md"
        
        if not design_index_path.exists():
            raise HTTPException(status_code=404, detail="Architecture diagram not found. Run 'autocode code-to-design' first.")
        
        with open(design_index_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Extract the Mermaid diagram from the markdown
        import re
        mermaid_match = re.search(r'```mermaid\n(.*?)\n```', content, re.DOTALL)
        
        if not mermaid_match:
            raise HTTPException(status_code=404, detail="No Mermaid diagram found in design/_index.md")
        
        mermaid_content = mermaid_match.group(1)
        
        # Extract project summary
        summary_match = re.search(r'\*\*Project Summary:\*\* (.+)', content)
        project_summary = summary_match.group(1) if summary_match else "Unknown"
        
        return {
            "mermaid_content": mermaid_content,
            "project_summary": project_summary,
            "last_updated": design_index_path.stat().st_mtime
        }
        
    except Exception as e:
        logger.error(f"Error reading architecture diagram: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/architecture/regenerate")
async def regenerate_architecture_diagram(background_tasks: BackgroundTasks):
    """Regenerate the architecture diagram using CLI function."""
    if not daemon:
        raise HTTPException(status_code=503, detail="Daemon not initialized")
    
    try:
        def regenerate_task():
            """Background task to regenerate the diagram using CLI."""
            # Use CLI function for design generation
            exit_code = code_to_design(directory="autocode")
            logger.info(f"Architecture diagram regenerated with exit code: {exit_code}")
            return exit_code
        
        background_tasks.add_task(regenerate_task)
        
        return {"message": "Architecture diagram regeneration started"}
        
    except Exception as e:
        logger.error(f"Error regenerating architecture diagram: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/scheduler/tasks/{task_name}/enable")
async def enable_scheduler_task(task_name: str):
    """Enable a scheduler task."""
    if not daemon:
        raise HTTPException(status_code=503, detail="Daemon not initialized")
    
    try:
        daemon.scheduler.enable_task(task_name)
        return {"message": f"Task '{task_name}' enabled"}
    except Exception as e:
        logger.error(f"Error enabling task {task_name}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/scheduler/tasks/{task_name}/disable")
async def disable_scheduler_task(task_name: str):
    """Disable a scheduler task."""
    if not daemon:
        raise HTTPException(status_code=503, detail="Daemon not initialized")
    
    try:
        daemon.scheduler.disable_task(task_name)
        return {"message": f"Task '{task_name}' disabled"}
    except Exception as e:
        logger.error(f"Error disabling task {task_name}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/design/files")
async def get_design_files():
    """Get list of all .md files in the design directory."""
    if not daemon:
        raise HTTPException(status_code=503, detail="Daemon not initialized")
    
    try:
        design_path = daemon.project_root / "design"
        
        if not design_path.exists():
            raise HTTPException(status_code=404, detail="Design directory not found")
        
        # Recursively find all .md files
        md_files = []
        for md_file in design_path.rglob("*.md"):
            # Get relative path from design directory
            relative_path = md_file.relative_to(design_path)
            md_files.append(str(relative_path).replace("\\", "/"))
        
        # Sort files for consistent ordering
        md_files.sort()
        
        return {
            "status": "success",
            "files": md_files,
            "total_files": len(md_files)
        }
        
    except Exception as e:
        logger.error(f"Error listing design files: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/ui-designer/component-tree")
async def get_component_tree(directory: str = "autocode/web"):
    """Generate component tree diagram for UI components."""
    if not daemon:
        raise HTTPException(status_code=503, detail="Daemon not initialized")
    
    try:
        from ..core.design.code_to_design import CodeToDesign
        
        # Initialize CodeToDesign
        code_to_design = CodeToDesign(daemon.project_root)
        
        # Generate component tree
        result = code_to_design.generate_component_tree(directory)
        
        if result["status"] == "error":
            raise HTTPException(status_code=500, detail=result["error"])
        
        return result
        
    except Exception as e:
        logger.error(f"Error generating component tree: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/ui-designer/component-tree/regenerate")
async def regenerate_component_tree(background_tasks: BackgroundTasks, directory: str = "autocode/web"):
    """Regenerate component tree diagram in the background."""
    if not daemon:
        raise HTTPException(status_code=503, detail="Daemon not initialized")
    
    try:
        def regenerate_task():
            """Background task to regenerate the component tree."""
            from ..core.design.code_to_design import CodeToDesign
            
            # Initialize CodeToDesign
            code_to_design = CodeToDesign(daemon.project_root)
            
            # Generate component tree
            result = code_to_design.generate_component_tree(directory)
            
            logger.info(f"Component tree regenerated: {result}")
        
        background_tasks.add_task(regenerate_task)
        
        return {"message": "Component tree regeneration started"}
        
    except Exception as e:
        logger.error(f"Error regenerating component tree: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# New CLI Wrapper Endpoints

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
    return {
        "status": "healthy",
        "daemon_running": daemon.is_running() if daemon else False
    }


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    return app


if __name__ == "__main__":
    import uvicorn
    
    # Run the application
    uvicorn.run(
        "autocode.api:app",
        host="127.0.0.1",
        port=8080,
        reload=True,
        log_level="info"
    )
