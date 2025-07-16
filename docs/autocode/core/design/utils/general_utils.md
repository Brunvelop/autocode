# GeneralUtils

## 🎯 Propósito
`GeneralUtils` es una clase de utilidad que contiene lógica compartida y agnóstica al proyecto para procesar los datos de análisis. Su responsabilidad principal es transformar la estructura de datos "plana" que producen los analizadores en una estructura de árbol jerárquico y calcular métricas agregadas sobre ella.

## 🏗️ Arquitectura
Esta clase no tiene una arquitectura compleja; es una colección de métodos que operan sobre estructuras de datos (diccionarios y listas).

El método más importante es `build_hierarchical_tree`, que funciona en dos pasadas:
1.  **Primera Pasada (Construcción del Árbol)**: Itera sobre las rutas de los módulos (ej. `autocode/core/design`) y construye una estructura de árbol anidada que representa la jerarquía de directorios.
2.  **Segunda Pasada (Población de Datos)**: Vuelve a iterar sobre los módulos y coloca los datos de análisis (clases, funciones, etc.) y las métricas en los nodos "hoja" correspondientes del árbol.
3.  **Agregación de Métricas**: Un método recursivo (`_calculate_aggregate_metrics`) recorre el árbol desde las hojas hacia la raíz, sumando las métricas de los hijos para calcular los totales de los nodos padres.

## 📋 Responsabilidades
- **Construir un Árbol Jerárquico**: Convierte una lista plana de módulos en una estructura de árbol anidada.
- **Calcular Métricas**: Calcula métricas para módulos individuales (número de clases, funciones, líneas de código, etc.).
- **Agregar Métricas**: Suma las métricas de los nodos hijos para proporcionar totales en los nodos padres, ofreciendo una vista resumida en cualquier nivel de la jerarquía.
- **Generar Estadísticas de Resumen**: Calcula estadísticas globales para todo el árbol.
- **Proporcionar Iconos**: Ofrece un mapeo por defecto de nombres de módulos comunes a iconos emoji para mejorar la visualización de los diagramas.
- **Exportar a JSON**: Proporciona una utilidad para guardar la estructura de árbol en un archivo JSON.

## 🔗 Dependencias
### Externas
- `pathlib`: Para la manipulación de rutas.
- `json`: Para la exportación a formato JSON.

## 📊 Interfaces Públicas
### `class GeneralUtils`
-   `__init__(self, config: Dict[str, Any] = None)`: Constructor.
-   `build_hierarchical_tree(self, flat_data: Dict[str, Any], ...) -> Dict[str, Any]`: El método principal que construye la estructura de árbol.
-   `generate_summary_stats(self, tree: Dict[str, Any]) -> Dict[str, Any]`: Genera estadísticas de resumen para un árbol.
-   `filter_tree_by_criteria(self, tree: Dict[str, Any], ...) -> Dict[str, Any]`: Filtra un árbol según criterios específicos.
-   `export_tree_to_json(self, tree: Dict[str, Any], output_path: Path) -> None`: Guarda el árbol en un archivo JSON.
-   `get_module_icons(self, custom_icons: Optional[Dict[str, str]] = None) -> Dict[str, str]`: Devuelve el mapeo de iconos para los módulos.

## 💡 Patrones de Uso
Esta clase es utilizada internamente por `MarkdownExporter` y `CodeToDesign` para procesar los resultados del análisis antes de generar la documentación.

```python
# Dentro de CodeToDesign o MarkdownExporter
from .general_utils import GeneralUtils

utils = GeneralUtils(self.config)
# 'analysis_results' es la salida plana de los analizadores
hierarchical_tree = utils.build_hierarchical_tree(analysis_results)
summary = utils.generate_summary_stats(hierarchical_tree)

# Ahora 'hierarchical_tree' y 'summary' pueden usarse para generar Markdown
```

## ⚠️ Consideraciones
- La lógica de construcción del árbol asume que las rutas de los módulos están separadas por `/` o `\`.
- El cálculo de métricas depende de la estructura de datos proporcionada por los analizadores. Cambios en esa estructura podrían requerir ajustes aquí.

## 🧪 Testing
- Probar la construcción del árbol con diferentes estructuras de directorios (planas, anidadas).
- Verificar que las métricas se calculan y agregan correctamente en todos los niveles del árbol.
- Comprobar que el filtrado y la exportación a JSON funcionan como se espera.
- Asegurarse de que el mapeo de iconos devuelve los valores correctos, incluyendo la sobreescritura con iconos personalizados.
