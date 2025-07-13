"""Generator factory for dynamic generator creation.

This module provides a factory to create diagram generators based on configuration
and output formats, making the system extensible and generalizable.
"""

from pathlib import Path
from typing import Dict, Any, List, Optional, Type
import logging

from .base_generator import BaseGenerator

logger = logging.getLogger(__name__)


class GeneratorRegistry:
    """Registry for generator classes."""
    
    def __init__(self):
        self._generators: Dict[str, Type[BaseGenerator]] = {}
        self._format_mappings: Dict[str, str] = {}
    
    def register_generator(self, name: str, generator_class: Type[BaseGenerator], 
                          formats: List[str]) -> None:
        """Register a generator class.
        
        Args:
            name: Generator name (e.g., 'mermaid', 'plantuml')
            generator_class: Generator class
            formats: Output formats this generator handles
        """
        self._generators[name] = generator_class
        for fmt in formats:
            self._format_mappings[fmt] = name
    
    def get_generator(self, name: str) -> Optional[Type[BaseGenerator]]:
        """Get generator class by name."""
        return self._generators.get(name)
    
    def get_generator_for_format(self, format_name: str) -> Optional[Type[BaseGenerator]]:
        """Get generator class for output format."""
        generator_name = self._format_mappings.get(format_name)
        return self._generators.get(generator_name) if generator_name else None
    
    def list_generators(self) -> List[str]:
        """List all registered generator names."""
        return list(self._generators.keys())
    
    def get_supported_formats(self) -> List[str]:
        """Get all supported output formats."""
        return list(self._format_mappings.keys())


# Global registry instance
_registry = GeneratorRegistry()


def register_generator(name: str, generator_class: Type[BaseGenerator], 
                      formats: List[str]) -> None:
    """Register a generator class in the global registry."""
    _registry.register_generator(name, generator_class, formats)


def get_registry() -> GeneratorRegistry:
    """Get the global generator registry."""
    return _registry


class GeneratorFactory:
    """Factory for creating diagram generators."""
    
    def __init__(self, config: Dict[str, Any] = None):
        """Initialize the factory.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config or {}
        self.registry = get_registry()
        
        # Auto-register built-in generators
        self._register_builtin_generators()
    
    def _register_builtin_generators(self) -> None:
        """Register built-in generators."""
        try:
            from .class_diagram_generator import ClassDiagramGenerator
            register_generator('mermaid', ClassDiagramGenerator, ['mermaid', 'md'])
        except ImportError:
            logger.warning("Class diagram generator not available")
        
        try:
            from .component_tree_generator import ComponentTreeGenerator
            register_generator('component_tree', ComponentTreeGenerator, ['component_tree', 'tree'])
        except ImportError:
            logger.warning("Component tree generator not available")
        
        # Could add more generators here
        # try:
        #     from .plantuml_generator import PlantUMLGenerator
        #     register_generator('plantuml', PlantUMLGenerator, ['plantuml', 'puml'])
        # except ImportError:
        #     logger.warning("PlantUML generator not available")
    
    def create_generator(self, generator_type: str) -> Optional[BaseGenerator]:
        """Create a generator by type.
        
        Args:
            generator_type: Type of generator ('mermaid', 'plantuml', etc.)
            
        Returns:
            Generator instance or None if not found
        """
        generator_class = self.registry.get_generator(generator_type)
        if generator_class:
            return generator_class(self.config)
        
        logger.warning(f"Generator type '{generator_type}' not found")
        return None
    
    def create_generator_for_format(self, format_name: str) -> Optional[BaseGenerator]:
        """Create a generator for a specific output format.
        
        Args:
            format_name: Output format name
            
        Returns:
            Generator instance or None if no generator available
        """
        generator_class = self.registry.get_generator_for_format(format_name)
        if generator_class:
            return generator_class(self.config)
        
        logger.debug(f"No generator available for format '{format_name}'")
        return None
    
    def get_generators_for_types(self, generator_types: List[str]) -> Dict[str, BaseGenerator]:
        """Create generators for multiple types.
        
        Args:
            generator_types: List of generator type names
            
        Returns:
            Dictionary mapping generator names to generator instances
        """
        generators = {}
        for gen_type in generator_types:
            generator = self.create_generator(gen_type)
            if generator:
                generators[gen_type] = generator
            else:
                logger.warning(f"Could not create generator for type '{gen_type}'")
        
        return generators
    
    def auto_detect_generators(self, diagram_types: List[str]) -> Dict[str, BaseGenerator]:
        """Auto-detect which generators are needed for given diagram types.
        
        Args:
            diagram_types: List of diagram types ('classes', 'components', etc.)
            
        Returns:
            Dictionary of generators needed for the diagram types
        """
        generators = {}
        
        # Map diagram types to generator types
        diagram_to_generator = {
            'classes': 'mermaid',
            'components': 'component_tree',
            'sequence': 'mermaid',
            'flowchart': 'mermaid',
            'architecture': 'mermaid'
        }
        
        for diagram_type in diagram_types:
            generator_type = diagram_to_generator.get(diagram_type)
            if generator_type and generator_type not in generators:
                generator = self.create_generator(generator_type)
                if generator:
                    generators[generator_type] = generator
        
        return generators
    
    def get_available_generators(self) -> List[str]:
        """Get list of available generator types."""
        return self.registry.list_generators()
    
    def get_supported_formats(self) -> List[str]:
        """Get list of supported output formats."""
        return self.registry.get_supported_formats()
    
    def supports_diagram_type(self, diagram_type: str) -> bool:
        """Check if any generator supports a specific diagram type.
        
        Args:
            diagram_type: Type of diagram to check
            
        Returns:
            True if supported, False otherwise
        """
        for generator_class in self.registry._generators.values():
            # Create a temporary instance to check support
            temp_generator = generator_class(self.config)
            if temp_generator.supports_diagram_type(diagram_type):
                return True
        
        return False
    
    def get_generator_info(self) -> Dict[str, Any]:
        """Get information about all available generators.
        
        Returns:
            Dictionary with generator metadata
        """
        info = {
            "available_generators": self.get_available_generators(),
            "supported_formats": self.get_supported_formats(),
            "generator_details": {}
        }
        
        for name, generator_class in self.registry._generators.items():
            temp_generator = generator_class(self.config)
            info["generator_details"][name] = {
                "class": generator_class.__name__,
                "format": temp_generator.get_diagram_format(),
                "supports_class_diagrams": temp_generator.supports_diagram_type("class"),
                "supports_components": temp_generator.supports_diagram_type("components")
            }
        
        return info
