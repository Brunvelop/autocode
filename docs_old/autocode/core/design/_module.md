# Módulo: Design

## 🎯 Propósito del Módulo
El módulo `design` es un sistema completo para la **generación automática de documentación de diseño** a partir del código fuente. Su propósito es analizar un proyecto, entender su estructura y componentes, y producir una serie de documentos Markdown con diagramas que describen la arquitectura del software de manera visual y estructurada.

## 🏗️ Arquitectura del Módulo
La arquitectura es modular y extensible, orquestada por la clase `CodeToDesign`.

```mermaid
graph TD
    A[CodeToDesign] --> B[Analyzers];
    A --> C[Diagram Generators];
    A --> D[Utils];
    
    B --> E{Extracted Data};
    C --> F[Diagrams];
    D -- Processes --> E;
    
    subgraph Markdown Exporter
        G[export()]
    end

    E --> G;
    F --> G;
    G --> H[Markdown Docs];
```
1.  **`CodeToDesign`** es el punto de entrada que coordina todo el proceso.
2.  Utiliza el módulo de **`analyzers`** para analizar el código fuente y extraer datos estructurados.
3.  Usa el módulo de **`utils`** para procesar estos datos (ej. construir un árbol jerárquico).
4.  Pasa los datos procesados al **`MarkdownExporter`**.
5.  El exportador utiliza el módulo de **`diagrams`** para generar los diagramas (ej. Mermaid).
6.  Finalmente, el exportador escribe los archivos de documentación `.md`.

## 📁 Componentes del Módulo
### `code_to_design.py` - Orquestador Principal
**Propósito**: La clase principal que dirige el proceso de análisis y generación de la documentación de diseño.
**Documentación**: [code_to_design.md](code_to_design.md)

### `/analyzers` - Módulo de Analizadores
**Propósito**: Contiene las clases para analizar diferentes lenguajes de programación (Python, JS, CSS, HTML).
**Documentación**: [analyzers/_module.md](analyzers/_module.md)

### `/diagrams` - Módulo de Generadores de Diagramas
**Propósito**: Contiene las clases para generar diagramas en diferentes formatos (actualmente Mermaid).
**Documentación**: [diagrams/_module.md](diagrams/_module.md)

### `/utils` - Módulo de Utilidades
**Propósito**: Proporciona funciones auxiliares para procesar los datos de análisis, como la construcción de árboles jerárquicos y el cálculo de métricas.
**Documentación**: [utils/_module.md](utils/_module.md)

## 💡 Flujo de Trabajo Típico
Un desarrollador o un proceso de CI/CD invocaría a `CodeToDesign` apuntando a un directorio del proyecto. El sistema analizaría automáticamente el código, generaría los diagramas y produciría una carpeta `design/` con toda la documentación de la arquitectura, lista para ser consultada o publicada.

<!-- Last updated: 2025-07-17 07:59:20 -->
