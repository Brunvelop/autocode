# Items from general_utils.py

**Source:** `C:\Users\bruno\Desktop\autocode\autocode\core\design\utils\general_utils.py`  
**Type:** python

**Metrics:**
- Total Classes: 1
- Total Functions: 0
- Total Imports: 3
- Total Loc: 389
- Average Methods Per Class: 11.0

## Classes

### GeneralUtils

**Line:** 12  
**LOC:** 378  

```mermaid
classDiagram
    class GeneralUtils {
        -__init__(config: Dict[str, Any])
        +build_hierarchical_tree(flat_data: Dict[str, Any], key_path: str) -> Dict[str, Any]
        -_get_default_metrics() -> Dict[str, int]
        -_extract_items_from_module(module_info: Dict[str, Any]) -> List
        -_calculate_module_metrics(module_info: Dict[str, Any]) -> Dict[str, int]
        -_calculate_aggregate_metrics(tree: Dict[str, Any]) -> Any
        +count_tree_nodes(tree: Dict[str, Any]) -> int
        +generate_summary_stats(tree: Dict[str, Any]) -> Dict[str, Any]
        +filter_tree_by_criteria(tree: Dict[str, Any], min_items: int, include_types: Optional) -> Dict[str, Any]
        +export_tree_to_json(tree: Dict[str, Any], output_path: Path) -> Any
        +get_module_icons(custom_icons: Optional) -> Dict[str, str]
    }

```

