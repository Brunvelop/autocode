# Task 009: Expansión de Wrappers CLI en la API

## Contexto del Proyecto
Este proyecto, autocode, es una herramienta para automatizar tareas de calidad de código, documentación, tests y análisis Git. Después de eliminar los endpoints legacy del servidor API, necesitamos asegurar que todos los comandos CLI disponibles tengan un wrapper en la API para mantener la funcionalidad completa desde la interfaz web.

## Estado Actual de los Comandos CLI
Los comandos CLI están definidos en `autocode/cli.py` usando Typer. Aquí están todos los comandos disponibles:

### Comandos CLI Existentes en autocode/cli.py
```python
import typer
from pathlib import Path
from typing import Optional, List

app = typer.Typer(help="Automated code quality and development tools")

@app.command("check-docs")
def check_docs(
    doc_index_output: Optional[str] = typer.Option(None, "--doc-index-output", help="Override output path for documentation index")
) -> int:
    """Check if documentation is up to date"""
    # Implementación existente
    project_root = Path.cwd()
    config = load_config()
    checker = DocChecker(project_root, config.docs)
    outdated_results = checker.get_outdated_docs()
    output = checker.format_results(outdated_results)
    print(output)
    return 1 if outdated_results else 0

@app.command("check-tests")
def check_tests() -> int:
    """Check if tests exist and are passing"""
    # Implementación existente
    project_root = Path.cwd()
    config = load_config()
    checker = TestChecker(project_root, config.tests)
    test_issues = checker.get_missing_and_failing_tests()
    output = checker.format_results(test_issues)
    print(output)
    return 1 if test_issues else 0

@app.command("git-changes")
def git_changes(
    output: Optional[str] = typer.Option(None, "-o", "--output", help="Output JSON file path (default: git_changes.json)"),
    verbose: bool = typer.Option(False, "-v", "--verbose", help="Show detailed diff information")
) -> int:
    """Analyze git changes for commit message generation"""
    # Implementación existente
    project_root = Path.cwd()
    analyzer = GitAnalyzer(project_root)
    # ... lógica completa

@app.command("daemon")
def daemon(
    host: str = typer.Option("127.0.0.1", "--host", help="Host to bind to (default: 127.0.0.1)"),
    port: int = typer.Option(8080, "--port", help="Port to bind to (default: 8080)"),
    verbose: bool = typer.Option(False, "-v", "--verbose", help="Enable verbose logging")
) -> int:
    """Start the autocode monitoring daemon with web interface"""
    # Este comando NO necesita wrapper porque ES el servidor API

@app.command("opencode")
def opencode(
    prompt: Optional[str] = typer.Option(None, "-p", "--prompt", help="Direct prompt to send to OpenCode"),
    prompt_file: Optional[str] = typer.Option(None, "-f", "--prompt-file", help="Load prompt from internal file"),
    list_prompts: bool = typer.Option(False, "--list-prompts", help="List all available internal prompts"),
    validate: bool = typer.Option(False, "--validate", help="Validate OpenCode setup and configuration"),
    debug: bool = typer.Option(False, "--debug", help="Enable debug mode (overrides config)"),
    json_output: bool = typer.Option(False, "--json", help="Output results in JSON format"),
    quiet: bool = typer.Option(False, "--quiet", help="Enable quiet mode (overrides config)"),
    verbose: bool = typer.Option(False, "-v", "--verbose", help="Show detailed output including debug info"),
    cwd: Optional[str] = typer.Option(None, "--cwd", help="Working directory for OpenCode execution")
) -> int:
    """Execute OpenCode AI analysis with prompts"""
    # Implementación existente con validación de argumentos mutuamente exclusivos

@app.command("code-to-design")
def code_to_design(
    directory: Optional[str] = typer.Option(None, "-d", "--directory", help="Directory to analyze"),
    pattern: str = typer.Option("*.py", "-p", "--pattern", help="File pattern to match (default: *.py)"),
    output_dir: Optional[str] = typer.Option(None, "-o", "--output-dir", help="Output directory for generated designs"),
    languages: Optional[List[str]] = typer.Option(None, "-l", "--languages", help="Languages to analyze"),
    diagrams: Optional[List[str]] = typer.Option(None, "-g", "--diagrams", help="Diagram types"),
    show_config: bool = typer.Option(False, "--show-config", help="Show loaded/normalized configuration"),
    directories: Optional[List[str]] = typer.Option(None, "--directories", help="Directories to analyze")
) -> int:
    """Generate design diagrams from code"""
    # Implementación existente

@app.command("count-tokens")
def count_tokens(
    file: Optional[str] = typer.Option(None, "-f", "--file", help="Count tokens in a specific file"),
    directory: Optional[str] = typer.Option(None, "-d", "--directory", help="Count tokens in all files in a directory"),
    pattern: str = typer.Option("*", "-p", "--pattern", help="File pattern to match when using --directory"),
    model: str = typer.Option("gpt-4", "-m", "--model", help="LLM model for token encoding (default: gpt-4)"),
    threshold: Optional[int] = typer.Option(None, "-t", "--threshold", help="Token threshold for warnings"),
    verbose: bool = typer.Option(False, "-v", "--verbose", help="Show detailed per-file information")
) -> int:
    """Count tokens in files for LLM analysis"""
    # Implementación existente con validación de argumentos mutuamente exclusivos
```

### Función de Configuración
```python
def load_config(working_dir: Path = None) -> AutocodeConfig:
    """Load configuration from autocode_config.yml searching up directory tree."""
    # Implementación existente que busca autocode_config.yml
    if working_dir is None:
        working_dir = Path.cwd()
    
    config_file = find_config_file(working_dir)
    if config_file is None:
        return AutocodeConfig()  # Default config
    
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            config_data = yaml.safe_load(f)
        return AutocodeConfig(**config_data)
    except Exception as e:
        print(f"⚠️  Warning: Error loading config: {e}")
        return AutocodeConfig()
```

## Estado Actual de los Wrappers API
En `autocode/api/server.py`, después de la migración de Task 008, estos son los wrappers CLI existentes:

### Wrappers CLI Existentes (Post-Task 008)
```python
# 1. EXISTE: generate-docs (invoca check_docs)
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

# 2. EXISTE: generate-design (invoca code_to_design)
@app.post("/api/generate-design", response_model=CheckExecutionResponse)
async def generate_design(
    directory: str = None,
    output_dir: str = None,
    background_tasks: BackgroundTasks = None
):
    """Generate design diagrams using CLI function."""
    try:
        def run_design_task():
            return code_to_design(directory=directory, output_dir=output_dir)
        
        background_tasks.add_task(run_design_task)
        return CheckExecutionResponse(success=True, result=None, error=None)
    except Exception as e:
        return handle_cli_error("code_to_design", e)

# 3. EXISTE: analyze-git (invoca git_changes)
@app.post("/api/analyze-git", response_model=CheckExecutionResponse)
async def analyze_git(
    output: str = None,
    verbose: bool = False,
    background_tasks: BackgroundTasks = None
):
    """Analyze git changes using CLI function."""
    try:
        def run_git_task():
            return git_changes(output=output, verbose=verbose)
        
        background_tasks.add_task(run_git_task)
        return CheckExecutionResponse(success=True, result=None, error=None)
    except Exception as e:
        return handle_cli_error("git_changes", e)

# 4. EXISTE: config/load (invoca load_config)
@app.get("/api/config/load", response_model=Dict[str, Any])
async def load_configuration():
    """Load configuration using CLI function."""
    try:
        config = load_config()
        return {"success": True, "config": config.dict(), "error": None}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

### Función de Manejo de Errores
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

## Objetivo de la Expansión
Crear wrappers para TODOS los comandos CLI faltantes, asegurando que la API sea un proxy completo del CLI:

### Comandos CLI que NECESITAN wrappers:
1. **check-tests**: Necesita `/api/check-tests`
2. **opencode**: Necesita `/api/opencode` 
3. **count-tokens**: Necesita `/api/count-tokens`

### Comandos CLI que NO necesitan wrappers:
- **daemon**: Es el propio servidor API
- **check-docs**: Ya tiene `/api/generate-docs`
- **git-changes**: Ya tiene `/api/analyze-git`
- **code-to-design**: Ya tiene `/api/generate-design`

## Instrucciones Paso a Paso

### 1. Añadir Import para check_tests si no existe
En `autocode/api/server.py`, verificar que esté importado:

```python
# Al inicio del archivo, verificar que esté presente:
from ..cli import check_docs, check_tests, git_changes, code_to_design, load_config
```

### 2. Crear Wrapper para check-tests
Añadir al final de los endpoints existentes en `server.py`:

```python
@app.post("/api/check-tests", response_model=CheckExecutionResponse)
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
```

### 3. Crear Wrapper para opencode
Este comando tiene múltiples parámetros opcionales y validación compleja:

```python
@app.post("/api/opencode", response_model=CheckExecutionResponse)
async def opencode_wrapper(
    background_tasks: BackgroundTasks,
    prompt: Optional[str] = None,
    prompt_file: Optional[str] = None,
    list_prompts: bool = False,
    validate: bool = False,
    debug: bool = False,
    json_output: bool = False,
    quiet: bool = False,
    verbose: bool = False,
    cwd: Optional[str] = None
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
```

### 4. Crear Wrapper para count-tokens
Este comando tiene argumentos mutuamente exclusivos (file vs directory):

```python
@app.post("/api/count-tokens", response_model=CheckExecutionResponse)
async def count_tokens_wrapper(
    background_tasks: BackgroundTasks,
    file: Optional[str] = None,
    directory: Optional[str] = None,
    pattern: str = "*",
    model: str = "gpt-4",
    threshold: Optional[int] = None,
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
```

### 5. Añadir Import para opencode si no existe
Es posible que necesites importar la función opencode del CLI:

```python
# Si no está importada, añadir al import existente:
from ..cli import check_docs, check_tests, git_changes, code_to_design, load_config, opencode, count_tokens
```

### 6. Actualizar Imports de Modelos si es Necesario
Verificar que CheckExecutionResponse esté importado:

```python
from .models import CheckExecutionResponse, AutocodeConfig
```

### 7. Verificar Posición de los Nuevos Endpoints
Colocar los nuevos wrappers DESPUÉS de los wrappers existentes pero ANTES de las rutas de páginas:

```python
# Wrappers CLI existentes...
# (generate_docs, generate_design, analyze_git, load_configuration)

# NUEVOS WRAPPERS AQUÍ
@app.post("/api/check-tests", response_model=CheckExecutionResponse)
async def check_tests_wrapper(background_tasks: BackgroundTasks):
    # ...

@app.post("/api/opencode", response_model=CheckExecutionResponse) 
async def opencode_wrapper(...):
    # ...

@app.post("/api/count-tokens", response_model=CheckExecutionResponse)
async def count_tokens_wrapper(...):
    # ...

# Rutas de páginas (dashboard, design, config, etc.)
# ...
```

## Criterios de Verificación

### 1. Servidor Debe Arrancar Sin Errores
```bash
cd /path/to/autocode
uv run autocode daemon
# No debe mostrar errores de import ni sintaxis
```

### 2. Nuevos Wrappers Deben Responder
```bash
# Test check-tests wrapper
curl -X POST http://127.0.0.1:8080/api/check-tests
# Debe devolver: {"success": true, "result": null, "error": null}

# Test opencode wrapper (list prompts)
curl -X POST "http://127.0.0.1:8080/api/opencode?list_prompts=true"
# Debe devolver CheckExecutionResponse válido

# Test count-tokens wrapper  
curl -X POST "http://127.0.0.1:8080/api/count-tokens?directory=autocode&pattern=*.py"
# Debe devolver CheckExecutionResponse válido
```

### 3. Parámetros Deben Pasarse Correctamente
```bash
# Test opencode con prompt
curl -X POST "http://127.0.0.1:8080/api/opencode" \
  -H "Content-Type: application/json" \
  -d '{"prompt": "test prompt", "debug": true}'

# Test count-tokens con file específico
curl -X POST "http://127.0.0.1:8080/api/count-tokens" \
  -H "Content-Type: application/json" \
  -d '{"file": "autocode/cli.py", "model": "gpt-4", "verbose": true}'
```

### 4. Manejo de Errores
```bash
# Test con parámetros inválidos para verificar error handling
curl -X POST "http://127.0.0.1:8080/api/count-tokens" \
  -H "Content-Type: application/json" \
  -d '{"file": "archivo_inexistente.py"}'
# Debe devolver: {"success": false, "result": null, "error": "..."}
```

### 5. Background Tasks Deben Funcionar
Los endpoints deben responder inmediatamente (success: true) y ejecutar en background.
Verificar logs del servidor para confirmación de ejecución.

### 6. Documentación OpenAPI Automática
```bash
# Verificar que aparezcan en la documentación automática
curl http://127.0.0.1:8080/docs
# O abrir en navegador: http://127.0.0.1:8080/docs
# Debe mostrar los 3 nuevos endpoints: /api/check-tests, /api/opencode, /api/count-tokens
```

### 7. Compatibilidad con Funciones CLI Existentes
```bash
# Verificar que las funciones CLI originales siguen funcionando
uv run autocode check-tests
uv run autocode opencode --list-prompts
uv run autocode count-tokens --file autocode/cli.py
```

### 8. Comparar Comportamiento CLI vs API
Para al menos un comando, ejecutar tanto la versión CLI como la API y comparar:

```bash
# CLI directo
uv run autocode check-tests > cli_output.txt

# API wrapper (esperar a que complete la background task)
curl -X POST http://127.0.0.1:8080/api/check-tests
# Revisar logs del servidor para ver si la salida es equivalente
```

## Template de Commit Message
```
feat(api): add CLI wrappers for all remaining commands

- Added /api/check-tests wrapper for check_tests CLI function
- Added /api/opencode wrapper with all parameters (prompt, debug, etc.)
- Added /api/count-tokens wrapper with file/directory support
- All wrappers use BackgroundTasks for async execution
- Maintained parameter compatibility with CLI commands
- Added proper error handling with handle_cli_error
- API now provides complete CLI functionality via HTTP

Coverage: API now wraps 6/7 CLI commands (daemon excluded as it IS the API)
