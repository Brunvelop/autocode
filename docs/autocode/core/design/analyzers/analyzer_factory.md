# AnalyzerFactory

## 🎯 Propósito
`AnalyzerFactory` es un componente central del sistema de diseño que se encarga de la creación dinámica de instancias de analizadores de código. Utiliza el patrón de diseño **Factory** y un **Registro (Registry)** para desacoplar el orquestador principal (`CodeToDesign`) de las implementaciones concretas de los analizadores (como `PythonAnalyzer`, `JavaScriptAnalyzer`, etc.). Esto hace que el sistema sea extensible y fácil de mantener.

## 🏗️ Arquitectura
La arquitectura se basa en dos componentes principales:
1.  **`AnalyzerRegistry`**: Un registro global (Singleton) que mantiene un mapeo entre nombres de analizadores (ej. "python"), las clases que los implementan (`PythonAnalyzer`), y las extensiones de archivo que soportan (`.py`, `.pyi`).
2.  **`AnalyzerFactory`**: La factoría que utiliza el registro para instanciar los analizadores. Puede crear un analizador específico por su nombre, por la extensión de un archivo, o auto-detectar los analizadores necesarios para un directorio escaneando las extensiones de los archivos que contiene.

El flujo es el siguiente:
1.  Al iniciar, los analizadores incorporados (Python, JS, etc.) se registran en el `AnalyzerRegistry`.
2.  Cuando se necesita un analizador, `CodeToDesign` solicita a `AnalyzerFactory` que lo cree.
3.  La factoría consulta el registro para encontrar la clase correcta y la instancia, pasándole la configuración del proyecto.

## 📋 Responsabilidades
- **Registrar Analizadores**: Mantiene un registro de todos los analizadores disponibles y las extensiones de archivo que manejan.
- **Crear Instancias de Analizadores**: Instancia un analizador específico cuando se le solicita.
- **Auto-detección**: Escanea un directorio para determinar qué tipos de archivos contiene y, por lo tanto, qué analizadores se necesitan.
- **Desacoplar Componentes**: Actúa como una capa de abstracción para que el resto del sistema no necesite conocer los detalles de implementación de cada analizador.
- **Centralizar la Lógica de Creación**: Proporciona un único punto para gestionar la creación de todos los analizadores.

## 🔗 Dependencias
### Internas
- `autocode.core.design.analyzers.base_analyzer.BaseAnalyzer`: La clase base de la que todos los analizadores deben heredar.
- Analizadores concretos (ej. `PythonAnalyzer`, `JavaScriptAnalyzer`) para el registro inicial.

### Externas
- `pathlib`: Para la manipulación de rutas.
- `importlib`: (Potencialmente) para cargar analizadores de forma dinámica en futuras versiones.
- `logging`: Para registrar advertencias si un analizador no está disponible.

## 📊 Interfaces Públicas
### `class AnalyzerFactory`
- `__init__(self, project_root: Path, config: Dict[str, Any] = None)`: Constructor.
- `create_analyzer(self, analyzer_type: str) -> Optional[BaseAnalyzer]`: Crea un analizador por su nombre (ej. "python").
- `create_analyzer_for_file(self, file_path: Path) -> Optional[BaseAnalyzer]`: Crea el analizador adecuado para un archivo específico.
- `get_analyzers_for_languages(self, languages: List[str]) -> Dict[str, BaseAnalyzer]`: Crea un diccionario de analizadores para una lista de lenguajes.
- `auto_detect_analyzers(self, directory: str) -> Dict[str, BaseAnalyzer]`: Auto-detecta y crea los analizadores necesarios para un directorio.
- `get_available_analyzers(self) -> List[str]`: Devuelve una lista de los nombres de todos los analizadores registrados.
- `get_supported_extensions(self) -> List[str]`: Devuelve una lista de todas las extensiones de archivo soportadas.

### `AnalyzerRegistry` y funciones de registro
- `register_analyzer(...)`: Función para añadir un nuevo analizador al sistema.

## 💡 Patrones de Uso
**Crear un analizador para Python:**
```python
from pathlib import Path
from autocode.core.design.analyzers.analyzer_factory import AnalyzerFactory

factory = AnalyzerFactory(Path('.'))
python_analyzer = factory.create_analyzer('python')

if python_analyzer:
    # Usar el analizador
    analysis_result = python_analyzer.analyze_file(Path('mi_script.py'))
```

**Auto-detectar los analizadores para un proyecto:**
```python
project_dir = 'src'
analyzers = factory.auto_detect_analyzers(project_dir)

for name, analyzer_instance in analyzers.items():
    print(f"Analizador detectado: {name}")
    # Procesar con cada analizador
```

## ⚠️ Consideraciones
- El sistema depende de que los analizadores se registren correctamente al inicio. Si un analizador no se puede importar, se registrará una advertencia y no estará disponible.
- La auto-detección se basa puramente en las extensiones de archivo presentes en un directorio, no en el contenido de los archivos.

## 🧪 Testing
- Verificar que los analizadores incorporados se registran correctamente.
- Probar la creación de analizadores por nombre y por extensión de archivo.
- Probar la función de auto-detección en un directorio con una mezcla de tipos de archivo (ej. `.py`, `.js`, `.html`).
- Asegurarse de que la factoría maneja correctamente los casos en que se solicita un analizador no existente.
