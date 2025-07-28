# Task 004: Crear Tests Completos para API Endpoints

## Contexto del Proyecto
Este proyecto autocode tiene una API FastAPI que sirve como thin wrapper sobre funciones CLI. El objetivo es crear tests completos que validen todos los endpoints, especialmente verificando que la API orquesta correctamente las llamadas a CLI sin duplicar lógica.

## Estado Actual de la API

### Estructura Completa de la API
El archivo `autocode/api/server.py` contiene estos endpoints principales:

```python
"""FastAPI application for autocode daemon."""
import asyncio
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from fastapi import Request

from ..orchestration.daemon import AutocodeDaemon
from ..cli import check_docs, check_tests, git_changes, code_to_design, load_config
from .models import (
    StatusResponse, CheckExecutionRequest, CheckExecutionResponse,
    AutocodeConfig, CheckResult, DaemonStatus
)

app = FastAPI(
    title="Autocode Monitoring API",
    description="API for autocode daemon monitoring and management",
    version="1.0.0"
)

# Global daemon instance
daemon: AutocodeDaemon = None

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

# API Routes - Daemon dependent
@app.get("/api/status", response_model=StatusResponse)
async def get_status():
    """Get current status of daemon and all checks."""
    if not daemon:
        raise HTTPException(status_code=503, detail="Daemon not initialized")
    
    daemon_status = daemon.get_daemon_status()
    check_results = daemon.get_all_results()
    return StatusResponse(daemon=daemon_status, checks=check_results, config=daemon.config)

@app.get("/api/daemon/status", response_model=DaemonStatus)
async def get_daemon_status():
    """Get daemon status."""
    if not daemon:
        raise HTTPException(status_code=503, detail="Daemon not initialized")
    return daemon.get_daemon_status()

# API Routes - CLI Wrappers (nuevos)
@app.post("/api/generate-docs", response_model=CheckExecutionResponse)
async def generate_docs(background_tasks: BackgroundTasks):
    """Generate/check documentation using CLI function."""
    try:
        def run_docs_task():
            return check_docs()
        
        background_tasks.add_task(run_docs_task)
        return CheckExecutionResponse(success=True, result="Documentation check started", error=None)
    except Exception as e:
        logger.error(f"Error running docs check: {e}")
        return CheckExecutionResponse(success=False, result=None, error=str(e))

@app.post("/api/generate-design", response_model=CheckExecutionResponse)
async def generate_design(
    directory: Optional[str] = None,
    output_dir: Optional[str] = None,
    background_tasks: BackgroundTasks = None
):
    """Generate design diagrams using CLI function."""
    try:
        def run_design_task():
            return code_to_design(directory=directory, output_dir=output_dir)
        
        background_tasks.add_task(run_design_task)
        return CheckExecutionResponse(success=True, result="Design generation started", error=None)
    except Exception as e:
        logger.error(f"Error running design generation: {e}")
        return CheckExecutionResponse(success=False, result=None, error=str(e))

@app.post("/api/checks/{check_name}/run", response_model=CheckExecutionResponse)
async def run_check(check_name: str, background_tasks: BackgroundTasks):
    """Run a specific check manually using CLI functions."""
    if not daemon:
        raise HTTPException(status_code=503, detail="Daemon not initialized")
    
    cli_function_map = {
        "doc_check": check_docs,
        "test_check": check_tests,
        "git_check": lambda: git_changes()
    }
    
    if check_name not in cli_function_map:
        raise HTTPException(status_code=400, detail=f"Unknown check: {check_name}")
    
    try:
        def run_check_task():
            cli_function = cli_function_map[check_name]
            return cli_function()
        
        background_tasks.add_task(run_check_task)
        return CheckExecutionResponse(success=True, result=f"Check '{check_name}' started", error=None)
    except Exception as e:
        logger.error(f"Error running check {check_name}: {e}")
        return CheckExecutionResponse(success=False, result=None, error=str(e))

@app.get("/api/config/load", response_model=Dict[str, Any])
async def load_configuration():
    """Load configuration using CLI function."""
    try:
        config = load_config()
        return {"success": True, "config": config.dict(), "error": None}
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

### Modelos de la API
```python
# autocode/api/models.py
from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime

class CheckExecutionResponse(BaseModel):
    success: bool
    result: Optional[Any]
    error: Optional[str]

class StatusResponse(BaseModel):
    daemon: DaemonStatus
    checks: Dict[str, CheckResult]
    config: AutocodeConfig

class DaemonStatus(BaseModel):
    running: bool
    uptime: float
    last_check: Optional[datetime]

class CheckResult(BaseModel):
    status: str
    last_run: Optional[datetime]
    error: Optional[str]
```

### Funciones CLI que se Testearán
```python
# autocode/cli.py - Funciones que la API llama
def check_docs(doc_index_output: Optional[str] = None) -> int:
    """Check if documentation is up to date"""
    # Retorna 0 para éxito, 1 para issues
    
def check_tests() -> int:
    """Check if tests exist and are passing"""
    # Retorna 0 para éxito, 1 para issues

def git_changes(output: Optional[str] = None, verbose: bool = False) -> int:
    """Analyze git changes for commit message generation"""
    # Retorna 0 para éxito, 1 para error

def code_to_design(directory: Optional[str] = None, output_dir: Optional[str] = None, **kwargs) -> int:
    """Generate design diagrams from code"""
    # Retorna 0 para éxito, 1 para error

def load_config(working_dir: Path = None) -> AutocodeConfig:
    """Load configuration from autocode_config.yml"""
    # Retorna configuración cargada
```

## Objetivo de los Tests
Crear tests que verifiquen:
1. **Thin wrapper behavior**: La API solo orquesta, no duplica lógica
2. **Correcta llamada a CLI**: Funciones CLI son llamadas con parámetros correctos
3. **Background tasks**: Operaciones largas se ejecutan en background
4. **Error handling**: Manejo apropiado de errores de CLI y daemon
5. **Response format**: Responses siguen el formato esperado

## Dependencias Necesarias

### Instalar Dependencias de Testing
```bash
# Instalar dependencias para testing async de FastAPI
uv add --dev httpx pytest-asyncio pytest-mock pytest-cov

# httpx: Cliente HTTP async para FastAPI testing
# pytest-asyncio: Soporte para tests async
# pytest-mock: Mocking capabilities
# pytest-cov: Coverage reporting
```

## Instrucciones Paso a Paso

### 1. Crear Estructura Base de Tests
```python
# tests/test_api.py
import pytest
import asyncio
from httpx import AsyncClient
from unittest.mock import patch, MagicMock, AsyncMock
from fastapi.testclient import TestClient

# Import the FastAPI app
from autocode.api.server import app
from autocode.api.models import CheckExecutionResponse, StatusResponse
from autocode.orchestration.daemon import AutocodeDaemon

# Create test client
client = TestClient(app)

@pytest.fixture
def mock_daemon():
    """Mock daemon for tests that require daemon functionality."""
    daemon = MagicMock(spec=AutocodeDaemon)
    daemon.get_daemon_status.return_value = {
        "running": True,
        "uptime": 100.0,
        "last_check": None
    }
    daemon.get_all_results.return_value = {
        "doc_check": {"status": "success", "last_run": None, "error": None},
        "test_check": {"status": "success", "last_run": None, "error": None},
        "git_check": {"status": "success", "last_run": None, "error": None}
    }
    daemon.config = MagicMock()
    return daemon

@pytest.fixture
async def async_client():
    """Create async client for testing."""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac
```

### 2. Tests para Endpoints de CLI Wrappers
```python
class TestCLIWrapperEndpoints:
    """Test endpoints that wrap CLI functions."""
    
    @patch('autocode.api.server.check_docs')
    @pytest.mark.asyncio
    async def test_generate_docs_success(self, mock_check_docs, async_client):
        """Test successful documentation generation."""
        # Setup mock
        mock_check_docs.return_value = 0  # Success
        
        # Make request
        response = await async_client.post("/api/generate-docs")
        
        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["result"] == "Documentation check started"
        assert data["error"] is None
        
        # Verify CLI function would be called (in background task)
        # Note: Background tasks are harder to test directly, so we verify the setup
    
    @patch('autocode.api.server.check_docs')
    @pytest.mark.asyncio
    async def test_generate_docs_exception(self, mock_check_docs, async_client):
        """Test documentation generation with exception."""
        # Setup mock to raise exception
        mock_check_docs.side_effect = Exception("Test error")
        
        # Make request
        response = await async_client.post("/api/generate-docs")
        
        # Verify error response
        assert response.status_code == 200  # FastAPI returns 200 but with error in body
        data = response.json()
        assert data["success"] is False
        assert data["result"] is None
        assert "Test error" in data["error"]
    
    @patch('autocode.api.server.code_to_design')
    @pytest.mark.asyncio
    async def test_generate_design_with_params(self, mock_code_to_design, async_client):
        """Test design generation with parameters."""
        # Setup mock
        mock_code_to_design.return_value = 0
        
        # Make request with parameters
        response = await async_client.post(
            "/api/generate-design",
            params={"directory": "autocode", "output_dir": "design"}
        )
        
        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["result"] == "Design generation started"
    
    @patch('autocode.api.server.load_config')
    @pytest.mark.asyncio
    async def test_load_configuration_success(self, mock_load_config, async_client):
        """Test configuration loading."""
        # Setup mock
        mock_config = MagicMock()
        mock_config.dict.return_value = {"docs": {"enabled": True}}
        mock_load_config.return_value = mock_config
        
        # Make request
        response = await async_client.get("/api/config/load")
        
        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "config" in data
        assert data["error"] is None
        
        # Verify CLI function was called
        mock_load_config.assert_called_once()
    
    @patch('autocode.api.server.check_docs')
    @pytest.mark.asyncio
    async def test_check_docs_sync_success(self, mock_check_docs, async_client):
        """Test synchronous docs check - success case."""
        # Setup mock
        mock_check_docs.return_value = 0  # Success
        
        # Make request
        response = await async_client.post("/api/docs/check-sync")
        
        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["exit_code"] == 0
        assert "up to date" in data["message"]
        
        # Verify CLI function was called
        mock_check_docs.assert_called_once()
    
    @patch('autocode.api.server.check_docs')
    @pytest.mark.asyncio
    async def test_check_docs_sync_issues(self, mock_check_docs, async_client):
        """Test synchronous docs check - issues found."""
        # Setup mock
        mock_check_docs.return_value = 1  # Issues found
        
        # Make request
        response = await async_client.post("/api/docs/check-sync")
        
        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False
        assert data["exit_code"] == 1
        assert "issues found" in data["message"]
```

### 3. Tests para Endpoints del Daemon
```python
class TestDaemonEndpoints:
    """Test endpoints that require daemon functionality."""
    
    @pytest.mark.asyncio
    async def test_get_status_no_daemon(self, async_client):
        """Test status endpoint when daemon is not initialized."""
        # Ensure daemon is None (default state)
        from autocode.api.server import daemon
        assert daemon is None
        
        # Make request
        response = await async_client.get("/api/status")
        
        # Verify error response
        assert response.status_code == 503
        data = response.json()
        assert "Daemon not initialized" in data["detail"]
    
    @patch('autocode.api.server.daemon')
    @pytest.mark.asyncio
    async def test_get_status_with_daemon(self, mock_daemon_instance, async_client):
        """Test status endpoint with daemon running."""
        # Setup mock daemon
        mock_daemon_instance.get_daemon_status.return_value = {
            "running": True,
            "uptime": 150.0,
            "last_check": None
        }
        mock_daemon_instance.get_all_results.return_value = {
            "doc_check": {"status": "success", "last_run": None, "error": None}
        }
        mock_daemon_instance.config = {"docs": {"enabled": True}}
        
        # Make request
        response = await async_client.get("/api/status")
        
        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert "daemon" in data
        assert "checks" in data
        assert "config" in data
        
        # Verify daemon methods were called
        mock_daemon_instance.get_daemon_status.assert_called_once()
        mock_daemon_instance.get_all_results.assert_called_once()
    
    @patch('autocode.api.server.daemon')
    @patch('autocode.api.server.check_docs')
    @pytest.mark.asyncio
    async def test_run_check_doc_check(self, mock_check_docs, mock_daemon_instance, async_client):
        """Test running specific check via API."""
        # Setup mocks
        mock_daemon_instance.__bool__.return_value = True  # Daemon exists
        mock_check_docs.return_value = 0
        
        # Make request
        response = await async_client.post("/api/checks/doc_check/run")
        
        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "doc_check" in data["result"]
    
    @patch('autocode.api.server.daemon')
    @pytest.mark.asyncio
    async def test_run_check_invalid_check(self, mock_daemon_instance, async_client):
        """Test running invalid check name."""
        # Setup mock
        mock_daemon_instance.__bool__.return_value = True
        
        # Make request with invalid check name
        response = await async_client.post("/api/checks/invalid_check/run")
        
        # Verify error response
        assert response.status_code == 400
        data = response.json()
        assert "Unknown check" in data["detail"]
```

### 4. Tests para Web Routes
```python
class TestWebRoutes:
    """Test web routes (HTML responses)."""
    
    @pytest.mark.asyncio
    async def test_root_redirect(self, async_client):
        """Test root redirects to dashboard."""
        response = await async_client.get("/", follow_redirects=False)
        
        assert response.status_code == 302
        assert response.headers["location"] == "/dashboard"
    
    @patch('autocode.api.server.templates')
    @pytest.mark.asyncio
    async def test_dashboard_page(self, mock_templates, async_client):
        """Test dashboard page rendering."""
        # Setup mock template response
        mock_templates.TemplateResponse.return_value = MagicMock()
        mock_templates.TemplateResponse.return_value.status_code = 200
        
        # Make request
        response = await async_client.get("/dashboard")
        
        # Verify template was called
        mock_templates.TemplateResponse.assert_called_once()
        call_args = mock_templates.TemplateResponse.call_args
        assert "pages/dashboard.html" in call_args[0]
        assert "request" in call_args[1]
```

### 5. Tests de Integración y Edge Cases
```python
class TestIntegrationAndEdgeCases:
    """Test integration scenarios and edge cases."""
    
    @patch('autocode.api.server.check_docs')
    @patch('autocode.api.server.code_to_design')
    @pytest.mark.asyncio
    async def test_multiple_background_tasks(self, mock_code_to_design, mock_check_docs, async_client):
        """Test multiple background tasks don't interfere."""
        # Setup mocks
        mock_check_docs.return_value = 0
        mock_code_to_design.return_value = 0
        
        # Make multiple requests
        response1 = await async_client.post("/api/generate-docs")
        response2 = await async_client.post("/api/generate-design")
        
        # Both should succeed
        assert response1.status_code == 200
        assert response2.status_code == 200
        
        data1 = response1.json()
        data2 = response2.json()
        assert data1["success"] is True
        assert data2["success"] is True
    
    @patch('autocode.api.server.load_config')
    @pytest.mark.asyncio
    async def test_config_load_exception(self, mock_load_config, async_client):
        """Test configuration loading with exception."""
        # Setup mock to raise exception
        mock_load_config.side_effect = Exception("Config file not found")
        
        # Make request
        response = await async_client.get("/api/config/load")
        
        # Verify error response
        assert response.status_code == 500
        data = response.json()
        assert "Config file not found" in data["detail"]
    
    @pytest.mark.asyncio
    async def test_nonexistent_endpoint(self, async_client):
        """Test request to non-existent endpoint."""
        response = await async_client.get("/api/nonexistent")
        
        assert response.status_code == 404
```

### 6. Configuración de Coverage
```python
# pytest.ini o agregar a pyproject.toml
[tool.pytest.ini_options]
testpaths = ["tests"]
asyncio_mode = "auto"  # Para tests async automáticos
addopts = [
    "--cov=autocode.api",
    "--cov-report=html",
    "--cov-report=term-missing",
    "--cov-fail-under=80",
    "-v"
]

# Para excluir archivos del coverage si es necesario
[tool.coverage.run]
omit = [
    "tests/*",
    "*/migrations/*",
    "*/venv/*",
    "*/__pycache__/*"
]
```

## Criterios de Verificación

### Comandos de Testing
```bash
# Ejecutar todos los tests de API
pytest tests/test_api.py -v

# Con coverage detallado
pytest tests/test_api.py --cov=autocode.api --cov-report=term-missing

# Solo tests de endpoints específicos
pytest tests/test_api.py::TestCLIWrapperEndpoints::test_generate_docs_success -v

# Ejecutar tests async específicamente
pytest tests/test_api.py -k "async" -v
```

### Verificaciones Específicas
1. **Coverage >80%**: Tests cubren la mayoría del código de la API
2. **Mock Verification**: CLI functions son mockeadas correctamente y se verifica su llamada
3. **Background Tasks**: Se testea que background tasks son configuradas (aunque no ejecutadas)
4. **Error Handling**: Todos los tipos de errores (daemon, CLI, exceptions) son manejados
5. **Response Format**: Responses siguen los modelos Pydantic definidos
6. **HTTP Status Codes**: Códigos de estado apropiados para cada escenario

### Verificación Manual Adicional
```bash
# Opcional: Verificar que los endpoints reales funcionan
# (después de implementar la API)
uv run autocode daemon &
sleep 2

# Test real endpoints
curl -X POST http://localhost:8080/api/generate-docs
curl http://localhost:8080/api/config/load
curl http://localhost:8080/api/status

# Stop daemon
pkill -f "autocode daemon"
```

### Métricas de Éxito
- **100% test pass rate**: Todos los tests pasan
- **>80% code coverage**: Cobertura alta del código API
- **Thin wrapper verification**: Tests confirman que API no duplica lógica CLI
- **Proper mocking**: CLI functions son mockeadas, no ejecutadas realmente
- **Comprehensive scenarios**: Success, error, edge cases cubiertos

## Template de Commit Message
```
test(api): add comprehensive tests for API endpoints with CLI mocking

- Installed httpx, pytest-asyncio, pytest-mock for async API testing
- Created test suite covering all CLI wrapper endpoints
- Implemented proper mocking of CLI functions to verify thin wrapper behavior
- Added tests for daemon-dependent endpoints with daemon mocking
- Covered success, error, and edge cases for all endpoint types
- Achieved >80% code coverage with detailed assertions
- Verified background task setup and error handling consistency
- Added integration tests for multiple concurrent requests
```
