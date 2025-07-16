# Módulo: Templates

## 🎯 Propósito del Módulo
Este módulo contiene las plantillas HTML que definen la estructura y el layout del dashboard web de `autocode`. Su responsabilidad es proporcionar plantillas Jinja2 bien estructuradas y semánticas que sirven como base para la interfaz web, integrándose con FastAPI y los assets estáticos para crear una experiencia de usuario cohesiva.

## 🏗️ Arquitectura del Módulo
El módulo es simple y contiene únicamente los archivos de plantilla HTML. Estos archivos son procesados por el motor de plantillas Jinja2 en el servidor (`api/server.py`) antes de ser enviados al navegador del cliente.

## 📁 Componentes del Módulo
### `index.html` - Plantilla Principal del Dashboard
**Propósito**: Define el esqueleto HTML de la página principal del dashboard, incluyendo todas las secciones, tarjetas y elementos que serán manipulados por `app.js`.
**Documentación**: [index.md](index.md)

## 🔗 Dependencias del Módulo
### Internas
- `autocode.web.static`: Las plantillas enlazan a los archivos CSS y JS de este módulo para obtener estilos e interactividad.

### Externas
- **Jinja2**: El motor de plantillas utilizado por FastAPI para renderizar estos archivos.

## 💡 Flujo de Trabajo Típico
Cuando un usuario accede a la ruta raíz (`/`) del servidor, `api/server.py` utiliza `Jinja2Templates` para renderizar `index.html`, generando las URLs correctas para los archivos estáticos, y envía el HTML resultante al navegador.
