# Items from models.py

**Source:** `C:\Users\bruno\Desktop\autocode\autocode\api\models.py`  
**Type:** python

**Metrics:**
- Total Classes: 15
- Total Functions: 0
- Total Imports: 3
- Total Loc: 129
- Average Methods Per Class: 0.0

## Classes

### CheckResult

**Line:** 10  
**LOC:** 8  

```mermaid
classDiagram
    class CheckResult {
        +check_name: str
        +status: str
        +message: str
        +details: Optional
        +timestamp: datetime
        +duration_seconds: Optional[float]
    }
    BaseModel <|-- CheckResult

```

### DaemonStatus

**Line:** 20  
**LOC:** 6  

```mermaid
classDiagram
    class DaemonStatus {
        +is_running: bool
        +uptime_seconds: Optional[float]
        +last_check_run: Optional[datetime]
        +total_checks_run: int
    }
    BaseModel <|-- DaemonStatus

```

### CheckConfig

**Line:** 28  
**LOC:** 4  

```mermaid
classDiagram
    class CheckConfig {
        +enabled: bool
        +interval_minutes: int
    }
    BaseModel <|-- CheckConfig

```

### TokenConfig

**Line:** 34  
**LOC:** 5  

```mermaid
classDiagram
    class TokenConfig {
        +enabled: bool
        +threshold: int
        +model: str
    }
    BaseModel <|-- TokenConfig

```

### DaemonConfig

**Line:** 41  
**LOC:** 6  

```mermaid
classDiagram
    class DaemonConfig {
        +doc_check: CheckConfig
        +git_check: CheckConfig
        +test_check: CheckConfig
        +token_alerts: TokenConfig
    }
    BaseModel <|-- DaemonConfig

```

### ApiConfig

**Line:** 49  
**LOC:** 4  

```mermaid
classDiagram
    class ApiConfig {
        +port: int
        +host: str
    }
    BaseModel <|-- ApiConfig

```

### DocIndexConfig

**Line:** 55  
**LOC:** 6  

```mermaid
classDiagram
    class DocIndexConfig {
        +enabled: bool
        +output_path: str
        +auto_generate: bool
        +update_on_docs_change: bool
    }
    BaseModel <|-- DocIndexConfig

```

### DocsConfig

**Line:** 63  
**LOC:** 6  

```mermaid
classDiagram
    class DocsConfig {
        +enabled: bool
        +directories: List[str]
        +file_extensions: List[str]
        +exclude: List[str]
    }
    BaseModel <|-- DocsConfig

```

### TestConfig

**Line:** 71  
**LOC:** 7  

```mermaid
classDiagram
    class TestConfig {
        +enabled: bool
        +directories: List[str]
        +exclude: List[str]
        +test_frameworks: List[str]
        +auto_execute: bool
    }
    BaseModel <|-- TestConfig

```

### OpenCodeConfig

**Line:** 80  
**LOC:** 9  

```mermaid
classDiagram
    class OpenCodeConfig {
        +enabled: bool
        +model: str
        +max_tokens: int
        +debug: bool
        +config_path: str
        +quiet_mode: bool
        +json_output: bool
    }
    BaseModel <|-- OpenCodeConfig

```

### CodeToDesignConfig

**Line:** 91  
**LOC:** 8  

```mermaid
classDiagram
    class CodeToDesignConfig {
        +enabled: bool
        +output_dir: str
        +language: str
        +languages: List[str]
        +diagrams: List[str]
        +directories: List[str]
    }
    BaseModel <|-- CodeToDesignConfig

```

### AutocodeConfig

**Line:** 101  
**LOC:** 9  

```mermaid
classDiagram
    class AutocodeConfig {
        +daemon: DaemonConfig
        +api: ApiConfig
        +opencode: OpenCodeConfig
        +doc_index: DocIndexConfig
        +docs: DocsConfig
        +tests: TestConfig
        +code_to_design: CodeToDesignConfig
    }
    BaseModel <|-- AutocodeConfig

```

### StatusResponse

**Line:** 112  
**LOC:** 5  

```mermaid
classDiagram
    class StatusResponse {
        +daemon: DaemonStatus
        +checks: Dict[str, CheckResult]
        +config: AutocodeConfig
    }
    BaseModel <|-- StatusResponse

```

### CheckExecutionRequest

**Line:** 119  
**LOC:** 4  

```mermaid
classDiagram
    class CheckExecutionRequest {
        +check_name: str
        +force: bool
    }
    BaseModel <|-- CheckExecutionRequest

```

### CheckExecutionResponse

**Line:** 125  
**LOC:** 5  

```mermaid
classDiagram
    class CheckExecutionResponse {
        +success: bool
        +result: Optional[CheckResult]
        +error: Optional[str]
    }
    BaseModel <|-- CheckExecutionResponse

```

