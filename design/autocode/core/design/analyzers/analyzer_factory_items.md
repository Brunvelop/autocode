# Items from analyzer_factory.py

**Source:** `C:\Users\bruno\Desktop\autocode\autocode\core\design\analyzers\analyzer_factory.py`  
**Type:** python

**Metrics:**
- Total Classes: 2
- Total Functions: 2
- Total Imports: 9
- Total Loc: 204
- Average Methods Per Class: 7.0

## Classes

### AnalyzerRegistry

**Line:** 17  
**LOC:** 36  

```mermaid
classDiagram
    class AnalyzerRegistry {
        -__init__()
        +register_analyzer(name: str, analyzer_class: Type[BaseAnalyzer], extensions: List[str]) -> Any
        +get_analyzer(name: str) -> Optional
        +get_analyzer_for_extension(extension: str) -> Optional
        +list_analyzers() -> List[str]
        +get_supported_extensions() -> List[str]
    }

```

### AnalyzerFactory

**Line:** 70  
**LOC:** 135  

```mermaid
classDiagram
    class AnalyzerFactory {
        -__init__(project_root: Path, config: Dict[str, Any])
        -_register_builtin_analyzers() -> Any
        +create_analyzer(analyzer_type: str) -> Optional[BaseAnalyzer]
        +create_analyzer_for_file(file_path: Path) -> Optional[BaseAnalyzer]
        +get_analyzers_for_languages(languages: List[str]) -> Dict[str, BaseAnalyzer]
        +auto_detect_analyzers(directory: str) -> Dict[str, BaseAnalyzer]
        +get_available_analyzers() -> List[str]
        +get_supported_extensions() -> List[str]
    }

```

## Functions

### register_analyzer

**Line:** 59  
**LOC:** 4  
**Parameters:** name, analyzer_class, extensions  
**Returns:** Any  

### get_registry

**Line:** 65  
**LOC:** 3  
**Returns:** AnalyzerRegistry  

