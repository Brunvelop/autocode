# cli.py

## 🎯 Propósito

Interfaz de línea de comandos unificada para autocode que proporciona acceso a todas las funcionalidades del proyecto a través de subcomandos especializados. Actúa como punto de entrada único para verificación de documentación, análisis de cambios git, monitoreo continuo, análisis de IA con OpenCode, verificación de tests, y conteo de tokens para análisis de LLM.

## 🏗️ Arquitectura

```mermaid
graph TB
    subgraph "CLI Architecture"
        MAIN[main()<br/>Entry Point]
        PARSER[create_parser()<br/>Argument Parser]
        CONFIG[load_config()<br/>Configuration Loader]
        
        subgraph "Command Handlers"
            CHECK[check_docs_command()<br/>Documentation Check]
            GIT[git_changes_command()<br/>Git Analysis]
            DAEMON[daemon_command()<br/>Web Monitoring]
            OPENCODE[opencode_command()<br/>AI Analysis]
            TOKENS[count_tokens_command()<br/>Token Analysis]
        end
        
        subgraph "Core Components"
            DC[DocChecker]
            GA[GitAnalyzer]
            DI[DocIndexer]
            OE[OpenCodeExecutor]
            TC[TokenCounter]
        end
        
        subgraph "Configuration"
            YAML[autocode_config.yml]
            AUTOCODECONFIG[AutocodeConfig]
        end
        
        subgraph "Output"
            CONSOLE[Console Output]
            JSON[JSON Files]
            INDEX[Documentation Index]
            EXIT[Exit Codes]
        end
    end
    
    MAIN --> PARSER
    PARSER --> CONFIG
    CONFIG --> YAML
    CONFIG --> AUTOCODECONFIG
    
    PARSER --> CHECK
    PARSER --> GIT
    PARSER --> DAEMON
    PARSER --> OPENCODE
    PARSER --> TOKENS
    
    CHECK --> DC
    CHECK --> DI
    GIT --> GA
    OPENCODE --> OE
    TOKENS --> TC
    
    DC --> CONSOLE
    GA --> CONSOLE
    GA --> JSON
    DI --> INDEX
    OE --> CONSOLE
    TC --> CONSOLE
    
    CHECK --> EXIT
    GIT --> EXIT
    DAEMON --> EXIT
    OPENCODE --> EXIT
    TOKENS --> EXIT
    
    classDef main fill:#e1f5fe
    classDef handler fill:#f3e5f5
    classDef component fill:#e8f5e8
    classDef config fill:#fff3e0
    classDef output fill:#e8f5e8
    
    class MAIN,PARSER,CONFIG main
    class CHECK,GIT,DAEMON,OPENCODE,TOKENS handler
    class DC,GA,DI,OE,TC component
    class YAML,AUTOCODECONFIG config
    class CONSOLE,JSON,INDEX,EXIT output
```

## 📋 Responsabilidades

### Responsabilidades Principales
- **Routing de Comandos**: Dirigir argumentos CLI a handlers apropiados para los 5 comandos principales
- **Parsing de Argumentos**: Validar y procesar argumentos de línea de comandos con subcomandos especializados
- **Configuration Management**: Cargar y gestionar configuración desde `autocode_config.yml`
- **Output Formatting**: Formatear salida para consumo humano y programático
- **Exit Code Management**: Proporcionar códigos de salida apropiados para scripts y CI/CD
- **Error Handling**: Manejo robusto de errores con mensajes descriptivos
- **Integration Orchestration**: Coordinar integración entre DocChecker, GitAnalyzer, DocIndexer, OpenCodeExecutor y TokenCounter

### Lo que NO hace
- No implementa lógica de análisis directamente (delegado a componentes especializados)
- No mantiene estado entre ejecuciones (cada comando es independiente)
- No modifica archivos de configuración (solo lectura)
- No ejecuta comandos git directamente (delegado a GitAnalyzer)

## 🔗 Dependencias

### Internas
- `autocode.core.doc_checker.DocChecker`: Verificación de documentación
- `autocode.core.git_analyzer.GitAnalyzer`: Análisis de cambios git
- `autocode.core.doc_indexer.DocIndexer`: Generación de índices de documentación
- `autocode.core.opencode_executor.OpenCodeExecutor`: Integración con OpenCode AI
- `autocode.core.token_counter.TokenCounter`: Conteo de tokens para LLM
- `autocode.api.models.AutocodeConfig`: Modelos de configuración
- `autocode.api.server.app`: Aplicación FastAPI para daemon

### Externas
- `argparse`: Parsing de argumentos de línea de comandos
- `sys`: Gestión de exit codes
- `json`: Serialización de datos
- `yaml`: Carga de configuración YAML
- `pathlib.Path`: Manipulación de rutas
- `uvicorn`: Servidor ASGI para daemon (importación condicional)
- `tiktoken`: Tokenización para análisis LLM (importación condicional)

## 📊 Comandos Disponibles

### `check-docs` - Verificación de Documentación

**Propósito**: Verificar si la documentación está actualizada comparando timestamps de archivos de código vs documentación, con generación automática de índices de documentación.

**Sintaxis**:
```bash
uv run -m autocode.cli check-docs [--doc-index-output PATH]
```

**Opciones**:
- `--doc-index-output PATH`: Sobrescribir ruta de salida para índice de documentación

**Comportamiento**:
1. Carga configuración desde `autocode_config.yml` (o usa defaults)
2. Detecta automáticamente directorios con código Python
3. Mapea archivos de código a documentación esperada
4. Compara fechas de modificación
5. Si toda la documentación está actualizada y la configuración lo permite, genera índice de documentación automáticamente

**Códigos de Salida**:
- `0`: Toda la documentación está actualizada
- `1`: Hay documentación desactualizada o faltante

**Ejemplo de Salida (Documentación Actualizada)**:
```
✅ All documentation is up to date!
📋 Documentation index generated: .clinerules/docs_index.json
```

**Ejemplo de Salida (Documentación Pendiente)**:
```
Documentación desactualizada:
- autocode\cli.py → docs\autocode\cli.md

Archivos sin documentación:
- autocode\orchestration\daemon.py
- autocode\orchestration\scheduler.py

Total: 3 archivos requieren atención
```

**Integración con DocIndexer**:
- Si `config.doc_index.enabled` y `config.doc_index.auto_generate` son True
- Y toda la documentación está actualizada
- Genera automáticamente índice de documentación en formato JSON
- Incluye estadísticas de documentación en la salida

### `git-changes` - Análisis de Cambios Git

**Propósito**: Analizar cambios en el repositorio git para generar información útil para commits y revisiones.

**Sintaxis**:
```bash
uv run -m autocode.cli git-changes [OPTIONS]
```

**Opciones**:
- `--output FILE, -o FILE`: Especificar archivo de salida (default: `git_changes.json`)
- `--verbose, -v`: Mostrar información detallada de diffs

**Comportamiento**:
1. Ejecuta `git status --porcelain` para obtener archivos modificados
2. Extrae diffs detallados para cada archivo
3. Genera estadísticas de cambios
4. Guarda información completa en archivo JSON
5. Muestra resumen en consola

**Códigos de Salida**:
- `0`: Análisis completado exitosamente
- `1`: Error durante el análisis

**Ejemplo de Salida**:
```
📊 Repository Status:
   Total files changed: 3
   Modified: 2
   Added: 1
   Deleted: 0
   Untracked: 0

📄 Modified Files:
   - docs/_index.md
   - autocode/cli.py
   - docs/autocode/_module.md

💾 Detailed changes saved to: git_changes.json
```

**Con `--verbose`**:
```
📋 Detailed Changes:
   🟢 docs/_index.md (modified)
      +15 -2
      +**📦 Versión Actual**: v3.0.0 (Sistema Sintético Generalizado)
      +### Herramientas de Desarrollo...
   🔴 autocode/cli.py (modified)
      +5 -1
      +def new_function():...
```

### `daemon` - Daemon de Monitoreo Web

**Propósito**: Iniciar el daemon de monitoreo continuo con interfaz web para supervisar en tiempo real el estado de documentación y cambios git.

**Sintaxis**:
```bash
uv run -m autocode.cli daemon [OPTIONS]
```

**Opciones**:
- `--host HOST`: Host para el servidor (default: `127.0.0.1`)
- `--port PORT`: Puerto para el servidor (default: `8080`)
- `--verbose, -v`: Habilitar logging detallado

**Comportamiento**:
1. Inicia servidor FastAPI con interfaz web
2. Proporciona dashboard en tiempo real en el navegador
3. Ejecuta verificaciones periódicas automáticamente
4. Ofrece API RESTful para integración programática
5. Mantiene estado y estadísticas de verificaciones

**Códigos de Salida**:
- `0`: Daemon iniciado y terminado exitosamente
- `1`: Error al iniciar el daemon o dependencias faltantes

**Ejemplo de Salida**:
```
🚀 Starting Autocode Monitoring Daemon
   📡 API Server: http://127.0.0.1:8080
   🌐 Web Interface: http://127.0.0.1:8080
   📊 Dashboard will auto-refresh every 5 seconds
   🔄 Checks run automatically per configuration

   Press Ctrl+C to stop the daemon
--------------------------------------------------
INFO:     Started server process [12345]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://127.0.0.1:8080
```

**Funcionalidades del Dashboard**:
- Estado en tiempo real del daemon
- Resultados de verificaciones más recientes
- Configuración dinámica de intervalos
- Ejecución manual de verificaciones
- Monitoreo de métricas de rendimiento

**API Endpoints Disponibles**:
- `GET /`: Dashboard web principal
- `GET /api/status`: Estado completo del sistema
- `GET /api/daemon/status`: Estado específico del daemon
- `POST /api/checks/{check_name}/run`: Ejecutar verificación manual
- `GET/PUT /api/config`: Gestionar configuración
- `GET /health`: Health check simple

### `opencode` - Análisis de Código con IA

**Propósito**: Ejecutar análisis de código inteligente usando OpenCode AI en modo headless para obtener insights, revisiones de código, y análisis automatizado.

**Sintaxis**:
```bash
uv run -m autocode.cli opencode [OPTIONS]
```

**Opciones**:
- `--prompt TEXT, -p TEXT`: Prompt directo para enviar a OpenCode
- `--prompt-file FILE, -f FILE`: Cargar prompt desde archivo interno (ej. 'code-review')
- `--list-prompts`: Listar todos los prompts internos disponibles
- `--validate`: Validar configuración y setup de OpenCode
- `--debug`: Activar modo debug (sobrescribe configuración)
- `--json`: Salida en formato JSON (sobrescribe configuración)
- `--quiet`: Modo silencioso (sobrescribe configuración)
- `--verbose, -v`: Mostrar salida detallada incluyendo debug info
- `--cwd PATH`: Directorio de trabajo para ejecución (default: directorio actual)

**Comportamiento**:
1. Inicializa OpenCodeExecutor con el directorio del proyecto
2. Valida que OpenCode esté instalado y configurado (si se usa --validate)
3. Lista prompts disponibles (si se usa --list-prompts)
4. Ejecuta OpenCode con prompt directo o desde archivo
5. Formatea salida con información detallada o JSON según opciones
6. Maneja errores y timeouts de forma robusta

**Códigos de Salida**:
- `0`: Análisis completado exitosamente
- `1`: Error durante la ejecución (configuración, red, timeout, etc.)

**Ejemplo de Salida Básica**:
```bash
uv run -m autocode.cli opencode -p "Analiza la calidad del código en este proyecto"
```
```
🤖 OpenCode Analysis Complete
El proyecto muestra una arquitectura bien estructurada con 
separación clara de responsabilidades. Puntos destacados:

✅ Fortalezas:
- Modularidad bien definida en vidi/, autocode/, tools/
- Documentación completa siguiendo patrones consistentes
- Uso apropiado de type hints
- Separación clara entre lógica de negocio e interfaces

⚠️ Áreas de Mejora:
- Algunos archivos podrían beneficiarse de más tests unitarios
- Considerar añadir más validación de entrada en endpoints API
- Oportunidad de optimizar imports en algunos módulos

💡 Recomendaciones:
- Implementar pre-commit hooks para mantener calidad
- Considerar usar coverage.py para monitorear cobertura de tests
- Evaluar implementar logging estructurado
```

**Ejemplo con Formato JSON**:
```bash
uv run -m autocode.cli opencode -p "Analiza bugs potenciales" --json
```
```json
{
  "exit_code": 0,
  "success": true,
  "stdout": "{\n  \"analysis_type\": \"bug_detection\",\n  \"findings\": [\n    {\n      \"type\": \"potential_bug\",\n      \"file\": \"autocode/models.py\",\n      \"line\": 42,\n      \"description\": \"Potential race condition in async method\",\n      \"severity\": \"medium\"\n    }\n  ],\n  \"summary\": \"1 potential issue found\"\n}",
  "stderr": "",
  "timestamp": "2025-01-07T11:22:00.000000"
}
```

**Ejemplo con Prompt Predefinido**:
```bash
uv run -m autocode.cli opencode --list-prompts
```
```
📋 Available Prompts:
   • code-review: Comprehensive code review focusing on best practices
   • security-audit: Security-focused analysis for vulnerabilities
   • performance-check: Performance analysis and optimization suggestions
   • documentation-review: Review and suggest documentation improvements
```

```bash
uv run -m autocode.cli opencode -f code-review --verbose
```
```
🤖 OpenCode Analysis Complete
Comprehensive Code Review Results:

[Detailed analysis output...]

📋 Debug Information:
------------------------------
Execution time: 23.4 seconds
Model used: claude-4-sonnet
Tokens consumed: 8,247
Configuration: /path/to/.opencode.json
```

**Ejemplo de Validación**:
```bash
uv run -m autocode.cli opencode --validate
```
```
✅ OpenCode setup is valid and ready to use
   Configuration validated successfully
   All dependencies satisfied
```

**Casos de Error Común**:
```bash
uv run -m autocode.cli opencode -p "Test prompt"
```
```
❌ Error executing OpenCode: OpenCode validation failed
Check OpenCode installation and configuration
```

**Manejo de Argumentos Mutuamente Exclusivos**:
```bash
uv run -m autocode.cli opencode --prompt "Test" --prompt-file "review"
```
```
❌ Error: Either --prompt or --prompt-file must be specified
```

**Uso de Prompts Predefinidos**:
```bash
uv run -m autocode.cli opencode --list-prompts
```
```
📋 Available Prompts:
   • hola-mundo: Prompt básico de demostración
   [Lista de prompts disponibles en autocode/prompts/]
```

**Integración con OpenCodeExecutor**:
- Utiliza `OpenCodeExecutor` para ejecutar OpenCode en modo headless
- Soporte para configuración personalizada de directorio de trabajo
- Formateo inteligente de salida con información de timing y debug
- Validación completa de setup antes de ejecución

### `count-tokens` - Análisis de Tokens LLM

**Propósito**: Contar tokens en archivos para análisis de modelos de lenguaje grandes (LLM), estimación de costos y verificación de límites de contexto.

**Sintaxis**:
```bash
uv run -m autocode.cli count-tokens [OPTIONS]
```

**Opciones**:
- `--file FILE, -f FILE`: Contar tokens en un archivo específico
- `--directory DIR, -d DIR`: Contar tokens en todos los archivos de un directorio
- `--pattern PATTERN, -p PATTERN`: Patrón de archivos al usar --directory (default: *)
- `--model MODEL, -m MODEL`: Modelo LLM para codificación de tokens (default: gpt-4)
- `--threshold NUM, -t NUM`: Umbral de tokens para advertencias
- `--verbose, -v`: Mostrar información detallada por archivo

**Comportamiento**:
1. Inicializa TokenCounter con el modelo especificado
2. Cuenta tokens usando tiktoken para codificación precisa
3. Calcula estadísticas de archivos y ratios
4. Verifica umbrales si se especifican
5. Muestra resultados formateados para análisis

**Códigos de Salida**:
- `0`: Análisis completado exitosamente
- `1`: Error durante el análisis (archivo no encontrado, tiktoken no instalado, etc.)

**Análisis de Archivo Individual**:
```bash
uv run -m autocode.cli count-tokens --file docs/_index.md --model gpt-4 --threshold 10000
```
```
📊 Token Analysis for docs/_index.md:
   Tokens: 3,247
   Model: gpt-4
   File size: 0.02 MB
   Tokens per KB: 156.3

✅ Within threshold of 10,000 tokens
   Remaining: 6,753 tokens
```

**Análisis de Directorio**:
```bash
uv run -m autocode.cli count-tokens --directory autocode --pattern "*.py" --verbose
```
```
📊 Token Analysis for autocode (pattern: *.py):
   Total files: 8
   Total tokens: 15,420
   Average per file: 1,927
   Model: gpt-4

📋 Individual Files:
   autocode/cli.py: 4,521 tokens
   autocode/api.py: 3,890 tokens
   autocode/daemon.py: 2,156 tokens
   autocode/models.py: 1,823 tokens
   autocode/doc_checker.py: 1,567 tokens
   autocode/git_analyzer.py: 1,032 tokens
   autocode/scheduler.py: 431 tokens
```

**Con Verificación de Umbral**:
```bash
uv run -m autocode.cli count-tokens --directory vidi --threshold 50000
```
```
📊 Token Analysis for vidi (pattern: *):
   Total files: 23
   Total tokens: 67,892
   Average per file: 2,952
   Model: gpt-4

⚠️  WARNING: Total exceeds threshold of 50,000 tokens
   Over by: 17,892 tokens
```

**Casos de Error**:
```bash
uv run -m autocode.cli count-tokens --file nonexistent.py
```
```
❌ File not found: nonexistent.py
```

```bash
uv run -m autocode.cli count-tokens --file test.py
```
```
❌ Error: tiktoken not installed. Run 'uv add tiktoken' to install.
```

**Modelos Soportados**:
- `gpt-4`: Modelo GPT-4 (default)
- `gpt-3.5-turbo`: Modelo GPT-3.5 Turbo
- `text-davinci-003`: Modelo davinci legacy
- Otros modelos soportados por tiktoken

**Casos de Uso Comunes**:
1. **Pre-análisis LLM**: Verificar que archivos no excedan límites de contexto
2. **Estimación de Costos**: Calcular costos antes de enviar a APIs de LLM
3. **Optimización de Prompts**: Analizar y optimizar el uso de tokens
4. **Monitoreo de Proyecto**: Rastrear crecimiento de tokens en el tiempo
5. **Validación CI/CD**: Verificar límites en pipelines automáticos

### `check-tests` - Verificación de Tests

**Propósito**: Verificar el estado de tests en el proyecto siguiendo estructura modular, detectando tests faltantes, tests que fallan, y tests huérfanos.

**Sintaxis**:
```bash
uv run -m autocode.cli check-tests
```

**Comportamiento**:
1. Inicializa TestChecker con el directorio del proyecto
2. Detecta automáticamente código Python que requiere tests
3. Mapea archivos de código a tests unitarios esperados
4. Mapea directorios a tests de integración esperados
5. Ejecuta pytest para validar tests existentes
6. Identifica tests huérfanos que ya no corresponden a código

**Códigos de Salida**:
- `0`: Todos los tests existen y están pasando
- `1`: Hay tests faltantes, fallando, o huérfanos

**Ejemplo de Salida (Tests Actualizados)**:
```
✅ All tests exist and are passing!
```

**Ejemplo de Salida (Tests Pendientes)**:
```
Tests faltantes:
- vidi/inference/engine.py → tests/vidi/inference/test_engine.py
- autocode/core/ → tests/autocode/core/test_core_integration.py

Tests fallando:
- tests/vidi/storyboard/test_processor.py

Tests huérfanos (código eliminado):
- tests/old_module/test_removed.py (archivo old_module/removed.py ya no existe)

Total: 4 tests requieren atención
```

**Casos de Uso Comunes**:
1. **Pre-commit**: Verificar que nuevo código tenga tests
2. **Code Coverage**: Mantener cobertura de tests adecuada
3. **Refactoring**: Identificar tests huérfanos después de refactoring
4. **CI/CD**: Validar tests en pipelines automáticos
5. **Code Review**: Verificar que PRs incluyan tests apropiados

## 🔧 Implementación

### Entry Point Principal

```python
def main():
    """Main CLI entry point."""
    parser = create_parser()
    args = parser.parse_args()
    
    # Default to check-docs for backwards compatibility
    if not args.command:
        args.command = "check-docs"
    
    # Route to appropriate command handler
    if args.command == "check-docs":
        exit_code = check_docs_command(args)
    elif args.command == "git-changes":
        exit_code = git_changes_command(args)
    elif args.command == "daemon":
        exit_code = daemon_command(args)
    elif args.command == "opencode":
        exit_code = opencode_command(args)
    elif args.command == "count-tokens":
        exit_code = count_tokens_command(args)
    else:
        parser.print_help()
        exit_code = 1
    
    sys.exit(exit_code)
```

### Configuration Loading

```python
def load_config(project_root: Path) -> AutocodeConfig:
    """Load configuration from autocode_config.yml.
    
    Args:
        project_root: Project root directory
        
    Returns:
        Loaded configuration with defaults
    """
    config_file = project_root / "autocode_config.yml"
    
    if not config_file.exists():
        # Return default configuration if file doesn't exist
        return AutocodeConfig()
    
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            config_data = yaml.safe_load(f)
        
        if not config_data:
            return AutocodeConfig()
        
        # Parse configuration with Pydantic
        return AutocodeConfig(**config_data)
        
    except Exception as e:
        print(f"⚠️  Warning: Error loading config from {config_file}: {e}")
        print("   Using default configuration")
        return AutocodeConfig()
```

### Parser Configuration

```python
def create_parser() -> argparse.ArgumentParser:
    """Create command line argument parser."""
    parser = argparse.ArgumentParser(
        prog="autocode",
        description="Automated code quality and development tools"
    )
    
    # Add subcommands
    subparsers = parser.add_subparsers(
        dest="command",
        help="Available commands"
    )
    
    # check-docs subcommand
    check_docs_parser = subparsers.add_parser(
        "check-docs",
        help="Check if documentation is up to date"
    )
    
    # git-changes subcommand
    git_changes_parser = subparsers.add_parser(
        "git-changes", 
        help="Analyze git changes for commit message generation"
    )
    git_changes_parser.add_argument(
        "--output", "-o",
        type=str,
        help="Output JSON file path (default: git_changes.json)"
    )
    git_changes_parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Show detailed diff information"
    )
    
    return parser
```

### Command Handlers

#### `check_docs_command(args) -> int`

**Implementación**:
```python
def check_docs_command(args) -> int:
    """Handle check-docs command."""
    # Get project root (current working directory)
    project_root = Path.cwd()
    
    # Load configuration
    config = load_config(project_root)
    
    # Initialize checker
    checker = DocChecker(project_root)
    
    # Check for outdated documentation
    outdated_results = checker.get_outdated_docs()
    
    # Format and display results
    output = checker.format_results(outdated_results)
    print(output)
    
    # Generate documentation index if docs are up to date and config allows it
    if not outdated_results and config.doc_index.enabled and config.doc_index.auto_generate:
        try:
            # Initialize doc indexer with CLI override if provided
            indexer = DocIndexer(project_root, config.doc_index, args.doc_index_output)
            
            # Generate the index
            index_path = indexer.generate_index()
            
            # Show success message
            relative_path = index_path.relative_to(project_root)
            print(f"📋 Documentation index generated: {relative_path}")
            
        except Exception as e:
            print(f"⚠️  Warning: Failed to generate documentation index: {e}")
            # Don't fail the command for index generation issues
    
    # Return appropriate exit code
    return 1 if outdated_results else 0
```

**Flujo de Ejecución**:
1. Obtiene directorio actual como project root
2. Carga configuración desde autocode_config.yml
3. Inicializa DocChecker
4. Obtiene lista de documentación desactualizada
5. Formatea y muestra resultados
6. Si no hay documentación pendiente, genera índice automáticamente (si está configurado)
7. Retorna código de salida apropiado

#### `git_changes_command(args) -> int`

**Implementación**:
```python
def git_changes_command(args) -> int:
    """Handle git-changes command."""
    # Get project root (current working directory)
    project_root = Path.cwd()
    
    # Initialize git analyzer  
    analyzer = GitAnalyzer(project_root)
    
    try:
        # Determine output file
        if args.output:
            output_file = Path(args.output)
        else:
            output_file = project_root / "git_changes.json"
        
        # Analyze changes and save to file
        changes_data = analyzer.save_changes_to_file(output_file)
        
        # Display summary
        # [Summary display logic...]
        
        # Show verbose output if requested
        if args.verbose:
            # [Verbose output logic...]
        
        return 0
        
    except Exception as e:
        print(f"❌ Error analyzing git changes: {e}")
        return 1
```

#### `daemon_command(args) -> int`

**Implementación**:
```python
def daemon_command(args) -> int:
    """Handle daemon command."""
    try:
        import uvicorn
        from .api.server import app
        
        print("🚀 Starting Autocode Monitoring Daemon")
        print(f"   📡 API Server: http://{args.host}:{args.port}")
        print(f"   🌐 Web Interface: http://{args.host}:{args.port}")
        print("   📊 Dashboard will auto-refresh every 5 seconds")
        print("   🔄 Checks run automatically per configuration")
        print("\n   Press Ctrl+C to stop the daemon")
        print("-" * 50)
        
        # Run the FastAPI application with uvicorn
        uvicorn.run(
            app,
            host=args.host,
            port=args.port,
            log_level="info" if args.verbose else "warning",
            access_log=args.verbose
        )
        
        return 0
        
    except KeyboardInterrupt:
        print("\n🛑 Daemon stopped by user")
        return 0
    except ImportError as e:
        print(f"❌ Error: Missing dependency for daemon mode: {e}")
        print("   Please ensure FastAPI and uvicorn are installed")
        return 1
    except Exception as e:
        print(f"❌ Error starting daemon: {e}")
        return 1
```

**Flujo de Ejecución**:
1. Importa dependencias necesarias (uvicorn, FastAPI app desde autocode.api.server)
2. Configura y muestra información del servidor
3. Inicia servidor FastAPI en el host y puerto especificados con configuración de logging
4. Maneja interrupciones de teclado y errores apropiadamente
5. Retorna código de salida apropiado

## 💡 Patrones de Uso

### Uso Básico en Desarrollo

```bash
# Verificar documentación antes de commit
uv run -m autocode.cli check-docs
if [ $? -eq 0 ]; then
    echo "✅ Documentation is up to date"
else
    echo "❌ Please update documentation before committing"
    exit 1
fi

# Analizar cambios para commit
uv run -m autocode.cli git-changes --verbose
# Review git_changes.json for commit message ideas
```

### Integración en Pre-commit Hook

```bash
#!/bin/bash
# .git/hooks/pre-commit

echo "🔍 Checking documentation status..."
uv run -m autocode.cli check-docs

if [ $? -ne 0 ]; then
    echo "❌ Documentation is outdated. Please update before committing."
    echo "💡 Hint: Check which files need documentation updates above."
    exit 1
fi

echo "✅ Documentation check passed"
```

### Uso en CI/CD Pipeline

```yaml
# GitHub Actions example
- name: Check Documentation
  run: |
    uv run -m autocode.cli check-docs
    if [ $? -ne 0 ]; then
      echo "::error::Documentation is outdated"
      exit 1
    fi

- name: Analyze Changes
  run: |
    uv run -m autocode.cli git-changes --output ci_changes.json
    
- name: Upload Analysis
  uses: actions/upload-artifact@v3
  with:
    name: git-analysis
    path: ci_changes.json
```

### Scripting y Automatización

```python
#!/usr/bin/env python3
"""Automated project health check"""

import subprocess
import sys
from pathlib import Path

def run_autocode_check():
    """Run documentation check and return status"""
    try:
        result = subprocess.run(
            ["uv", "run", "-m", "autocode.cli", "check-docs"],
            cwd=Path.cwd(),
            capture_output=True,
            text=True
        )
        
        print(result.stdout)
        if result.stderr:
            print(result.stderr, file=sys.stderr)
        
        return result.returncode == 0
        
    except subprocess.CalledProcessError as e:
        print(f"Error running autocode: {e}")
        return False

def analyze_git_changes():
    """Analyze git changes for insights"""
    try:
        subprocess.run(
            ["uv", "run", "-m", "autocode.cli", "git-changes", "--verbose"],
            cwd=Path.cwd(),
            check=True
        )
        
        # Process git_changes.json if needed
        changes_file = Path("git_changes.json")
        if changes_file.exists():
            print(f"📄 Git analysis saved to {changes_file}")
            
    except subprocess.CalledProcessError as e:
        print(f"Error analyzing git changes: {e}")

if __name__ == "__main__":
    print("🔍 Running project health check...")
    
    docs_ok = run_autocode_check()
    if docs_ok:
        print("✅ Documentation is up to date")
    else:
        print("❌ Documentation needs attention")
    
    print("\n📊 Analyzing recent changes...")
    analyze_git_changes()
    
    sys.exit(0 if docs_ok else 1)
```

## ⚠️ Consideraciones

### Limitaciones
- **Working Directory**: Siempre usa el directorio actual como project root
- **Git Dependency**: `git-changes` requiere repositorio git válido
- **File System Access**: Requiere permisos de lectura/escritura en directorio del proyecto

### Mejores Prácticas
- **Ejecutar desde Project Root**: Siempre ejecutar desde el directorio raíz del proyecto
- **Check Exit Codes**: Siempre verificar códigos de salida en scripts
- **Handle Errors**: Manejar apropiadamente errores en automatización

### Casos Especiales
- **Empty Repository**: `git-changes` funciona con repositorios vacíos
- **No Documentation**: `check-docs` reporta todos los archivos como faltantes si no hay docs/
- **Permission Issues**: Fallos silenciosos si no hay permisos de escritura

## 🧪 Testing

### Test Manual Básico

```bash
# Test check-docs
uv run -m autocode.cli check-docs
echo "Exit code: $?"

# Test git-changes (sin cambios)
uv run -m autocode.cli git-changes
ls -la git_changes.json

# Test git-changes (con cambios)
echo "test" > test_file.txt
git add test_file.txt
uv run -m autocode.cli git-changes --verbose
rm test_file.txt
git reset HEAD test_file.txt
```

### Validación de Argumentos

```bash
# Test argumentos inválidos
uv run -m autocode.cli invalid-command  # Should show help
uv run -m autocode.cli git-changes --invalid-flag  # Should error

# Test help
uv run -m autocode.cli --help
uv run -m autocode.cli check-docs --help
uv run -m autocode.cli git-changes --help
```

### Test de Integración

```python
import subprocess
import tempfile
from pathlib import Path

def test_cli_integration():
    """Test CLI in temporary project directory"""
    with tempfile.TemporaryDirectory() as tmpdir:
        project_dir = Path(tmpdir)
        
        # Initialize git repo
        subprocess.run(["git", "init"], cwd=project_dir)
        
        # Create minimal Python project
        (project_dir / "test_module").mkdir()
        (project_dir / "test_module" / "test.py").write_text("# Test file")
        
        # Test check-docs
        result = subprocess.run(
            ["uv", "run", "-m", "autocode.cli", "check-docs"],
            cwd=project_dir,
            capture_output=True,
            text=True
        )
        
        # Should find missing documentation
        assert result.returncode == 1
        assert "sin documentación" in result.stdout
        
        print("✅ CLI integration test passed")

if __name__ == "__main__":
    test_cli_integration()
```

## 🔄 Flujo de Datos

### Entrada
- **Command Line Arguments**: Comando y opciones especificadas por usuario
- **Working Directory**: Directorio desde donde se ejecuta el comando
- **File System State**: Estado actual de archivos de código y documentación
- **Git Repository State**: Estado del repositorio git (para git-changes)

### Procesamiento
1. **Argument Parsing**: Validación y routing de comandos
2. **Component Initialization**: Creación de DocChecker o GitAnalyzer
3. **Business Logic**: Ejecución de lógica específica del comando
4. **Output Formatting**: Formateo de resultados para display

### Salida
- **Console Output**: Información formateada para usuario
- **Exit Codes**: 0 para éxito, 1 para problemas encontrados
- **File Output**: Archivos JSON con datos estructurados (git-changes)
- **Error Messages**: Mensajes descriptivos para debugging

## 🚀 Extensibilidad

### Añadir Nuevos Comandos

```python
# En create_parser()
validate_parser = subparsers.add_parser(
    "validate-code",
    help="Validate code quality"
)
validate_parser.add_argument("--strict", action="store_true")

# En main()
elif args.command == "validate-code":
    exit_code = validate_code_command(args)

# Nuevo handler
def validate_code_command(args) -> int:
    """Handle validate-code command."""
    # Implementation
    return 0
```

### Añadir Opciones Globales

```python
# En create_parser()
parser.add_argument(
    "--config",
    type=str,
    help="Configuration file path"
)

# Uso en handlers
def check_docs_command(args) -> int:
    if args.config:
        # Load configuration
        pass
    # Rest of implementation
```

### Personalizar Output

```python
# Añadir formato JSON a check-docs
check_docs_parser.add_argument(
    "--format",
    choices=["text", "json"],
    default="text",
    help="Output format"
)

# En check_docs_command
if args.format == "json":
    output = json.dumps({
        "outdated_docs": [
            {"file": str(result.doc_file), "status": result.status}
            for result in outdated_results
        ]
    }, indent=2)
else:
    output = checker.format_results(outdated_results)
