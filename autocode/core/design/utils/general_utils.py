"""General utilities for the design module.

This module contains shared utility functions that are project-agnostic
and can be used across different codebases.
"""

from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path
import json


class GeneralUtils:
    """General utilities for design generation."""
    
    def __init__(self, config: Dict[str, Any] = None):
        """Initialize with configuration.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config or {}
    
    def build_hierarchical_tree(self, flat_data: Dict[str, Any], 
                               key_path: str = "modules") -> Dict[str, Any]:
        """Build a hierarchical tree structure from flat module data.
        
        Args:
            flat_data: Flat data structure with modules
            key_path: Path to the modules data in flat_data
            
        Returns:
            Hierarchical tree structure with aggregated metrics
        """
        tree = {}
        modules = flat_data.get(key_path, {})
        
        # First pass: Create the tree structure
        for module_path, module_info in modules.items():
            if module_path == ".":
                continue
                
            # Split path into parts (handle both / and \ separators)
            parts = module_path.replace('\\', '/').split('/')
            
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
                        "original_path": module_path,
                        "children": {},
                        "items": [],  # Generic items (classes, functions, components, etc.)
                        "metrics": self._get_default_metrics(),
                        "is_leaf": False
                    }
                
                current_level = current_level[part]["children"]
        
        # Second pass: Add data to leaf nodes
        for module_path, module_info in modules.items():
            if module_path == ".":
                continue
                
            # Navigate to the correct node
            leaf_parts = module_path.replace('\\', '/').split('/')
            leaf_node = tree
            for i, part in enumerate(leaf_parts):
                if i == len(leaf_parts) - 1:
                    # Last part - this is our target node
                    leaf_node = leaf_node[part]
                else:
                    # Navigate to children
                    leaf_node = leaf_node[part]["children"]
            
            # Only set as leaf if it has no children
            if not leaf_node["children"]:
                leaf_node["is_leaf"] = True
                leaf_node["items"] = self._extract_items_from_module(module_info)
                leaf_node["metrics"] = self._calculate_module_metrics(module_info)
                leaf_node["original_path"] = module_path
        
        # Calculate aggregate metrics for parent nodes
        self._calculate_aggregate_metrics(tree)
        
        return tree
    
    def _get_default_metrics(self) -> Dict[str, int]:
        """Get default metrics structure.
        
        Returns:
            Default metrics dictionary
        """
        return {
            "total_items": 0,
            "total_files": 0,
            "total_loc": 0,
            "classes": 0,
            "functions": 0,
            "components": 0
        }
    
    def _extract_items_from_module(self, module_info: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract items (classes, functions, components) from module info.
        
        Args:
            module_info: Module information dictionary
            
        Returns:
            List of items with normalized structure
        """
        items = []
        
        # Extract from analysis_data if available (new structure)
        if "analysis_data" in module_info:
            for analysis in module_info["analysis_data"]:
                # Add classes
                for cls in analysis.get("classes", []):
                    items.append({
                        "name": cls["name"],
                        "type": "class",
                        "loc": cls.get("loc", 0),
                        "methods": len(cls.get("methods", [])),
                        "file": cls.get("file", ""),
                        "source": analysis
                    })
                
                # Add functions
                for func in analysis.get("functions", []):
                    items.append({
                        "name": func["name"],
                        "type": "function", 
                        "loc": func.get("loc", 0),
                        "parameters": len(func.get("parameters", [])),
                        "file": analysis.get("file_path", ""),
                        "source": analysis
                    })
                
                # Add components (for web files)
                for comp in analysis.get("components", []):
                    items.append({
                        "name": comp["name"],
                        "type": "component",
                        "loc": comp.get("loc", 0),
                        "methods": len(comp.get("methods", [])),
                        "file": analysis.get("file_path", ""),
                        "source": analysis
                    })
        
        # Fallback: extract from legacy structure
        elif "classes" in module_info:
            for cls in module_info["classes"]:
                items.append({
                    "name": cls["name"],
                    "type": "class",
                    "loc": cls.get("loc", 0),
                    "methods": cls.get("num_methods", 0),
                    "file": cls.get("file", ""),
                    "source": cls
                })
        
        return items
    
    def _calculate_module_metrics(self, module_info: Dict[str, Any]) -> Dict[str, int]:
        """Calculate metrics for a module.
        
        Args:
            module_info: Module information dictionary
            
        Returns:
            Calculated metrics
        """
        metrics = self._get_default_metrics()
        
        # Count from analysis_data if available
        if "analysis_data" in module_info:
            for analysis in module_info["analysis_data"]:
                analysis_metrics = analysis.get("metrics", {})
                metrics["classes"] += analysis_metrics.get("total_classes", 0)
                metrics["functions"] += analysis_metrics.get("total_functions", 0)
                metrics["components"] += analysis_metrics.get("total_components", 0)
                metrics["total_loc"] += analysis_metrics.get("total_loc", 0)
            
            metrics["total_files"] = len(module_info["analysis_data"])
        
        # Fallback: legacy structure
        elif "classes" in module_info:
            metrics["classes"] = len(module_info["classes"])
            metrics["total_loc"] = sum(cls.get("loc", 0) for cls in module_info["classes"])
            metrics["total_files"] = len(module_info.get("files", {}))
        
        metrics["total_items"] = metrics["classes"] + metrics["functions"] + metrics["components"]
        
        return metrics
    
    def _calculate_aggregate_metrics(self, tree: Dict[str, Any]) -> None:
        """Calculate aggregate metrics for all nodes in the tree.
        
        Args:
            tree: Module tree structure
        """
        for node_name, node in tree.items():
            if node["is_leaf"]:
                continue
                
            # Recursively calculate for children first
            if node["children"]:
                self._calculate_aggregate_metrics(node["children"])
                
                # Sum metrics from all children
                aggregated = self._get_default_metrics()
                
                for child_name, child in node["children"].items():
                    child_metrics = child["metrics"]
                    for key in aggregated:
                        aggregated[key] += child_metrics.get(key, 0)
                
                node["metrics"] = aggregated
    
    def count_tree_nodes(self, tree: Dict[str, Any]) -> int:
        """Count total nodes in the tree.
        
        Args:
            tree: Tree structure
            
        Returns:
            Total number of nodes
        """
        count = 0
        for node in tree.values():
            count += 1
            if node.get("children"):
                count += self.count_tree_nodes(node["children"])
        return count
    
    def generate_summary_stats(self, tree: Dict[str, Any]) -> Dict[str, Any]:
        """Generate summary statistics from tree.
        
        Args:
            tree: Tree structure
            
        Returns:
            Summary statistics
        """
        total_metrics = self._get_default_metrics()
        
        for node in tree.values():
            node_metrics = node.get("metrics", {})
            for key in total_metrics:
                total_metrics[key] += node_metrics.get(key, 0)
        
        return {
            "total_nodes": self.count_tree_nodes(tree),
            "metrics": total_metrics,
            "avg_items_per_node": total_metrics["total_items"] / len(tree) if tree else 0,
            "avg_loc_per_item": total_metrics["total_loc"] / total_metrics["total_items"] if total_metrics["total_items"] > 0 else 0
        }
    
    def filter_tree_by_criteria(self, tree: Dict[str, Any], 
                               min_items: int = 0,
                               include_types: Optional[List[str]] = None) -> Dict[str, Any]:
        """Filter tree nodes by criteria.
        
        Args:
            tree: Tree structure
            min_items: Minimum number of items required
            include_types: Types to include (None means all)
            
        Returns:
            Filtered tree structure
        """
        filtered_tree = {}
        
        for node_name, node in tree.items():
            node_metrics = node.get("metrics", {})
            
            # Check minimum items criteria
            if node_metrics.get("total_items", 0) < min_items:
                continue
            
            # Check type inclusion
            if include_types:
                has_included_type = False
                for item in node.get("items", []):
                    if item.get("type") in include_types:
                        has_included_type = True
                        break
                
                if not has_included_type and node.get("children"):
                    # Check children recursively
                    filtered_children = self.filter_tree_by_criteria(
                        node["children"], min_items, include_types
                    )
                    if filtered_children:
                        has_included_type = True
                
                if not has_included_type:
                    continue
            
            # Include this node
            filtered_node = node.copy()
            if node.get("children"):
                filtered_node["children"] = self.filter_tree_by_criteria(
                    node["children"], min_items, include_types
                )
            
            filtered_tree[node_name] = filtered_node
        
        return filtered_tree
    
    def export_tree_to_json(self, tree: Dict[str, Any], output_path: Path) -> None:
        """Export tree structure to JSON file.
        
        Args:
            tree: Tree structure
            output_path: Output file path
        """
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(tree, f, indent=2, default=str)
    
    def get_module_icons(self, custom_icons: Optional[Dict[str, str]] = None) -> Dict[str, str]:
        """Get module icons mapping with defaults and custom overrides.
        
        Args:
            custom_icons: Custom icon mappings to override defaults
            
        Returns:
            Complete icon mapping
        """
        default_icons = {
            # Generic programming concepts
            "core": "⚙️ Core",
            "api": "🌐 API", 
            "web": "🖥️ Web",
            "ui": "🎨 UI",
            "components": "🧩 Components",
            "utils": "🔧 Utils",
            "helpers": "🤝 Helpers",
            "lib": "📚 Lib",
            "libs": "📚 Libraries",
            "src": "📂 Source",
            "app": "📱 App",
            "main": "🏠 Main",
            "config": "⚙️ Config",
            "settings": "⚙️ Settings",
            "models": "📊 Models",
            "views": "👁️ Views",
            "controllers": "🎮 Controllers",
            "services": "🔄 Services",
            "middleware": "🔗 Middleware",
            "routes": "🛣️ Routes",
            "auth": "🔐 Auth",
            "security": "🔒 Security",
            "database": "💾 Database",
            "db": "💾 DB",
            "storage": "💿 Storage",
            "cache": "⚡ Cache",
            "tests": "🧪 Tests",
            "test": "🧪 Test",
            "docs": "📚 Docs",
            "documentation": "📚 Documentation",
            "examples": "📝 Examples",
            "scripts": "📜 Scripts",
            "tools": "🔨 Tools",
            "cli": "💻 CLI",
            "assets": "🎭 Assets",
            "static": "📁 Static",
            "public": "🌐 Public",
            "templates": "📄 Templates",
            "layouts": "🏗️ Layouts"
        }
        
        # Apply custom icons from config
        config_icons = self.config.get("module_icons", {})
        default_icons.update(config_icons)
        
        # Apply parameter custom icons
        if custom_icons:
            default_icons.update(custom_icons)
        
        return default_icons
