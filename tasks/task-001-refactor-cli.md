# Task 001: Instalar Typer y Refactorizar CLI

## Contexto del Proyecto
Este proyecto, autocode, es una herramienta para automatizar tareas de calidad de código, documentación, tests y análisis Git. Su propósito es proporcionar un conjunto de comandos CLI que pueden ejecutarse individualmente o a través de un daemon con interfaz web.

## Estado Actual del CLI
El CLI actual está en `autocode/cli.py` y utiliza argparse con la siguiente estructura:

### Estructura Completa Actual
```python
import argparse
import sys
from pathlib import Path
from typing import Optional

# Imports de módulos core
from .core.docs import DocChecker, DocIndexer
from .core.test import TestChecker
from .core.git import GitAnalyzer
from .core.ai import OpenCodeExecutor, validate_opencode_setup
from .core.design import CodeToDesign
from .api.models import AutocodeConfig

def create_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="autocode",
        description="Automated code quality and development tools"
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # check-docs subcommand
    check_docs_parser = subparsers.add_parser("check-docs", help="Check if documentation is up to date")
    check_docs_parser.add_argument("--doc-index-output", type=str, help="Override output path for documentation index")
    
    # check-tests subcommand
    check_tests_parser = subparsers.add_parser("check-tests", help="Check if tests exist and are passing")
    
    # git-changes subcommand
    git_changes_parser = subparsers.add_parser("git-changes", help="Analyze git changes for commit message generation")
    git_changes_parser.add_argument("--output", "-o", type=str, help="Output JSON file path (default: git_changes.json)")
    git_changes_parser.add_argument("--verbose", "-v", action="store_true", help="Show detailed diff information")
    
    # daemon subcommand
    daemon_parser = subparsers.add_parser("daemon", help="Start the autocode monitoring daemon with web interface")
    daemon_parser.add_argument("--host", type=str, default="127.0.0.1", help="Host to bind to (default: 127.0.0.1)")
    daemon_parser.add_argument("--port", type=int, default=8080, help="Port to bind to (default: 8080)")
    daemon_parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose logging")
    
    # opencode subcommand (complejo con mutually exclusive groups)
    opencode_parser = subparsers.add_parser("opencode", help="Execute OpenCode AI analysis with prompts")
    prompt_group = opencode_parser.add_mutually_exclusive_group()
    prompt_group.add_argument("--prompt", "-p", type=str, help="Direct prompt to send to OpenCode")
    prompt_group.add_argument("--prompt-file", "-f", type=str, help="Load prompt from internal file")
    opencode_parser.add_argument("--list-prompts", action="store_true", help="List all available internal prompts")
    opencode_parser.add_argument("--validate", action="store_true", help="Validate OpenCode setup and configuration")
    opencode_parser.add_argument("--debug", action="store_true", help="Enable debug mode")
    opencode_parser.add_argument("--json", action="store_true", help="Output results in JSON format")
    opencode_parser.add_argument("--quiet", action="store_true", help="Enable quiet mode")
    opencode_parser.add_argument("--verbose", "-v", action="store_true", help="Show detailed output including debug info")
    opencode_parser.add_argument("--cwd", type=str, help="Working directory for OpenCode execution")
    
    # code-to-design subcommand
    code_to_design_parser = subparsers.add_parser("code-to-design", help="Generate design diagrams from code")
    code_to_design_parser.add_argument("--directory", "-d", type=str, help="Directory to analyze")
    code_to_design_parser.add_argument("--pattern", "-p", type=str, default="*.py", help="File pattern to match")
    code_to_design_parser.add_argument("--output-dir", "-o", type=str, help="Output directory for generated designs")
    code_to_design_parser.add_argument("--languages", "-l", type=str, nargs="+", help="Languages to analyze")
    code_to_design_parser.add_argument("--diagrams", "-g", type=str, nargs="+", help="Diagram types")
    code_to_design_parser.add_argument("--show-config", action="store_true", help="Show loaded configuration")
    code_to_design_parser.add_argument("--directories", type=str, nargs="+", help="Multiple directories to analyze")
    
    # count-tokens subcommand
    count_tokens_parser = subparsers.add_parser("count-tokens", help="Count tokens in files for LLM analysis")
    file_group = count_tokens_parser.add_mutually_exclusive_group(required=True)
    file_group.add_argument("--file", "-f", type=str, help="Count tokens in a specific file")
    file_group.add_argument("--directory", "-d", type=str, help="Count tokens in all files in a directory")
    count_tokens_parser.add_argument("--pattern", "-p", type=str, default="*", help="File pattern to match")
    count_tokens_parser.add_argument("--model", "-m", type=str, default="gpt-4", help="LLM model for token encoding")
    count_tokens_parser.add_argument("--threshold", "-t", type=int, help="Token threshold for warnings")
    count_tokens_parser.add_argument("--verbose", "-v", action="store_true", help="Show detailed per-file information")
    
    return parser

def main():
    parser = create_parser()
    args = parser.parse_args()
    
    if not args.command:
        args.command = "check-docs"
    
    # Route to appropriate command handler
    if args.command == "check-docs":
        exit_code = check_docs_command(args)
    elif args.command == "check-tests":
        exit_code = check_tests_command(args)
    elif args.command == "git-changes":
        exit_code = git_changes_command(args)
    elif args.command == "daemon":
        exit_code = daemon_command(args)
    elif args.command == "opencode":
        exit_code = opencode_command(args)
    elif args.command == "code-to-design":
        exit_code = code_to_design_command(args)
    elif args.command == "count-tokens":
        exit_code = count_tokens_command(args)
    else:
        parser.print_help()
        exit_code = 1
    
    sys.exit(exit_code)
```

### Ejemplos de Handlers Actuales
```python
def check_docs_command(args) -> int:
    """Handle check-docs command."""
    project_root = Path.cwd()
    config = load_config()
    checker = DocChecker(project_root, config.docs)
    outdated_results = checker.get_outdated_docs()
    output = checker.format_results(outdated_results)
    print(output)
    return 1 if outdated_results else 0

def daemon_command(args) -> int:
    """Handle daemon command."""
    try:
        import uvicorn
        from .api.server import app
        print("🚀 Starting Autocode Monitoring Daemon")
        uvicorn.run(app, host=args.host, port=args.port, log_level="info" if args.verbose else "warning")
        return 0
    except KeyboardInterrupt:
        print("\n🛑 Daemon stopped by user")
        return 0
    except Exception as e:
        print(f"❌ Error starting daemon: {e}")
        return 1

def git_changes_command(args) -> int:
    """Handle git-changes command."""
    project_root = Path.cwd()
    analyzer = GitAnalyzer(project_root)
    try:
        output_file = Path(args.output) if args.output else project_root / "git_changes.json"
        changes_data = analyzer.save_changes_to_file(output_file)
        # Print summary and save results
        print(f"📊 Repository Status: {changes_data['repository_status']}")
        return 0
    except Exception as e:
        print(f"❌ Error analyzing git changes: {e}")
        return 1
```

### Función de Configuración
```python
def load_config(working_dir: Path = None) -> AutocodeConfig:
    """Load configuration from autocode_config.yml searching up directory tree."""
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

## Objetivo de la Refactorización
Convertir el CLI basado en argparse a Typer para:
1. **Funciones reutilizables**: Cada comando será una función independiente callable desde código Python
2. **Mejor typing**: Aprovechando el soporte nativo de Typer para type hints
3. **Preparación para API**: Las funciones podrán ser importadas y utilizadas en la API

## Instrucciones Paso a Paso

### 1. Instalar Typer
```bash
uv add typer
```

### 2. Refactorizar la Estructura Principal
Reemplazar el argparse con Typer app:

```python
import typer
from typing import Optional, List

app = typer.Typer(help="Automated code quality and development tools")

@app.command("check-docs")
def check_docs(
    doc_index_output: Optional[str] = typer.Option(None, "--doc-index-output", help="Override output path for documentation index")
) -> int:
    """Check if documentation is up to date"""
    # Mantener la lógica actual exactamente igual
    project_root = Path.cwd()
    config = load_config()
    checker = DocChecker(project_root, config.docs)
    outdated_results = checker.get_outdated_docs()
    output = checker.format_results(outdated_results)
    print(output)
    return 1 if outdated_results else 0

def main():
    app()
```

### 3. Convertir Todos los Comandos
Convertir cada handler actual manteniendo la lógica interna intacta:

```python
@app.command("check-tests")
def check_tests() -> int:
    """Check if tests exist and are passing"""
    # Lógica actual de check_tests_command

@app.command("git-changes")
def git_changes(
    output: Optional[str] = typer.Option(None, "-o", "--output", help="Output JSON file path"),
    verbose: bool = typer.Option(False, "-v", "--verbose", help="Show detailed diff information")
) -> int:
    """Analyze git changes for commit message generation"""
    # Lógica actual de git_changes_command

@app.command("daemon")
def daemon(
    host: str = typer.Option("127.0.0.1", "--host", help="Host to bind to"),
    port: int = typer.Option(8080, "--port", help="Port to bind to"),
    verbose: bool = typer.Option(False, "-v", "--verbose", help="Enable verbose logging")
) -> int:
    """Start the autocode monitoring daemon with web interface"""
    # Lógica actual de daemon_command
```

### 4. Manejar Comandos Complejos
Para opencode con mutually exclusive groups, usar Typer callbacks:

```python
@app.command("opencode")
def opencode(
    prompt: Optional[str] = typer.Option(None, "-p", "--prompt", help="Direct prompt to send to OpenCode"),
    prompt_file: Optional[str] = typer.Option(None, "-f", "--prompt-file", help="Load prompt from internal file"),
    list_prompts: bool = typer.Option(False, "--list-prompts", help="List all available internal prompts"),
    validate: bool = typer.Option(False, "--validate", help="Validate OpenCode setup"),
    debug: bool = typer.Option(False, "--debug", help="Enable debug mode"),
    json_output: bool = typer.Option(False, "--json", help="Output results in JSON format"),
    quiet: bool = typer.Option(False, "--quiet", help="Enable quiet mode"),
    verbose: bool = typer.Option(False, "-v", "--verbose", help="Show detailed output"),
    cwd: Optional[str] = typer.Option(None, "--cwd", help="Working directory for OpenCode execution")
) -> int:
    """Execute OpenCode AI analysis with prompts"""
    # Validación de argumentos mutuamente exclusivos al inicio
    if prompt and prompt_file:
        typer.echo("Error: --prompt and --prompt-file are mutually exclusive", err=True)
        raise typer.Exit(1)
    # Resto de lógica actual de opencode_command
```

### 5. Actualizar Imports y Estructura
```python
# Al inicio del archivo
import typer
from typing import Optional, List
from pathlib import Path

# Mantener todos los imports actuales de módulos core
from .core.docs import DocChecker, DocIndexer
from .core.test import TestChecker
from .core.git import GitAnalyzer
# ... resto de imports actuales

# Crear la app de Typer
app = typer.Typer(help="Automated code quality and development tools")

# Al final del archivo
def main():
    app()

if __name__ == "__main__":
    main()
```

## Criterios de Verificación

### Comandos a Probar
1. **Help general**: `uv run autocode --help` debe mostrar todos los comandos
2. **Help específico**: `uv run autocode check-docs --help` debe mostrar opciones del comando
3. **Funcionamiento**: `uv run autocode check-docs` debe ejecutar igual que antes
4. **Argumentos**: `uv run autocode daemon --host 0.0.0.0 --port 9000` debe funcionar
5. **Comandos complejos**: `uv run autocode opencode --list-prompts` debe ejecutar

### Verificaciones Específicas
- El output de cada comando debe ser **idéntico** al anterior
- Los códigos de retorno (0 para éxito, 1 para error) deben mantenerse
- La carga de configuración debe funcionar igual
- No debe haber imports rotos ni errores de sintaxis
- Ejecutar `pytest` si hay tests existentes - todos deben pasar

### Comparación Antes/Después
Para al menos 3 comandos:
1. Ejecutar con argparse y guardar output
2. Ejecutar con Typer y comparar output
3. Verificar que sean idénticos

## Template de Commit Message
```
feat(cli): refactor CLI from argparse to Typer

- Installed Typer dependency via uv add typer
- Converted all command handlers to Typer @app.command decorators
- Maintained exact same functionality and output for all commands
- Made CLI functions importable and reusable for API integration
- Preserved all argument parsing, validation, and error handling
```
