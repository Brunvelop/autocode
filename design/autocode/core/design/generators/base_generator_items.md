# Items from base_generator.py

**Source:** `C:\Users\bruno\Desktop\autocode\autocode\core\design\generators\base_generator.py`  
**Type:** python

**Metrics:**
- Total Classes: 1
- Total Functions: 0
- Total Imports: 2
- Total Loc: 68
- Average Methods Per Class: 5.0

## Classes

### BaseGenerator

**Line:** 10  
**LOC:** 59  

```mermaid
classDiagram
    class BaseGenerator {
        -__init__(config: Dict[str, Any])
        +generate_class_diagram(class_info: Dict) -> str
        +generate_diagram(data: Dict[str, Any], diagram_type: str) -> str
        +supports_diagram_type(diagram_type: str) -> bool
        +get_diagram_format() -> str
    }
    ABC <|-- BaseGenerator

```

