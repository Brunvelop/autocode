"""Web analyzers module.

This module contains specialized analyzers for web technologies like HTML and CSS.
"""

from .html_analyzer import HTMLAnalyzer
from .css_analyzer import CSSAnalyzer

__all__ = ["HTMLAnalyzer", "CSSAnalyzer"]
