# AutocodeDaemon

## 🎯 Propósito
`AutocodeDaemon` es el orquestador central del sistema de monitoreo continuo. Su responsabilidad es ejecutar periódicamente las diferentes verificaciones (`DocChecker`, `GitAnalyzer`, `TestChecker`), mantener el estado de los resultados y proporcionar esta información a la API.

## 🏗️ Arquitectura
1.  **Inicialización**: Al crearse, el daemon instancia todos los componentes de verificación necesarios (`DocChecker`, `GitAnalyzer`, `TestChecker`) y un `Scheduler` para programar las tareas.
2.  **Configuración de Tareas**: Utiliza el `Scheduler` para registrar las diferentes verificaciones como tareas periódicas. El intervalo de cada tarea se lee desde la configuración (`autocode_config.yml`).
3.  **Ejecución de Verificaciones**: Cada función de verificación (ej. `run_doc_check`) invoca al componente del `core` correspondiente, procesa sus resultados para crear un objeto `CheckResult` estandarizado, y almacena este resultado en un diccionario de estado.
4.  **Ciclo de Vida**: El daemon tiene métodos `start()` y `stop()` que son gestionados por el servidor FastAPI. `start()` ejecuta una ronda inicial de todas las verificaciones y luego inicia el bucle del planificador.
5.  **Interfaz de Estado**: Proporciona métodos (`get_daemon_status`, `get_all_results`) para que la API pueda consultar el estado actual del sistema en cualquier momento.

## 📋 Responsabilidades
- **Orquestar Verificaciones**: Gestiona la ejecución periódica de todas las verificaciones del sistema.
- **Mantener el Estado**: Almacena el último resultado de cada verificación en memoria.
- **Cargar Configuración**: Carga y aplica la configuración del proyecto desde `autocode_config.yml`.
- **Permitir Ejecución Manual**: Ofrece un método para disparar una verificación específica de forma manual.
- **Integrarse con el Scheduler**: Delega la programación y ejecución de las tareas al `Scheduler`.

## 🔗 Dependencias
### Internas
- `autocode.orchestration.scheduler.Scheduler`: Para la programación de tareas.
- Todos los componentes del `core` que realizan verificaciones (`DocChecker`, `GitAnalyzer`, `TestChecker`).
- `autocode.api.models`: Para las estructuras de datos de resultados y estado.
- `autocode.cli.load_config`: Para cargar la configuración.

### Externas
- `asyncio`: Para la gestión de tareas asíncronas.
- `logging`: Para el registro de eventos.

## 📊 Interfaces Públicas
### `class AutocodeDaemon`
-   `__init__(self, project_root: Path, config: AutocodeConfig = None)`: Constructor.
-   `start(self)`: Inicia el bucle principal del daemon y las tareas programadas.
-   `stop(self)`: Detiene el daemon y sus tareas.
-   `run_doc_check(self) -> CheckResult`: Ejecuta la verificación de documentación.
-   `run_git_check(self) -> CheckResult`: Ejecuta el análisis de Git.
-   `run_test_check(self) -> CheckResult`: Ejecuta la verificación de tests.
-   `run_check_manually(self, check_name: str) -> CheckResult`: Dispara una verificación específica.
-   `get_daemon_status(self) -> DaemonStatus`: Devuelve el estado actual del daemon.
-   `get_all_results(self) -> Dict[str, CheckResult]`: Devuelve los últimos resultados de todas las verificaciones.
-   `update_config(self, config: AutocodeConfig)`: Permite actualizar la configuración en caliente.

## 💡 Patrones de Uso
El `AutocodeDaemon` es instanciado y gestionado exclusivamente por el `api/server.py`. No está diseñado para ser utilizado directamente por el usuario final, sino para ser el motor detrás del servidor de monitoreo.

## ⚠️ Consideraciones
- El estado del daemon (los resultados de las verificaciones) se mantiene en memoria. Si el proceso se reinicia, este estado se pierde y se regenera en la siguiente ejecución de las verificaciones.
- La lógica de cada verificación está encapsulada en su propio método, lo que facilita la adición de nuevas verificaciones en el futuro.
