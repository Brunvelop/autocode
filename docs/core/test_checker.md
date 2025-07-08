# TestChecker - Verificador de Tests para Proyecto Modular

## 🎯 Propósito

TestChecker es el componente responsable de verificar el estado de los tests en el proyecto Vidi siguiendo una estructura modular. Su responsabilidad principal es detectar tests faltantes, validar tests existentes, y identificar tests huérfanos que ya no corresponden a código existente. Mapea automáticamente archivos de código a sus tests correspondientes pero no los crea, proporcionando información para que los desarrolladores mantengan una cobertura de tests adecuada.

## 🏗️ Arquitectura

```mermaid
graph TB
    subgraph "TestChecker Architecture"
        TC[TestChecker<br/>Main Controller]
        
        subgraph "Discovery"
            FCD[find_code_directories<br/>Auto-discover Code Dirs]
            GPF[get_all_python_files<br/>Find Python Files]
            GCD[get_all_code_directories_with_subdirs<br/>Directory Mapping]
        end
        
        subgraph "Mapping"
            MCFUT[map_code_file_to_unit_test<br/>File → Unit Test]
            MDIT[map_directory_to_integration_test<br/>Dir → Integration Test]
            MTCF[map_test_to_code_file<br/>Test → Code (Reverse)]
        end
        
        subgraph "Validation"
            CAT[check_all_tests<br/>Comprehensive Check]
            ET[execute_tests<br/>Run pytest]
            PPF[parse_pytest_failures<br/>Parse Results]
            FOT[find_orphaned_tests<br/>Detect Orphans]
        end
        
        subgraph "Test Types"
            UT[Unit Tests<br/>test_filename.py]
            IT[Integration Tests<br/>test_module_integration.py]
            OT[Orphaned Tests<br/>No matching code]
        end
        
        subgraph "Test Status"
            MISS[Missing Tests<br/>No test file found]
            FAIL[Failing Tests<br/>Tests exist but fail]
            PASS[Passing Tests<br/>Tests exist and pass]
            ORPH[Orphaned Tests<br/>Code no longer exists]
        end
    end
    
    TC --> FCD
    TC --> GPF
    TC --> GCD
    
    FCD --> MCFUT
    GPF --> MCFUT
    GCD --> MDIT
    
    MCFUT --> CAT
    MDIT --> CAT
    MTCF --> FOT
    
    CAT --> ET
    ET --> PPF
    CAT --> FOT
    
    CAT --> UT
    CAT --> IT
    FOT --> OT
    
    UT --> MISS
    UT --> FAIL
    UT --> PASS
    IT --> MISS
    IT --> FAIL
    IT --> PASS
    OT --> ORPH
    
    classDef controller fill:#e1f5fe
    classDef discovery fill:#f3e5f5
    classDef mapping fill:#e8f5e8
    classDef validation fill:#fff3e0
    classDef types fill:#f1f8e9
    classDef status fill:#fce4ec
    
    class TC controller
    class FCD,GPF,GCD discovery
    class MCFUT,MDIT,MTCF mapping
    class CAT,ET,PPF,FOT validation
    class UT,IT,OT types
    class MISS,FAIL,PASS,ORPH status
```

## 📋 Responsabilidades

### Detección y Mapeo
- **Auto-discovery de código**: Encuentra automáticamente directorios con código Python
- **Mapeo de archivos**: Asocia cada archivo de código con su test unitario esperado
- **Mapeo de directorios**: Asocia cada directorio con su test de integración esperado
- **Mapeo inverso**: Identifica qué código corresponde a cada test existente

### Validación de Tests
- **Detección de tests faltantes**: Identifica código sin tests correspondientes
- **Ejecución de tests**: Ejecuta pytest para validar tests existentes
- **Análisis de fallos**: Parsea resultados de pytest para identificar tests que fallan
- **Detección de huérfanos**: Encuentra tests que ya no corresponden a código existente

### Estructura Modular
- **Tests unitarios**: Un test por cada archivo de código (`test_filename.py`)
- **Tests de integración**: Un test por cada módulo/directorio (`test_module_integration.py`)
- **Exclusión de __init__.py**: No requiere tests para archivos de inicialización
- **Estructura espejo**: Los tests replican la estructura de directorios del código

## 🔗 Dependencias

### Internas
- `pathlib`: Manipulación de rutas y archivos
- `typing`: Type hints para mejor desarrollo
- `subprocess`: Ejecución de pytest
- `sys`: Acceso al intérprete Python

### Externas
- `pytest`: Framework de testing requerido para ejecución de tests

## 📊 Interfaces Públicas

### Clase Principal: TestChecker

#### Constructor
```python
TestChecker(project_root: Path = None, config: Optional['TestConfig'] = None)
```

#### Métodos de Discovery
```python
def find_code_directories(self) -> List[Path]:
    """Auto-discover directories containing Python code."""

def get_all_python_files(self) -> List[Path]:
    """Get all Python files excluding __init__.py."""

def get_all_code_directories_with_subdirs(self) -> Set[Path]:
    """Get all directories that contain Python code."""
```

#### Métodos de Mapeo
```python
def map_code_file_to_unit_test(self, code_file: Path) -> Path:
    """Map code file to unit test: engine.py → test_engine.py"""

def map_directory_to_integration_test(self, code_dir: Path) -> Path:
    """Map directory to integration test: inference/ → test_inference_integration.py"""

def map_test_to_code_file(self, test_file: Path) -> Path:
    """Reverse mapping: test file → code file/directory"""
```

#### Métodos de Validación
```python
def check_all_tests(self) -> List[TestStatus]:
    """Comprehensive test status check."""

def execute_tests(self) -> tuple[int, str, str]:
    """Execute pytest and return results."""

def find_orphaned_tests(self) -> List[TestStatus]:
    """Find tests without corresponding code."""

def get_missing_and_failing_tests(self) -> List[TestStatus]:
    """Get tests that need attention."""
```

#### Métodos de Formato
```python
def format_results(self, results: List[TestStatus]) -> str:
    """Format results for human-readable display."""
```

### Estructura de Datos: TestStatus

```python
class TestStatus(NamedTuple):
    """Status of a code-test pair."""
    code_file: Path        # Archivo de código correspondiente
    test_file: Path        # Archivo de test esperado/existente
    status: str           # 'missing', 'failing', 'passing', 'orphaned'
    test_type: str        # 'unit', 'integration'
```

## 🔧 Configuración

### Estructura de Directorios Esperada
```
proyecto/
├── vidi/                           # Código fuente
│   ├── inference/
│   │   ├── __init__.py            # No requiere test
│   │   ├── engine.py              # Requiere tests/vidi/inference/test_engine.py
│   │   └── models/
│   │       ├── __init__.py        # No requiere test
│   │       └── registry.py        # Requiere tests/vidi/inference/models/test_registry.py
│   └── storyboard/
│       ├── __init__.py            # No requiere test
│       └── processor.py           # Requiere tests/vidi/storyboard/test_processor.py
└── tests/                         # Directorio de tests
    ├── vidi/
    │   ├── inference/
    │   │   ├── test_engine.py                      # Test unitario
    │   │   ├── test_inference_integration.py       # Test de integración
    │   │   └── models/
    │   │       ├── test_registry.py                # Test unitario
    │   │       └── test_models_integration.py      # Test de integración
    │   └── storyboard/
    │       ├── test_processor.py                   # Test unitario
    │       └── test_storyboard_integration.py      # Test de integración
    └── autocode/                                   # Tests para herramientas autocode
        └── core/
            ├── test_doc_checker.py
            └── test_core_integration.py
```

### Reglas de Mapeo

#### Tests Unitarios
- **Patrón**: `code_file.py` → `test_code_file.py`
- **Ubicación**: Réplica exacta de la estructura de directorios en `tests/`
- **Ejemplo**: `vidi/inference/engine.py` → `tests/vidi/inference/test_engine.py`

#### Tests de Integración
- **Patrón**: `directory/` → `test_directory_integration.py`
- **Ubicación**: Dentro del directorio correspondiente en `tests/`
- **Ejemplo**: `vidi/inference/` → `tests/vidi/inference/test_inference_integration.py`

#### Exclusiones
- **__init__.py**: Nunca requiere tests (archivos de inicialización)
- **Directorios sin .py**: Directorios que solo contienen subdirectorios
- **Archivos de configuración**: .json, .yaml, .toml, etc.

## 💡 Patrones de Uso

### Verificación Básica
```python
from autocode.core.test_checker import TestChecker

# Inicializar checker
checker = TestChecker()

# Verificar todos los tests
results = checker.check_all_tests()

# Mostrar resultados
output = checker.format_results(results)
print(output)
```

### Verificación de Tests Faltantes
```python
# Solo obtener tests que necesitan atención
issues = checker.get_missing_and_failing_tests()

for issue in issues:
    print(f"{issue.status}: {issue.code_file} → {issue.test_file}")
```

### Integración con CLI
```python
def check_tests_command(args) -> int:
    """Handle check-tests command."""
    checker = TestChecker()
    test_issues = checker.get_missing_and_failing_tests()
    
    if test_issues:
        output = checker.format_results(test_issues)
        print(output)
        return 1  # Issues found
    else:
        print("✅ All tests exist and are passing!")
        return 0  # All good
```

### Análisis de Cobertura
```python
# Obtener estadísticas de cobertura
all_results = checker.check_all_tests()

total_tests = len(all_results)
missing = len([r for r in all_results if r.status == 'missing'])
failing = len([r for r in all_results if r.status == 'failing'])
passing = len([r for r in all_results if r.status == 'passing'])

coverage = (passing / total_tests * 100) if total_tests > 0 else 0
print(f"Test Coverage: {coverage:.1f}% ({passing}/{total_tests})")
```

## ⚠️ Consideraciones

### Limitaciones
- **Python Específico**: Diseñado específicamente para proyectos Python
- **Estructura Fija**: Requiere estructura de directorios predecible
- **pytest Dependency**: Requiere pytest instalado para ejecución de tests
- **File System Based**: Depende de timestamps del sistema de archivos

### Casos Especiales
- **Tests Complejos**: No detecta dependencias complejas entre tests
- **Tests Parametrizados**: Considera el archivo completo, no tests individuales
- **Tests Async**: Funciona con tests asyncio pero no los detecta específicamente
- **Mock Dependencies**: No valida si los mocks están actualizados

### Consideraciones de Rendimiento
- **Lazy Execution**: Solo ejecuta pytest cuando hay tests existentes
- **Timeout Protection**: Timeout de 5 minutos para evitar tests colgados
- **Memory Efficient**: No carga contenido de archivos en memoria
- **Incremental**: Puede verificar archivos específicos (futuro)

### Integración con Otros Sistemas
- **CI/CD**: Exit codes apropiados para integración con pipelines
- **IDE Integration**: Formato compatible con IDEs que parsean pytest
- **Autocode Daemon**: Integración con sistema de monitoreo continuo
- **Git Hooks**: Uso en pre-commit hooks para validación automática

## 🧪 Testing

### Verificar Funcionamiento Básico
```python
# Test de auto-discovery
checker = TestChecker()
code_dirs = checker.find_code_directories()
assert len(code_dirs) > 0, "Should find code directories"

# Test de mapeo
python_files = checker.get_all_python_files()
for code_file in python_files[:5]:  # Test first 5
    test_file = checker.map_code_file_to_unit_test(code_file)
    assert test_file.name.startswith('test_'), "Test file should start with test_"
```

### Validar Estructura de Tests
```bash
# CLI testing
uv run -m autocode.cli check-tests
echo $?  # Should be 0 if all tests are present and passing

# Create a missing test file
mkdir -p tests/vidi/inference
echo "def test_placeholder(): pass" > tests/vidi/inference/test_engine.py

# Run again
uv run -m autocode.cli check-tests
```

### Verificar Ejecución de Tests
```python
# Test execution
exit_code, stdout, stderr = checker.execute_tests()
assert exit_code == 0, f"Tests should pass: {stderr}"
assert "PASSED" in stdout or "collected 0 items" in stdout
```

## 🔄 Flujo de Datos

### Entrada
1. **Project Root**: Directorio base del proyecto
2. **Code Structure**: Estructura de directorios con código Python
3. **Existing Tests**: Tests ya presentes en directorio tests/
4. **pytest Configuration**: Configuración de pytest (pytest.ini, etc.)

### Procesamiento
1. **Code Discovery**: Encuentra todos los archivos Python relevantes
2. **Structure Mapping**: Mapea código a tests esperados
3. **Existence Check**: Verifica si tests existen
4. **Test Execution**: Ejecuta tests existentes con pytest
5. **Result Parsing**: Analiza output de pytest para detectar fallos
6. **Status Assignment**: Asigna estado a cada par código-test

### Salida
1. **TestStatus Objects**: Lista estructurada de estados
2. **Formatted Output**: Texto formateado para humanos
3. **Exit Codes**: 0 para éxito, 1 para issues encontrados
4. **Integration Data**: Datos para integración con daemon y CLI

## 💡 Casos de Uso Típicos

### Development Workflow
```bash
# Verificar tests antes de commit
uv run -m autocode.cli check-tests

# Si hay tests faltantes, crear estructura básica
mkdir -p tests/vidi/new_module
echo "# Tests for new_module" > tests/vidi/new_module/test_new_file.py
```

### Continuous Integration
```yaml
# .github/workflows/tests.yml
- name: Check test coverage
  run: uv run -m autocode.cli check-tests
  
- name: Run tests
  run: uv run -m pytest tests/ -v
```

### Code Review Process
```python
# En script de revisión
checker = TestChecker()
missing_tests = [r for r in checker.check_all_tests() if r.status == 'missing']

if missing_tests:
    print("❌ Code review failed: Missing tests detected")
    for test in missing_tests:
        print(f"   {test.code_file} needs {test.test_file}")
    sys.exit(1)
```

### Refactoring Support
```python
# Después de refactoring, verificar tests huérfanos
orphaned = checker.find_orphaned_tests()
if orphaned:
    print("🧹 Cleanup needed: Found orphaned tests")
    for test in orphaned:
        print(f"   Consider removing {test.test_file}")
```

## 🚀 Extensiones Futuras

### Soporte Multi-lenguaje
```python
class EnhancedTestChecker(TestChecker):
    def get_all_source_files(self):
        """Support for .js, .ts, .go, etc."""
        # Extend beyond Python
```

### Integración con Coverage
```python
def get_coverage_report(self):
    """Integrate with pytest-cov for coverage analysis."""
    # Add coverage analysis
```

### Tests Inteligentes
```python
def suggest_test_structure(self, code_file: Path):
    """Analyze code and suggest test structure."""
    # AI-powered test suggestions
```

### Performance Optimization
```python
def incremental_check(self, changed_files: List[Path]):
    """Only check tests for changed files."""
    # Optimize for large codebases
