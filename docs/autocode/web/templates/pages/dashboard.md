# Página: Dashboard (dashboard.html)

## 🎯 Propósito
Este archivo define la página principal de la aplicación: el **Dashboard de Monitoreo**. Su propósito es ofrecer una vista centralizada del estado del sistema `autocode`, mostrando estadísticas generales, el estado de las verificaciones individuales (documentación, tests, git) y permitiendo la configuración en tiempo real de estas verificaciones.

## 🏗️ Arquitectura
Esta plantilla **extiende** `base.html`, heredando la estructura principal de la aplicación (cabecera, pie de página, barra lateral). Utiliza la herencia de plantillas de Jinja2 para inyectar su contenido en el bloque `{% block content %}`. A su vez, **importa y utiliza macros** de componentes reutilizables (`stat_card` y `check_card`) para construir su layout.

```mermaid
graph TD
    A[base.html] <|-- B(dashboard.html);
    
    subgraph "Componentes Utilizados"
        C[components/stat_card.html];
        D[components/check_card.html];
    end
    
    B -- Importa y usa --> C;
    B -- Importa y usa --> D;
    
    subgraph "Secciones del Dashboard"
        B --> E[System Status];
        B --> F[Active Checks];
        B --> G[Configuration];
    end
    
    E -- Usa --> C;
    F -- Usa --> D;
    
    H[app.js] -- Controla y actualiza --> B;
```

## 📋 Responsabilidades
- **Heredar el layout base**: Se asegura de que la página del dashboard tenga la misma apariencia que el resto de la aplicación.
- **Mostrar estadísticas generales**: Utiliza la macro `stat_card` para mostrar métricas de alto nivel como el tiempo de actividad del sistema (`Uptime`).
- **Mostrar el estado de las verificaciones**: Utiliza la macro `check_card` para crear una tarjeta por cada tipo de verificación activa (Docs, Test, Git).
- **Proporcionar una interfaz de configuración**: Renderiza un formulario con controles (`<input>`, `<select>`) para que el usuario pueda habilitar/deshabilitar las verificaciones, ajustar sus intervalos de ejecución y configurar otros parámetros como los umbrales de tokens.
- **Conectar con la lógica del frontend**: Asigna IDs y eventos `onchange` a los elementos del formulario para que `app.js` pueda leer sus valores y enviar actualizaciones de configuración a la API.

## 🔗 Dependencias
### Internas (Plantillas)
- `base.html`: Hereda su estructura de esta plantilla.
- `components/stat_card.html`: Importa y utiliza la macro `stat_card`.
- `components/check_card.html`: Importa y utiliza la macro `check_card`.

### Externas
- **JavaScript (`app.js`)**: Es la contraparte indispensable de esta plantilla. `app.js` es responsable de:
    - Poblar todos los datos dinámicos (estadísticas, estados de las tarjetas).
    - Cargar la configuración actual y establecer los valores de los inputs del formulario.
    - Manejar los eventos `onchange` para detectar cambios en la configuración.
    - Llamar a la función `updateConfig()` que envía la configuración actualizada a la API del backend.

## 💡 Patrones de Uso
Esta plantilla es el punto de entrada principal de la aplicación cuando se navega a la ruta `/dashboard`. No está diseñada para ser incluida en otras plantillas, sino para ser renderizada directamente por el servidor de FastAPI.

## ⚠️ Consideraciones
- **Acoplamiento con `app.js`**: La funcionalidad de la sección de configuración depende totalmente de la función `updateConfig()` definida en `app.js`. Los IDs de los elementos del formulario (`doc-check-enabled`, `git-check-interval`, etc.) están directamente ligados a la lógica en ese script.
- **Componentización**: La página demuestra un buen uso de la componentización al reutilizar las macros `stat_card` y `check_card`, lo que mantiene el código de la plantilla limpio y organizado.

## 🧪 Testing
Para verificar esta página:
1. Navegar a la ruta `/dashboard` de la aplicación.
2. Verificar que las tres secciones (System Status, Active Checks, Configuration) se renderizan correctamente.
3. Comprobar que las tarjetas de estadísticas y de verificaciones muestran sus datos iniciales (probablemente placeholders o datos cacheados).
4. Interactuar con los controles de configuración (checkboxes, inputs numéricos). Verificar que `app.js` carga los valores iniciales correctamente desde la API.
5. Cambiar un valor de configuración (e.g., deshabilitar una verificación) y confirmar, a través de las herramientas de desarrollador, que se realiza una llamada a la API para guardar la nueva configuración.
