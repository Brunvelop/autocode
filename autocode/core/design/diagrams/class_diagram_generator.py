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
        diagram += f"    class {class_info['name']} {{\n"
        
        # Add attributes with visibility and types
        for attr in class_info['attributes']:
            attr_line = f"        {attr['visibility']}{attr['name']}"
            if attr['type']:
                attr_line += f": {attr['type']}"
            diagram += attr_line + "\n"
        
        # Add methods with visibility, parameters, and return types
        for method in class_info['methods']:
            method_line = f"        {method['visibility']}{method['name']}("
            
            # Add parameters (skip 'self' for readability)
            params = [p for p in method['parameters'] if p['name'] != 'self']
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
            if method['return_type']:
                method_line += f" -> {method['return_type']}"
            
            diagram += method_line + "\n"
        
        diagram += "    }\n"
        
        # Add inheritance relationships
        for base in class_info['bases']:
            diagram += f"    {base} <|-- {class_info['name']}\n"
        
        # Add decorators as stereotypes
        for method in class_info['methods']:
            if method['is_property']:
                diagram += f"    {class_info['name']} : <<property>> {method['name']}\n"
            elif method['is_static']:
                diagram += f"    {class_info['name']} : <<static>> {method['name']}\n"
            elif method['is_class']:
                diagram += f"    {class_info['name']} : <<class>> {method['name']}\n"
        
        return diagram
