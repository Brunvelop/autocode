"""
Autocode module for automated code quality and documentation checks.
"""

from .doc_checker import DocChecker
from .git_analyzer import GitAnalyzer
from .opencode_executor import OpenCodeExecutor, validate_opencode_setup

__version__ = "0.1.0"
__all__ = ["DocChecker", "GitAnalyzer", "OpenCodeExecutor", "validate_opencode_setup"]
