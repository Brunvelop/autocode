# CodeToDesign

## 🎯 Propósito
Este módulo es el orquestador principal para transformar código fuente en documentación de diseño modular y visual. Su función es analizar un proyecto, extraer su estructura y componentes clave, y generar una serie de archivos Markdown que describen la arquitectura del software, incluyendo diagramas y métricas.

## 🏗️ Arquitectura
La clase `CodeToDesign` actúa como el punto de entrada central. Utiliza un patrón de **Factoría** para crear dinámicamente los analizadores de código (`AnalyzerFactory`) y los generadores de diagramas (`GeneratorFactory`) necesarios según la configuración del proyecto.

El flujo de trabajo es el siguiente:
1.  **Inicialización**: Carga una configuración y prepara las factorías.
2.  **Detección Automática**: Identifica los analizadores adecuados para el directorio a procesar (por ejemplo, `PythonAnalyzer` para un directorio con código Python).
3.  **Análisis**: Ejecuta los analizadores para recorrer el código y extraer datos estructurados sobre clases, funciones, componentes, etc.
4.  **Fusión de Resultados**: Combina los resultados de múltiples analizadores (si se usan varios, por ejemplo, para un proyecto con Python y JavaScript).
5.  **Generación de Documentación**: Utiliza los datos analizados para generar archivos Markdown:
    *   Un `_index.md` con una vista general y un diagrama de la arquitectura.
    *   Un `_module.md` para cada subdirectorio, resumiendo su contenido.
    *   Un `*_items.md` para cada archivo de código, detallando sus componentes internos.

## 📋 Responsabilidades
- **Orquestar el Proceso**: Coordina la interacción entre los analizadores, los generadores y el exportador de Markdown.
- **Gestionar la Configuración**: Normaliza y gestiona la configuración del proceso, aplicando valores por defecto.
- **Analizar Directorios**: Invoca a los analizadores para procesar el código fuente.
- **Generar Archivos Markdown**: Crea una estructura de directorios de salida y escribe los archivos de documentación.
- **Generar Vistas de Alto Nivel**: Crea el `_index.md` y los `_module.md` que resumen la estructura del proyecto.
- **Generar Detalles de Componentes**: Crea los archivos `*_items.md` con la documentación detallada de cada clase, función, etc.

## 🔗 Dependencias
### Internas
- `autocode.core.design.analyzers.AnalyzerFactory`: Para crear instancias de los analizadores de código.
- `autocode.core.design.diagrams.GeneratorFactory`: Para crear instancias de los generadores de diagramas (ej. Mermaid).
- `autocode.core.design.diagrams.MarkdownExporter`: (Implícitamente usado) para formatear la salida a Markdown.
- `autocode.core.design.utils.GeneralUtils`: Para tareas auxiliares como construir árboles jerárquicos y calcular métricas.

## 📊 Interfaces Públicas
### `class CodeToDesign`
- `__init__(self, project_root: Path, config: Dict[str, Any] = None)`: Constructor.
- `generate_design(self, directory: str, patterns: Optional[List[str]] = None) -> Dict[str, Any]`: Método principal que ejecuta todo el proceso de análisis y generación para un directorio.
- `generate_markdown_files(...) -> List[Path]`: Genera los archivos Markdown a partir de resultados de análisis.
- `generate_visual_index(...) -> str`: Genera el contenido para el archivo `_index.md`.
- `generate_component_tree(self, directory: str) -> Dict[str, Any]`: Genera un diagrama del árbol de componentes de UI para un directorio específico.
- `get_analyzer_info() -> Dict[str, Any]`: Devuelve información sobre los analizadores disponibles.
- `get_generator_info() -> Dict[str, Any]`: Devuelve información sobre los generadores disponibles.
- `get_system_info() -> Dict[str, Any]`: Proporciona una vista completa de la configuración del sistema.

## 💡 Patrones de Uso
**Generar la documentación de diseño para todo un proyecto:**
```python
from pathlib import Path
from autocode.core.design.code_to_design import CodeToDesign

project_path = Path('.')
# La configuración puede cargarse desde un archivo o pasarse directamente
config = {
    "output_dir": "design_docs",
    "auto_detect": True,
    "diagrams": ["classes", "mermaid"]
}

transformer = CodeToDesign(project_path, config)
result = transformer.generate_design(str(project_path))

if result['status'] == 'success':
    print(f"Se generaron {len(result['generated_files'])} archivos de diseño.")
    for f in result['generated_files']:
        print(f"- {f}")
```

## ⚠️ Consideraciones
- La calidad de la documentación generada depende directamente de la capacidad de los analizadores para interpretar el código fuente correctamente.
- La configuración es clave para controlar qué se analiza, qué diagramas se generan y cómo se estructura la salida.
- El sistema está diseñado para ser extensible: se pueden añadir nuevos analizadores para otros lenguajes o nuevos generadores para diferentes formatos de diagramas.

## 🧪 Testing
- Las pruebas deben cubrir proyectos con diferentes estructuras y lenguajes (Python, JS, etc.).
- Verificar que la detección automática de analizadores funciona correctamente.
- Comprobar que la estructura de directorios de salida se crea como se espera.
- Validar que los archivos Markdown generados son sintácticamente correctos y que los diagramas Mermaid son válidos.
