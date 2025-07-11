# Classes from code_to_design.py

Source: `autocode\core\design\code_to_design.py`

## CodeToDesign

**Metrics:** LOC: 705 | Methods: 16

```mermaid
classDiagram
    class CodeToDesign {
        -__init__(project_root: Path, config: Dict[str, Any])
        -_extract_method_info(node: ast.FunctionDef) -> Dict[str, Any]
        -_extract_attribute_info(target: ast.Name, assign_node: ast.Assign) -> Dict[str, Any]
        -_get_type_annotation(annotation: ast.expr) -> str
        +analyze_directory(directory: str, pattern: str) -> Dict[str, Dict]
        +generate_mermaid_class_diagram(class_info: Dict) -> str
        -_build_module_tree(structures: Dict[str, Dict]) -> Dict[str, Any]
        -_calculate_aggregate_metrics(tree: Dict[str, Any]) -> Any
        +generate_visual_index(structures: Dict[str, Dict]) -> str
        -_count_modules(tree: Dict[str, Any]) -> int
        -_generate_mermaid_subgraphs(tree: Dict[str, Any], module_icons: Dict[str, str], node_counter: int, indent_level: int) -> Tuple[str, int]
        -_generate_click_declarations(nodes_info: List) -> str
        -_generate_navigation_hub(tree: Dict[str, Any], module_icons: Dict[str, str], level: int) -> str
        -_generate_module_details(tree: Dict[str, Any]) -> str
        +generate_markdown_files(structures: Dict[str, Dict]) -> List[Path]
        +generate_design(directory: str, pattern: str) -> Dict[str, Any]
    }

```

