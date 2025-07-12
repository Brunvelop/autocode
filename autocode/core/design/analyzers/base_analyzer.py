"""Base analyzer interface for code analysis.

This module defines the base interface that all code analyzers should implement.
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, Any


class BaseAnalyzer(ABC):
    """Base abstract class for code analyzers."""

    def __init__(self, project_root: Path, config: Dict[str, Any] = None):
        """Initialize the analyzer.
        
        Args:
            project_root: Project root directory
            config: Configuration dictionary
        """
        self.project_root = project_root
        self.config = config or {}

    @abstractmethod
    def analyze_directory(self, directory: str, pattern: str = "*.py") -> Dict[str, Dict]:
        """Analyze all files in a directory maintaining structure.
        
        Args:
            directory: Relative directory to analyze
            pattern: File pattern
            
        Returns:
            Dictionary of extracted structures organized by directory
        """
        pass

    @abstractmethod
    def get_supported_extensions(self) -> list[str]:
        """Get list of supported file extensions.
        
        Returns:
            List of supported file extensions (e.g., ['.py', '.pyi'])
        """
        pass
