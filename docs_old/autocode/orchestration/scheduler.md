# scheduler.py

## 🎯 Propósito
Sistema de programación de tareas periódicas que ejecuta funciones a intervalos regulares de forma asíncrona. Proporciona gestión dinámica de tareas, soporte para funciones síncronas y asíncronas, y manejo robusto de errores.

## 🏗️ Arquitectura
```mermaid
graph TB
    A[Scheduler] --> B[ScheduledTask]
    A --> C[AsyncIO Event Loop]
    
    B --> D[Task Properties]
    D --> E[name: str]
    D --> F[func: Callable]
    D --> G[interval_seconds: int]
    D --> H[enabled: bool]
    D --> I[last_run: datetime]
    D --> J[next_run: datetime]
    
    C --> K[Task Execution]
    K --> L[Check Due Tasks]
    K --> M[Run Concurrently]
    K --> N[Update Timings]
    
    A --> O[Task Management]
    O --> P[add_task()]
    O --> Q[remove_task()]
    O --> R[enable_task()]
    O --> S[disable_task()]
    O --> T[update_task_interval()]
    
    A --> U[Status Monitoring]
    U --> V[get_task_status()]
    U --> W[get_all_tasks_status()]
    
    A --> X[Lifecycle Control]
    X --> Y[start()]
    X --> Z[stop()]
    X --> AA[is_running()]
```

## 📋 Responsabilidades
- **Programación de tareas**: Ejecutar funciones a intervalos regulares definidos
- **Gestión dinámica**: Añadir, eliminar, habilitar/deshabilitar tareas en tiempo real
- **Ejecución asíncrona**: Ejecutar múltiples tareas concurrentemente sin bloqueo
- **Manejo de errores**: Continuar operación aunque tareas individuales fallen
- **Monitoreo de estado**: Proporcionar información detallada sobre tareas y ejecuciones
- **Compatibilidad**: Soportar tanto funciones síncronas como asíncronas

## 🔗 Dependencias
### Internas
- `ScheduledTask` - Dataclass que representa una tarea programada

### Externas
- `asyncio` - Programación asíncrona y manejo de eventos
- `logging` - Sistema de logging para eventos y errores
- `datetime` - Manejo de fechas y cálculos de tiempo
- `timedelta` - Cálculos de intervalos de tiempo
- `typing` - Type hints para Callable, Dict, List, Optional
- `dataclasses` - Decorador dataclass para ScheduledTask

## 📊 Interfaces Públicas
### Clase ScheduledTask
```python
@dataclass
class ScheduledTask:
    name: str
    func: Callable
    interval_seconds: int
    last_run: Optional[datetime] = None
    next_run: Optional[datetime] = None
    enabled: bool = True
```

### Clase Scheduler
```python
class Scheduler:
    def __init__(self)
    def add_task(self, name: str, func: Callable, interval_seconds: int, enabled: bool = True)
    def remove_task(self, name: str)
    def enable_task(self, name: str)
    def disable_task(self, name: str)
    def update_task_interval(self, name: str, interval_seconds: int)
    def get_task_status(self, name: str) -> Optional[Dict]
    def get_all_tasks_status(self) -> Dict[str, Dict]
    async def run_task(self, task: ScheduledTask)
    async def start(self)
    def stop(self)
    def is_running(self) -> bool
```

## 🔧 Configuración
### Inicialización
```python
def __init__(self):
    self.tasks: Dict[str, ScheduledTask] = {}
    self.running = False
    self.logger = logging.getLogger(__name__)
    self._stop_event = asyncio.Event()
```

### Estructura de Datos
```python
# Almacenamiento de tareas
self.tasks: Dict[str, ScheduledTask] = {
    "task_name": ScheduledTask(
        name="task_name",
        func=some_function,
        interval_seconds=60,
        last_run=datetime.now(),
        next_run=datetime.now() + timedelta(seconds=60),
        enabled=True
    )
}
```

## 💡 Patrones de Uso
### Uso Básico
```python
# Crear scheduler
scheduler = Scheduler()

# Añadir tareas
def my_periodic_task():
    print("Task executed!")

scheduler.add_task("my_task", my_periodic_task, interval_seconds=30)

# Iniciar scheduler
await scheduler.start()

# Parar scheduler
scheduler.stop()
```

### Gestión de Tareas
```python
# Añadir tarea síncrona
def sync_task():
    print("Sync task")

scheduler.add_task("sync_task", sync_task, 60)

# Añadir tarea asíncrona
async def async_task():
    print("Async task")

scheduler.add_task("async_task", async_task, 120)

# Habilitar/deshabilitar tareas
scheduler.disable_task("sync_task")
scheduler.enable_task("sync_task")

# Actualizar intervalo
scheduler.update_task_interval("async_task", 300)

# Remover tarea
scheduler.remove_task("sync_task")
```

### Monitoreo de Estado
```python
# Estado de tarea específica
status = scheduler.get_task_status("my_task")
print(f"Enabled: {status['enabled']}")
print(f"Last run: {status['last_run']}")
print(f"Next run: {status['next_run']}")
print(f"Seconds until next: {status['seconds_until_next']}")

# Estado de todas las tareas
all_status = scheduler.get_all_tasks_status()
for task_name, task_status in all_status.items():
    print(f"{task_name}: {task_status['enabled']}")
```

## ⚠️ Consideraciones
### Funcionamiento
- **Ejecución concurrente**: Múltiples tareas pueden ejecutarse simultáneamente
- **Manejo de errores**: Errores en una tarea no afectan otras tareas
- **Precisión de tiempo**: Usa polling de 1 segundo para verificar tareas pendientes
- **Compatibilidad**: Detecta automáticamente si una función es síncrona o asíncrona

### Limitaciones
- **Precisión**: Máxima precisión de 1 segundo debido al polling
- **Persistencia**: Tareas se pierden al reiniciar el proceso
- **Concurrencia**: Tareas largas pueden solaparse si su duración excede el intervalo
- **Memoria**: Mantiene historial de ejecuciones en memoria

## 🧪 Testing
### Pruebas Básicas
```python
# Test inicialización
scheduler = Scheduler()
assert not scheduler.is_running()
assert len(scheduler.tasks) == 0

# Test añadir tarea
def test_task():
    pass

scheduler.add_task("test", test_task, 60)
assert "test" in scheduler.tasks
assert scheduler.tasks["test"].interval_seconds == 60
```

### Pruebas de Ejecución
```python
import asyncio
from unittest.mock import Mock

async def test_task_execution():
    scheduler = Scheduler()
    
    # Mock function
    mock_func = Mock()
    scheduler.add_task("test_task", mock_func, 1)
    
    # Start scheduler in background
    task = asyncio.create_task(scheduler.start())
    
    # Wait for task to run
    await asyncio.sleep(2)
    
    # Stop scheduler
    scheduler.stop()
    await task
    
    # Verify task was called
    assert mock_func.called
```

### Pruebas de Gestión
```python
def test_task_management():
    scheduler = Scheduler()
    
    def dummy_task():
        pass
    
    # Test add
    scheduler.add_task("test", dummy_task, 60)
    assert "test" in scheduler.tasks
    
    # Test enable/disable
    scheduler.disable_task("test")
    assert not scheduler.tasks["test"].enabled
    
    scheduler.enable_task("test")
    assert scheduler.tasks["test"].enabled
    
    # Test update interval
    scheduler.update_task_interval("test", 120)
    assert scheduler.tasks["test"].interval_seconds == 120
    
    # Test remove
    scheduler.remove_task("test")
    assert "test" not in scheduler.tasks
```

## 🔄 Flujo de Datos
### Flujo de Ejecución
1. **Inicio**: `start()` inicia el loop principal
2. **Verificación**: Cada segundo verifica tareas pendientes
3. **Selección**: Identifica tareas cuyo `next_run` ha llegado
4. **Ejecución**: Ejecuta tareas seleccionadas concurrentemente
5. **Actualización**: Actualiza `last_run` y `next_run` para cada tarea
6. **Continuación**: Repite el ciclo hasta que se llame `stop()`

### Flujo de Tarea Individual
```python
async def run_task(self, task: ScheduledTask):
    # 1. Log inicio
    self.logger.info(f"Running task '{task.name}'")
    start_time = datetime.now()
    
    # 2. Ejecutar función (sync o async)
    if asyncio.iscoroutinefunction(task.func):
        await task.func()
    else:
        task.func()
    
    # 3. Actualizar tiempos
    task.last_run = start_time
    task.next_run = start_time + timedelta(seconds=task.interval_seconds)
    
    # 4. Log completado
    duration = (datetime.now() - start_time).total_seconds()
    self.logger.info(f"Task '{task.name}' completed in {duration:.2f}s")
```

### Flujo de Manejo de Errores
```python
try:
    # Ejecutar tarea
    await task.func()
except Exception as e:
    # 1. Log error
    self.logger.error(f"Error running task '{task.name}': {e}")
    
    # 2. Actualizar tiempos para continuar programación
    task.last_run = datetime.now()
    task.next_run = task.last_run + timedelta(seconds=task.interval_seconds)
    
    # 3. Continuar con otras tareas (no propagar error)
```

## 📈 Métricas y Monitoreo
### Estado de Tarea
```python
{
    "name": "task_name",
    "enabled": True,
    "interval_seconds": 60,
    "last_run": "2025-01-07T12:00:00",
    "next_run": "2025-01-07T12:01:00",
    "seconds_until_next": 45.2
}
```

### Logging
```python
# Eventos importantes
logger.info(f"Added task '{name}' with {interval_seconds}s interval")
logger.info(f"Running task '{task.name}'")
logger.info(f"Task '{task.name}' completed in {duration:.2f}s")
logger.error(f"Error running task '{task.name}': {e}")
logger.info("Starting scheduler")
logger.info("Scheduler stopped")
```

### Cálculos de Tiempo
```python
# Tiempo hasta próxima ejecución
seconds_until_next = (task.next_run - datetime.now()).total_seconds()

# Actualización de próxima ejecución
task.next_run = task.last_run + timedelta(seconds=task.interval_seconds)

# Duración de ejecución
duration = (datetime.now() - start_time).total_seconds()
```

## 🚀 Extensibilidad
### Tareas Avanzadas
```python
# Tarea con parámetros
def parameterized_task(param1, param2):
    print(f"Task with {param1} and {param2}")

# Usar lambda o functools.partial
from functools import partial
scheduler.add_task("param_task", partial(parameterized_task, "value1", "value2"), 60)

# Tarea con estado
class StatefulTask:
    def __init__(self):
        self.counter = 0
    
    def run(self):
        self.counter += 1
        print(f"Task executed {self.counter} times")

stateful_task = StatefulTask()
scheduler.add_task("stateful", stateful_task.run, 30)
```

### Tareas Condicionales
```python
def conditional_task():
    if some_condition():
        print("Condition met, executing task")
    else:
        print("Condition not met, skipping")

scheduler.add_task("conditional", conditional_task, 60)
```

### Tareas con Cleanup
```python
async def cleanup_task():
    try:
        # Trabajo principal
        await do_main_work()
    finally:
        # Cleanup siempre se ejecuta
        await cleanup_resources()

scheduler.add_task("cleanup_task", cleanup_task, 300)
```

### Integración con Daemon
```python
# Uso típico en AutocodeDaemon
class AutocodeDaemon:
    def _setup_tasks(self):
        # Añadir tareas basadas en configuración
        if self.config.daemon.doc_check.enabled:
            self.scheduler.add_task(
                name="doc_check",
                func=self.run_doc_check,
                interval_seconds=self.config.daemon.doc_check.interval_minutes * 60,
                enabled=True
            )
    
    def update_config(self, config):
        # Actualizar tareas existentes
        self.scheduler.update_task_interval(
            "doc_check",
            config.daemon.doc_check.interval_minutes * 60
        )
        
        if config.daemon.doc_check.enabled:
            self.scheduler.enable_task("doc_check")
        else:
            self.scheduler.disable_task("doc_check")
```

### Monitoreo Avanzado
```python
def get_scheduler_metrics(scheduler):
    """Obtener métricas detalladas del scheduler."""
    all_tasks = scheduler.get_all_tasks_status()
    
    enabled_tasks = [task for task in all_tasks.values() if task['enabled']]
    disabled_tasks = [task for task in all_tasks.values() if not task['enabled']]
    
    next_execution = None
    if enabled_tasks:
        next_times = [task['seconds_until_next'] for task in enabled_tasks 
                     if task['seconds_until_next'] and task['seconds_until_next'] > 0]
        if next_times:
            next_execution = min(next_times)
    
    return {
        "total_tasks": len(all_tasks),
        "enabled_tasks": len(enabled_tasks),
        "disabled_tasks": len(disabled_tasks),
        "next_execution_in_seconds": next_execution,
        "is_running": scheduler.is_running()
    }
