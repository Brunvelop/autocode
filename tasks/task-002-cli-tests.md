# Task 002: Crear Tests Auto-Updatables para CLI con Typer

## Contexto del Proyecto
Este proyecto autocode utiliza un CLI basado en Typer para manejar comandos como check-docs, git-changes, daemon, etc. El objetivo de esta tarea es crear tests que se adapten automáticamente a los cambios en el CLI usando la introspección de Typer, minimizando el mantenimiento manual.

## Estado Actual del Proyecto

### Estructura del CLI con Typer
El CLI debería estar estructurado con Typer así:

```python
# autocode/cli.py
import typer
from typing import Optional, List
from pathlib import Path

app = typer.Typer(help="Automated code quality and development tools")

@app.command("check-docs")
def check_docs(
    doc_index_output: Optional[str] = typer.Option(None, "--doc-index-output", help="Override output path for documentation index")
) -> int:
    """Check if documentation is up to date"""
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
    project_root = Path.cwd()
    config = load_config()
    checker = TestChecker(project_root, config.tests)
    test_issues = checker.get_missing_and_failing_tests()
    output = checker.format_results(test_issues)
    print(output)
    return 1 if test_issues else 0

@app.command("git-changes")
def git_changes(
    output: Optional[str] = typer.Option(None, "-o", "--output", help="Output JSON file path"),
    verbose: bool = typer.Option(False, "-v", "--verbose", help="Show detailed diff information")
) -> int:
    """Analyze git changes for commit message generation"""
    project_root = Path.cwd()
    analyzer = GitAnalyzer(project_root)
    try:
        output_file = Path(output) if output else project_root / "git_changes.json"
        changes_data = analyzer.save_changes_to_file(output_file)
        print(f"📊 Repository Status: {changes_data['repository_status']}")
        return 0
    except Exception as e:
        print(f"❌ Error analyzing git changes: {e}")
        return 1

@app.command("daemon")
def daemon(
    host: str = typer.Option("127.0.0.1", "--host", help="Host to bind to"),
    port: int = typer.Option(8080, "--port", help="Port to bind to"),
    verbose: bool = typer.Option(False, "-v", "--verbose", help="Enable verbose logging")
) -> int:
    """Start the autocode monitoring daemon with web interface"""
    try:
        import uvicorn
        from .api.server import app as fastapi_app
        print("🚀 Starting Autocode Monitoring Daemon")
        uvicorn.run(fastapi_app, host=host, port=port, log_level="info" if verbose else "warning")
        return 0
    except KeyboardInterrupt:
        print("\n🛑 Daemon stopped by user")
        return 0
    except Exception as e:
        print(f"❌ Error starting daemon: {e}")
        return 1

def main():
    app()

if __name__ == "__main__":
    main()
```

### Configuración del Proyecto
- Usa `uv` para gestión de dependencias
- Estructura de directorios: `autocode/` como paquete principal
- Tests organizados en directorio `tests/`

### Módulos Core del Proyecto
```python
# Imports principales del CLI
from .core.docs import DocChecker, DocIndexer
from .core.test import TestChecker
from .core.git import GitAnalyzer
from .core.ai import OpenCodeExecutor, validate_opencode_setup
from .core.design import CodeToDesign
from .api.models import AutocodeConfig
```

## Objetivo de los Tests Auto-Updatables
Crear tests que usen la introspección de Typer para:
1. **Detectar automáticamente comandos**: Usando `app.registered_commands`
2. **Validar parámetros dinámicamente**: Inspeccionando `command.params`
3. **Probar help automáticamente**: Verificando outputs de `--help`
4. **Adaptar a cambios**: Tests que se ajusten si se añaden/modifican comandos

## Dependencias Necesarias

### Instalar Dependencias de Testing
```bash
# Instalar pytest y dependencias de testing
uv add --dev pytest pytest-mock pytest-cov

# Typer incluye typer.testing para CliRunner
# No necesita instalación adicional
```

## Instrucciones Paso a Paso

### 1. Crear Estructura de Tests
```bash
# Crear directorio tests si no existe
mkdir -p tests
touch tests/__init__.py
```

### 2. Crear test_cli.py Base
```python
# tests/test_cli.py
import pytest
from typer.testing import CliRunner
from unittest.mock import patch, MagicMock
from pathlib import Path

# Import the CLI app
from autocode.cli import app

# Create a test runner
runner = CliRunner()

@pytest.fixture
def mock_project_root(tmp_path):
    """Create a temporary project root for testing."""
    return tmp_path

@pytest.fixture
def commands():
    """Get all registered commands dynamically."""
    return {cmd.name: cmd for cmd in app.registered_commands}
```

### 3. Tests Dinámicos para Comandos
```python
class TestCLICommands:
    """Test CLI commands using dynamic introspection."""
    
    def test_all_commands_have_help(self, commands):
        """Test that all commands respond to --help."""
        for cmd_name in commands.keys():
            result = runner.invoke(app, [cmd_name, "--help"])
            assert result.exit_code == 0
            assert "Usage:" in result.stdout
            assert cmd_name in result.stdout
    
    @pytest.mark.parametrize("cmd_name", lambda: list(app.registered_commands.keys()))
    def test_command_help_contains_description(self, cmd_name):
        """Test that each command's help contains its description."""
        result = runner.invoke(app, [cmd_name, "--help"])
        assert result.exit_code == 0
        
        # Get the command object
        command = next(cmd for cmd in app.registered_commands if cmd.name == cmd_name)
        if command.help:
            assert command.help in result.stdout
    
    def test_command_parameters_validation(self, commands):
        """Test that command parameters are properly defined."""
        for cmd_name, command in commands.items():
            # Verify command has expected structure
            assert hasattr(command, 'params')
            assert hasattr(command, 'callback')
            
            # Test help shows parameters
            result = runner.invoke(app, [cmd_name, "--help"])
            assert result.exit_code == 0
            
            # Check that parameters with help text show up
            for param in command.params:
                if hasattr(param, 'help') and param.help:
                    # Parameter help should appear in --help output
                    pass  # We'll verify this exists in help output
```

### 4. Tests Específicos con Mocking
```python
class TestSpecificCommands:
    """Test specific command functionality with mocking."""
    
    @patch('autocode.cli.DocChecker')
    @patch('autocode.cli.load_config')
    def test_check_docs_success(self, mock_load_config, mock_doc_checker):
        """Test check-docs command with successful outcome."""
        # Setup mocks
        mock_config = MagicMock()
        mock_load_config.return_value = mock_config
        
        mock_checker_instance = MagicMock()
        mock_checker_instance.get_outdated_docs.return_value = []  # No outdated docs
        mock_checker_instance.format_results.return_value = "✅ All docs up to date"
        mock_doc_checker.return_value = mock_checker_instance
        
        # Run command
        result = runner.invoke(app, ["check-docs"])
        
        # Verify
        assert result.exit_code == 0
        assert "✅" in result.stdout
        mock_doc_checker.assert_called_once()
        mock_checker_instance.get_outdated_docs.assert_called_once()
    
    @patch('autocode.cli.DocChecker')
    @patch('autocode.cli.load_config')
    def test_check_docs_outdated(self, mock_load_config, mock_doc_checker):
        """Test check-docs command with outdated docs."""
        # Setup mocks
        mock_config = MagicMock()
        mock_load_config.return_value = mock_config
        
        mock_checker_instance = MagicMock()
        mock_checker_instance.get_outdated_docs.return_value = ["some_file.py"]  # Has outdated docs
        mock_checker_instance.format_results.return_value = "❌ Outdated docs found"
        mock_doc_checker.return_value = mock_checker_instance
        
        # Run command
        result = runner.invoke(app, ["check-docs"])
        
        # Verify
        assert result.exit_code == 1  # Should return 1 for issues
        assert "❌" in result.stdout
    
    @patch('autocode.cli.GitAnalyzer')
    def test_git_changes_default_output(self, mock_git_analyzer):
        """Test git-changes command with default output file."""
        # Setup mock
        mock_analyzer_instance = MagicMock()
        mock_analyzer_instance.save_changes_to_file.return_value = {
            "repository_status": {"total_files": 5, "modified": 3}
        }
        mock_git_analyzer.return_value = mock_analyzer_instance
        
        # Run command
        result = runner.invoke(app, ["git-changes"])
        
        # Verify
        assert result.exit_code == 0
        assert "📊 Repository Status" in result.stdout
        mock_analyzer_instance.save_changes_to_file.assert_called_once()
    
    @patch('autocode.cli.GitAnalyzer')
    def test_git_changes_custom_output(self, mock_git_analyzer):
        """Test git-changes command with custom output file."""
        # Setup mock
        mock_analyzer_instance = MagicMock()
        mock_analyzer_instance.save_changes_to_file.return_value = {
            "repository_status": {"total_files": 5, "modified": 3}
        }
        mock_git_analyzer.return_value = mock_analyzer_instance
        
        # Run command
        result = runner.invoke(app, ["git-changes", "--output", "custom.json"])
        
        # Verify
        assert result.exit_code == 0
        # Check that custom output path was used
        call_args = mock_analyzer_instance.save_changes_to_file.call_args[0][0]
        assert str(call_args).endswith("custom.json")
```

### 5. Tests de Introspección Avanzada
```python
class TestCLIIntrospection:
    """Advanced tests using Typer introspection."""
    
    def test_cli_app_structure(self):
        """Test overall CLI application structure."""
        # Verify app is properly configured
        assert app.info.name is None or isinstance(app.info.name, str)
        assert len(app.registered_commands) >= 6  # Expected minimum commands
        
        # Verify all commands are callable
        for command in app.registered_commands:
            assert callable(command.callback)
    
    def test_command_signatures_consistency(self, commands):
        """Test that command signatures are consistent."""
        for cmd_name, command in commands.items():
            # All commands should return int (exit code)
            import inspect
            signature = inspect.signature(command.callback)
            
            # Check return annotation if present
            if signature.return_annotation != inspect.Signature.empty:
                assert signature.return_annotation == int
    
    def test_auto_discovery_of_new_commands(self):
        """Test that adding new commands is automatically detected."""
        # This test demonstrates auto-adaptation
        command_names = [cmd.name for cmd in app.registered_commands]
        
        # Core expected commands
        expected_commands = ["check-docs", "check-tests", "git-changes", "daemon"]
        
        for expected in expected_commands:
            assert expected in command_names
        
        # If new commands are added, they'll automatically be tested
        # by the parametrized tests above
    
    @pytest.mark.parametrize("cmd_name", lambda: [cmd.name for cmd in app.registered_commands])
    def test_command_error_handling(self, cmd_name):
        """Test that commands handle invalid arguments gracefully."""
        # Test with invalid flag
        result = runner.invoke(app, [cmd_name, "--invalid-flag"])
        
        # Should exit with error but not crash
        assert result.exit_code != 0
        assert ("No such option" in result.stdout or 
                "Unrecognized arguments" in result.stdout or
                "Usage:" in result.stdout)
```

### 6. Configuration para Coverage
```python
# pytest.ini o pyproject.toml
[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]
addopts = [
    "--cov=autocode",
    "--cov-report=html",
    "--cov-report=term-missing",
    "--cov-fail-under=80"
]
```

## Criterios de Verificación

### Comandos de Testing
```bash
# Ejecutar todos los tests
pytest tests/test_cli.py -v

# Con coverage
pytest tests/test_cli.py --cov=autocode.cli --cov-report=term-missing

# Solo tests de un comando específico
pytest tests/test_cli.py::TestSpecificCommands::test_check_docs_success -v
```

### Verificaciones Específicas
1. **Cobertura >80%**: Tests cubren la mayoría del código CLI
2. **Auto-adaptación**: Añadir un nuevo comando @app.command() hace que tests automáticamente lo incluyan
3. **Help consistency**: Todos los comandos responden correctamente a --help
4. **Error handling**: Comandos manejan argumentos inválidos apropiadamente
5. **Mocking correcto**: Tests no ejecutan lógica real (ej. no crean archivos reales)

### Test de Auto-Adaptación
Para verificar que los tests se adaptan automáticamente:

1. Añadir temporalmente un nuevo comando:
```python
@app.command("test-command")
def test_command(test_arg: str = typer.Option("default", help="Test argument")) -> int:
    """Test command for auto-adaptation."""
    print(f"Test: {test_arg}")
    return 0
```

2. Ejecutar tests - deberían pasar automáticamente incluyendo el nuevo comando
3. Remover el comando temporal

## Template de Commit Message
```
test(cli): add auto-updatable CLI tests with Typer introspection

- Created comprehensive test suite in tests/test_cli.py
- Implemented dynamic command discovery using app.registered_commands
- Added parametrized tests that auto-adapt to CLI changes
- Mocked external dependencies (DocChecker, GitAnalyzer, etc.)
- Achieved >80% code coverage with pytest-cov
- Tests automatically include new commands without manual updates
```
