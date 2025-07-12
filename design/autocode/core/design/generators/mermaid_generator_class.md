# Classes from mermaid_generator.py

Source: `autocode\core\design\generators\mermaid_generator.py`

## MermaidGenerator

**Metrics:** LOC: 69 | Methods: 2

```mermaid
classDiagram
    class MermaidGenerator {
        +get_diagram_format() -> str
        +generate_class_diagram(class_info: Dict) -> str
    }
    BaseGenerator <|-- MermaidGenerator

```

