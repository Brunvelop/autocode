# Items from css_analyzer.py

**Source:** `C:\Users\bruno\Desktop\autocode\autocode\core\design\analyzers\web\css_analyzer.py`  
**Type:** python

**Metrics:**
- Total Classes: 1
- Total Functions: 0
- Total Imports: 4
- Total Loc: 412
- Average Methods Per Class: 15.0

## Classes

### CSSAnalyzer

**Line:** 14  
**LOC:** 399  

```mermaid
classDiagram
    class CSSAnalyzer {
        -__init__(project_root: Path, config: Dict[str, Any])
        +get_supported_extensions() -> List[str]
        +analyze_file(file_path: Path) -> AnalysisResult
        -_extract_rules(content: str) -> List
        -_extract_selectors(rules: List) -> List
        -_extract_all_properties(rules: List) -> List
        -_extract_media_queries(content: str) -> List
        -_extract_imports(content: str) -> List
        -_extract_variables(content: str) -> List
        -_classify_selector(selector: str) -> str
        -_calculate_specificity(selector: str) -> int
        -_categorize_property(property_name: str) -> str
        -_classify_media_query(condition: str) -> str
        -_classify_variable_value(value: str) -> str
        -_get_line_number(content: str, position: int) -> int
    }
    BaseAnalyzer <|-- CSSAnalyzer

```

