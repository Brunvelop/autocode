"""
Documentation checking module with functional architecture.
"""

# New functional API
from .checker import check_documentation, get_issues_only, has_documentation_issues
from .formatters import format_cli_output, format_json_output, format_summary_only
from .types import (
    DocCheckResult,
    DocStatus,
    DocType,
    StatusType,
    CodeFile,
    CodeDirectory,
    DocFile
)

# Keep DocIndexer for compatibility (until it's also refactored)
from .doc_indexer import DocIndexer

__all__ = [
    # Main API functions
    "check_documentation",
    "get_issues_only", 
    "has_documentation_issues",
    
    # Formatters
    "format_cli_output",
    "format_json_output", 
    "format_summary_only",
    
    # Types
    "DocCheckResult",
    "DocStatus",
    "DocType",
    "StatusType",
    "CodeFile",
    "CodeDirectory", 
    "DocFile",
    
    # Legacy compatibility (will be removed when other modules are refactored)
    "DocIndexer"
]
