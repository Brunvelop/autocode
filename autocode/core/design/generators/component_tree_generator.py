"""Component Tree diagram generator.

This module provides functionality to generate Mermaid diagrams from UI component structures.
"""

from typing import Dict, List, Any
from .base_generator import BaseGenerator


class ComponentTreeGenerator(BaseGenerator):
    """Generator for Component Tree diagrams using Mermaid."""

    def get_diagram_format(self) -> str:
        """Get the diagram format name.
        
        Returns:
            Format name 'mermaid'
        """
        return "mermaid"

    def generate_class_diagram(self, class_info: Dict) -> str:
        """Generate a class diagram for a single class.
        
        This method is not used for component tree generation.
        
        Args:
            class_info: Class information dictionary
            
        Returns:
            Empty string as this generator doesn't create class diagrams
        """
        return "graph TD\n    NotSupported[\"⚠️ Class diagrams not supported for UI components\"]"

    def generate_component_tree_diagram(self, analysis_data: Dict[str, Any]) -> str:
        """Generate Mermaid component tree diagram from analysis data.
        
        Args:
            analysis_data: Analysis data from JavaScriptAnalyzer
            
        Returns:
            Mermaid diagram string
        """
        diagram = "graph TD\n"
        diagram += '    classDef default fill:#f9f9f9,stroke:#333,stroke-width:2px,color:#333\n'
        diagram += '    classDef component fill:#e1f5fe,stroke:#0277bd,stroke-width:2px,color:#0277bd\n'
        diagram += '    classDef element fill:#f3e5f5,stroke:#7b1fa2,stroke-width:2px,color:#7b1fa2\n'
        diagram += '    classDef container fill:#e8f5e8,stroke:#2e7d32,stroke-width:2px,color:#2e7d32\n\n'
        
        modules = analysis_data.get("modules", {})
        if not modules:
            diagram += '    NoData["🚫 No UI components found"]\n'
            return diagram
        
        # Track nodes to avoid duplicates
        nodes_added = set()
        node_counter = 1
        
        # Create root node
        root_id = "Root"
        diagram += f'    {root_id}["🎨 UI Components"]:::container\n'
        nodes_added.add(root_id)
        
        # Process each module
        for module_path, module_data in modules.items():
            if module_path == ".":
                module_display = "Root"
            else:
                module_display = module_path.replace("\\", "/")
            
            module_id = f"M{node_counter}"
            node_counter += 1
            
            # Add module node
            if module_id not in nodes_added:
                diagram += f'    {module_id}["📁 {module_display}"]:::container\n'
                diagram += f'    {root_id} --> {module_id}\n'
                nodes_added.add(module_id)
            
            # Process files in module
            files = module_data.get("files", {})
            for file_name, file_data in files.items():
                file_type = file_data.get("file_type", "unknown")
                components = file_data.get("components", [])
                elements = file_data.get("elements", [])
                
                if not components and not elements:
                    continue
                
                file_id = f"F{node_counter}"
                node_counter += 1
                
                # Choose icon based on file type
                if file_type == "html":
                    icon = "🌐"
                elif file_type == "javascript":
                    icon = "⚡"
                elif file_type == "css":
                    icon = "🎨"
                else:
                    icon = "📄"
                
                # Add file node
                diagram += f'    {file_id}["{icon} {file_name}"]:::element\n'
                diagram += f'    {module_id} --> {file_id}\n'
                
                # Add components
                for component in components:
                    comp_id = f"C{node_counter}"
                    node_counter += 1
                    
                    comp_name = component.get("name", "Unknown")
                    comp_type = component.get("type", "component")
                    
                    # Choose icon based on component type
                    if comp_type == "custom_element":
                        icon = "⚙️"
                    elif comp_type == "class_component":
                        icon = "🏗️"
                    elif comp_type == "function_component":
                        icon = "🔧"
                    else:
                        icon = "🧩"
                    
                    diagram += f'    {comp_id}["{icon} {comp_name}"]:::component\n'
                    diagram += f'    {file_id} --> {comp_id}\n'
                    
                    # Add props if available
                    props = component.get("props", [])
                    if props and len(props) > 0:
                        props_id = f"P{node_counter}"
                        node_counter += 1
                        props_text = ", ".join(props[:3])  # Show first 3 props
                        if len(props) > 3:
                            props_text += f"... (+{len(props)-3})"
                        diagram += f'    {props_id}["📝 Props: {props_text}"]:::default\n'
                        diagram += f'    {comp_id} --> {props_id}\n'
                
                # Add significant elements (with IDs or classes)
                significant_elements = [
                    el for el in elements 
                    if el.get("id") or el.get("classes") or el.get("selector")
                ]
                
                for element in significant_elements[:5]:  # Limit to 5 elements
                    elem_id = f"E{node_counter}"
                    node_counter += 1
                    
                    if element.get("selector"):
                        elem_name = f"Query: {element['selector']}"
                        icon = "🔍"
                    elif element.get("id"):
                        elem_name = f"#{element['id']}"
                        icon = "🎯"
                    elif element.get("classes"):
                        classes = element.get("classes", [])
                        if isinstance(classes, list) and classes:
                            elem_name = f".{classes[0]}"
                        else:
                            elem_name = f".{classes}"
                        icon = "🏷️"
                    else:
                        elem_name = element.get("tag", "element")
                        icon = "📦"
                    
                    diagram += f'    {elem_id}["{icon} {elem_name}"]:::element\n'
                    diagram += f'    {file_id} --> {elem_id}\n'
        
        # Add relationships between components
        self._add_component_relationships(diagram, modules, nodes_added)
        
        # Add summary information
        total_components = analysis_data.get("summary", {}).get("total_components", 0)
        total_files = analysis_data.get("summary", {}).get("total_files", 0)
        
        if total_components > 0:
            summary_id = f"S{node_counter}"
            diagram += f'\n    {summary_id}["📊 Summary: {total_components} components in {total_files} files"]:::default\n'
            diagram += f'    {root_id} --> {summary_id}\n'
        
        return diagram

    def _add_component_relationships(self, diagram: str, modules: Dict, nodes_added: set) -> str:
        """Add relationships between components based on their structure.
        
        Args:
            diagram: Current diagram string
            modules: Module data
            nodes_added: Set of already added nodes
            
        Returns:
            Updated diagram string
        """
        # This is a simplified relationship detection
        # In a real implementation, you'd analyze parent-child relationships
        # from the actual component analysis
        relationships = []
        
        for module_path, module_data in modules.items():
            files = module_data.get("files", {})
            for file_name, file_data in files.items():
                relationships_data = file_data.get("relationships", [])
                for rel in relationships_data:
                    parent = rel.get("parent")
                    child = rel.get("child")
                    if parent and child:
                        relationships.append((parent, child))
        
        # Add relationship lines (simplified)
        for parent, child in relationships[:5]:  # Limit relationships shown
            diagram += f'    %% Relationship: {parent} contains {child}\n'
        
        return diagram

    def generate_component_summary(self, analysis_data: Dict[str, Any]) -> str:
        """Generate a text summary of the component analysis.
        
        Args:
            analysis_data: Analysis data from JavaScriptAnalyzer
            
        Returns:
            Text summary
        """
        summary = analysis_data.get("summary", {})
        modules = analysis_data.get("modules", {})
        
        total_components = summary.get("total_components", 0)
        total_files = summary.get("total_files", 0)
        total_modules = summary.get("total_modules", 0)
        
        text = f"# Component Tree Analysis Summary\n\n"
        text += f"- **Total Components:** {total_components}\n"
        text += f"- **Total Files:** {total_files}\n"
        text += f"- **Total Modules:** {total_modules}\n\n"
        
        if total_components == 0:
            text += "No UI components were found in the analyzed files.\n"
            return text
        
        text += "## Components by Type\n\n"
        
        # Count components by type
        component_types = {}
        for module_data in modules.values():
            files = module_data.get("files", {})
            for file_data in files.values():
                components = file_data.get("components", [])
                for comp in components:
                    comp_type = comp.get("type", "unknown")
                    component_types[comp_type] = component_types.get(comp_type, 0) + 1
        
        for comp_type, count in component_types.items():
            text += f"- **{comp_type.replace('_', ' ').title()}:** {count}\n"
        
        text += "\n## Files by Type\n\n"
        
        # Count files by type
        file_types = {}
        for module_data in modules.values():
            files = module_data.get("files", {})
            for file_data in files.values():
                file_type = file_data.get("file_type", "unknown")
                file_types[file_type] = file_types.get(file_type, 0) + 1
        
        for file_type, count in file_types.items():
            text += f"- **{file_type.upper()}:** {count} files\n"
        
        return text
