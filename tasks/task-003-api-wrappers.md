# Task 003: Refactorizar API como Thin Wrappers sobre Funciones CLI

## Contexto del Proyecto
Este proyecto autocode tiene una API FastAPI existente que maneja el monitoreo y control del daemon. El objetivo es refactorizar esta API para que actúe como un "thin wrapper" sobre las funciones CLI en lugar de duplicar lógica, facilitando el mantenimiento y la consistencia.

## Estado Actual de la API

### Estructura Actual Completa
El archivo `autocode/api/server.py` contiene:

```python
"""FastAPI application for autocode daemon."""
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
    StatusResponse, CheckExecutionRequest, CheckExecutionResponse,
    AutocodeConfig, CheckResult, DaemonStatus
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
app.mount("/design", StaticFiles(directory=Path(__file__).parent.parent.parent / "design"), name="design")

@app.on_event("startup")
async def startup_event():
    """Initialize daemon on startup."""
    global daemon, daemon_task
    logger.info("Starting autocode daemon")
    daemon = AutocodeDaemon()
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

# Web Routes
@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    """Redirect to dashboard."""
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/dashboard", status_code=302)

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request):
    """Serve the dashboard page."""
    return templates.TemplateResponse("pages/dashboard.html", {"request": request})

# API Routes
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

@app.get("/api/checks", response_model=Dict[str, CheckResult])
async def get_all_checks():
    """Get results of all checks."""
    if not daemon:
        raise HTTPException(status_code=503, detail="Daemon not initialized")
    
    return daemon.get_all_results()

@app.post("/api/checks/{check_name}/run", response_model=CheckExecutionResponse)
async def run_check(check_name: str, background_tasks: BackgroundTasks):
    """Run a specific check manually."""
    if not daemon:
        raise HTTPException(status_code=503, detail="Daemon not initialized")
    
    if check_name not in ["doc_check", "git_check", "test_check"]:
        raise HTTPException(status_code=400, detail=f"Unknown check: {check_name}")
    
    try:
        def run_check_task():
            daemon.run_check_manually(check_name)
        
        background_tasks.add_task(run_check_task)
        
        return CheckExecutionResponse(
            success=True,
            result=None,
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
```

### Estructura de Modelos Actuales
```python
# autocode/api/models.py contiene modelos como:
class StatusResponse(BaseModel):
    daemon: DaemonStatus
    checks: Dict[str, CheckResult]
    config: AutocodeConfig

class CheckExecutionResponse(BaseModel):
    success: bool
    result: Optional[Any]
    error: Optional[str]

class DaemonStatus(BaseModel):
    running: bool
    uptime: float
    last_check: Optional[datetime]
```

### Funciones CLI Disponibles (Post-Typer)
Después de la refactorización con Typer, las funciones CLI estarán disponibles como:

```python
# autocode/cli.py
@app.command("check-docs")
def check_docs(doc_index_output: Optional[str] = None) -> int:
    """Check if documentation is up to date"""
    # Lógica completa aquí
    return 0 or 1

@app.command("check-tests") 
def check_tests() -> int:
    """Check if tests exist and are passing"""
    # Lógica completa aquí
    return 0 or 1

@app.command("git-changes")
def git_changes(output: Optional[str] = None, verbose: bool = False) -> int:
    """Analyze git changes for commit message generation"""
    # Lógica completa aquí
    return 0 or 1

@app.command("code-to-design")
def code_to_design(
    directory: Optional[str] = None,
    pattern: str = "*.py",
    output_dir: Optional[str] = None,
    languages: Optional[List[str]] = None,
    diagrams: Optional[List[str]] = None,
    show_config: bool = False,
    directories: Optional[List[str]] = None
) -> int:
    """Generate design diagrams from code"""
    # Lógica completa aquí
    return 0 or 1
```

## Objetivo de la Refactorización
Convertir la API actual en un "thin wrapper" que:
1. **Elimina duplicación de lógica**: La API solo orquesta llamadas a CLI
2. **Mantiene consistencia**: Misma lógica en CLI y API
3. **Facilita mantenimiento**: Un solo lugar para cambios de lógica
4. **Preserva funcionalidad existente**: Sin romper endpoints actuales

## Instrucciones Paso a Paso

### 1. Importar Funciones CLI
```python
# Al inicio de autocode/api/server.py, añadir:
from ..cli import check_docs, check_tests, git_changes, code_to_design, load_config
```

### 2. Crear Nuevos Endpoints Wrapper
Añadir endpoints que mapeen directamente a funciones CLI:

```python
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
            result="Documentation check started",
            error=None
        )
    except Exception as e:
        logger.error(f"Error running docs check: {e}")
        return CheckExecutionResponse(
            success=False,
            result=None,
            error=str(e)
        )

@app.post("/api/generate-design", response_model=CheckExecutionResponse)
async def generate_design(
    directory: Optional[str] = None,
    output_dir: Optional[str] = None,
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
            result="Design generation started",
            error=None
        )
    except Exception as e:
        logger.error(f"Error running design generation: {e}")
        return CheckExecutionResponse(
            success=False,
            result=None,
            error=str(e)
        )

@app.post("/api/analyze-git", response_model=CheckExecutionResponse)
async def analyze_git(
    output: Optional[str] = None,
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
            result="Git analysis started",
            error=None
        )
    except Exception as e:
        logger.error(f"Error running git analysis: {e}")
        return CheckExecutionResponse(
            success=False,
            result=None,
            error=str(e)
        )
```

### 3. Refactorizar Endpoints Existentes
Modificar endpoints existentes para usar funciones CLI cuando sea posible:

```python
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
            result=f"Check '{check_name}' started",
            error=None
        )
    except Exception as e:
        logger.error(f"Error running check {check_name}: {e}")
        return CheckExecutionResponse(
            success=False,
            result=None,
            error=str(e)
        )
```

### 4. Añadir Endpoints Síncronos para Casos Simples
Para operaciones rápidas, proporcionar endpoints síncronos:

```python
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
```

### 5. Mantener Endpoints del Daemon Existentes
Preservar endpoints que dependen específicamente del daemon:

```python
# Mantener estos endpoints sin cambios ya que requieren el daemon
@app.get("/api/status", response_model=StatusResponse)
async def get_status():
    """Get current status of daemon and all checks."""
    # Mantener lógica actual del daemon
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
    # Mantener lógica actual
    if not daemon:
        raise HTTPException(status_code=503, detail="Daemon not initialized")
    
    return daemon.get_daemon_status()
```

### 6. Actualizar Manejo de Errores
Estandarizar el manejo de errores para los wrappers:

```python
def handle_cli_error(func_name: str, error: Exception) -> CheckExecutionResponse:
    """Standard error handling for CLI function calls."""
    logger.error(f"Error in CLI function '{func_name}': {error}")
    return CheckExecutionResponse(
        success=False,
        result=None,
        error=f"CLI function '{func_name}' failed: {str(error)}"
    )

# Usar en los endpoints:
except Exception as e:
    return handle_cli_error("check_docs", e)
```

## Criterios de Verificación

### Verificación Manual con cURL
```bash
# Iniciar el daemon
uv run autocode daemon

# Probar nuevos endpoints
curl -X POST http://localhost:8080/api/generate-docs
curl -X POST http://localhost:8080/api/generate-design
curl -X POST http://localhost:8080/api/analyze-git

# Probar endpoints síncronos
curl http://localhost:8080/api/config/load
curl -X POST http://localhost:8080/api/docs/check-sync

# Verificar endpoints existentes siguen funcionando
curl http://localhost:8080/api/status
curl http://localhost:8080/api/checks
```

### Verificaciones de Código
1. **Thin Layer Verification**: Cada nuevo endpoint debe tener máximo 10-15 líneas de lógica
2. **No Duplicación**: La lógica real está solo en las funciones CLI
3. **Error Handling**: Todos los endpoints manejan errores consistentemente
4. **Background Tasks**: Operaciones largas usan BackgroundTasks
5. **Imports Correctos**: Las funciones CLI se importan correctamente

### Testing con Diferentes Escenarios
```bash
# Test successful operations
curl -X POST http://localhost:8080/api/generate-docs
# Should return: {"success": true, "result": "Documentation check started", "error": null}

# Test with parameters
curl -X POST "http://localhost:8080/api/generate-design?directory=autocode&output_dir=design"

# Test error handling
curl -X POST http://localhost:8080/api/checks/invalid_check/run
# Should return error response

# Test daemon dependency
curl http://localhost:8080/api/status
# Should work if daemon is running, error if not
```

### Verificación de No-Regresión
Comparar responses antes y después de la refactorización:

1. **Endpoints del daemon**: `/api/status`, `/api/daemon/status` deben retornar exactamente lo mismo
2. **Endpoints de checks**: `/api/checks` debe mantener funcionalidad
3. **Web routes**: Dashboard y páginas web deben seguir funcionando
4. **Static files**: Servir archivos estáticos debe continuar

## Template de Commit Message
```
feat(api): refactor API as thin wrappers over CLI functions

- Imported CLI functions (check_docs, check_tests, git_changes, code_to_design)
- Added new wrapper endpoints: /api/generate-docs, /api/generate-design, /api/analyze-git
- Refactored /api/checks/{check_name}/run to use CLI functions
- Added synchronous endpoints for quick operations
- Maintained existing daemon-dependent endpoints unchanged
- Implemented consistent error handling across all wrapper endpoints
- Used BackgroundTasks for long-running operations
- Preserved all existing functionality while eliminating logic duplication
```
