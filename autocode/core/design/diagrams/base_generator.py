"""Base generator interface for diagram generation.

This module defines the base interface that all diagram generators should implement.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional


class BaseGenerator(ABC):
    """Base abstract class for diagram generators."""

    def __init__(self, config: Dict[str, Any] = None):
        """Initialize the generator.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config or {}

    def generate_class_diagram(self, class_info: Dict) -> str:
        """Generate a class diagram for a single class.
        
        This method is optional and can be overridden by subclasses that support class diagrams.
        
        Args:
            class_info: Class information dictionary
            
        Returns:
            Diagram string in the specific format, or empty string if not supported
        """
        return f"graph TD\n    NotSupported[\"⚠️ Class diagrams not supported by {self.__class__.__name__}\"]"

    def generate_diagram(self, data: Dict[str, Any], diagram_type: str = "default") -> str:
        """Generate a diagram from data.
        
        This is a generic method that can be overridden by subclasses for custom diagram types.
        
        Args:
            data: Data to generate diagram from
            diagram_type: Type of diagram to generate
            
        Returns:
            Diagram string in the specific format
        """
        if diagram_type == "class" and "name" in data:
            return self.generate_class_diagram(data)
        return f"graph TD\n    NotSupported[\"⚠️ Diagram type '{diagram_type}' not supported by {self.__class__.__name__}\"]"

    def supports_diagram_type(self, diagram_type: str) -> bool:
        """Check if generator supports a specific diagram type.
        
        Args:
            diagram_type: Type of diagram to check
            
        Returns:
            True if supported, False otherwise
        """
        return diagram_type == "class"

    @abstractmethod
    def get_diagram_format(self) -> str:
        """Get the diagram format name.
        
        Returns:
            Format name (e.g., 'mermaid', 'plantuml', 'dot')
        """
        pass
