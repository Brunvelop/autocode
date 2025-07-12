"""Utility functions for the design module.

This module contains shared utility functions used across the design module.
"""

from typing import Dict, Any, Tuple, List


def build_module_tree(structures: Dict[str, Dict]) -> Dict[str, Any]:
    """Build a hierarchical tree structure from flat module data.
    
    Args:
        structures: Extracted code structures organized by directory
        
    Returns:
        Hierarchical tree structure with aggregated metrics
    """
    tree = {}
    
    # First pass: Create the tree structure
    for module_dir, module_info in structures["modules"].items():
        if module_dir == ".":
            continue
            
        # Split path into parts
        parts = module_dir.replace('\\', '/').split('/')
        
        # Navigate/create tree structure
        current_level = tree
        path_so_far = []
        
        for part in parts:
            path_so_far.append(part)
            full_path = '/'.join(path_so_far)
            
            if part not in current_level:
                current_level[part] = {
                    "name": part,
                    "full_path": full_path,
                    "original_path": module_dir,
                    "children": {},
                    "classes": [],
                    "metrics": {"classes": 0, "loc": 0, "files": 0},
                    "is_leaf": False
                }
            
            current_level = current_level[part]["children"]
    
    # Second pass: Add data to leaf nodes only
    for module_dir, module_info in structures["modules"].items():
        if module_dir == ".":
            continue
            
        # Navigate to the correct node
        leaf_parts = module_dir.replace('\\', '/').split('/')
        leaf_node = tree
        for i, part in enumerate(leaf_parts):
            if i == len(leaf_parts) - 1:
                # Last part - this is our target node
                leaf_node = leaf_node[part]
            else:
                # Navigate to children
                leaf_node = leaf_node[part]["children"]
        
        # Only set as leaf if it has no children (which means it's a terminal node)
        if not leaf_node["children"]:
            leaf_node["is_leaf"] = True
            leaf_node["classes"] = module_info["classes"]
            leaf_node["metrics"] = {
                "classes": len(module_info["classes"]),
                "loc": sum(cls["loc"] for cls in module_info["classes"]),
                "files": len(module_info["files"])
            }
            leaf_node["original_path"] = module_dir
    
    # Calculate aggregate metrics for parent nodes
    calculate_aggregate_metrics(tree)
    
    return tree


def calculate_aggregate_metrics(tree: Dict[str, Any]) -> None:
    """Calculate aggregate metrics for all nodes in the tree.
    
    Args:
        tree: Module tree structure
    """
    for node_name, node in tree.items():
        if node["is_leaf"]:
            continue
            
        # Recursively calculate for children first
        if node["children"]:
            calculate_aggregate_metrics(node["children"])
            
            # Sum metrics from all children
            total_classes = 0
            total_loc = 0
            total_files = 0
            
            for child_name, child in node["children"].items():
                total_classes += child["metrics"]["classes"]
                total_loc += child["metrics"]["loc"]
                total_files += child["metrics"]["files"]
            
            node["metrics"] = {
                "classes": total_classes,
                "loc": total_loc,
                "files": total_files
            }


def count_modules(tree: Dict[str, Any]) -> int:
    """Count total modules in the tree.
    
    Args:
        tree: Module tree structure
        
    Returns:
        Total number of modules
    """
    count = 0
    for node in tree.values():
        count += 1
        if node["children"]:
            count += count_modules(node["children"])
    return count


def generate_mermaid_subgraphs(tree: Dict[str, Any], 
                              module_icons: Dict[str, str], node_counter: int, 
                              indent_level: int) -> Tuple[str, int, List[Dict[str, Any]]]:
    """Generate Mermaid subgraphs recursively.
    
    Args:
        tree: Module tree structure
        module_icons: Icon mapping for modules
        node_counter: Current node counter
        indent_level: Indentation level
        
    Returns:
        Tuple of (generated content, updated node counter, node info list)
    """
    content = ""
    indent = "    " * indent_level
    nodes_info = []
    
    for node_name, node in tree.items():
        icon_name = module_icons.get(node_name, f"📁 {node_name}")
        metrics = node["metrics"]
        
        if metrics["classes"] == 0:
            continue
            
        subgraph_title = f"{icon_name} [{metrics['classes']} Classes | {metrics['loc']} LOC]"
        content += f'{indent}subgraph "{subgraph_title}"\n'
        
        if node["is_leaf"]:
            # Add class nodes for leaf modules
            for cls in node["classes"]:
                node_id = f"C{node_counter}"
                node_counter += 1
                content += f'{indent}    {node_id}["{cls["name"]}<br/>LOC: {cls["loc"]}"]\n'
                
                # Store node info for link generation
                nodes_info.append({
                    "node_id": node_id,
                    "class_name": cls["name"],
                    "file_name": cls["file_name"],
                    "module_path": node["original_path"],
                    "loc": cls["loc"],
                    "num_methods": cls["num_methods"]
                })
        else:
            # Recursively add children
            child_content, node_counter, child_nodes = generate_mermaid_subgraphs(
                node["children"], module_icons, node_counter, indent_level + 1
            )
            content += child_content
            nodes_info.extend(child_nodes)
        
        content += f'{indent}end\n'
    
    return content, node_counter, nodes_info


def generate_click_declarations(nodes_info: List[Dict[str, Any]]) -> str:
    """Generate Mermaid click declarations for interactive nodes.
    
    Args:
        nodes_info: List of node information dictionaries
        
    Returns:
        Generated click declarations content
    """
    content = "    %% Interactive links to class documentation\n"
    
    for node_info in nodes_info:
        node_id = node_info["node_id"]
        class_name = node_info["class_name"]
        file_name = node_info["file_name"]
        module_path = node_info["module_path"].replace('\\', '/')
        loc = node_info["loc"]
        num_methods = node_info["num_methods"]
        
        # Generate link path for FastAPI static serving
        link_path = f"/design/{module_path}/{file_name}_class.md#{class_name.lower()}"
        
        # Generate tooltip with metrics
        tooltip = f"{class_name} - LOC: {loc} | Methods: {num_methods}"
        
        # Add click declaration
        content += f'    click {node_id} "{link_path}" "{tooltip}"\n'
    
    return content


def generate_navigation_hub(tree: Dict[str, Any], 
                           module_icons: Dict[str, str], level: int = 0) -> str:
    """Generate navigation hub recursively.
    
    Args:
        tree: Module tree structure
        module_icons: Icon mapping for modules
        level: Current hierarchy level
        
    Returns:
        Generated navigation content
    """
    content = ""
    
    for node_name, node in tree.items():
        icon_name = module_icons.get(node_name, f"📁 {node_name}")
        metrics = node["metrics"]
        
        if metrics["classes"] == 0:
            continue
            
        # Generate header with appropriate level
        header_level = "#" * (3 + level)
        content += f"{header_level} {icon_name} {node_name.title()} ({metrics['classes']} Classes | {metrics['loc']} LOC)\n\n"
        
        if node["is_leaf"]:
            # Add class links for leaf modules
            sorted_classes = sorted(node["classes"], key=lambda x: x["name"])
            
            for cls in sorted_classes:
                # Generate link path
                normalized_path = node["original_path"].replace('\\', '/')
                link_path = f"{normalized_path}/{cls['file_name']}_class.md#{cls['name'].lower()}"
                
                # Create markdown link with metrics
                content += f"- [{cls['name']}]({link_path}) - LOC: {cls['loc']} | Methods: {cls['num_methods']}\n"
            
            content += "\n"
        else:
            # Recursively add children
            child_content = generate_navigation_hub(node["children"], module_icons, level + 1)
            content += child_content
    
    return content


def generate_module_details(tree: Dict[str, Any]) -> str:
    """Generate module details section.
    
    Args:
        tree: Module tree structure
        
    Returns:
        Generated module details content
    """
    content = ""
    
    def add_module_details(nodes: Dict[str, Any], prefix: str = ""):
        nonlocal content
        for node_name, node in nodes.items():
            metrics = node["metrics"]
            
            if metrics["classes"] == 0:
                continue
                
            full_name = f"{prefix}{node_name.title()}" if prefix else node_name.title()
            content += f"### {full_name}\n"
            content += f"- **Classes:** {metrics['classes']}\n"
            content += f"- **Lines of Code:** {metrics['loc']:,}\n"
            content += f"- **Average LOC per Class:** {metrics['loc'] // metrics['classes'] if metrics['classes'] > 0 else 0}\n"
            
            if not node["is_leaf"]:
                content += f"- **Submodules:** {len(node['children'])}\n"
            
            content += "\n"
            
            # Recursively add children
            if node["children"]:
                add_module_details(node["children"], f"{full_name} > ")
    
    add_module_details(tree)
    return content
