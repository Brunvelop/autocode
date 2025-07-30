# Componente: Check Card (check_card.html)

## 🎯 Propósito
Este archivo define una **macro de Jinja2** llamada `check_card`. Su propósito es generar un componente de UI reutilizable (una "tarjeta") que muestra el estado y los detalles de una verificación específica del sistema `autocode` (e.g., `doc`, `test`, `git`). La tarjeta es dinámica y adapta su contenido según el tipo de verificación que representa.

## 🏗️ Arquitectura
El componente está encapsulado en una macro de Jinja2, lo que permite que sea llamado como una función desde otras plantillas, pasando parámetros para su configuración. La estructura interna de la tarjeta está diseñada para ser actualizada dinámicamente por JavaScript, con IDs específicos para cada elemento que necesita ser modificado.

```mermaid
graph TD
    A[Plantilla Padre (e.g., dashboard.html)] -- Llama a la macro --> B(check_card macro);
    B -- Recibe parámetros --> C{check_type, check_config};
    B -- Genera HTML --> D[div.check-card];
    
    subgraph "Estructura de la Tarjeta"
        D --> E[Header: Título y Controles];
        D --> F[Details: Mensajes y Estadísticas];
    end
    
    E --> G[Botón "Run Now"];
    E --> H[Indicador de Estado];
    
    F --> I{Contenido Condicional};
    I -- Si check_type es 'doc' --> J[Estadísticas del Índice de Docs];
    I -- Si check_type es 'test' --> K[Estadísticas de Pruebas];
    I -- Si check_type es 'git' --> L[Información de Tokens];
    
    M[app.js] -- Actualiza dinámicamente --> D;
```

## 📋 Responsabilidades
- **Generar la estructura HTML**: Crea el esqueleto de la tarjeta con un encabezado, controles y un área de detalles.
- **Ser reutilizable**: Al ser una macro, puede ser invocada múltiples veces en una página para diferentes tipos de verificaciones.
- **Configuración paramétrica**: Acepta `check_type` y `check_config` para personalizar el título y los identificadores.
- **Renderizado condicional**: Muestra bloques de información específicos (estadísticas de tests, tokens de git, etc.) solo si el `check_type` corresponde.
- **Proporcionar hooks para JS**: Asigna IDs únicos y predecibles a los elementos HTML (`<span>`, `<div>`) para que puedan ser fácilmente seleccionados y actualizados por el código JavaScript del frontend (`app.js`).

## 🔗 Dependencias
### Internas
- Ninguna. Es una macro autocontenida. Sin embargo, está diseñada para ser utilizada por otras plantillas Jinja2.

### Externas
- **JavaScript (`app.js`)**: La tarjeta depende completamente del JavaScript del lado del cliente para tener funcionalidad. El HTML generado es estático; `app.js` es responsable de:
    - Manejar el `onclick` del botón "Run Now".
    - Actualizar el indicador de estado, el mensaje y la marca de tiempo.
    - Poblar las estadísticas detalladas después de recibir datos de la API.

## 📊 Interfaces Públicas (Parámetros de la Macro)
- `check_type` (string): Un identificador único para el tipo de verificación (e.g., `'doc'`, `'test'`, `'git'`). Se usa para generar los IDs de los elementos.
- `check_config` (dict): Un diccionario de configuración que debe contener al menos una clave `title` para el encabezado de la tarjeta.

## 💡 Patrones de Uso
Para usar este componente, se debe importar la macro en una plantilla y luego llamarla con los parámetros requeridos.

```jinja
{# 1. Importar la macro al inicio de la plantilla padre #}
{% from 'components/check_card.html' import check_card %}

{# 2. Llamar a la macro donde se quiera renderizar la tarjeta #}
<div class="cards-container">
    {{ check_card('doc', {'title': 'Documentation Check'}) }}
    {{ check_card('test', {'title': 'Test Suite Status'}) }}
</div>
```

## ⚠️ Consideraciones
- **Dependencia de JavaScript**: Sin el correspondiente código en `app.js` para manejar las interacciones y actualizaciones, esta tarjeta es solo una estructura estática y no funcional.
- **IDs Específicos**: La lógica de JavaScript está fuertemente acoplada a los IDs generados por esta macro (e.g., `doc-check-status`, `test-check-message`). Cualquier cambio en los IDs aquí debe reflejarse en el JavaScript.
- **Contenido Condicional**: La lógica `{% if check_type == '...' %}` asegura que solo se renderice el HTML relevante para cada tipo de tarjeta, manteniendo el DOM limpio.

## 🧪 Testing
Para verificar este componente:
1. Cargar una página que utilice esta macro (como el Dashboard).
2. Verificar que las tarjetas se renderizan correctamente con los títulos pasados en la configuración.
3. Usar las herramientas de desarrollador para inspeccionar el DOM y confirmar que los IDs se han generado correctamente (e.g., `doc-check`, `test-check`).
4. Hacer clic en el botón "Run Now" y observar (en conjunto con `app.js` y la API) si el estado, los mensajes y los detalles de la tarjeta se actualizan como se espera.
