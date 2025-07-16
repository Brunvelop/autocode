# ComponentTreeGenerator

## 🎯 Propósito
`ComponentTreeGenerator` es una implementación de `BaseGenerator` diseñada para visualizar la arquitectura de interfaces de usuario (UI). Su responsabilidad es tomar los datos de análisis de componentes de UI (provenientes de analizadores como `JavaScriptAnalyzer` o `HTMLAnalyzer`) y generar un **diagrama de árbol de componentes** en formato Mermaid.

## 🏗️ Arquitectura
Heredando de `BaseGenerator`, esta clase se especializa en diagramas de tipo "components" o "component_tree". La lógica principal reside en el método `generate_component_tree_diagram`, que construye un diagrama de flujo (`graph TD`) de Mermaid.

El proceso de construcción del diagrama es jerárquico:
1.  **Define Estilos**: Comienza definiendo clases de CSS de Mermaid para estilizar diferentes tipos de nodos (componentes, elementos HTML, contenedores).
2.  **Nodo Raíz**: Crea un nodo raíz para representar el conjunto de componentes de UI.
3.  **Itera sobre Módulos y Archivos**: Recorre la estructura de datos de análisis, creando nodos para cada módulo (directorio) y cada archivo que contiene componentes.
4.  **Crea Nodos de Componentes**: Para cada componente encontrado, añade un nodo al diagrama, usando un icono para representar su tipo (componente de clase, funcional, etc.).
5.  **Añade Detalles del Componente**: Agrega nodos hijos para mostrar información clave como `props` y `event_handlers`, proporcionando una vista rápida de la interfaz del componente.
6.  **Añade Elementos Significativos**: Incluye nodos para elementos HTML importantes (aquellos con `id` o `class`) para dar contexto.
7.  **Añade Resumen**: Finaliza con un nodo de resumen que muestra estadísticas totales.

## 📋 Responsabilidades
- **Generar Diagramas de Árbol de Componentes**: Traduce una estructura de datos de componentes de UI a un diagrama de Mermaid.
- **Visualizar Jerarquía**: Muestra la relación entre módulos, archivos y los componentes que contienen.
- **Resumir Interfaces de Componentes**: Muestra `props` y eventos de forma concisa.
- **Estilizar Nodos**: Utiliza `classDef` de Mermaid para diferenciar visualmente los tipos de nodos.
- **Generar Resúmenes en Texto**: Proporciona un método adicional (`generate_component_summary`) para crear un resumen textual del análisis de componentes.

## 🔗 Dependencias
### Internas
- `autocode.core.design.diagrams.base_generator.BaseGenerator`: La clase base de la que hereda.

### Externas
- Ninguna.

## 📊 Interfaces Públicas
### `class ComponentTreeGenerator(BaseGenerator)`
-   `get_diagram_format(self) -> str`: Devuelve "mermaid".
-   `supports_diagram_type(self, diagram_type: str) -> bool`: Devuelve `True` si el tipo es "components" o "component_tree".
-   `generate_diagram(...) -> str`: Orquesta la generación del diagrama de árbol de componentes.
-   `generate_component_tree_diagram(...) -> str`: Contiene la lógica principal para construir el diagrama.
-   `generate_component_summary(...) -> str`: Genera un resumen en formato de texto.

## 💡 Patrones de Uso
Este generador es invocado por `CodeToDesign` cuando se analizan archivos de frontend (HTML, JS, etc.) y la configuración solicita diagramas de componentes.

**Uso programático (ejemplo):**
```python
from autocode.core.design.diagrams.component_tree_generator import ComponentTreeGenerator

# Datos de ejemplo que un analizador de JS podría producir
analysis_data = {
    "modules": {
        "components": {
            "files": {
                "MyComponent": {
                    "components": [{
                        "name": "MyComponent",
                        "type": "class_component",
                        "props": ["prop1", "prop2"]
                    }]
                }
            }
        }
    },
    "summary": {"total_components": 1, "total_files": 1}
}

generator = ComponentTreeGenerator()
mermaid_code = generator.generate_diagram(analysis_data)
print(mermaid_code)
```

## ⚠️ Consideraciones
- La calidad y detalle del diagrama dependen completamente de la información extraída por los analizadores de frontend.
- La detección de relaciones entre componentes es simplificada y podría mejorarse con un análisis más profundo del código.
- Para evitar diagramas demasiado grandes, la cantidad de `props`, eventos y elementos mostrados está limitada.

## 🧪 Testing
- Probar con datos de análisis que incluyan diferentes tipos de componentes y archivos.
- Verificar que la jerarquía (módulo -> archivo -> componente) se representa correctamente.
- Comprobar que los detalles de los componentes (props, eventos) se muestran como se espera.
- Probar con datos de análisis vacíos para asegurar que se genera un mensaje de "No UI components found".
