"""
Autocode module for automated code quality and documentation checks.
"""

from .core.doc_checker import DocChecker
from .core.git_analyzer import GitAnalyzer
from .core.opencode_executor import OpenCodeExecutor, validate_opencode_setup

__version__ = "0.3.0"
__all__ = ["DocChecker", "GitAnalyzer", "OpenCodeExecutor", "validate_opencode_setup"]
