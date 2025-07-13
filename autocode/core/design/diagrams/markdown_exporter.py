"""Markdown exporter for design documentation.

This module handles the generation and export of markdown files with diagrams
from code analysis results.
"""

from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import logging

logger = logging.getLogger(__name__)


class MarkdownExporter:
    """Handles export of analysis results to markdown files with diagrams."""
    
    def __init__(self, output_base: Path, config: Dict[str, Any] = None, utils=None):
        """Initialize the exporter.
        
        Args:
            output_base: Base directory for output files
            config: Configuration dictionary
            utils: GeneralUtils instance for hierarchical operations
        """
        self.output_base = output_base
        self.config = config or {}
        self.utils = utils
    
    def export(self, analysis_results: Dict[str, Any], generators: Dict[str, Any]) -> List[Path]:
        """Export analysis results to markdown files.
        
        Args:
            analysis_results: Combined analysis results from all analyzers
            generators: Dictionary of diagram generators
            
        Returns:
            List of generated file paths
        """
        return self.generate_markdown_files(analysis_results, generators)
    
    def generate_markdown_files(self, analysis_results: Dict[str, Any], 
                               generators: Dict[str, Any],
                               output_dir: Optional[Path] = None) -> List[Path]:
        """Generate modular Markdown files maintaining directory structure.
        
        Args:
            analysis_results: Combined analysis results from all analyzers
            generators: Dictionary of diagram generators
            output_dir: Custom output directory (defaults to self.output_base)
            
        Returns:
            List of generated file paths
        """
        generated_dir = output_dir if output_dir is not None else self.output_base
        generated_dir.mkdir(parents=True, exist_ok=True)
        
        generated_files = []
        
        # Generate visual index if configured
        if self.config.get("generate_index", True):
            index_path = generated_dir / "_index.md"
            index_content = self.generate_visual_index(analysis_results, generators)
            
            with open(index_path, "w", encoding="utf-8") as f:
                f.write(index_content)
            generated_files.append(index_path)
        
        # Generate files for each module
        modules = analysis_results.get("modules", {})
        for module_dir, module_info in modules.items():
            if module_dir == ".":
                target_dir = generated_dir
            else:
                target_dir = generated_dir / module_dir
                target_dir.mkdir(parents=True, exist_ok=True)
            
            # Generate module-level documentation
            module_files = self._generate_module_files(module_dir, module_info, target_dir, generators)
            generated_files.extend(module_files)
        
        return generated_files

    def generate_visual_index(self, analysis_results: Dict[str, Any], 
                             generators: Dict[str, Any],
                             project_name: Optional[str] = None) -> str:
        """Generate a visual index using hierarchical structure.
        
        Args:
            analysis_results: Combined analysis results from all analyzers
            generators: Dictionary of diagram generators
            project_name: Name of the project (auto-detected if None)
            
        Returns:
            Markdown content with visual index
        """
        # Build hierarchical tree using the utilities if available
        if self.utils:
            module_tree = self.utils.build_hierarchical_tree(analysis_results)
            summary_stats = self.utils.generate_summary_stats(module_tree)
        else:
            # Fallback to simple structure if utils not available
            module_tree = {}
            summary_stats = {"metrics": {"total_items": 0, "total_loc": 0, "classes": 0, "functions": 0, "components": 0}, "total_nodes": 0}
        
        # Get project name from config or auto-detect
        if not project_name:
            project_name = self.config.get("project_name", self.output_base.parent.name.title())
        
        # Generate visual index content
        content = f"# 🏗️ {project_name} Architecture Overview\n\n"
        
        # Add summary with generic metrics
        metrics = summary_stats["metrics"]
        content += f"**Project Summary:** "
        content += f"{metrics['total_items']} Items | "
        content += f"{metrics['total_loc']:,} LOC | "
        content += f"{summary_stats['total_nodes']} Modules\n\n"
        
        # Add breakdown by type
        if metrics['classes'] > 0:
            content += f"- **Classes:** {metrics['classes']}\n"
        if metrics['functions'] > 0:
            content += f"- **Functions:** {metrics['functions']}\n"
        if metrics['components'] > 0:
            content += f"- **Components:** {metrics['components']}\n"
        content += "\n"
        
        # Generate Mermaid diagram using mermaid generator if available
        if "mermaid" in generators:
            content += "```mermaid\n"
            content += self._generate_architecture_diagram(module_tree, project_name)
            content += "\n```\n\n"
        
        # Add module details
        content += "## Module Details\n\n"
        content += self._generate_module_details_section(module_tree)
        
        return content
    
    def _generate_architecture_diagram(self, module_tree: Dict[str, Any], 
                                     project_name: str) -> str:
        """Generate Mermaid architecture diagram.
        
        Args:
            module_tree: Hierarchical module tree
            project_name: Name of the project
            
        Returns:
            Mermaid diagram content
        """
        diagram = "graph TD\n"
        diagram += f'    subgraph "{project_name}"\n'
        
        # Get module icons
        module_icons = self.utils.get_module_icons() if self.utils else {}
        
        node_counter = 0
        
        # Generate nodes for each module
        for module_name, module_data in module_tree.items():
            metrics = module_data.get("metrics", {})
            if metrics.get("total_items", 0) == 0:
                continue
            
            # Get icon for module
            icon = module_icons.get(module_name.lower(), f"📁 {module_name.title()}")
            
            # Create node with metrics
            node_id = f"M{node_counter}"
            node_counter += 1
            
            diagram += f'        {node_id}["{icon}\\n{metrics["total_items"]} items"]\n'
            
            # Add children if any
            if module_data.get("children"):
                child_diagram, node_counter = self._generate_child_nodes(
                    module_data["children"], node_id, node_counter, module_icons, 2
                )
                diagram += child_diagram
        
        diagram += "    end\n"
        return diagram
    
    def _generate_child_nodes(self, children: Dict[str, Any], parent_id: str, 
                            node_counter: int, module_icons: Dict[str, str], 
                            indent_level: int) -> Tuple[str, int]:
        """Generate child nodes recursively.
        
        Args:
            children: Child modules
            parent_id: Parent node ID
            node_counter: Current node counter
            module_icons: Module icon mapping
            indent_level: Indentation level
            
        Returns:
            Tuple of (diagram content, updated node counter)
        """
        diagram = ""
        indent = "    " * indent_level
        
        for child_name, child_data in children.items():
            metrics = child_data.get("metrics", {})
            if metrics.get("total_items", 0) == 0:
                continue
            
            # Get icon for child
            icon = module_icons.get(child_name.lower(), f"📁 {child_name.title()}")
            
            # Create child node
            child_id = f"M{node_counter}"
            node_counter += 1
            
            diagram += f'{indent}{child_id}["{icon}\\n{metrics["total_items"]} items"]\n'
            diagram += f'{indent}{parent_id} --> {child_id}\n'
            
            # Add grandchildren if any
            if child_data.get("children"):
                grandchild_diagram, node_counter = self._generate_child_nodes(
                    child_data["children"], child_id, node_counter, module_icons, indent_level + 1
                )
                diagram += grandchild_diagram
        
        return diagram, node_counter
    
    def _generate_module_details_section(self, module_tree: Dict[str, Any]) -> str:
        """Generate module details section.
        
        Args:
            module_tree: Hierarchical module tree
            
        Returns:
            Module details content
        """
        content = ""
        
        def add_module_details(nodes: Dict[str, Any], prefix: str = "", level: int = 3):
            nonlocal content
            for node_name, node in nodes.items():
                metrics = node.get("metrics", {})
                
                if metrics.get("total_items", 0) == 0:
                    continue
                
                header_level = "#" * level
                full_name = f"{prefix}{node_name.title()}" if prefix else node_name.title()
                
                content += f"{header_level} {full_name}\n"
                content += f"- **Total Items:** {metrics['total_items']}\n"
                content += f"- **Files:** {metrics['total_files']}\n"
                content += f"- **Lines of Code:** {metrics['total_loc']:,}\n"
                
                if metrics['classes'] > 0:
                    content += f"- **Classes:** {metrics['classes']}\n"
                if metrics['functions'] > 0:
                    content += f"- **Functions:** {metrics['functions']}\n"
                if metrics['components'] > 0:
                    content += f"- **Components:** {metrics['components']}\n"
                
                if not node.get("is_leaf") and node.get("children"):
                    content += f"- **Submodules:** {len(node['children'])}\n"
                
                content += "\n"
                
                # Recursively add children
                if node.get("children"):
                    add_module_details(node["children"], f"{full_name} > ", level + 1)
        
        add_module_details(module_tree)
        return content
    
    def _generate_module_files(self, module_dir: str, module_info: Dict[str, Any], 
                              target_dir: Path, generators: Dict[str, Any]) -> List[Path]:
        """Generate files for a specific module.
        
        Args:
            module_dir: Module directory path
            module_info: Module information
            target_dir: Target output directory
            generators: Dictionary of diagram generators
            
        Returns:
            List of generated file paths
        """
        generated_files = []
        
        # Generate _module.md for directories (except root)
        if module_dir != ".":
            module_md_path = target_dir / "_module.md"
            module_content = self._generate_module_overview(module_dir, module_info)
            
            with open(module_md_path, "w", encoding="utf-8") as f:
                f.write(module_content)
            generated_files.append(module_md_path)
        
        # Generate individual item files
        if "analysis_data" in module_info:
            for analysis_data in module_info["analysis_data"]:
                item_files = self._generate_analysis_files(analysis_data, target_dir, generators)
                generated_files.extend(item_files)
        
        return generated_files
    
    def _generate_module_overview(self, module_dir: str, module_info: Dict[str, Any]) -> str:
        """Generate module overview content.
        
        Args:
            module_dir: Module directory path
            module_info: Module information
            
        Returns:
            Module overview markdown content
        """
        content = f"# Module: {module_dir}\n\n"
        
        # Add summary
        if "summary" in module_info:
            summary = module_info["summary"]
            content += f"**Summary:** {summary.get('total_files', 0)} files, "
            content += f"{summary.get('total_items', 0)} items\n\n"
        
        # Add items by file
        if "analysis_data" in module_info:
            content += "## Items in this module\n\n"
            
            for analysis_data in module_info["analysis_data"]:
                file_path = analysis_data.get("file_path", "")
                file_name = Path(file_path).stem if file_path else "unknown"
                
                # Add classes
                classes = analysis_data.get("classes", [])
                if classes:
                    content += f"### {file_name} - Classes\n"
                    for cls in classes:
                        content += f"- [{cls['name']}]({file_name}_items.md#{cls['name'].lower()})\n"
                    content += "\n"
                
                # Add functions
                functions = analysis_data.get("functions", [])
                if functions:
                    content += f"### {file_name} - Functions\n"
                    for func in functions:
                        content += f"- [{func['name']}]({file_name}_items.md#{func['name'].lower()})\n"
                    content += "\n"
                
                # Add components
                components = analysis_data.get("components", [])
                if components:
                    content += f"### {file_name} - Components\n"
                    for comp in components:
                        content += f"- [{comp['name']}]({file_name}_items.md#{comp['name'].lower()})\n"
                    content += "\n"
        
        return content
    
    def _generate_analysis_files(self, analysis_data: Dict[str, Any], 
                                target_dir: Path, generators: Dict[str, Any]) -> List[Path]:
        """Generate files for analysis data.
        
        Args:
            analysis_data: Analysis data from an analyzer
            target_dir: Target output directory
            generators: Dictionary of diagram generators
            
        Returns:
            List of generated file paths
        """
        generated_files = []
        
        file_path = analysis_data.get("file_path", "")
        file_name = Path(file_path).stem if file_path else "unknown"
        
        # Only generate if there are items to document
        has_items = (analysis_data.get("classes") or 
                    analysis_data.get("functions") or 
                    analysis_data.get("components"))
        
        if has_items:
            item_file_path = target_dir / f"{file_name}_items.md"
            content = self._generate_items_content(analysis_data, generators)
            
            with open(item_file_path, "w", encoding="utf-8") as f:
                f.write(content)
            generated_files.append(item_file_path)
        
        return generated_files
    
    def _generate_items_content(self, analysis_data: Dict[str, Any], generators: Dict[str, Any]) -> str:
        """Generate content for items in a file.
        
        Args:
            analysis_data: Analysis data from an analyzer
            generators: Dictionary of diagram generators
            
        Returns:
            Items documentation content
        """
        file_path = analysis_data.get("file_path", "")
        file_type = analysis_data.get("file_type", "unknown")
        
        content = f"# Items from {Path(file_path).name}\n\n"
        content += f"**Source:** `{file_path}`  \n"
        content += f"**Type:** {file_type}\n\n"
        
        # Add metrics if available
        if "metrics" in analysis_data:
            metrics = analysis_data["metrics"]
            content += "**Metrics:**\n"
            for key, value in metrics.items():
                if isinstance(value, (int, float)):
                    content += f"- {key.replace('_', ' ').title()}: {value:,}\n"
            content += "\n"
        
        # Generate content for each item type
        for item_type in ["classes", "functions", "components"]:
            items = analysis_data.get(item_type, [])
            if items:
                content += f"## {item_type.title()}\n\n"
                
                for item in items:
                    item_content = self._generate_item_content(item, item_type, generators)
                    content += item_content
        
        return content
    
    def _generate_item_content(self, item: Dict[str, Any], item_type: str, generators: Dict[str, Any]) -> str:
        """Generate content for a specific item.
        
        Args:
            item: Item data
            item_type: Type of item ('classes', 'functions', 'components')
            generators: Dictionary of diagram generators
            
        Returns:
            Item documentation content
        """
        name = item.get("name", "Unknown")
        content = f"### {name}\n\n"
        
        # Add basic info
        if "line_number" in item:
            content += f"**Line:** {item['line_number']}  \n"
        
        if "loc" in item:
            content += f"**LOC:** {item['loc']}  \n"
        
        # Add type-specific content
        if item_type == "classes" and "mermaid" in generators:
            content += "\n```mermaid\n"
            try:
                content += generators["mermaid"].generate_class_diagram(item)
            except Exception:
                content += f"classDiagram\n    class {name} {{\n    }}"
            content += "\n```\n\n"
        
        elif item_type == "functions":
            params = item.get("parameters", [])
            if params:
                param_str = ", ".join(p.get("name", str(p)) for p in params)
                content += f"**Parameters:** {param_str}  \n"
            
            if "return_type" in item:
                content += f"**Returns:** {item['return_type']}  \n"
            content += "\n"
        
        elif item_type == "components":
            if "type" in item:
                content += f"**Type:** {item['type']}  \n"
            
            methods = item.get("methods", [])
            if methods:
                content += f"**Methods:** {len(methods)}  \n"
            content += "\n"
        
        return content
