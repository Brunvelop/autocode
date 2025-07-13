# Items from markdown_exporter.py

**Source:** `C:\Users\bruno\Desktop\autocode\autocode\core\design\diagrams\markdown_exporter.py`  
**Type:** python

**Metrics:**
- Total Classes: 1
- Total Functions: 0
- Total Imports: 3
- Total Loc: 475
- Average Methods Per Class: 12.0

## Classes

### MarkdownExporter

**Line:** 14  
**LOC:** 462  

```mermaid
classDiagram
    class MarkdownExporter {
        -__init__(output_base: Path, config: Dict[str, Any], utils)
        +export(analysis_results: Dict[str, Any], generators: Dict[str, Any]) -> List[Path]
        +generate_markdown_files(analysis_results: Dict[str, Any], generators: Dict[str, Any], output_dir: Optional[Path]) -> List[Path]
        +generate_visual_index(analysis_results: Dict[str, Any], generators: Dict[str, Any], project_name: Optional[str]) -> str
        -_generate_architecture_diagram(module_tree: Dict[str, Any], project_name: str) -> str
        -_generate_child_nodes(children: Dict[str, Any], parent_id: str, node_counter: int, module_icons: Dict[str, str], indent_level: int) -> Tuple[str, int]
        -_generate_module_details_section(module_tree: Dict[str, Any]) -> str
        -_generate_module_files(module_dir: str, module_info: Dict[str, Any], target_dir: Path, generators: Dict[str, Any]) -> List[Path]
        -_generate_module_overview(module_dir: str, module_info: Dict[str, Any]) -> str
        -_generate_analysis_files(analysis_data: Dict[str, Any], target_dir: Path, generators: Dict[str, Any]) -> List[Path]
        -_generate_items_content(analysis_data: Dict[str, Any], generators: Dict[str, Any]) -> str
        -_generate_item_content(item: Dict[str, Any], item_type: str, generators: Dict[str, Any]) -> str
    }

```

