# Items from class_diagram_generator.py

**Source:** `C:\Users\bruno\Desktop\autocode\autocode\core\design\diagrams\class_diagram_generator.py`  
**Type:** python

**Metrics:**
- Total Classes: 1
- Total Functions: 0
- Total Imports: 2
- Total Loc: 90
- Average Methods Per Class: 3.0

## Classes

### ClassDiagramGenerator

**Line:** 11  
**LOC:** 80  

```mermaid
classDiagram
    class ClassDiagramGenerator {
        +get_diagram_format() -> str
        +supports_diagram_type(diagram_type: str) -> bool
        +generate_class_diagram(class_info: Dict) -> str
    }
    BaseGenerator <|-- ClassDiagramGenerator

```

