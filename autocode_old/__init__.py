"""
Autocode module for automated code quality and documentation checks.
"""

from .core.docs import check_documentation
from .core.git import GitAnalyzer
from .core.ai import OpenCodeExecutor, validate_opencode_setup

__version__ = "0.3.0"
__all__ = ["check_documentation", "GitAnalyzer", "OpenCodeExecutor", "validate_opencode_setup"]
