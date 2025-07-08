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

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


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
async def dashboard(request: Request):
    """Serve the main dashboard."""
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
    """Run a specific check manually."""
    if not daemon:
        raise HTTPException(status_code=503, detail="Daemon not initialized")
    
    if check_name not in ["doc_check", "git_check", "test_check"]:
        raise HTTPException(status_code=400, detail=f"Unknown check: {check_name}")
    
    try:
        # Run check in background
        def run_check_task():
            daemon.run_check_manually(check_name)
        
        background_tasks.add_task(run_check_task)
        
        return CheckExecutionResponse(
            success=True,
            result=None,  # Will be available after background task completes
            error=None
        )
    
    except Exception as e:
        logger.error(f"Error running check {check_name}: {e}")
        return CheckExecutionResponse(
            success=False,
            result=None,
            error=str(e)
        )


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
