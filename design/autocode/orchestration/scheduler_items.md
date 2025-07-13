# Items from scheduler.py

**Source:** `C:\Users\bruno\Desktop\autocode\autocode\orchestration\scheduler.py`  
**Type:** python

**Metrics:**
- Total Classes: 2
- Total Functions: 0
- Total Imports: 5
- Total Loc: 178
- Average Methods Per Class: 5.5

## Classes

### ScheduledTask

**Line:** 13  
**LOC:** 12  

```mermaid
classDiagram
    class ScheduledTask {
        -__post_init__()
    }

```

### Scheduler

**Line:** 27  
**LOC:** 152  

```mermaid
classDiagram
    class Scheduler {
        -__init__()
        +add_task(name: str, func: Callable, interval_seconds: int, enabled: bool)
        +remove_task(name: str)
        +enable_task(name: str)
        +disable_task(name: str)
        +update_task_interval(name: str, interval_seconds: int)
        +get_task_status(name: str) -> Optional[Dict]
        +get_all_tasks_status() -> Dict[str, Dict]
        +stop()
        +is_running() -> bool
    }

```

