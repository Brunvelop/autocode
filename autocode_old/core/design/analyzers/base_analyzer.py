"""Base analyzer interface for code analysis.

This module defines the base interface that all code analyzers should implement.
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, Any, List, Optional, Union
import logging

logger = logging.getLogger(__name__)


class AnalysisResult:
    """Container for analysis results with metadata."""
    
    def __init__(self, 
                 status: str = "success",
                 data: Dict[str, Any] = None,
                 errors: List[str] = None,
                 warnings: List[str] = None,
                 metadata: Dict[str, Any] = None):
        """Initialize analysis result.
        
        Args:
            status: Analysis status ('success', 'error', 'warning')
            data: Analysis data
            errors: List of error messages
            warnings: List of warning messages
            metadata: Additional metadata (e.g., processing time, file count)
        """
        self.status = status
        self.data = data or {}
        self.errors = errors or []
        self.warnings = warnings or []
        self.metadata = metadata or {}
    
    def is_successful(self) -> bool:
        """Check if analysis was successful."""
        return self.status == "success"
    
    def has_errors(self) -> bool:
        """Check if analysis has errors."""
        return len(self.errors) > 0
    
    def has_warnings(self) -> bool:
        """Check if analysis has warnings."""
        return len(self.warnings) > 0


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
        self.logger = logging.getLogger(self.__class__.__name__)

    @abstractmethod
    def get_supported_extensions(self) -> List[str]:
        """Get list of supported file extensions.
        
        Returns:
            List of supported file extensions (e.g., ['.py', '.pyi'])
        """
        pass
    
    @abstractmethod
    def analyze_file(self, file_path: Path) -> AnalysisResult:
        """Analyze a single file.
        
        Args:
            file_path: Path to the file to analyze
            
        Returns:
            Analysis result with extracted information
        """
        pass
    
    def analyze_directory(self, directory: str, 
                         patterns: Optional[List[str]] = None,
                         recursive: bool = True,
                         follow_symlinks: bool = False) -> AnalysisResult:
        """Analyze all files in a directory maintaining structure.
        
        Args:
            directory: Relative directory to analyze
            patterns: File patterns to match (defaults to supported extensions)
            recursive: Whether to analyze subdirectories
            follow_symlinks: Whether to follow symbolic links
            
        Returns:
            Analysis result with extracted structures organized by directory
        """
        dir_path = self.project_root / directory
        if not dir_path.exists():
            return AnalysisResult(
                status="error",
                errors=[f"Directory not found: {directory}"]
            )
        
        # Use supported extensions if no patterns provided
        if patterns is None:
            patterns = [f"*{ext}" for ext in self.get_supported_extensions()]
        
        # Find all matching files
        all_files = []
        for pattern in patterns:
            if recursive:
                files = dir_path.rglob(pattern)
            else:
                files = dir_path.glob(pattern)
            
            all_files.extend([f for f in files if f.is_file()])
        
        # Remove duplicates and filter by extensions
        supported_extensions = set(self.get_supported_extensions())
        unique_files = []
        seen = set()
        
        for file_path in all_files:
            if file_path not in seen and file_path.suffix.lower() in supported_extensions:
                unique_files.append(file_path)
                seen.add(file_path)
        
        # Analyze each file
        results = {"modules": {}}
        errors = []
        warnings = []
        
        for file_path in unique_files:
            try:
                file_result = self.analyze_file(file_path)
                
                # Organize by module structure
                rel_path = file_path.relative_to(dir_path)
                module_path = str(rel_path.parent) if rel_path.parent != Path('.') else "."
                
                if module_path not in results["modules"]:
                    results["modules"][module_path] = {
                        "files": {},
                        "analysis_data": [],
                        "summary": {"total_files": 0, "total_items": 0}
                    }
                
                # Store file analysis
                file_name = file_path.stem
                results["modules"][module_path]["files"][file_name] = {
                    "path": str(rel_path),
                    "analysis_result": file_result.data,
                    "status": file_result.status
                }
                
                # Aggregate data (to be customized by subclasses)
                if file_result.data:
                    results["modules"][module_path]["analysis_data"].append(file_result.data)
                    results["modules"][module_path]["summary"]["total_files"] += 1
                
                # Collect errors and warnings
                errors.extend(file_result.errors)
                warnings.extend(file_result.warnings)
                
            except Exception as e:
                error_msg = f"Error analyzing {file_path}: {str(e)}"
                errors.append(error_msg)
                self.logger.error(error_msg)
        
        # Determine overall status
        if errors:
            status = "error" if not results["modules"] else "warning"
        elif warnings:
            status = "warning"
        else:
            status = "success"
        
        return AnalysisResult(
            status=status,
            data=results,
            errors=errors,
            warnings=warnings,
            metadata={
                "total_files_analyzed": len(unique_files),
                "total_modules": len(results["modules"]),
                "directory": directory
            }
        )
    
    def get_file_patterns(self) -> List[str]:
        """Get default file patterns for this analyzer.
        
        Returns:
            List of glob patterns for files this analyzer can handle
        """
        return [f"*{ext}" for ext in self.get_supported_extensions()]
    
    def can_analyze_file(self, file_path: Path) -> bool:
        """Check if this analyzer can handle a specific file.
        
        Args:
            file_path: Path to the file
            
        Returns:
            True if analyzer can handle this file type
        """
        return file_path.suffix.lower() in self.get_supported_extensions()
    
    def get_analyzer_name(self) -> str:
        """Get a human-readable name for this analyzer.
        
        Returns:
            Analyzer name
        """
        return self.__class__.__name__.replace("Analyzer", "")
    
    def get_analyzer_info(self) -> Dict[str, Any]:
        """Get information about this analyzer.
        
        Returns:
            Dictionary with analyzer metadata
        """
        return {
            "name": self.get_analyzer_name(),
            "class": self.__class__.__name__,
            "supported_extensions": self.get_supported_extensions(),
            "file_patterns": self.get_file_patterns(),
            "config": self.config
        }
