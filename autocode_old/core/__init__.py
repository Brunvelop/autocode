"""
Core functionality for autocode.

This module is organized into thematic submodules for better maintainability:
- docs: Documentation checking and indexing
- git: Git analysis and change tracking
- test: Test status checking and validation
- ai: AI-powered analysis and token counting
- design: Design generation from code
"""

# Documentation tools
from .docs import check_documentation, DocIndexer

# Git analysis tools
from .git import GitAnalyzer

# Test checking tools
from .test import TestChecker

# AI and analysis tools
from .ai import OpenCodeExecutor, validate_opencode_setup, TokenCounter

# Design generation tools
from .design import CodeToDesign

__all__ = [
    "check_documentation",
    "GitAnalyzer", 
    "OpenCodeExecutor",
    "validate_opencode_setup",
    "DocIndexer",
    "TokenCounter",
    "TestChecker",
    "CodeToDesign"
]
