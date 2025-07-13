# Items from analyzer.py

**Source:** `C:\Users\bruno\Desktop\autocode\autocode\core\design\analyzers\javascript\analyzer.py`  
**Type:** python

**Metrics:**
- Total Classes: 1
- Total Functions: 0
- Total Imports: 4
- Total Loc: 303
- Average Methods Per Class: 10.0

## Classes

### JavaScriptAnalyzer

**Line:** 14  
**LOC:** 290  

```mermaid
classDiagram
    class JavaScriptAnalyzer {
        -__init__(project_root: Path, config: Dict[str, Any])
        +get_supported_extensions() -> List[str]
        +analyze_file(file_path: Path) -> AnalysisResult
        -_extract_classes(content: str) -> List
        -_extract_functions(content: str) -> List
        -_extract_imports(content: str) -> List
        -_extract_exports(content: str) -> List
        -_extract_class_body(content: str, start_pos: int) -> str
        -_extract_methods_from_class_body(class_body: str) -> List
        -_get_line_number(content: str, position: int) -> int
    }
    BaseAnalyzer <|-- JavaScriptAnalyzer

```

