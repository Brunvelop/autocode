# Plantilla HTML del Dashboard

## 🎯 Propósito
Este archivo es la plantilla HTML principal para el dashboard de monitoreo de `autocode`. Su propósito es definir la estructura y el layout de la interfaz de usuario que se muestra en el navegador. Actúa como el "esqueleto" de la página, que luego es poblado con datos dinámicos por el script `app.js`.

## 🏗️ Arquitectura
El archivo es un documento HTML estándar, pero utiliza la sintaxis de plantillas de **Jinja2** para la integración con FastAPI.

1.  **Encabezado (`<head>`)**:
    -   Define metadatos básicos como el `charset` y el `viewport`.
    -   Enlaza las hojas de estilo CSS: `design-tokens.css` para las variables de diseño y `style.css` para los estilos específicos de la página. La función `url_for('static', ...)` de Jinja2 es utilizada por FastAPI para generar las rutas correctas a los archivos estáticos.

2.  **Cuerpo (`<body>`)**:
    -   **Estructura de Layout**: Utiliza un contenedor principal (`.container`) y divide la página en secciones semánticas: `<header>`, `<main>` y `<footer>`.
    -   **Componentes de la UI**: Define la estructura estática de cada componente del dashboard, como las tarjetas de estado (`.card`), las tarjetas de verificación (`.check-card`) y el formulario de configuración (`.config-card`).
    -   **Identificadores (`id`)**: Asigna `id` únicos a todos los elementos que necesitan ser actualizados dinámicamente (ej. `id="daemon-indicator"`, `id="doc-check-message"`). Estos `id` son el punto de anclaje que `app.js` utiliza para seleccionar y manipular los elementos.
    -   **Manejo de Eventos**: Asigna manejadores de eventos `onclick` a los botones (ej. `onclick="runCheck('doc_check')"`), que llaman a las funciones globales definidas en `app.js`.

3.  **Scripts**:
    -   Carga la biblioteca externa **Mermaid.js** desde un CDN para renderizar los diagramas.
    -   Carga el script principal de la aplicación, `app.js`, al final del cuerpo para asegurar que el DOM esté completamente cargado antes de que el script intente manipularlo.

## 📋 Responsabilidades
- **Definir la Estructura del DOM**: Establece la jerarquía de todos los elementos visibles en la página.
- **Enlazar Assets Estáticos**: Carga los archivos CSS y JavaScript necesarios.
- **Proporcionar Puntos de Anclaje para JavaScript**: Define los `id` que `app.js` usará para las actualizaciones dinámicas.
- **Conectar Eventos de Usuario a Funciones JS**: Asigna las acciones del usuario (clics) a las funciones JavaScript correspondientes.

## 🔗 Dependencias
### Internas
- `web/static/design-tokens.css`: Para las variables de diseño.
- `web/static/style.css`: Para los estilos visuales.
- `web/static/app.js`: Para toda la interactividad y la lógica del frontend.

### Externas
- **Mermaid.js**: Biblioteca para la renderización de diagramas.

## 💡 Patrones de Uso
Este archivo no se sirve estáticamente. Es procesado por el servidor FastAPI (`api/server.py`) usando el motor de plantillas Jinja2. Cuando un usuario solicita la ruta `/`, FastAPI renderiza esta plantilla y la devuelve como una respuesta HTML.

## ⚠️ Consideraciones
- **Acoplamiento con `app.js`**: Existe un fuerte acoplamiento entre los `id` de los elementos en este archivo y el código JavaScript que los manipula. Un cambio en un `id` aquí debe reflejarse en `app.js`.
- **Renderizado del Lado del Servidor (Ligero)**: Aunque se usa un motor de plantillas (Jinja2), su uso aquí es mínimo (solo para `url_for`). La mayor parte del renderizado dinámico ocurre en el lado del cliente, a través de JavaScript.

## 🧪 Testing
- El testing es principalmente visual y funcional. Se debe cargar la página en un navegador y verificar que:
    -   Todos los elementos se renderizan correctamente.
    -   No hay errores de carga de assets en la consola.
    -   Las interacciones del usuario (clics en botones) funcionan como se espera.
- Se pueden usar herramientas de validación de HTML para asegurar que la estructura es correcta.
