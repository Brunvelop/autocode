# Componente: UI Designer (ui_designer.html)

## 🎯 Propósito
Este archivo define el componente principal de la interfaz de usuario para el "Visor de Documentación de Diseño". Su propósito es proporcionar la estructura HTML para la página donde los usuarios pueden cargar, visualizar e interactuar con los diagramas de arquitectura y diseño generados por `autocode`.

## 🏗️ Arquitectura
Es un componente HTML autocontenido que estructura la página del visor de diseño. Contiene placeholders y `divs` con IDs específicos que son el objetivo del script `ui-designer.js` para inyectar contenido dinámico. No es una macro, sino un bloque de HTML diseñado para ser incluido en una página principal.

```mermaid
graph TD
    A[pages/ui_designer.html] -- Incluye --> B(components/ui_designer.html);
    
    subgraph "Estructura del Componente"
        B --> C[Header: Título y Controles];
        B --> D[Content: Contenedor de Archivos y Leyenda];
    end
    
    C --> E[Botón "Load Diagrams"];
    C --> F[Botón "Refresh"];
    
    D --> G["div#design-files-list"];
    D --> H[Leyenda de Funcionalidades];
    
    I[ui-designer.js] -- Manipula y puebla --> G;
    I -- Responde a los clics de --> E;
    I -- Responde a los clics de --> F;
```

## 📋 Responsabilidades
- **Estructurar la página del visor**: Define el layout general con una cabecera, un área de contenido principal y una leyenda.
- **Proporcionar controles de usuario**: Incluye botones para "Cargar Diagramas" y "Refrescar".
- **Definir el área de renderizado**: Contiene el `div` (`#design-files-list`) donde el script `ui-designer.js` cargará y mostrará la lista de archivos de diseño y sus diagramas.
- **Informar al usuario**: Muestra un mensaje inicial y una leyenda que explica las características de la herramienta.
- **Proporcionar hooks para JavaScript**: Utiliza IDs (`ui-designer-title`, `ui-designer-summary`, `design-files-list`) y `onclick` para conectar la estructura HTML con la lógica del frontend.

## 🔗 Dependencias
### Internas
- **`pages/ui_designer.html`**: Este componente está diseñado para ser incluido dentro de la plantilla de la página principal del visor.

### Externas
- **JavaScript (`ui-designer.js`)**: Este componente es la contraparte lógica de esta estructura HTML. Es responsable de:
    - Manejar los eventos `onclick` de los botones.
    - Llamar a la API para obtener los archivos de diseño.
    - Renderizar la lista de archivos y los diagramas de Mermaid dentro de `#design-files-list`.
- **CSS (`style.css`)**: Define la apariencia visual de este componente.

## 📊 Interfaces Públicas
La "interfaz" de este componente son los hooks que proporciona para la interacción con JavaScript:
- `onclick="loadDesignFiles()"`: Llama a la función global para iniciar la carga de diagramas.
- `onclick="refreshDesignFiles()"`: Llama a la función global para volver a cargar los diagramas.
- `id="ui-designer-title"`: El `<h3>` para el título principal.
- `id="ui-designer-summary"`: El `<p>` para el resumen.
- `id="design-files-list"`: El `<div>` principal donde se inyecta todo el contenido dinámico.

## 💡 Patrones de Uso
Este componente se utiliza incluyéndolo en la plantilla de la página que servirá como visor de diseño.

```jinja
{# En pages/ui_designer.html #}
{% extends "base.html" %}

{% block title %}UI Designer{% endblock %}

{% block content %}
    {% include 'components/ui_designer.html' %}
{% endblock %}

{% block extra_js %}
    {# El script específico que controla este componente #}
    <script src="/static/js/components/ui-designer.js" defer></script>
{% endblock %}
```

## ⚠️ Consideraciones
- **Dependencia de JS**: La funcionalidad completa de este componente depende críticamente de `ui-designer.js`. Sin él, la página es estática y los botones no tienen efecto.
- **Estado Inicial**: Muestra un mensaje de "listo para cargar" por defecto. Este mensaje es reemplazado por `ui-designer.js` durante el proceso de carga.

## 🧪 Testing
Para verificar este componente:
1. Navegar a la página `/ui-designer`.
2. Verificar que la estructura inicial, incluyendo el título, los botones y la leyenda, se muestra correctamente.
3. Hacer clic en "Load Diagrams" y confirmar que el script `ui-designer.js` se activa y comienza a poblar el área `#design-files-list`.
4. Inspeccionar el DOM para confirmar que la estructura HTML generada dinámicamente se anida correctamente dentro de este componente.
