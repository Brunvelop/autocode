"""Class diagram generator using Mermaid format.

This module provides functionality to generate Mermaid class diagrams from code structures.
"""

from typing import Dict

from .base_generator import BaseGenerator


class ClassDiagramGenerator(BaseGenerator):
    """Generator for class diagrams using Mermaid format."""

    def get_diagram_format(self) -> str:
        """Get the diagram format name.
        
        Returns:
            Format name 'mermaid'
        """
        return "mermaid"

    def supports_diagram_type(self, diagram_type: str) -> bool:
        """Check if generator supports a specific diagram type.
        
        Args:
            diagram_type: Type of diagram to check
            
        Returns:
            True if supported, False otherwise
        """
        return diagram_type == "class"

    def generate_class_diagram(self, class_info: Dict) -> str:
        """Generate Mermaid class diagram for a single class.
        
        Args:
            class_info: Class information dictionary
            
        Returns:
            Mermaid diagram string
        """
        diagram = "classDiagram\n"
        class_name = class_info['name']
        
        # Start class definition
        diagram += f"    class {class_name} {{\n"
        
        # Track if class has any members
        has_members = False
        
        # Add attributes with visibility and types
        for attr in class_info.get('attributes', []):
            attr_line = f"        {attr['visibility']}{attr['name']}"
            if attr.get('type'):
                attr_line += f": {attr['type']}"
            diagram += attr_line + "\n"
            has_members = True
        
        # Add methods with visibility, parameters, and return types
        for method in class_info.get('methods', []):
            method_line = f"        {method['visibility']}{method['name']}("
            
            # Add parameters (skip 'self' for readability)
            params = [p for p in method.get('parameters', []) if p.get('name') != 'self']
            if params:
                param_strs = []
                for param in params:
                    param_str = param['name']
                    if param.get('type'):
                        param_str += f": {param['type']}"
                    param_strs.append(param_str)
                method_line += ", ".join(param_strs)
            
            method_line += ")"
            
            # Add return type
            if method.get('return_type'):
                method_line += f" -> {method['return_type']}"
            
            diagram += method_line + "\n"
            has_members = True
        
        # If class has no members, add a placeholder comment to ensure valid syntax
        if not has_members:
            diagram += "        %% No explicit members\n"
        
        # Close class definition
        diagram += "    }\n"
        
        # Add inheritance relationships (separate from class definition, with proper spacing)
        for base in class_info.get('bases', []):
            diagram += f"    {base} <|-- {class_name}\n"
        
        # Add decorators as stereotypes (with proper spacing)
        for method in class_info.get('methods', []):
            if method.get('is_property'):
                diagram += f"    {class_name} : <<property>> {method['name']}\n"
            elif method.get('is_static'):
                diagram += f"    {class_name} : <<static>> {method['name']}\n"
            elif method.get('is_class'):
                diagram += f"    {class_name} : <<class>> {method['name']}\n"
        
        return diagram
