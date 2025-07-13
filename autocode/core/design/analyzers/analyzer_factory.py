"""Analyzer factory for dynamic analyzer creation.

This module provides a factory to create analyzers based on configuration
and file extensions, making the system extensible and generalizable.
"""

from pathlib import Path
from typing import Dict, Any, List, Optional, Type
import importlib
import logging

from .base_analyzer import BaseAnalyzer

logger = logging.getLogger(__name__)


class AnalyzerRegistry:
    """Registry for analyzer classes."""
    
    def __init__(self):
        self._analyzers: Dict[str, Type[BaseAnalyzer]] = {}
        self._extension_mappings: Dict[str, str] = {}
    
    def register_analyzer(self, name: str, analyzer_class: Type[BaseAnalyzer], 
                         extensions: List[str]) -> None:
        """Register an analyzer class.
        
        Args:
            name: Analyzer name (e.g., 'python', 'javascript')
            analyzer_class: Analyzer class
            extensions: File extensions this analyzer handles
        """
        self._analyzers[name] = analyzer_class
        for ext in extensions:
            self._extension_mappings[ext] = name
    
    def get_analyzer(self, name: str) -> Optional[Type[BaseAnalyzer]]:
        """Get analyzer class by name."""
        return self._analyzers.get(name)
    
    def get_analyzer_for_extension(self, extension: str) -> Optional[Type[BaseAnalyzer]]:
        """Get analyzer class for file extension."""
        analyzer_name = self._extension_mappings.get(extension)
        return self._analyzers.get(analyzer_name) if analyzer_name else None
    
    def list_analyzers(self) -> List[str]:
        """List all registered analyzer names."""
        return list(self._analyzers.keys())
    
    def get_supported_extensions(self) -> List[str]:
        """Get all supported file extensions."""
        return list(self._extension_mappings.keys())


# Global registry instance
_registry = AnalyzerRegistry()


def register_analyzer(name: str, analyzer_class: Type[BaseAnalyzer], 
                     extensions: List[str]) -> None:
    """Register an analyzer class in the global registry."""
    _registry.register_analyzer(name, analyzer_class, extensions)


def get_registry() -> AnalyzerRegistry:
    """Get the global analyzer registry."""
    return _registry


class AnalyzerFactory:
    """Factory for creating code analyzers."""
    
    def __init__(self, project_root: Path, config: Dict[str, Any] = None):
        """Initialize the factory.
        
        Args:
            project_root: Project root directory
            config: Configuration dictionary
        """
        self.project_root = project_root
        self.config = config or {}
        self.registry = get_registry()
        
        # Auto-register built-in analyzers
        self._register_builtin_analyzers()
    
    def _register_builtin_analyzers(self) -> None:
        """Register built-in analyzers."""
        try:
            from .python.analyzer import PythonAnalyzer
            register_analyzer('python', PythonAnalyzer, ['.py', '.pyi'])
        except ImportError:
            logger.warning("Python analyzer not available")
        
        try:
            from .javascript.analyzer import JavaScriptAnalyzer
            register_analyzer('javascript', JavaScriptAnalyzer, ['.js', '.ts'])
        except ImportError:
            logger.warning("JavaScript analyzer not available")
        
        try:
            from .web.html_analyzer import HTMLAnalyzer
            register_analyzer('html', HTMLAnalyzer, ['.html', '.htm'])
        except ImportError:
            logger.warning("HTML analyzer not available")
        
        try:
            from .web.css_analyzer import CSSAnalyzer
            register_analyzer('css', CSSAnalyzer, ['.css', '.scss', '.sass'])
        except ImportError:
            logger.warning("CSS analyzer not available")
    
    def create_analyzer(self, analyzer_type: str) -> Optional[BaseAnalyzer]:
        """Create an analyzer by type.
        
        Args:
            analyzer_type: Type of analyzer ('python', 'javascript', etc.)
            
        Returns:
            Analyzer instance or None if not found
        """
        analyzer_class = self.registry.get_analyzer(analyzer_type)
        if analyzer_class:
            return analyzer_class(self.project_root, self.config)
        
        logger.warning(f"Analyzer type '{analyzer_type}' not found")
        return None
    
    def create_analyzer_for_file(self, file_path: Path) -> Optional[BaseAnalyzer]:
        """Create an analyzer for a specific file.
        
        Args:
            file_path: Path to the file
            
        Returns:
            Analyzer instance or None if no analyzer available
        """
        extension = file_path.suffix.lower()
        analyzer_class = self.registry.get_analyzer_for_extension(extension)
        if analyzer_class:
            return analyzer_class(self.project_root, self.config)
        
        logger.debug(f"No analyzer available for extension '{extension}'")
        return None
    
    def get_analyzers_for_languages(self, languages: List[str]) -> Dict[str, BaseAnalyzer]:
        """Create analyzers for multiple languages.
        
        Args:
            languages: List of language names
            
        Returns:
            Dictionary mapping language names to analyzer instances
        """
        analyzers = {}
        for language in languages:
            analyzer = self.create_analyzer(language)
            if analyzer:
                analyzers[language] = analyzer
            else:
                logger.warning(f"Could not create analyzer for language '{language}'")
        
        return analyzers
    
    def auto_detect_analyzers(self, directory: str) -> Dict[str, BaseAnalyzer]:
        """Auto-detect which analyzers are needed for a directory.
        
        Args:
            directory: Directory path to scan
            
        Returns:
            Dictionary of analyzers needed for the directory
        """
        dir_path = self.project_root / directory
        if not dir_path.exists():
            return {}
        
        # Find all file extensions in the directory
        extensions = set()
        for file_path in dir_path.rglob("*"):
            if file_path.is_file():
                extensions.add(file_path.suffix.lower())
        
        # Create analyzers for found extensions
        analyzers = {}
        for extension in extensions:
            analyzer_class = self.registry.get_analyzer_for_extension(extension)
            if analyzer_class:
                analyzer_name = next(
                    name for name, cls in self.registry._analyzers.items() 
                    if cls == analyzer_class
                )
                if analyzer_name not in analyzers:
                    analyzers[analyzer_name] = analyzer_class(self.project_root, self.config)
        
        return analyzers
    
    def get_available_analyzers(self) -> List[str]:
        """Get list of available analyzer types."""
        return self.registry.list_analyzers()
    
    def get_supported_extensions(self) -> List[str]:
        """Get list of supported file extensions."""
        return self.registry.get_supported_extensions()
