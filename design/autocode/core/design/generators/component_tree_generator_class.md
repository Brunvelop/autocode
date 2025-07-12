# Classes from component_tree_generator.py

Source: `autocode\core\design\generators\component_tree_generator.py`

## ComponentTreeGenerator

**Metrics:** LOC: 258 | Methods: 5

```mermaid
classDiagram
    class ComponentTreeGenerator {
        +get_diagram_format() -> str
        +generate_class_diagram(class_info: Dict) -> str
        +generate_component_tree_diagram(analysis_data: Dict[str, Any]) -> str
        -_add_component_relationships(diagram: str, modules: Dict, nodes_added: set) -> str
        +generate_component_summary(analysis_data: Dict[str, Any]) -> str
    }
    BaseGenerator <|-- ComponentTreeGenerator

```

