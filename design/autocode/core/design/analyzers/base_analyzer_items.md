# Items from base_analyzer.py

**Source:** `C:\Users\bruno\Desktop\autocode\autocode\core\design\analyzers\base_analyzer.py`  
**Type:** python

**Metrics:**
- Total Classes: 2
- Total Functions: 0
- Total Imports: 4
- Total Loc: 233
- Average Methods Per Class: 6.0

## Classes

### AnalysisResult

**Line:** 14  
**LOC:** 35  

```mermaid
classDiagram
    class AnalysisResult {
        -__init__(status: str, data: Dict[str, Any], errors: List[str], warnings: List[str], metadata: Dict[str, Any])
        +is_successful() -> bool
        +has_errors() -> bool
        +has_warnings() -> bool
    }

```

### BaseAnalyzer

**Line:** 51  
**LOC:** 183  

```mermaid
classDiagram
    class BaseAnalyzer {
        -__init__(project_root: Path, config: Dict[str, Any])
        +get_supported_extensions() -> List[str]
        +analyze_file(file_path: Path) -> AnalysisResult
        +analyze_directory(directory: str, patterns: Optional, recursive: bool, follow_symlinks: bool) -> AnalysisResult
        +get_file_patterns() -> List[str]
        +can_analyze_file(file_path: Path) -> bool
        +get_analyzer_name() -> str
        +get_analyzer_info() -> Dict[str, Any]
    }
    ABC <|-- BaseAnalyzer

```

