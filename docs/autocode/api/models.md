# Modelos de Datos de la API

## 🎯 Propósito
Este módulo define todos los modelos de datos utilizados por la API de `autocode`, tanto para la configuración del sistema como para las respuestas de los endpoints. Utiliza **Pydantic** para definir esquemas de datos tipados, lo que garantiza la validación automática, la serialización y deserialización de JSON, y una documentación clara de la API (a través de OpenAPI/Swagger).

## 🏗️ Arquitectura
El módulo consiste en una serie de clases que heredan de `pydantic.BaseModel`. Cada clase representa una entidad de datos específica.

-   **Modelos de Configuración**: Clases como `DaemonConfig`, `DocsConfig`, `TestConfig`, etc., definen la estructura del archivo de configuración `autocode_config.yml`. La clase principal `AutocodeConfig` anida estas configuraciones, proporcionando un único punto de entrada para cargar toda la configuración del proyecto.
-   **Modelos de Estado y Resultados**: Clases como `DaemonStatus` y `CheckResult` definen la estructura de los datos que la API devuelve para informar sobre el estado del sistema y los resultados de las verificaciones.
-   **Modelos de Petición/Respuesta**: Clases como `CheckExecutionRequest` y `StatusResponse` definen los esquemas para las peticiones que la API espera y las respuestas que devuelve, asegurando un contrato claro entre el cliente y el servidor.

## 📋 Responsabilidades
- **Definir la Estructura de la Configuración**: Establece el esquema completo para el archivo `autocode_config.yml`, incluyendo valores por defecto.
- **Validar Datos**: Pydantic valida automáticamente que los datos cargados desde el archivo de configuración o recibidos en una petición de API se ajustan a los tipos y restricciones definidos.
- **Serializar a JSON**: Convierte los objetos de Python en representaciones JSON para las respuestas de la API.
- **Deserializar de JSON**: Convierte los datos JSON de las peticiones de la API en objetos de Python.
- **Documentar la API**: Sirve como la "fuente de la verdad" para la documentación automática de la API generada por FastAPI.

## 🔗 Dependencias
### Externas
- `pydantic`: La biblioteca fundamental para la definición y validación de modelos de datos.
- `datetime`: Para campos de fecha y hora.
- `typing`: Para anotaciones de tipo avanzadas.

## 📊 Interfaces Públicas (Clases Principales)
-   **`AutocodeConfig`**: El modelo raíz que contiene toda la configuración del sistema.
-   **`CheckResult`**: Representa el resultado de una única ejecución de una verificación (ej. `DocChecker`).
-   **`DaemonStatus`**: Contiene información sobre el estado actual del daemon de monitoreo.
-   **`StatusResponse`**: El modelo para la respuesta del endpoint `/status`, que combina el estado del daemon, los resultados de las verificaciones y la configuración actual.

## 💡 Patrones de Uso
Estos modelos son utilizados principalmente por dos componentes:
1.  **`cli.py`**: Utiliza `AutocodeConfig` para cargar y validar la configuración del proyecto desde `autocode_config.yml`.
2.  **`api/server.py`**: Utiliza los modelos como esquemas de petición y respuesta en los endpoints de FastAPI.

**Ejemplo de uso en `server.py`:**
```python
from .models import StatusResponse, AutocodeConfig

@app.get("/status", response_model=StatusResponse)
def get_status():
    # La lógica para obtener el estado...
    # FastAPI usará el modelo StatusResponse para validar y serializar la respuesta.
    return StatusResponse(...)
```

## ⚠️ Consideraciones
- Cualquier cambio en estos modelos puede afectar la API pública y la estructura del archivo de configuración. Deben ser versionados y modificados con cuidado.
- El uso de valores por defecto en los modelos de Pydantic hace que el sistema sea robusto, ya que puede funcionar incluso con un archivo de configuración vacío o inexistente.
