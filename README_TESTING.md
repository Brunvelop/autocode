# Testing Guide for Autocode Interfaces

Este documento proporciona una guía completa para ejecutar y entender los tests del módulo `autocode/interfaces`. Los tests están diseñados siguiendo principios de buen código (SOLID, DRY, KISS) y pensando en la escalabilidad futura del proyecto.

## 🚀 Ejecución Rápida

```bash
# Ejecutar todos los tests con coverage
pytest

# Ejecutar tests específicos por módulo
pytest tests/interfaces/test_models.py
pytest tests/interfaces/test_registry.py
pytest tests/interfaces/test_api.py
pytest tests/interfaces/test_cli.py
pytest tests/interfaces/test_mcp.py

# Ejecutar tests de integración
pytest tests/test_integration.py
```

## 📁 Estructura de Tests

```
tests/
├── __init__.py
├── conftest.py                    # Fixtures globales y configuración
├── pytest.ini                    # Configuración de pytest
├── interfaces/
│   ├── __init__.py
│   ├── test_models.py            # Tests para Pydantic models
│   ├── test_registry.py          # Tests para función registry
│   ├── test_api.py               # Tests para FastAPI endpoints
│   ├── test_cli.py               # Tests para CLI con Click
│   └── test_mcp.py               # Tests para integración MCP
└── test_integration.py           # Tests de integración cross-module
```

### Principios de Organización

- **Mirroring Structure**: Los tests siguen la estructura del código fuente para facilitar la navegación
- **Separación de Responsabilidades**: Unit tests vs integration tests claramente separados
- **Isolation**: Cada test es independiente gracias a fixtures de cleanup
- **Mocks Inteligentes**: Se usan mocks para dependencias externas, preservando la lógica interna

## 🎯 Cobertura por Módulo

### `models.py` - Tests de Validación de Datos
- **ExplicitParam**: Validación de parámetros con types, defaults, required fields
- **FunctionInfo**: Metadata completa de funciones con arbitrary types
- **GenericOutput**: Responses estandarizadas con success/error handling
- **Edge Cases**: Valores inválidos, None defaults, tipos complejos

**Principio aplicado**: *Single Responsibility* - cada model tiene una responsabilidad clara.

### `registry.py` - Tests del Corazón del Sistema
- **Function Registration**: Decorator automático con inferencia de parámetros
- **Parameter Inference**: Extracción de types desde signatures y docstrings
- **Public API**: `get_function`, `get_function_info`, `get_parameters`, etc.
- **Error Handling**: RegistryError para casos no encontrados
- **Stats & Metrics**: Registry statistics para monitoring

**Principio aplicado**: *Open/Closed* - extensible para nuevas funciones sin modificar código existente.

### `api.py` - Tests de Endpoints Dinámicos
- **Dynamic Model Generation**: Pydantic models generados automáticamente
- **Request/Response Handling**: Formateo consistente de responses
- **Error Management**: HTTP status codes apropiados (400/500)
- **Endpoint Registration**: Generación automática de GET/POST routes
- **Integration**: TestClient para simulación de requests reales

**Principio aplicado**: *DRY* - generación automática elimina código repetitivo.

### `cli.py` - Tests de Interfaz de Línea de Comandos  
- **Dynamic Commands**: Comandos Click generados desde registry
- **Parameter Mapping**: Types Python → Click types automáticamente
- **Built-in Commands**: `list`, `serve-api`, `serve-mcp`, `serve`
- **Error Handling**: Graceful handling con Abort para user experience
- **Help System**: Documentación automática desde docstrings

**Principio aplicado**: *Interface Segregation* - comandos específicos para diferentes necesidades.

### `mcp.py` - Tests de Integración MCP
- **MCP Server Creation**: FastApiMCP integration seamless
- **App Modification**: Preservación de funcionalidad API original
- **Error Propagation**: RuntimeError con chaining para debugging
- **Logging**: Comprehensive logging para monitoring

**Principio aplicado**: *Dependency Inversion* - MCP como abstraction layer.

### `test_integration.py` - Tests End-to-End
- **Cross-Module Integration**: Registry ↔ API ↔ CLI ↔ MCP
- **Real-World Scenarios**: Simulación de code quality tools
- **Consistency Checks**: Mismo comportamiento across interfaces
- **Error Propagation**: Manejo de errores consistent entre módulos

## 🛠️ Configuración y Herramientas

### `pytest.ini` - Configuración Central
```ini
[tool:pytest]
testpaths = tests
addopts = 
    -v                              # Verbose output
    --tb=short                      # Short traceback format
    --cov=autocode                  # Coverage analysis
    --cov-report=term-missing       # Show missing lines
    --cov-report=html:htmlcov       # HTML report
    --cov-fail-under=80             # Minimum 80% coverage
```

### `conftest.py` - Fixtures Globales
- **cleanup_registry**: Auto-cleanup para isolation entre tests
- **sample_function/function_info**: Objetos reutilizables para testing
- **mock_uvicorn/fastapi_app**: Mocks para dependencias externas
- **populated_registry**: Registry con datos de test para integration
- **test clients**: FastAPI TestClient y Click CliRunner factories

## 📊 Comandos de Testing

### Comandos Básicos
```bash
# Tests completos con coverage
pytest

# Tests específicos por markers
pytest -m unit          # Solo unit tests
pytest -m integration   # Solo integration tests
pytest -m api          # Solo tests de API
pytest -m cli          # Solo tests de CLI

# Tests con output detallado
pytest -v -s

# Tests con coverage específico
pytest --cov=autocode.autocode.interfaces --cov-report=term-missing
```

### Debugging y Desarrollo
```bash
# Ejecutar test específico
pytest tests/interfaces/test_registry.py::TestGenerateFunctionInfo::test_generate_function_info_simple

# Tests con pdb debugger
pytest --pdb

# Tests paralelos (requiere pytest-xdist)
pytest -n auto

# Ver warnings completos
pytest --disable-warnings=false
```

### Coverage Analysis
```bash
# Generar reporte HTML
pytest --cov-report=html
open htmlcov/index.html

# Coverage con detalles por línea
pytest --cov-report=term-missing

# Coverage solo para módulos específicos
pytest --cov=autocode.autocode.interfaces.registry --cov-report=term
```

## 🎨 Principios de Testing Aplicados

### 1. **Test Early, Test Often** (Agile)
- Tests automatizados en cada commit
- Detección temprana de regressions
- CI/CD ready para deploys seguros

### 2. **SOLID Principles**
- **S**: Cada test verifica una responsabilidad específica
- **O**: Tests extensibles sin modificar existentes
- **L**: Mocks sustituyen dependencias sin romper contracts
- **I**: Interfaces específicas para diferentes tipos de tests
- **D**: Tests dependen de abstractions, no implementations

### 3. **DRY (Don't Repeat Yourself)**
- Fixtures reutilizables en `conftest.py`
- Parametrized tests para múltiples scenarios
- Helper functions para setup común

### 4. **KISS (Keep It Simple, Stupid)**
- Tests legibles como documentación
- Setup mínimo necesario por test
- Asserts claros y específicos

## 🚀 Beneficios para el Futuro

### Escalabilidad
- **Nuevas Funciones**: Añadir functions al registry → tests automáticos
- **Nuevos Interfaces**: Pattern establecido para CLI/API/MCP extensions  
- **CI/CD Integration**: GitHub Actions ready para automatic testing

### Mantenibilidad  
- **Refactoring Seguro**: High coverage previene regressions
- **Documentation**: Tests como living documentation del sistema
- **Onboarding**: Nuevos developers entienden el sistema via tests

### Calidad
- **Edge Cases**: Coverage de error scenarios y boundary conditions
- **Integration**: Cross-module testing asegura cohesión
- **Real-World**: Simulation de uso real (code quality tools)

## 🎯 Métricas de Calidad

### Coverage Targets
- **Minimum**: 80% coverage (enforced by pytest.ini)
- **Target**: 90%+ para módulos core (registry, api)
- **Integration**: 100% de paths críticos cubiertos

### Test Categories
- **Unit Tests**: ~70% del total (fast, isolated)
- **Integration Tests**: ~25% del total (cross-module)
- **End-to-End**: ~5% del total (realistic scenarios)

### Performance
- **Fast Tests**: <1s para unit tests individuales
- **Full Suite**: <30s para test suite completo
- **Parallel Execution**: Support para pytest-xdist

## 📝 Mejores Prácticas

### Escribir Nuevos Tests
1. **Seguir Naming Convention**: `test_function_name_scenario`
2. **Usar Fixtures**: Aprovechar fixtures existentes en `conftest.py`
3. **Mock External Dependencies**: No hacer real HTTP calls, file I/O
4. **Test Both Paths**: Happy path y error scenarios
5. **Clear Assertions**: Asserts específicos con mensajes claros

### Mantener Tests
1. **Update con Cambios**: Tests deben reflejar cambios en código
2. **Refactor Tests**: Eliminar duplicación, improve readability
3. **Monitor Coverage**: Aim for high coverage sin obsesión
4. **Review Tests**: Tests también necesitan code review

### Debugging Tests
1. **Use pytest -v**: Para output detallado
2. **Add print()**: Temporary debugging (remove afterwards)
3. **Use pdb**: `pytest --pdb` para interactive debugging
4. **Isolate Failing**: Run specific test para faster iteration

## 🤝 Contribuciones

Al agregar nuevas funciones a `autocode/interfaces`:

1. **Add Unit Tests**: Para la función específica
2. **Update Integration**: Si afecta cross-module behavior  
3. **Test Documentation**: Docstrings como parte del test
4. **Run Full Suite**: Asegurar no breaks en existing functionality
5. **Update Coverage**: Maintain o improve coverage metrics

Los tests están diseñados para **crecer con el proyecto**. Cada nueva función registrada automáticamente obtiene tests de API y CLI, y la infraestructura soporta expansion a nuevos tipos de interfaces sin modification major.

## 📞 Soporte

Para preguntas sobre testing:
1. **Revisar este documento** para patrones establecidos
2. **Examinar tests existentes** como ejemplos
3. **Usar fixtures globales** cuando sea posible
4. **Seguir principios SOLID** en test design

Los tests son **living documentation** - mantienen el código robusto y facilitan evolución segura del proyecto.
