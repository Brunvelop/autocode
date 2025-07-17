# Lógica Principal del Frontend (app.js)

## 🎯 Propósito
Este archivo JavaScript es el **orquestador principal del frontend** de `autocode`. Su responsabilidad es dar vida a la interfaz de usuario, gestionando el estado de la aplicación, la comunicación con la API, la actualización dinámica del DOM y la interacción del usuario en las diferentes páginas.

## 🏗️ Arquitectura
El código se encapsula en la clase `AutocodeDashboard`, que actúa como el controlador principal de la aplicación.

1.  **`AutocodeDashboard` (Clase Principal)**:
    -   **`constructor()` e `init()`**: Detecta la página actual (`dashboard` o `ui-designer`), configura la navegación y lanza la carga de datos iniciales y el refresco automático.
    -   **`fetchAndUpdateStatus()` y `fetchAndUpdateConfig()`**: Utilizan `fetch` (a través del `APIClient` si estuviera disponible, aunque aquí es directo) para obtener datos del estado y la configuración desde los endpoints `/api/status` y `/api/config`.
    -   **`updateUI(data)`**: Método central que recibe los datos de la API y delega la actualización del DOM a métodos más específicos.
    -   **Métodos de Actualización Específicos**: `updateDaemonStatus`, `updateCheckCard`, `updateConfigUI`, etc., se encargan de manipular elementos concretos del DOM.
    -   **Renderizado de Diagramas**: Métodos como `renderArchitectureDiagram` y `renderComponentTree` contienen la lógica para usar `Mermaid.js` y mostrar visualizaciones complejas.
    -   **Manejo de Estado**: Gestiona el estado de la carga (`isLoading`) y el temporizador de auto-refresco.

2.  **Funciones Globales**:
    -   Funciones como `runCheck()`, `updateConfig()`, `regenerateArchitecture()`, etc., están expuestas globalmente para ser llamadas desde los atributos `onclick` en las plantillas HTML. Actúan como un puente hacia la instancia de la clase `AutocodeDashboard`.

3.  **Manejo de Eventos**:
    -   `DOMContentLoaded`: Inicia la aplicación creando una instancia de `AutocodeDashboard`.
    -   `keydown`: Implementa atajos de teclado (ej. Barra espaciadora para refrescar).
    -   `visibilitychange`: Pausa el refresco automático cuando la pestaña no está visible para ahorrar recursos.

## 📋 Responsabilidades
- **Orquestación General**: Inicializa la aplicación y coordina las diferentes partes del frontend.
- **Comunicación con la API**: Obtiene datos de estado y configuración, y envía actualizaciones.
- **Actualización del DOM**: Refleja en tiempo real el estado del backend en la interfaz de usuario.
- **Gestión de la Interfaz de Usuario**: Maneja la lógica de las diferentes páginas y componentes.
- **Manejo de Interacciones**: Procesa los clics de botones y los atajos de teclado.
- **Renderizado de Visualizaciones**: Controla la librería `Mermaid.js` para dibujar diagramas.
- **Control del Refresco Automático**: Gestiona el ciclo de vida del temporizador de actualización.

## 🔗 Dependencias
### Internas
- Depende de la estructura de la API RESTful definida en `api/server.py`.
- Depende de la estructura del DOM y los IDs definidos en las plantillas de `web/templates/`.
- Utiliza implícitamente el `APIClient` definido en `js/utils/api-fetch.js` si está presente (aunque el código actual usa `fetch` directamente).

### Externas
- **Mermaid.js**: Biblioteca externa fundamental para renderizar los diagramas.

## 💡 Patrones de Uso
Este script es cargado por `base.html` y actúa como el punto de entrada principal para toda la lógica del frontend.

## ⚠️ Consideraciones
- **Acoplamiento al DOM**: El código está fuertemente acoplado a los `id` de los elementos HTML. Cambios en las plantillas pueden requerir cambios aquí.
- **Estado Global**: La instancia `dashboard` se almacena en una variable global, un patrón simple y efectivo para esta aplicación, pero que podría ser refactorizado en un sistema más grande.
- **Funciones Globales**: El uso de funciones globales para los `onclick` es una forma sencilla de vincular eventos, pero en un framework moderno se preferirían los manejadores de eventos adjuntados mediante JavaScript.

## 🧪 Testing
- El testing de este archivo es principalmente manual y visual, verificando que la interfaz se actualiza correctamente y que los botones funcionan.
- Se pueden usar herramientas de testing de frontend como Jest o Cypress para escribir tests automatizados que simulen interacciones del usuario y verifiquen los cambios en el DOM.
- Probar la respuesta de la UI ante diferentes respuestas de la API (éxito, error, datos vacíos).
