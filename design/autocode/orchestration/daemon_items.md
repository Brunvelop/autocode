# Items from daemon.py

**Source:** `C:\Users\bruno\Desktop\autocode\autocode\orchestration\daemon.py`  
**Type:** python

**Metrics:**
- Total Classes: 1
- Total Functions: 0
- Total Imports: 15
- Total Loc: 493
- Average Methods Per Class: 11.0

## Classes

### AutocodeDaemon

**Line:** 21  
**LOC:** 473  

```mermaid
classDiagram
    class AutocodeDaemon {
        -__init__(project_root: Path, config: AutocodeConfig)
        -_setup_tasks()
        +run_doc_check() -> CheckResult
        +run_git_check() -> CheckResult
        +run_test_check() -> CheckResult
        +run_check_manually(check_name: str) -> CheckResult
        +get_daemon_status() -> DaemonStatus
        +get_all_results() -> Dict[str, CheckResult]
        +update_config(config: AutocodeConfig)
        +stop()
        +is_running() -> bool
    }

```

