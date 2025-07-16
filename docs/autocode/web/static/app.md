# JavaScript del Dashboard

## 🎯 Propósito
Este archivo JavaScript es el cerebro del frontend del dashboard de monitoreo de `autocode`. Su responsabilidad es hacer que la página `index.html` sea interactiva y dinámica, comunicándose con la API del backend para obtener y mostrar datos en tiempo real.

## 🏗️ Arquitectura
El código está estructurado en una clase principal, `AutocodeDashboard`, que encapsula toda la lógica del frontend.

1.  **`AutocodeDashboard` (Clase Principal)**:
    -   **`init()`**: Se llama al cargar la página. Inicia un temporizador para la actualización automática y carga los datos iniciales.
    -   **`fetchAndUpdateStatus()`**: Realiza una petición `fetch` al endpoint `/api/status` del backend.
    -   **`updateUI(data)`**: Una vez recibidos los datos, este método orquesta la actualización de las diferentes secciones del DOM (estado del daemon, resultados de las verificaciones, etc.).
    -   **Métodos de Actualización Específicos**: Métodos como `updateDaemonStatus`, `updateCheckCard`, `updateTokenInfo`, etc., se encargan de manipular elementos específicos del DOM para reflejar los nuevos datos.
    -   **Métodos de Formato**: Funciones de utilidad como `formatDuration` y `formatTimestamp` convierten los datos del backend (segundos, timestamps ISO) a un formato legible por humanos.
    -   **Manejo de Diagramas**: Contiene la lógica para cargar los datos de los diagramas desde la API y utilizar la biblioteca `Mermaid.js` para renderizarlos en la página.

2.  **Funciones Globales**:
    -   Funciones como `runCheck(checkName)` y `updateConfig()` están expuestas globalmente para ser llamadas directamente desde los atributos `onclick` de los botones en `index.html`. Estas funciones interactúan con la instancia de `AutocodeDashboard`.

3.  **Manejo de Eventos**:
    -   Un listener `DOMContentLoaded` asegura que el script se ejecute solo después de que toda la página HTML se haya cargado.
    -   Listeners para atajos de teclado (barra espaciadora para refrescar) y para el cambio de visibilidad de la pestaña (para pausar las actualizaciones automáticas) mejoran la experiencia de usuario.

## 📋 Responsabilidades
- **Obtener Datos de la API**: Realiza peticiones `fetch` periódicas al backend para obtener el estado más reciente.
- **Actualizar el DOM**: Manipula dinámicamente el contenido de la página HTML para mostrar los datos recibidos, sin necesidad de recargar la página.
- **Gestionar la Interacción del Usuario**: Maneja los clics en los botones (ej. "Run Now", "Update Config") y los atajos de teclado.
- **Renderizar Diagramas**: Utiliza la biblioteca `Mermaid.js` para visualizar los diagramas de arquitectura y de componentes.
- **Controlar el Refresco Automático**: Gestiona un temporizador para actualizar los datos periódicamente y lo pausa de forma inteligente cuando la pestaña no está visible.
- **Manejar Errores**: Muestra mensajes de error en la interfaz si no puede comunicarse con la API.

## 🔗 Dependencias
### Internas
- Depende de la estructura de la API definida en `api/server.py` y de los modelos de datos en `api/models.py`.
- Depende de la estructura del DOM definida en `web/templates/index.html`.

### Externas
- **Mermaid.js**: Biblioteca externa (cargada en `index.html`) necesaria para renderizar los diagramas.

## 💡 Patrones de Uso
Este script es cargado y ejecutado por el navegador cuando un usuario visita la página principal del dashboard. No se invoca directamente desde el backend.

## ⚠️ Consideraciones
- **Manejo del Estado**: El estado de la aplicación se mantiene de forma simple dentro de la instancia de la clase `AutocodeDashboard`. Para aplicaciones más complejas, se podría considerar un patrón de gestión de estado más robusto (como Redux, Vuex, etc.).
- **Acoplamiento al DOM**: El código está fuertemente acoplado a los `id` de los elementos en `index.html`. Cualquier cambio en los `id` del HTML requerirá una actualización correspondiente en este archivo.

## 🧪 Testing
- El testing de este archivo es principalmente manual y visual, verificando que la interfaz se actualiza correctamente y que los botones funcionan.
- Se pueden usar herramientas de testing de frontend como Jest o Cypress para escribir tests automatizados que simulen interacciones del usuario y verifiquen los cambios en el DOM.
- Probar la respuesta de la UI ante diferentes respuestas de la API (éxito, error, datos vacíos).
