# Items from component_tree_generator.py

**Source:** `C:\Users\bruno\Desktop\autocode\autocode\core\design\diagrams\component_tree_generator.py`  
**Type:** python

**Metrics:**
- Total Classes: 1
- Total Functions: 0
- Total Imports: 2
- Total Loc: 307
- Average Methods Per Class: 6.0

## Classes

### ComponentTreeGenerator

**Line:** 10  
**LOC:** 298  

```mermaid
classDiagram
    class ComponentTreeGenerator {
        +get_diagram_format() -> str
        +supports_diagram_type(diagram_type: str) -> bool
        +generate_diagram(data: Dict[str, Any], diagram_type: str) -> str
        +generate_component_tree_diagram(analysis_data: Dict[str, Any]) -> str
        -_add_component_relationships(diagram: str, modules: Dict, nodes_added: set) -> str
        +generate_component_summary(analysis_data: Dict[str, Any]) -> str
    }
    BaseGenerator <|-- ComponentTreeGenerator

```

