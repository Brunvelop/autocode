# Items from code_to_design.py

**Source:** `C:\Users\bruno\Desktop\autocode\autocode\core\design\code_to_design.py`  
**Type:** python

**Metrics:**
- Total Classes: 1
- Total Functions: 0
- Total Imports: 7
- Total Loc: 710
- Average Methods Per Class: 19.0

## Classes

### CodeToDesign

**Line:** 19  
**LOC:** 692  

```mermaid
classDiagram
    class CodeToDesign {
        -__init__(project_root: Path, config: Dict[str, Any])
        -_normalize_config(config: Dict[str, Any]) -> Dict[str, Any]
        -_initialize_analyzers() -> Dict[str, Any]
        -_initialize_generators() -> Dict[str, Any]
        +generate_visual_index(analysis_results: Dict[str, Any], project_name: Optional[str]) -> str
        -_generate_architecture_diagram(module_tree: Dict[str, Any], project_name: str) -> str
        -_generate_child_nodes(children: Dict[str, Any], parent_id: str, node_counter: int, module_icons: Dict[str, str], indent_level: int) -> Tuple[str, int]
        -_generate_module_details_section(module_tree: Dict[str, Any]) -> str
        +generate_markdown_files(analysis_results: Dict[str, Any], output_dir: Optional[Path]) -> List[Path]
        -_generate_module_files(module_dir: str, module_info: Dict[str, Any], target_dir: Path) -> List[Path]
        -_generate_module_overview(module_dir: str, module_info: Dict[str, Any]) -> str
        -_generate_analysis_files(analysis_data: Dict[str, Any], target_dir: Path) -> List[Path]
        -_generate_items_content(analysis_data: Dict[str, Any]) -> str
        -_generate_item_content(item: Dict[str, Any], item_type: str) -> str
        +generate_design(directory: str, patterns: Optional) -> Dict[str, Any]
        -_merge_analysis_results(combined_results: Dict[str, Any], new_results: Dict[str, Any]) -> Any
        +get_analyzer_info() -> Dict[str, Any]
        +get_generator_info() -> Dict[str, Any]
        +get_system_info() -> Dict[str, Any]
    }

```

