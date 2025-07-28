# Task 008: Migración de la API a una Capa Delgada sobre el CLI (Eliminación de Endpoints Legacy)

## Contexto del Proyecto
Este proyecto, autocode, es una herramienta para automatizar tareas de calidad de código, documentación, tests y análisis Git. Incluye un daemon con interfaz web que expone una API RESTful para interactuar con las funcionalidades desde el navegador. El objetivo es simplificar esta API convirtiéndola en una "thin layer" (capa delgada) que solo invoque comandos CLI existentes.

## Estado Actual de la API
La API actual está en `autocode/api/server.py` y utiliza FastAPI con una mezcla de endpoints legacy (que implementan lógica compleja) y wrappers CLI (que invocan comandos del CLI directamente).

### Estructura Actual del Servidor
```python
# Imports actuales
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

# Global daemon instance
daemon: AutocodeDaemon = None
daemon_task: asyncio.Task = None

app = FastAPI(
    title="Autocode Monitoring API",
    description="API for autocode daemon monitoring and management",
    version="1.0.0"
)
```

### Endpoints Legacy a Eliminar
Estos endpoints implementan lógica compleja y dependen del AutocodeDaemon:

```python
# 1. Endpoints de status del daemon
@app.get("/api/status", response_model=StatusResponse)
async def get_status():
    if not daemon:
        raise HTTPException(status_code=503, detail="Daemon not initialized")
    daemon_status = daemon.get_daemon_status()
    check_results = daemon.get_all_results()
    return StatusResponse(daemon=daemon_status, checks=check_results, config=daemon.config)

@app.get("/api/daemon/status", response_model=DaemonStatus)
async def get_daemon_status():
    if not daemon:
        raise HTTPException(status_code=503, detail="Daemon not initialized")
    return daemon.get_daemon_status()

# 2. Endpoints de checks individuales
@app.get("/api/checks", response_model=Dict[str, CheckResult])
async def get_all_checks():
    if not daemon:
        raise HTTPException(status_code=503, detail="Daemon not initialized")
    return daemon.get_all_results()

@app.get("/api/checks/{check_name}", response_model=CheckResult)
async def get_check_result(check_name: str):
    if not daemon:
        raise HTTPException(status_code=503, detail="Daemon not initialized")
    results = daemon.get_all_results()
    if check_name not in results:
        raise HTTPException(status_code=404, detail=f"Check '{check_name}' not found")
    return results[check_name]

@app.post("/api/checks/{check_name}/run", response_model=CheckExecutionResponse)
async def run_check(check_name: str, background_tasks: BackgroundTasks):
    # Mapeo a funciones CLI pero con lógica compleja
    cli_function_map = {
        "doc_check": check_docs,
        "test_check": check_tests,
        "git_check": lambda: git_changes()
    }
    # ... lógica compleja para ejecutar y manejar resultados

# 3. Configuración legacy
@app.get("/api/config", response_model=AutocodeConfig)
async def get_config():
    if not daemon:
        raise HTTPException(status_code=503, detail="Daemon not initialized")
    return daemon.config

@app.put("/api/config")
async def update_config(config: AutocodeConfig):
    if not daemon:
        raise HTTPException(status_code=503, detail="Daemon not initialized")
    try:
        daemon.update_config(config)
        return {"message": "Configuration updated successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# 4. Tokens legacy
@app.get("/api/tokens/count")
async def count_tokens(file_path: str = "git_changes.json"):
    # Lógica compleja con TokenCounter
    if not daemon:
        raise HTTPException(status_code=503, detail="Daemon not initialized")
    # ... implementación compleja

# 5. Scheduler legacy
@app.get("/api/scheduler/tasks")
async def get_scheduler_tasks():
    if not daemon:
        raise HTTPException(status_code=503, detail="Daemon not initialized")
    return daemon.scheduler.get_all_tasks_status()

# 6. Architecture/Design legacy
@app.get("/api/architecture/diagram")
async def get_architecture_diagram():
    # Lógica compleja para leer archivos de diseño
    if not daemon:
        raise HTTPException(status_code=503, detail="Daemon not initialized")
    # ... implementación compleja

# 7. UI Designer legacy
@app.get("/api/ui-designer/component-tree")
async def get_component_tree(directory: str = "autocode/web"):
    # Lógica compleja con CodeToDesign
    if not daemon:
        raise HTTPException(status_code=503, detail="Daemon not initialized")
    # ... implementación compleja
```

### Wrappers CLI Existentes (Mantener)
Estos endpoints ya siguen el patrón deseado:

```python
@app.post("/api/generate-docs", response_model=CheckExecutionResponse)
async def generate_docs(background_tasks: BackgroundTasks):
    """Generate/check documentation using CLI function."""
    try:
        def run_docs_task():
            return check_docs()
        
        background_tasks.add_task(run_docs_task)
        return CheckExecutionResponse(success=True, result=None, error=None)
    except Exception as e:
        return handle_cli_error("check_docs", e)

@app.post("/api/generate-design", response_model=CheckExecutionResponse)
async def generate_design(directory: str = None, output_dir: str = None, 
                         background_tasks: BackgroundTasks = None):
    """Generate design diagrams using CLI function."""
    try:
        def run_design_task():
            return code_to_design(directory=directory, output_dir=output_dir)
        
        background_tasks.add_task(run_design_task)
        return CheckExecutionResponse(success=True, result=None, error=None)
    except Exception as e:
        return handle_cli_error("code_to_design", e)

@app.post("/api/analyze-git", response_model=CheckExecutionResponse)
async def analyze_git(output: str = None, verbose: bool = False,
                     background_tasks: BackgroundTasks = None):
    """Analyze git changes using CLI function."""
    try:
        def run_git_task():
            return git_changes(output=output, verbose=verbose)
        
        background_tasks.add_task(run_git_task)
        return CheckExecutionResponse(success=True, result=None, error=None)
    except Exception as e:
        return handle_cli_error("git_changes", e)

@app.get("/api/config/load", response_model=Dict[str, Any])
async def load_configuration():
    """Load configuration using CLI function."""
    try:
        config = load_config()
        return {"success": True, "config": config.dict(), "error": None}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

### Función de Manejo de Errores Existente
```python
def handle_cli_error(func_name: str, error: Exception) -> CheckExecutionResponse:
    """Standard error handling for CLI function calls."""
    logger.error(f"Error in CLI function '{func_name}': {error}")
    return CheckExecutionResponse(
        success=False,
        result=None,
        error=f"CLI function '{func_name}' failed: {str(error)}"
    )
```

### Endpoints a Conservar
```python
# Rutas de páginas (serving HTML templates)
@app.get("/", response_class=HTMLResponse)
@app.get("/dashboard", response_class=HTMLResponse) 
@app.get("/design", response_class=HTMLResponse)
@app.get("/config", response_class=HTMLResponse)

# Montajes de archivos estáticos
app.mount("/static", StaticFiles(directory=Path(__file__).parent.parent / "web" / "static"), name="static")
app.mount("/design", StaticFiles(directory=Path(__file__).parent.parent.parent / "design"), name="design")

# Health check
@app.get("/health")
async def health_check():
    return {"status": "healthy", "daemon_running": False}  # Simplificado
```

## Objetivo de la Migración
Simplificar drásticamente el servidor API eliminando toda la lógica compleja y dependencias del AutocodeDaemon, manteniendo solo:
1. **Rutas de páginas**: Para servir las templates HTML
2. **Archivos estáticos**: Montaje de /static y /design
3. **Wrappers CLI**: Endpoints que invocan comandos CLI directamente
4. **Health check**: Endpoint simple de salud

## Instrucciones Paso a Paso

### 1. Backup del Archivo Original
```bash
cp autocode/api/server.py autocode/api/server.py.backup
```

### 2. Eliminar Imports Innecesarios
Remover imports relacionados con AutocodeDaemon:

```python
# ELIMINAR estas líneas:
from ..orchestration.daemon import AutocodeDaemon
from .models import (
    StatusResponse,           # Solo si no se usa en otros endpoints
    CheckExecutionRequest,    # Solo si no se usa
    CheckResult,             # Solo si no se usa  
    DaemonStatus            # Solo si no se usa
)

# MANTENER estos imports esenciales:
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from fastapi import Request
from .models import CheckExecutionResponse, AutocodeConfig  # Solo los necesarios
from ..cli import check_docs, check_tests, git_changes, code_to_design, load_config
```

### 3. Eliminar Variables Globales del Daemon
```python
# ELIMINAR estas líneas:
# Global daemon instance
daemon: AutocodeDaemon = None
daemon_task: asyncio.Task = None
```

### 4. Simplificar Eventos de Startup/Shutdown
```python
# ELIMINAR completamente:
@app.on_event("startup")
async def startup_event():
    # Todo el código de inicialización del daemon

@app.on_event("shutdown")  
async def shutdown_event():
    # Todo el código de limpieza del daemon
```

### 5. Eliminar Endpoints Legacy Específicos
Remover completamente estos endpoints (funciones completas):

```python
# ELIMINAR COMPLETAMENTE estas funciones:
get_status()
get_daemon_status()
get_all_checks()
get_check_result(check_name: str)
run_check(check_name: str, background_tasks: BackgroundTasks)  # El legacy, no los wrappers
get_config()  # El que depende del daemon
update_config(config: AutocodeConfig)  # El que depende del daemon
count_tokens(file_path: str)
count_tokens_multiple(file_paths: List[str])
get_scheduler_tasks()
get_scheduler_task(task_name: str)
get_architecture_diagram()
regenerate_architecture_diagram(background_tasks: BackgroundTasks)
enable_scheduler_task(task_name: str)
disable_scheduler_task(task_name: str)
get_design_files()
get_component_tree(directory: str)
regenerate_component_tree(background_tasks: BackgroundTasks, directory: str)
check_docs_sync()  # Si existe
```

### 6. Simplificar Health Check
```python
@app.get("/health")
async def health_check():
    """Simple health check."""
    return {"status": "healthy"}
```

### 7. Conservar Wrappers CLI Existentes
Mantener exactamente como están:
- `/api/generate-docs`
- `/api/generate-design` 
- `/api/analyze-git`
- `/api/config/load`

### 8. Conservar Rutas de Páginas
Mantener exactamente como están:
- `/` (redirect a dashboard)
- `/dashboard`
- `/design`
- `/config`
- `/index` (backward compatibility)

### 9. Actualizar create_app() si Existe
```python
def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    return app
```

### 10. Limpiar el Main Block
```python
if __name__ == "__main__":
    import uvicorn
    
    # Run the application
    uvicorn.run(
        "autocode.api.server:app",  # Mantener referencia correcta
        host="127.0.0.1",
        port=8080,
        reload=True,
        log_level="info"
    )
```

## Criterios de Verificación

### Servidor Debe Arrancar
```bash
cd /path/to/autocode
uv run autocode daemon
# Debe arrancar sin errores y mostrar:
# 🚀 Starting Autocode Monitoring Daemon
# 🌐 Web Interface: http://127.0.0.1:8080
```

### Endpoints Eliminados Deben Devolver 404
```bash
# Estos deben devolver 404 Not Found:
curl http://127.0.0.1:8080/api/status
curl http://127.0.0.1:8080/api/daemon/status  
curl http://127.0.0.1:8080/api/checks
curl http://127.0.0.1:8080/api/checks/doc_check
curl -X POST http://127.0.0.1:8080/api/checks/doc_check/run
curl http://127.0.0.1:8080/api/config
curl -X PUT http://127.0.0.1:8080/api/config -H "Content-Type: application/json" -d '{}'
curl http://127.0.0.1:8080/api/tokens/count
curl http://127.0.0.1:8080/api/scheduler/tasks
curl http://127.0.0.1:8080/api/architecture/diagram
curl http://127.0.0.1:8080/api/ui-designer/component-tree
```

### Wrappers CLI Deben Funcionar
```bash
# Estos deben devolver 200 OK con respuesta JSON:
curl -X POST http://127.0.0.1:8080/api/generate-docs
curl -X POST http://127.0.0.1:8080/api/generate-design
curl -X POST http://127.0.0.1:8080/api/analyze-git
curl http://127.0.0.1:8080/api/config/load
```

### Páginas Web Deben Cargar
```bash
# Estos deben devolver 200 OK con HTML:
curl http://127.0.0.1:8080/
curl http://127.0.0.1:8080/dashboard
curl http://127.0.0.1:8080/design
curl http://127.0.0.1:8080/config
```

### Health Check Debe Funcionar
```bash
curl http://127.0.0.1:8080/health
# Debe devolver: {"status": "healthy"}
```

### Archivos Estáticos Deben Servirse
```bash
# Estos deben devolver 200 OK:
curl http://127.0.0.1:8080/static/app.js
curl http://127.0.0.1:8080/design/_index.md  # Si existe
```

### Verificación de Logs
Al ejecutar `uv run autocode daemon`, los logs NO deben mostrar:
- Errores de import
- Referencias a AutocodeDaemon
- Errores de inicialización de scheduler
- Warnings sobre funciones eliminadas

### Comparación del Tamaño del Archivo
```bash
# Antes de los cambios:
wc -l autocode/api/server.py.backup

# Después de los cambios:  
wc -l autocode/api/server.py

# El archivo debería ser significativamente más pequeño (estimado: reducción de ~60-70%)
```

## Template de Commit Message
```
refactor(api): migrate to thin CLI layer, remove legacy endpoints

- Removed daemon-dependent endpoints: /api/status, /api/checks, /api/config, etc.
- Eliminated AutocodeDaemon imports and global variables  
- Removed startup/shutdown event handlers for daemon
- Kept CLI wrapper endpoints: /api/generate-docs, /api/generate-design, etc.
- Preserved page routes and static file serving
- Simplified health check endpoint
- Reduced server.py complexity by ~70% for easier maintenance

Breaking changes:
- Legacy API endpoints now return 404
- All functionality now routed through CLI wrappers
