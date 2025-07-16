# Módulo: Utils

## 🎯 Propósito del Módulo
Este módulo proporciona una colección de funciones de utilidad de propósito general para el sistema de generación de diseño. Su principal responsabilidad es manejar tareas de procesamiento de datos que son compartidas por otros componentes, como la transformación de estructuras de datos y el cálculo de métricas.

## 🏗️ Arquitectura del Módulo
El módulo está compuesto por clases de utilidad que no mantienen un estado propio significativo, sino que operan sobre los datos que se les proporcionan.

```mermaid
graph TD
    A[Datos de Análisis (Planos)] --> B[GeneralUtils];
    B --> C[Árbol Jerárquico];
    B --> D[Estadísticas y Métricas];
```

## 📁 Componentes del Módulo
### `general_utils.py` - Utilidades Generales
**Propósito**: Contiene la lógica para construir un árbol jerárquico a partir de datos planos, agregar métricas y otras funciones auxiliares.
**Documentación**: [general_utils.md](general_utils.md)

## 💡 Flujo de Trabajo Típico
La clase `GeneralUtils` es instanciada y utilizada por `CodeToDesign` y `MarkdownExporter` para procesar los resultados de los analizadores. Por ejemplo, después de que los analizadores devuelven una lista plana de módulos, `GeneralUtils` la convierte en un árbol anidado, que es mucho más fácil de usar para generar una vista de arquitectura jerárquica.
