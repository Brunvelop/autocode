# Módulo: Diagrams

## 🎯 Propósito del Módulo
Este módulo es responsable de **generar representaciones visuales** del código analizado. Contiene un framework extensible para crear diferentes tipos de diagramas (como diagramas de clases o de componentes) en varios formatos (actualmente Mermaid).

## 🏗️ Arquitectura del Módulo
La arquitectura es muy similar a la del módulo de `analyzers`, utilizando un **Patrón de Factoría** para la creación de generadores.

```mermaid
graph TD
    A[GeneratorFactory] --> B{Creates};
    B --> C[ClassDiagramGenerator];
    B --> D[ComponentTreeGenerator];
    
    E[BaseGenerator] --> C;
    E --> D;

    subgraph Markdown Exporter
        F[export()]
    end

    C -- Mermaid Code --> F;
    D -- Mermaid Code --> F;
```
1.  **`GeneratorFactory`** crea las instancias de los generadores necesarios.
2.  Cada generador hereda de **`BaseGenerator`**, que define la interfaz común.
3.  Los generadores concretos (`ClassDiagramGenerator`, `ComponentTreeGenerator`) contienen la lógica para traducir los datos de análisis a la sintaxis de un formato de diagrama específico (Mermaid).
4.  El **`MarkdownExporter`** utiliza estos generadores para obtener el código del diagrama y lo incrusta en los archivos de documentación.

## 📁 Componentes del Módulo
### `base_generator.py` - Interfaz del Generador
**Propósito**: Define la clase base abstracta `BaseGenerator` que todos los generadores de diagramas deben implementar.
**Documentación**: [base_generator.md](base_generator.md)

### `generator_factory.py` - Factoría de Generadores
**Propósito**: Crea dinámicamente las instancias de los generadores correctos.
**Documentación**: [generator_factory.md](generator_factory.md)

### `class_diagram_generator.py` - Generador de Diagramas de Clases
**Propósito**: Genera diagramas de clases en formato Mermaid.
**Documentación**: [class_diagram_generator.md](class_diagram_generator.md)

### `component_tree_generator.py` - Generador de Árboles de Componentes
**Propósito**: Genera diagramas de árbol de componentes de UI en formato Mermaid.
**Documentación**: [component_tree_generator.md](component_tree_generator.md)

### `markdown_exporter.py` - Exportador a Markdown
**Propósito**: Orquesta la creación de los archivos `.md` finales, combinando texto y los diagramas generados.
**Documentación**: [markdown_exporter.md](markdown_exporter.md)

## 💡 Flujo de Trabajo Típico
El `MarkdownExporter` recibe los datos del análisis y una lista de generadores instanciados por la `GeneratorFactory`. Cuando necesita insertar un diagrama en un archivo `.md`, invoca al método correspondiente del generador (ej. `generate_class_diagram`), obtiene el string de código Mermaid y lo escribe dentro de un bloque de código ```mermaid.
