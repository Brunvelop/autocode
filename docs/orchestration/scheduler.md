# Autocode Scheduler

## 🎯 Propósito

El módulo scheduler.py proporciona un sistema simple pero robusto de programación de tareas para la ejecución periódica de verificaciones. La clase Scheduler gestiona tareas programadas con intervalos configurables, permitiendo ejecución asíncrona y control dinámico de la habilitación/deshabilitación de tareas.

## 🏗️ Arquitectura

```mermaid
graph TB
    subgraph "Scheduler Architecture"
        SCHEDULER[Scheduler<br/>Main Controller]
        TASKS[tasks: Dict[str, ScheduledTask]<br/>Task Storage]
        STOPEVENT[_stop_event: asyncio.Event<br/>Shutdown Control]
        
        subgraph "ScheduledTask"
            NAME[name: str]
            FUNC[func: Callable]
            INTERVAL[interval_seconds: int]
            LASTRUN[last_run: Optional[datetime]]
            NEXTRUN[next_run: Optional[datetime]]
            ENABLED[enabled: bool]
        end
        
        subgraph "Task Management"
            ADD[add_task()]
            REMOVE[remove_task()]
            ENABLE[enable_task()]
            DISABLE[disable_task()]
            UPDATE[update_task_interval()]
        end
        
        subgraph "Execution Engine"
            START[start()]
            RUNTASK[run_task()]
            STOP[stop()]
            LOOP[Main Loop]
        end
        
        subgraph "Status & Monitoring"
            STATUS[get_task_status()]
            ALLSTATUS[get_all_tasks_status()]
            RUNNING[is_running()]
        end
    end
    
    SCHEDULER --> TASKS
    SCHEDULER --> STOPEVENT
    
    TASKS --> NAME
    TASKS --> FUNC
    TASKS --> INTERVAL
    TASKS --> LASTRUN
    TASKS --> NEXTRUN
    TASKS --> ENABLED
    
    SCHEDULER --> ADD
    SCHEDULER --> REMOVE
    SCHEDULER --> ENABLE
    SCHEDULER --> DISABLE
    SCHEDULER --> UPDATE
    
    SCHEDULER --> START
    SCHEDULER --> RUNTASK
    SCHEDULER --> STOP
    SCHEDULER --> LOOP
    
    SCHEDULER --> STATUS
    SCHEDULER --> ALLSTATUS
    SCHEDULER --> RUNNING
    
    START --> LOOP
    LOOP --> RUNTASK
    RUNTASK --> TASKS
    
    classDef scheduler fill:#e1f5fe
    classDef task fill:#f3e5f5
    classDef management fill:#e8f5e8
    classDef execution fill:#fff3e0
    classDef monitoring fill:#ffebee
    
    class SCHEDULER,TASKS,STOPEVENT scheduler
    class NAME,FUNC,INTERVAL,LASTRUN,NEXTRUN,ENABLED task
    class ADD,REMOVE,ENABLE,DISABLE,UPDATE management
    class START,RUNTASK,STOP,LOOP execution
    class STATUS,ALLSTATUS,RUNNING monitoring
```

## 📋 Responsabilidades

### Responsabilidades Principales
- **Task Scheduling**: Gestionar la programación y ejecución de tareas con intervalos configurables
- **Timing Management**: Calcular y controlar cuándo debe ejecutarse cada tarea basado en intervalos
- **Async Execution**: Ejecutar tareas de forma asíncrona sin bloquear el hilo principal
- **Dynamic Control**: Permitir habilitación/deshabilitación de tareas en tiempo de ejecución
- **Error Handling**: Manejar errores en tareas individuales sin afectar el funcionamiento general
- **State Management**: Mantener estado de ejecución y timing de cada tarea
- **Graceful Shutdown**: Proporcionar mecanismo limpio de parada del scheduler

### Lo que NO hace
- No persiste estado de tareas entre reinicios
- No implementa lógica de negocio específica (delegado a las funciones de tarea)
- No maneja dependencias entre tareas
- No proporciona scheduling basado en cron o calendarios complejos

## 🔗 Dependencias

### Internas
Ninguna - es un módulo independiente que no depende de otros componentes del sistema.

### Externas
- `asyncio`: Programación asíncrona y eventos
- `logging`: Sistema de logging para debugging
- `datetime`: Manipulación de fechas y timestamps
- `timedelta`: Cálculo de intervalos de tiempo
- `dataclasses`: Definición de la estructura ScheduledTask
- `typing`: Type hints para mejor documentación del código

## 📊 Interfaces Públicas

### Clase Principal

#### `ScheduledTask`

**Definición**:
```python
@dataclass
class ScheduledTask:
    """Represents a scheduled task."""
    name: str
    func: Callable
    interval_seconds: int
    last_run: Optional[datetime] = None
    next_run: Optional[datetime] = None
    enabled: bool = True
    
    def __post_init__(self):
        if self.next_run is None:
            self.next_run = datetime.now() + timedelta(seconds=self.interval_seconds)
```

**Campos**:
- `name`: Identificador único de la tarea
- `func`: Función a ejecutar (puede ser sync o async)
- `interval_seconds`: Intervalo en segundos entre ejecuciones
- `last_run`: Timestamp de la última ejecución (None si nunca se ejecutó)
- `next_run`: Timestamp de la próxima ejecución programada
- `enabled`: Estado de habilitación de la tarea

#### `Scheduler`

**Constructor**:
```python
def __init__(self):
    """Initialize scheduler with empty task list."""
    self.tasks: Dict[str, ScheduledTask] = {}
    self.running = False
    self.logger = logging.getLogger(__name__)
    self._stop_event = asyncio.Event()
```

**Métodos de Gestión de Tareas**:
```python
def add_task(self, name: str, func: Callable, interval_seconds: int, enabled: bool = True) -> None:
    """Add a task to the scheduler."""

def remove_task(self, name: str) -> None:
    """Remove a task from the scheduler."""

def enable_task(self, name: str) -> None:
    """Enable a task."""

def disable_task(self, name: str) -> None:
    """Disable a task."""

def update_task_interval(self, name: str, interval_seconds: int) -> None:
    """Update task interval and recalculate next run time."""
```

**Métodos de Ejecución**:
```python
async def start(self) -> None:
    """Start the scheduler main loop."""

def stop(self) -> None:
    """Stop the scheduler gracefully."""

async def run_task(self, task: ScheduledTask) -> None:
    """Execute a single task."""
```

**Métodos de Monitoreo**:
```python
def get_task_status(self, name: str) -> Optional[Dict]:
    """Get status of a specific task."""

def get_all_tasks_status(self) -> Dict[str, Dict]:
    """Get status of all tasks."""

def is_running(self) -> bool:
    """Check if scheduler is running."""
```

## 🔧 Gestión de Tareas

### Añadir Tareas
```python
scheduler = Scheduler()

# Añadir tarea básica
scheduler.add_task(
    name="doc_check",
    func=my_doc_check_function,
    interval_seconds=300,  # 5 minutos
    enabled=True
)

# Añadir tarea async
async def async_task():
    print("Ejecutando tarea async")

scheduler.add_task(
    name="async_check",
    func=async_task,
    interval_seconds=180,  # 3 minutos
    enabled=True
)
```

### Control Dinámico de Tareas
```python
# Deshabilitar tarea temporalmente
scheduler.disable_task("doc_check")

# Cambiar intervalo de tarea
scheduler.update_task_interval("doc_check", 600)  # Cambiar a 10 minutos

# Rehabilitar tarea
scheduler.enable_task("doc_check")

# Remover tarea completamente
scheduler.remove_task("old_task")
```

### Ejecución del Scheduler
```python
import asyncio

async def main():
    scheduler = Scheduler()
    
    # Configurar tareas
    scheduler.add_task("task1", my_function, 60)
    scheduler.add_task("task2", my_other_function, 120)
    
    # Iniciar scheduler
    await scheduler.start()

# Ejecutar
asyncio.run(main())
```

## 💡 Flujo de Trabajo

### Ciclo de Vida del Scheduler

```python
# 1. Inicialización
scheduler = Scheduler()

# 2. Configuración de tareas
scheduler.add_task("doc_check", check_docs, 300)
scheduler.add_task("git_check", check_git, 180)

# 3. Inicio (ejecuta loop principal)
await scheduler.start()  # Loop infinito hasta stop()

# 4. Parada (desde otro contexto)
scheduler.stop()  # Señala al loop que pare
```

### Loop Principal
```python
async def start(self):
    """Main scheduler loop."""
    if self.running:
        return
    
    self.running = True
    self.logger.info("Starting scheduler")
    
    try:
        while self.running:
            current_time = datetime.now()
            
            # Identificar tareas a ejecutar
            tasks_to_run = []
            for task in self.tasks.values():
                if not task.enabled:
                    continue
                
                if task.next_run and current_time >= task.next_run:
                    tasks_to_run.append(task)
            
            # Ejecutar tareas concurrentemente
            if tasks_to_run:
                await asyncio.gather(*[self.run_task(task) for task in tasks_to_run])
            
            # Esperar antes del próximo check (con posibilidad de stop)
            try:
                await asyncio.wait_for(self._stop_event.wait(), timeout=1.0)
                break  # Stop event was set
            except asyncio.TimeoutError:
                pass  # Continue the loop
                
    except Exception as e:
        self.logger.error(f"Scheduler error: {e}")
    finally:
        self.running = False
        self.logger.info("Scheduler stopped")
```

### Ejecución de Tareas
```python
async def run_task(self, task: ScheduledTask):
    """Execute a single task with error handling."""
    try:
        self.logger.info(f"Running task '{task.name}'")
        start_time = datetime.now()
        
        # Ejecutar función (sync o async)
        if asyncio.iscoroutinefunction(task.func):
            await task.func()
        else:
            task.func()
        
        # Actualizar timing
        task.last_run = start_time
        task.next_run = start_time + timedelta(seconds=task.interval_seconds)
        
        duration = (datetime.now() - start_time).total_seconds()
        self.logger.info(f"Task '{task.name}' completed in {duration:.2f}s")
        
    except Exception as e:
        self.logger.error(f"Error running task '{task.name}': {e}")
        # Aún actualizar next_run para continuar el schedule
        task.last_run = datetime.now()
        task.next_run = task.last_run + timedelta(seconds=task.interval_seconds)
```

## 📊 Monitoreo y Estado

### Estado de Tarea Individual
```python
def get_task_status(self, name: str) -> Optional[Dict]:
    """Get comprehensive status of a specific task."""
    if name not in self.tasks:
        return None
    
    task = self.tasks[name]
    return {
        "name": task.name,
        "enabled": task.enabled,
        "interval_seconds": task.interval_seconds,
        "last_run": task.last_run.isoformat() if task.last_run else None,
        "next_run": task.next_run.isoformat() if task.next_run else None,
        "seconds_until_next": (task.next_run - datetime.now()).total_seconds() if task.next_run else None
    }
```

**Ejemplo de Respuesta**:
```json
{
  "name": "doc_check",
  "enabled": true,
  "interval_seconds": 300,
  "last_run": "2025-01-07T14:30:00.123456",
  "next_run": "2025-01-07T14:35:00.123456",
  "seconds_until_next": 245.8
}
```

### Estado de Todas las Tareas
```python
def get_all_tasks_status(self) -> Dict[str, Dict]:
    """Get status of all tasks."""
    return {name: self.get_task_status(name) for name in self.tasks}
```

**Ejemplo de Respuesta**:
```json
{
  "doc_check": {
    "name": "doc_check",
    "enabled": true,
    "interval_seconds": 300,
    "last_run": "2025-01-07T14:30:00.123456",
    "next_run": "2025-01-07T14:35:00.123456",
    "seconds_until_next": 245.8
  },
  "git_check": {
    "name": "git_check",
    "enabled": false,
    "interval_seconds": 180,
    "last_run": null,
    "next_run": null,
    "seconds_until_next": null
  }
}
```

## 🔧 Configuración Avanzada

### Intervalos Dinámicos
```python
# Cambiar intervalo en tiempo de ejecución
def update_task_interval(self, name: str, interval_seconds: int):
    """Update task interval and recalculate next run."""
    if name in self.tasks:
        task = self.tasks[name]
        task.interval_seconds = interval_seconds
        
        # Recalcular próxima ejecución
        if task.last_run:
            task.next_run = task.last_run + timedelta(seconds=interval_seconds)
        else:
            task.next_run = datetime.now() + timedelta(seconds=interval_seconds)
        
        self.logger.info(f"Updated task '{name}' interval to {interval_seconds}s")
```

### Configuración desde Diccionario
```python
def setup_tasks_from_config(scheduler: Scheduler, config: Dict):
    """Setup tasks from configuration dictionary."""
    for task_name, task_config in config.items():
        scheduler.add_task(
            name=task_name,
            func=task_config["function"],
            interval_seconds=task_config["interval"],
            enabled=task_config.get("enabled", True)
        )

# Ejemplo de uso
config = {
    "doc_check": {
        "function": check_documentation,
        "interval": 300,
        "enabled": True
    },
    "git_check": {
        "function": analyze_git_changes,
        "interval": 180,
        "enabled": True
    }
}

setup_tasks_from_config(scheduler, config)
```

## ⚠️ Consideraciones

### Manejo de Errores
- **Errores en Tareas**: Los errores en tareas individuales no detienen el scheduler
- **Logging Detallado**: Todos los errores se registran con información de debugging
- **Recovery Automático**: Las tareas se reprograman automáticamente después de errores
- **Graceful Degradation**: El scheduler continúa funcionando aunque fallen tareas específicas

### Limitaciones
- **Precisión de Timing**: Los intervalos son aproximados debido al polling de 1 segundo
- **No Persistencia**: Las tareas no se guardan entre reinicios
- **Memoria**: Las tareas deshabilitadas permanecen en memoria hasta ser removidas explícitamente
- **Concurrencia**: Múltiples instancias del mismo task pueden ejecutarse simultáneamente si se superponen

### Mejores Prácticas
- **Intervalos Mínimos**: Usar intervalos de al menos 10 segundos para evitar sobrecarga
- **Funciones Idempotentes**: Las funciones de tarea deben ser idempotentes
- **Manejo de Excepciones**: Las funciones de tarea deben manejar sus propias excepciones
- **Resource Management**: Limpiar recursos apropiadamente en funciones de tarea

## 🧪 Testing

### Test Básico de Funcionalidad
```python
import pytest
import asyncio
from datetime import datetime

def test_scheduler_initialization():
    scheduler = Scheduler()
    assert len(scheduler.tasks) == 0
    assert not scheduler.is_running()

def test_add_task():
    scheduler = Scheduler()
    
    def test_func():
        pass
    
    scheduler.add_task("test", test_func, 60)
    
    assert "test" in scheduler.tasks
    assert scheduler.tasks["test"].name == "test"
    assert scheduler.tasks["test"].interval_seconds == 60
    assert scheduler.tasks["test"].enabled == True

def test_task_control():
    scheduler = Scheduler()
    scheduler.add_task("test", lambda: None, 60)
    
    # Test disable
    scheduler.disable_task("test")
    assert not scheduler.tasks["test"].enabled
    
    # Test enable
    scheduler.enable_task("test")
    assert scheduler.tasks["test"].enabled
    
    # Test remove
    scheduler.remove_task("test")
    assert "test" not in scheduler.tasks
```

### Test de Ejecución
```python
@pytest.mark.asyncio
async def test_task_execution():
    scheduler = Scheduler()
    
    # Variable para verificar ejecución
    execution_count = 0
    
    def test_task():
        nonlocal execution_count
        execution_count += 1
    
    # Añadir tarea con intervalo corto
    scheduler.add_task("test", test_task, 1)  # 1 segundo
    
    # Ejecutar scheduler brevemente
    task = asyncio.create_task(scheduler.start())
    await asyncio.sleep(2.5)  # Esperar 2.5 segundos
    scheduler.stop()
    
    # Verificar que la tarea se ejecutó al menos 2 veces
    assert execution_count >= 2
```

### Test de Funciones Async
```python
@pytest.mark.asyncio
async def test_async_task_execution():
    scheduler = Scheduler()
    
    execution_count = 0
    
    async def async_task():
        nonlocal execution_count
        execution_count += 1
        await asyncio.sleep(0.1)  # Simular trabajo async
    
    scheduler.add_task("async_test", async_task, 1)
    
    # Test execution
    task = asyncio.create_task(scheduler.start())
    await asyncio.sleep(2.5)
    scheduler.stop()
    
    assert execution_count >= 2
```

## 🔄 Patrones de Uso

### Scheduler Simple
```python
async def simple_scheduler_example():
    scheduler = Scheduler()
    
    def print_time():
        print(f"Current time: {datetime.now()}")
    
    # Añadir tarea que imprime la hora cada 30 segundos
    scheduler.add_task("time_printer", print_time, 30)
    
    # Ejecutar
    await scheduler.start()

# Ejecutar
asyncio.run(simple_scheduler_example())
```

### Scheduler con Control Dinámico
```python
class DynamicScheduler:
    def __init__(self):
        self.scheduler = Scheduler()
        self.setup_initial_tasks()
    
    def setup_initial_tasks(self):
        self.scheduler.add_task("health_check", self.health_check, 60)
        self.scheduler.add_task("cleanup", self.cleanup, 300)
    
    def health_check(self):
        print("Running health check...")
        
        # Ajustar intervalo basado en condiciones
        if self.is_system_busy():
            self.scheduler.update_task_interval("health_check", 120)  # Reducir frecuencia
        else:
            self.scheduler.update_task_interval("health_check", 30)   # Aumentar frecuencia
    
    def cleanup(self):
        print("Running cleanup...")
    
    def is_system_busy(self):
        # Lógica para determinar si el sistema está ocupado
        return False
    
    async def run(self):
        await self.scheduler.start()

# Uso
dynamic_scheduler = DynamicScheduler()
asyncio.run(dynamic_scheduler.run())
```

### Scheduler con Configuración Externa
```python
import yaml

class ConfigurableScheduler:
    def __init__(self, config_file: str):
        self.scheduler = Scheduler()
        self.load_config(config_file)
    
    def load_config(self, config_file: str):
        with open(config_file, 'r') as f:
            config = yaml.safe_load(f)
        
        for task_name, task_config in config['tasks'].items():
            function = self.get_function_by_name(task_config['function'])
            self.scheduler.add_task(
                name=task_name,
                func=function,
                interval_seconds=task_config['interval'],
                enabled=task_config.get('enabled', True)
            )
    
    def get_function_by_name(self, function_name: str):
        # Mapeo de nombres a funciones
        functions = {
            'health_check': self.health_check,
            'backup': self.backup,
            'monitor': self.monitor
        }
        return functions.get(function_name)
    
    def health_check(self):
        print("Health check...")
    
    def backup(self):
        print("Backup...")
    
    def monitor(self):
        print("Monitor...")
    
    async def run(self):
        await self.scheduler.start()

# config.yml:
# tasks:
#   health:
#     function: health_check
#     interval: 60
#     enabled: true
#   backup:
#     function: backup
#     interval: 3600
#     enabled: true

# Uso
scheduler = ConfigurableScheduler("config.yml")
asyncio.run(scheduler.run())
```

## 🚀 Casos de Uso

### Monitoreo de Sistema
```python
# Configuración para monitoreo de sistema
scheduler.add_task("cpu_check", monitor_cpu, 30)
scheduler.add_task("memory_check", monitor_memory, 60) 
scheduler.add_task("disk_check", monitor_disk, 300)
scheduler.add_task("network_check", monitor_network, 120)
```

### Mantenimiento Automático
```python
# Configuración para tareas de mantenimiento
scheduler.add_task("log_rotation", rotate_logs, 3600)      # Cada hora
scheduler.add_task("cache_cleanup", cleanup_cache, 1800)   # Cada 30 min
scheduler.add_task("temp_cleanup", cleanup_temp, 7200)     # Cada 2 horas
scheduler.add_task("backup", backup_data, 86400)          # Cada día
```

### Desarrollo y Testing
```python
# Configuración para desarrollo
scheduler.add_task("doc_check", check_documentation, 300)  # Cada 5 min
scheduler.add_task("test_run", run_tests, 600)            # Cada 10 min
scheduler.add_task("lint_check", run_linter, 900)         # Cada 15 min
scheduler.add_task("build_check", check_build, 1200)      # Cada 20 min
