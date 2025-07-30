# MarkdownExporter

## 🎯 Propósito
`MarkdownExporter` es el componente final en el pipeline de generación de diseño. Su responsabilidad es tomar los resultados estructurados del análisis de código y utilizar los generadores de diagramas para producir la documentación final en formato Markdown. Orquesta la creación de la estructura de directorios de salida y la escritura de cada archivo (`_index.md`, `_module.md`, `*_items.md`).

## 🏗️ Arquitectura
Esta clase no hereda de una base, ya que su función es muy específica. Actúa como un "compositor" que ensambla el contenido de los archivos Markdown.

El flujo de trabajo es el siguiente:
1.  **Inicialización**: Se instancia con la ruta base de salida y la configuración.
2.  **Exportación Principal (`export`)**: Este método recibe los resultados del análisis y los generadores de diagramas disponibles.
3.  **Generación de Archivo de Índice (`_index.md`)**: Si está configurado, crea el archivo principal con una vista general de la arquitectura, incluyendo un diagrama de alto nivel.
4.  **Generación de Archivos de Módulo (`_module.md`)**: Itera sobre cada módulo (directorio) en los resultados del análisis y genera un archivo de resumen para él.
5.  **Generación de Archivos de Ítems (`*_items.md`)**: Para cada archivo de código analizado, genera un documento detallado que describe sus clases, funciones o componentes, incluyendo los diagramas correspondientes.

## 📋 Responsabilidades
- **Crear Estructura de Directorios**: Replica la estructura de directorios del código fuente dentro del directorio de salida de la documentación.
- **Generar `_index.md`**: Crea el punto de entrada principal de la documentación de diseño, con resúmenes y diagramas de arquitectura.
- **Generar `_module.md`**: Crea los resúmenes para cada módulo, listando los archivos que contiene y enlazando a su documentación detallada.
- **Generar `*_items.md`**: Crea la documentación detallada para cada archivo de código, invocando a los generadores de diagramas para visualizar clases o componentes.
- **Ensamblar Contenido**: Combina texto, métricas y diagramas para formar el contenido final de cada archivo Markdown.

## 🔗 Dependencias
### Internas
- Depende de las estructuras de datos producidas por los **analizadores** y de las instancias de los **generadores** de diagramas.
- `autocode.core.design.utils.GeneralUtils` (opcional): Para operaciones avanzadas como la construcción de árboles jerárquicos y el cálculo de métricas.

### Externas
- `pathlib`: Para la manipulación de rutas de archivos.
- `logging`: Para el registro de información.

## 📊 Interfaces Públicas
### `class MarkdownExporter`
-   `__init__(self, output_base: Path, config: Dict[str, Any] = None, utils=None)`: Constructor.
-   `export(self, analysis_results: Dict[str, Any], generators: Dict[str, Any]) -> List[Path]`: El método principal que orquesta todo el proceso de exportación a Markdown.
-   `generate_markdown_files(...) -> List[Path]`: Lógica principal para generar todos los archivos.
-   `generate_visual_index(...) -> str`: Genera el contenido del `_index.md`.
-   `_generate_module_overview(...) -> str`: Genera el contenido de un `_module.md`.
-   `_generate_items_content(...) -> str`: Genera el contenido de un archivo `*_items.md`.

## 💡 Patrones de Uso
El `MarkdownExporter` es utilizado casi exclusivamente por la clase `CodeToDesign` al final de su proceso `generate_design`.

```python
# Dentro de CodeToDesign.generate_design
# ... después de ejecutar los analizadores ...

exporter = MarkdownExporter(self.output_base, self.config, self.utils)
generated_files = exporter.export(combined_results, self.generators)
```

## ⚠️ Consideraciones
- La calidad y la estructura de la salida dependen directamente de la calidad de los datos de entrada (`analysis_results`).
- La generación de diagramas se delega completamente a los generadores pasados como argumento, por lo que el exportador no necesita conocer los detalles de la sintaxis de Mermaid u otros formatos.

## 🧪 Testing
- Probar que la estructura de directorios se crea correctamente en la salida.
- Verificar que se generan los tres tipos de archivos (`_index.md`, `_module.md`, `*_items.md`).
- Comprobar que los enlaces entre los diferentes archivos Markdown son correctos.
- Validar que el contenido de los archivos es correcto, incluyendo la inserción de los diagramas generados.
