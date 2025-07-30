# Módulo: Páginas de la Aplicación

## 🎯 Propósito del Módulo
Este módulo contiene las plantillas de Jinja2 que definen las páginas principales y completas de la aplicación web `autocode`. Cada archivo en este directorio representa una vista o ruta accesible para el usuario, y su principal responsabilidad es ensamblar los componentes de UI necesarios sobre la plantilla base para construir una página cohesiva y funcional.

## 🏗️ Arquitectura del Módulo
Las plantillas de este módulo actúan como "ensambladoras". Todas extienden la plantilla `base.html` y utilizan los componentes definidos en `templates/components` para construir su contenido. Son el nivel más alto en la jerarquía de plantillas.

```mermaid
graph TD
    A[base.html] <|-- B{Páginas};
    C[Componentes] -- Son usados por --> B;
    
    subgraph "Páginas Disponibles"
        D[dashboard.html];
        E[ui_designer.html];
    end

    B -- Contiene --> D;
    B -- Contiene --> E;
    
    F[Servidor FastAPI] -- Renderiza --> B;
```

## 📁 Componentes del Módulo
### `dashboard.html` - Dashboard de Monitoreo
**Propósito**: La página principal de la aplicación, que muestra el estado del sistema, las verificaciones y la configuración.
**Documentación**: [dashboard.md](dashboard.md)

### `ui_designer.html` - Visor de Diseño
**Propósito**: La página dedicada a visualizar la documentación de diseño y los diagramas de arquitectura.
**Documentación**: [ui_designer.md](ui_designer.md)

## 🔗 Dependencias del Módulo
### Internas
- **`autocode.web.templates.base.html`**: Todas las páginas extienden la plantilla base.
- **`autocode.web.templates.components`**: Utilizan los componentes de este módulo para construir su contenido.
- **`autocode.web.static.js`**: Cada página puede cargar scripts específicos necesarios para su funcionalidad.

### Externas
- **FastAPI**: El servidor web es responsable de renderizar estas plantillas y pasarles los datos necesarios.

## 💡 Flujo de Trabajo Típico
1. Un usuario navega a una ruta de la aplicación (e.g., `/dashboard`).
2. El router de FastAPI invoca una función que renderiza la plantilla correspondiente de este módulo (e.g., `dashboard.html`).
3. La plantilla extiende `base.html`, importa los componentes que necesita, y construye el HTML final.
4. El navegador recibe el HTML y carga los scripts asociados, haciendo la página interactiva.
