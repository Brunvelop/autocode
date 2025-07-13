# Items from python_analyzer.py

**Source:** `C:\Users\bruno\Desktop\autocode\autocode\core\design\analyzers\python_analyzer.py`  
**Type:** python

**Metrics:**
- Total Classes: 1
- Total Functions: 0
- Total Imports: 4
- Total Loc: 323
- Average Methods Per Class: 8.0

## Classes

### PythonAnalyzer

**Line:** 13  
**LOC:** 311  

```mermaid
classDiagram
    class PythonAnalyzer {
        +get_supported_extensions() -> List[str]
        +analyze_file(file_path: Path) -> AnalysisResult
        -_extract_class_info(node: ast.ClassDef, file_path: Path) -> Dict[str, Any]
        -_extract_function_info(node: ast.FunctionDef) -> Dict[str, Any]
        -_extract_import_info(node: ast.stmt) -> Dict[str, Any]
        -_extract_method_info(node: ast.FunctionDef) -> Dict[str, Any]
        -_extract_attribute_info(target: ast.Name, assign_node: ast.Assign) -> Dict[str, Any]
        -_get_type_annotation(annotation: ast.expr) -> str
    }
    BaseAnalyzer <|-- PythonAnalyzer

```

