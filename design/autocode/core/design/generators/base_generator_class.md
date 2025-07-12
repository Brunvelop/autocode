# Classes from base_generator.py

Source: `autocode\core\design\generators\base_generator.py`

## BaseGenerator

**Metrics:** LOC: 59 | Methods: 5

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

