# TestChecker

## 🎯 Propósito
`TestChecker` es el componente responsable de verificar el estado de los tests en el proyecto, siguiendo una estructura modular. Su responsabilidad principal es detectar tests faltantes, validar tests existentes ejecutándolos, e identificar tests huérfanos que ya no corresponden a código fuente existente. Mapea automáticamente archivos de código a sus tests correspondientes pero no los crea, proporcionando información para que los desarrolladores mantengan una cobertura de tests adecuada.

## 🏗️ Arquitectura
El sistema se basa en la clase `TestChecker`, que sigue una convención de mapeo estricta entre el código fuente y los tests:
-   **Unit Tests**: Un archivo `autocode/core/git/git_analyzer.py` se mapea a `tests/autocode/core/git/test_git_analyzer.py`.
-   **Integration Tests**: Un directorio `autocode/api/` se mapea a un archivo de test `tests/autocode/api/test_api_integration.py`.

El flujo de trabajo es:
1.  **Descubrimiento de Código**: Escanea el proyecto para encontrar todos los archivos y directorios de código Python relevantes.
2.  **Mapeo a Tests**: Para cada archivo o directorio de código, determina la ruta esperada de su archivo de test correspondiente.
3.  **Verificación de Existencia**: Comprueba si los archivos de test esperados existen. Si no, los marca como `missing`.
4.  **Detección de Huérfanos**: Escanea el directorio `tests/` y, para cada test, verifica si su archivo o directorio de código correspondiente todavía existe. Si no, lo marca como `orphaned`.
5.  **Ejecución de Tests**: Ejecuta `pytest` sobre el directorio `tests/` para determinar qué tests existentes están pasando (`passing`) o fallando (`failing`).
6.  **Reporte**: Consolida todos los hallazgos en una lista estructurada y la formatea para su visualización.

## 📋 Responsabilidades
- **Mapear código a tests**: Implementa la lógica para determinar el nombre y la ubicación de un archivo de test basándose en un archivo o directorio de código.
- **Detectar tests faltantes**: Identifica código que carece de su archivo de test correspondiente.
- **Detectar tests huérfanos**: Encuentra archivos de test que apuntan a código que ya no existe.
- **Ejecutar tests**: Lanza `pytest` como un subproceso para validar los tests existentes.
- **Parsear resultados de pytest**: Interpreta la salida de `pytest` para identificar los archivos de test que fallan.
- **Formatear un informe de estado**: Presenta un resumen claro de los tests que requieren atención.

## 🔗 Dependencias
### Internas
- Ninguna.

### Externas
- `subprocess`: Para ejecutar `pytest`.
- `sys`: Para obtener la ruta al ejecutable de Python actual y asegurar que `pytest` se ejecuta en el mismo entorno.
- `pathlib`: Para la manipulación de rutas del sistema de archivos.

## 📊 Interfaces Públicas
### `class TestChecker`
- `__init__(self, project_root: Path, config: Optional['TestConfig'] = None)`: Constructor.
- `check_all_tests(self) -> List[TestStatus]`: Realiza una verificación completa de todos los tests.
- `get_missing_and_failing_tests(self) -> List[TestStatus]`: Devuelve una lista filtrada solo con los tests que necesitan atención.
- `find_orphaned_tests(self) -> List[TestStatus]`: Busca específicamente tests huérfanos.
- `execute_tests(self) -> tuple[int, str, str]`: Ejecuta `pytest` y devuelve el código de salida, stdout y stderr.
- `format_results(self, results: List[TestStatus]) -> str`: Formatea los resultados para ser mostrados.

### `class TestStatus(NamedTuple)`
- Estructura de datos para almacenar el estado de un par código-test.

## 💡 Patrones de Uso
**Verificar el estado de todos los tests y mostrar un informe:**
```python
from pathlib import Path
from autocode.core.test.test_checker import TestChecker

project_path = Path('.')
checker = TestChecker(project_path)

# Obtener solo los tests que necesitan atención
pending_tests = checker.get_missing_and_failing_tests()

# Formatear y mostrar el informe
report = checker.format_results(pending_tests)
print(report)
```

## ⚠️ Consideraciones
- Requiere que `pytest` esté instalado en el entorno virtual (`uv add --dev pytest`).
- La ejecución de tests puede ser un proceso largo. Se ha establecido un timeout de 5 minutos.
- El parseo de los resultados de `pytest` es básico y depende del formato de salida estándar. Cambios en la configuración de `pytest` podrían afectarlo.

## 🧪 Testing
- Probar en un repositorio con tests que pasan, tests que fallan, tests faltantes y tests huérfanos.
- Verificar que el mapeo funciona correctamente para archivos y directorios en diferentes niveles de anidamiento.
- Asegurarse de que el comando `pytest` se construye y ejecuta correctamente.
- Probar el caso en que el directorio `tests/` no existe o está vacío.
