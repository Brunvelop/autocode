"""
Autocode module for automated code quality and documentation checks.
"""

from .doc_checker import DocChecker
from .git_analyzer import GitAnalyzer

__version__ = "0.1.0"
__all__ = ["DocChecker", "GitAnalyzer"]
