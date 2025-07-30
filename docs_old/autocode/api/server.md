# Servidor de la API

## 🎯 Propósito
Este módulo implementa el servidor web y la API RESTful para el sistema de monitoreo en tiempo real de `autocode`. Utiliza **FastAPI** para proporcionar una interfaz web (dashboard) y una serie de endpoints programáticos para interactuar con el `AutocodeDaemon`.

## 🏗️ Arquitectura
1.  **Aplicación FastAPI**: Se crea una instancia de `FastAPI` que actúa como el núcleo del servidor.
2.  **Ciclo de Vida de la Aplicación (`@app.on_event`)**:
    -   **`startup`**: Al iniciar el servidor, se crea e inicia una instancia global del `AutocodeDaemon` en una tarea de fondo de `asyncio`. Esto asegura que las verificaciones automáticas se ejecuten periódicamente sin bloquear el servidor.
    -   **`shutdown`**: Al detener el servidor, se detiene de forma segura el daemon y se cancela su tarea de fondo.
3.  **Servicio de Archivos Estáticos y Plantillas**:
    -   Se utiliza `StaticFiles` para servir los archivos CSS y JavaScript del frontend desde el directorio `web/static/`.
    -   Se utiliza `Jinja2Templates` para renderizar la plantilla HTML principal (`index.html`) del dashboard.
4.  **Rutas de la API (`@app.get`, `@app.post`, etc.)**:
    -   Se define una ruta raíz (`/`) que sirve el dashboard HTML.
    -   Se definen múltiples endpoints bajo `/api/` que actúan como la interfaz RESTful. Estos endpoints interactúan con la instancia global del `daemon` para obtener su estado, los resultados de las verificaciones, la configuración, o para disparar acciones como la ejecución manual de una verificación.
    -   Los modelos de Pydantic (de `api/models.py`) se utilizan para definir los esquemas de las respuestas (`response_model`), garantizando que la salida de la API sea consistente y esté validada.

## 📋 Responsabilidades
- **Servir el Dashboard Web**: Proporciona la interfaz de usuario principal para el monitoreo visual.
- **Exponer el Estado del Sistema**: Ofrece endpoints para consultar el estado del daemon y los resultados de las verificaciones (`/api/status`, `/api/checks`).
- **Permitir la Interacción Programática**: Proporciona endpoints para ejecutar verificaciones manualmente (`/api/checks/{check_name}/run`) y gestionar la configuración.
- **Gestionar el Ciclo de Vida del Daemon**: Asegura que el `AutocodeDaemon` se inicie y se detenga correctamente junto con el servidor.
- **Proporcionar Endpoints de Utilidad**: Ofrece funcionalidades adicionales a través de la API, como el conteo de tokens y la regeneración de diagramas de arquitectura.

## 🔗 Dependencias
### Internas
- `autocode.orchestration.daemon.AutocodeDaemon`: El componente principal que ejecuta las verificaciones.
- `autocode.api.models`: Para los esquemas de datos de la API.
- Módulos del `core` (como `TokenCounter`, `CodeToDesign`) son importados dinámicamente por algunos endpoints.

### Externas
- `fastapi`: El framework web principal.
- `uvicorn`: El servidor ASGI que ejecuta la aplicación FastAPI.
- `jinja2`: Para el renderizado de las plantillas HTML.
- `asyncio`: Para la gestión de tareas en segundo plano.

## 📊 Interfaces Públicas (Endpoints Principales)

### Endpoints de la Interfaz Web
-   **`GET /`**: Redirige a `/dashboard`.
-   **`GET /dashboard`**: Sirve la página principal del dashboard.
-   **`GET /ui-designer`**: Sirve la página del visor de documentación de diseño.

### Endpoints de Estado y Verificaciones
-   **`GET /api/status`**: Devuelve un estado completo del sistema (daemon, checks, config).
-   **`GET /api/daemon/status`**: Devuelve solo el estado del daemon.
-   **`GET /api/checks`**: Devuelve los resultados de todas las verificaciones.
-   **`GET /api/checks/{check_name}`**: Devuelve el resultado de una verificación específica.
-   **`POST /api/checks/{check_name}/run`**: Dispara la ejecución de una verificación en segundo plano.

### Endpoints de Configuración
-   **`GET /api/config`**: Devuelve la configuración actual del sistema.
-   **`PUT /api/config`**: Permite actualizar la configuración del daemon en caliente.

### Endpoints del Scheduler
-   **`GET /api/scheduler/tasks`**: Devuelve el estado de todas las tareas programadas.
-   **`POST /api/scheduler/tasks/{task_name}/enable`**: Activa una tarea programada.
-   **`POST /api/scheduler/tasks/{task_name}/disable`**: Desactiva una tarea programada.

### Endpoints de Diseño y Arquitectura
-   **`GET /api/design/files`**: Devuelve una lista de todos los archivos `.md` en el directorio de diseño.
-   **`GET /api/architecture/diagram`**: Extrae y devuelve el diagrama Mermaid del archivo `design/_index.md`.
-   **`POST /api/architecture/regenerate`**: Inicia la regeneración de toda la documentación de diseño en segundo plano.
-   **`GET /api/ui-designer/component-tree`**: Genera y devuelve un diagrama del árbol de componentes de la UI.

### Endpoints de Utilidad (Tokens)
-   **`GET /api/tokens/count`**: Cuenta los tokens en un único archivo.
-   **`POST /api/tokens/count-multiple`**: Cuenta los tokens en múltiples archivos y devuelve un agregado.

### Endpoint de Salud
-   **`GET /health`**: Un endpoint simple para verificar que el servidor está en funcionamiento.

## 💡 Patrones de Uso
Este servidor se inicia a través del comando `autocode daemon` de la CLI. Una vez en ejecución, los usuarios pueden acceder al dashboard en su navegador, y otros sistemas pueden interactuar con la API RESTful para la automatización.

```bash
# Iniciar el servidor
autocode daemon --host 0.0.0.0 --port 8000

# Consultar el estado desde otro terminal
curl http://localhost:8000/api/status
```

## ⚠️ Consideraciones
- El servidor mantiene una instancia **global única** del `AutocodeDaemon`. Esto es adecuado para una aplicación de monitoreo de un solo proceso, pero no escalaría a un entorno con múltiples workers sin un rediseño (ej. usando un broker de mensajes).
- La ejecución de tareas en segundo plano (`BackgroundTasks`) es ideal para operaciones que no necesitan devolver un resultado inmediato al cliente, como la ejecución manual de una verificación.
