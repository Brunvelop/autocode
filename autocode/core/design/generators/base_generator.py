"""Base generator interface for diagram generation.

This module defines the base interface that all diagram generators should implement.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any


class BaseGenerator(ABC):
    """Base abstract class for diagram generators."""

    def __init__(self, config: Dict[str, Any] = None):
        """Initialize the generator.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config or {}

    @abstractmethod
    def generate_class_diagram(self, class_info: Dict) -> str:
        """Generate a class diagram for a single class.
        
        Args:
            class_info: Class information dictionary
            
        Returns:
            Diagram string in the specific format
        """
        pass

    @abstractmethod
    def get_diagram_format(self) -> str:
        """Get the diagram format name.
        
        Returns:
            Format name (e.g., 'mermaid', 'plantuml', 'dot')
        """
        pass
