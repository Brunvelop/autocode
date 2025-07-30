# BaseAnalyzer

## 🎯 Propósito
`BaseAnalyzer` es una **clase base abstracta** que define el contrato o la interfaz que todos los analizadores de código específicos (como `PythonAnalyzer`, `JavaScriptAnalyzer`, etc.) deben seguir. Su propósito es garantizar que todos los analizadores tengan una estructura y un comportamiento consistentes, permitiendo que el sistema de diseño los trate de manera uniforme.

## 🏗️ Arquitectura
Este módulo utiliza el patrón de diseño **Template Method** y define una interfaz a través de una clase abstracta (`ABC` de Python).

-   **`BaseAnalyzer` (Clase Abstracta)**:
    -   Define métodos abstractos (`@abstractmethod`) como `get_supported_extensions` y `analyze_file`, que las clases hijas **deben** implementar.
    -   Proporciona una implementación concreta y reutilizable para `analyze_directory`, que contiene la lógica común para recorrer un directorio, encontrar archivos relevantes y orquestar el análisis de cada uno. Las clases hijas heredan este método sin necesidad de sobreescribirlo.

-   **`AnalysisResult` (Clase de Datos)**:
    -   Actúa como un contenedor estandarizado para los resultados de cualquier análisis. Encapsula no solo los datos extraídos, sino también metadatos como el estado del análisis (`success`, `error`), listas de errores y advertencias. Esto permite un manejo de errores robusto y unificado.

## 📋 Responsabilidades
- **Definir el Contrato del Analizador**: Establece qué métodos debe tener cualquier analizador.
- **Proporcionar Lógica Común**: Ofrece una implementación por defecto para analizar un directorio completo, evitando la duplicación de código en las clases hijas.
- **Estandarizar los Resultados**: A través de la clase `AnalysisResult`, asegura que todos los analizadores devuelvan la información en un formato consistente.
- **Gestionar la Configuración**: Proporciona un mecanismo base para que los analizadores reciban la configuración del proyecto.

## 🔗 Dependencias
### Internas
- Ninguna.

### Externas
- `abc` (Abstract Base Classes): Para definir la clase y los métodos abstractos.
- `pathlib`: Para la manipulación de rutas de archivos.
- `logging`: Para el registro de eventos y errores.

## 📊 Interfaces Públicas
### `class BaseAnalyzer(ABC)`
-   `__init__(self, project_root: Path, config: Dict[str, Any] = None)`: Constructor base.
-   `get_supported_extensions(self) -> List[str]`: **Método abstracto**. Debe devolver las extensiones de archivo que soporta el analizador (ej. `['.py']`).
-   `analyze_file(self, file_path: Path) -> AnalysisResult`: **Método abstracto**. Debe implementar la lógica para analizar un único archivo.
-   `analyze_directory(...) -> AnalysisResult`: Método concreto que orquesta el análisis de un directorio.
-   `can_analyze_file(self, file_path: Path) -> bool`: Comprueba si el analizador es adecuado para un archivo.
-   `get_analyzer_info(self) -> Dict[str, Any]`: Devuelve metadatos sobre el analizador.

### `class AnalysisResult`
-   `__init__(...)`: Constructor.
-   `is_successful(self) -> bool`: Devuelve `True` si el análisis fue exitoso.
-   `has_errors(self) -> bool`: Devuelve `True` si se produjeron errores.

## 💡 Patrones de Uso
`BaseAnalyzer` no se instancia directamente. Se utiliza como clase base para crear nuevos analizadores.

**Ejemplo de implementación de un nuevo analizador:**
```python
from .base_analyzer import BaseAnalyzer, AnalysisResult

class MyNewLanguageAnalyzer(BaseAnalyzer):
    def get_supported_extensions(self) -> List[str]:
        return ['.mylang']

    def analyze_file(self, file_path: Path) -> AnalysisResult:
        # Lógica para analizar un archivo .mylang
        try:
            content = file_path.read_text()
            # ... procesar contenido ...
            data = {"items": ["item1", "item2"]}
            return AnalysisResult(status="success", data=data)
        except Exception as e:
            return AnalysisResult(status="error", errors=[str(e)])
```

## ⚠️ Consideraciones
- Cualquier clase que herede de `BaseAnalyzer` debe implementar todos sus métodos abstractos, o de lo contrario se producirá un `TypeError` en tiempo de ejecución.
- La lógica de `analyze_directory` es genérica y puede que necesite ser ajustada o extendida en analizadores muy especializados.

## 🧪 Testing
- Las pruebas para este módulo se centran en las clases hijas.
- Se debe verificar que la lógica de `analyze_directory` funciona correctamente: encuentra los archivos correctos, invoca a `analyze_file` para cada uno y agrega los resultados de manera adecuada.
- Probar la clase `AnalysisResult` para asegurar que gestiona correctamente los estados, errores y datos.
