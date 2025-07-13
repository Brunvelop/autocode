"""HTML analyzer for extracting DOM structure and components.

This module provides functionality to analyze HTML files and extract
DOM structure, custom elements, and component relationships.
"""

from pathlib import Path
from typing import Dict, Any, List, Optional
from bs4 import BeautifulSoup
import re

from ..base_analyzer import BaseAnalyzer, AnalysisResult


class HTMLAnalyzer(BaseAnalyzer):
    """Analyzer for HTML files to extract DOM structure and components."""
    
    def get_supported_extensions(self) -> List[str]:
        """Get list of supported file extensions.
        
        Returns:
            List of supported HTML extensions
        """
        return ['.html', '.htm']
    
    def analyze_file(self, file_path: Path) -> AnalysisResult:
        """Analyze a single HTML file.
        
        Args:
            file_path: Path to the HTML file to analyze
            
        Returns:
            Analysis result with extracted DOM information
        """
        if not self.can_analyze_file(file_path):
            return AnalysisResult(
                status="error",
                errors=[f"Unsupported file type: {file_path.suffix}"]
            )
        
        try:
            content = file_path.read_text(encoding='utf-8')
            
            # Parse HTML with BeautifulSoup
            try:
                soup = BeautifulSoup(content, 'html.parser')
            except Exception as e:
                return AnalysisResult(
                    status="error",
                    errors=[f"HTML parsing error in {file_path}: {str(e)}"]
                )
            
            # Extract various HTML elements
            elements = self._extract_elements(soup)
            custom_elements = self._extract_custom_elements(soup)
            form_elements = self._extract_form_elements(soup)
            scripts = self._extract_scripts(soup)
            links = self._extract_links(soup)
            relationships = self._extract_relationships(soup)
            
            # Calculate metrics
            total_elements = len(elements)
            total_loc = len(content.splitlines())
            
            return AnalysisResult(
                status="success",
                data={
                    "file_path": str(file_path),
                    "file_type": "html",
                    "elements": elements,
                    "custom_elements": custom_elements,
                    "form_elements": form_elements,
                    "scripts": scripts,
                    "links": links,
                    "relationships": relationships,
                    "metrics": {
                        "total_elements": total_elements,
                        "custom_elements": len(custom_elements),
                        "form_elements": len(form_elements),
                        "script_tags": len(scripts),
                        "external_links": len(links),
                        "total_loc": total_loc,
                        "dom_depth": self._calculate_dom_depth(soup)
                    }
                }
            )
            
        except UnicodeDecodeError as e:
            return AnalysisResult(
                status="error",
                errors=[f"Encoding error reading {file_path}: {str(e)}"]
            )
        except Exception as e:
            return AnalysisResult(
                status="error",
                errors=[f"Unexpected error analyzing {file_path}: {str(e)}"]
            )
    
    def _extract_elements(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """Extract all HTML elements with their attributes.
        
        Args:
            soup: BeautifulSoup parsed HTML
            
        Returns:
            List of element information dictionaries
        """
        elements = []
        
        for element in soup.find_all(True):
            if element.name in ['html', 'head', 'body']:
                continue  # Skip structural elements
            
            element_info = {
                "tag": element.name,
                "id": element.get('id'),
                "classes": element.get('class', []),
                "attributes": dict(element.attrs),
                "text_content": element.get_text(strip=True)[:100] if element.get_text(strip=True) else None,
                "has_children": len(list(element.children)) > 0,
                "line_number": getattr(element, 'sourceline', 0)
            }
            
            elements.append(element_info)
        
        return elements
    
    def _extract_custom_elements(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """Extract custom elements (elements with hyphens in name).
        
        Args:
            soup: BeautifulSoup parsed HTML
            
        Returns:
            List of custom element information
        """
        custom_elements = []
        
        for element in soup.find_all(True):
            if '-' in element.name:
                custom_info = {
                    "name": element.name,
                    "attributes": dict(element.attrs),
                    "children": [child.name for child in element.find_all(True, recursive=False) if child.name],
                    "line_number": getattr(element, 'sourceline', 0),
                    "type": "custom_element"
                }
                custom_elements.append(custom_info)
        
        return custom_elements
    
    def _extract_form_elements(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """Extract form-related elements.
        
        Args:
            soup: BeautifulSoup parsed HTML
            
        Returns:
            List of form element information
        """
        form_elements = []
        form_tags = ['form', 'input', 'textarea', 'select', 'button', 'label']
        
        for tag in form_tags:
            for element in soup.find_all(tag):
                form_info = {
                    "tag": element.name,
                    "type": element.get('type', ''),
                    "name": element.get('name'),
                    "id": element.get('id'),
                    "required": element.has_attr('required'),
                    "attributes": dict(element.attrs),
                    "line_number": getattr(element, 'sourceline', 0)
                }
                form_elements.append(form_info)
        
        return form_elements
    
    def _extract_scripts(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """Extract script tags and their information.
        
        Args:
            soup: BeautifulSoup parsed HTML
            
        Returns:
            List of script information
        """
        scripts = []
        
        for script in soup.find_all('script'):
            script_info = {
                "src": script.get('src'),
                "type": script.get('type', 'text/javascript'),
                "async": script.has_attr('async'),
                "defer": script.has_attr('defer'),
                "has_inline_code": bool(script.string and script.string.strip()),
                "inline_code_length": len(script.string.strip()) if script.string else 0,
                "line_number": getattr(script, 'sourceline', 0)
            }
            scripts.append(script_info)
        
        return scripts
    
    def _extract_links(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """Extract link elements (CSS, external resources).
        
        Args:
            soup: BeautifulSoup parsed HTML
            
        Returns:
            List of link information
        """
        links = []
        
        # Link tags
        for link in soup.find_all('link'):
            link_info = {
                "rel": link.get('rel', []),
                "href": link.get('href'),
                "type": link.get('type'),
                "media": link.get('media'),
                "line_number": getattr(link, 'sourceline', 0),
                "tag_type": "link"
            }
            links.append(link_info)
        
        # Anchor tags with external links
        for anchor in soup.find_all('a', href=True):
            href = anchor.get('href')
            if href and (href.startswith('http') or href.startswith('//')):
                link_info = {
                    "href": href,
                    "text": anchor.get_text(strip=True),
                    "target": anchor.get('target'),
                    "line_number": getattr(anchor, 'sourceline', 0),
                    "tag_type": "anchor"
                }
                links.append(link_info)
        
        return links
    
    def _extract_relationships(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """Extract parent-child relationships between elements.
        
        Args:
            soup: BeautifulSoup parsed HTML
            
        Returns:
            List of relationship information
        """
        relationships = []
        
        def extract_relationships_recursive(element, parent_info=None):
            if not element.name:
                return
            
            current_info = {
                "tag": element.name,
                "id": element.get('id'),
                "classes": element.get('class', [])
            }
            
            if parent_info:
                relationships.append({
                    "parent": parent_info,
                    "child": current_info,
                    "relationship_type": "parent_child"
                })
            
            # Process children
            for child in element.find_all(True, recursive=False):
                extract_relationships_recursive(child, current_info)
        
        # Start from body or root elements
        body = soup.find('body')
        if body:
            for child in body.find_all(True, recursive=False):
                extract_relationships_recursive(child)
        
        return relationships
    
    def _calculate_dom_depth(self, soup: BeautifulSoup) -> int:
        """Calculate the maximum depth of the DOM tree.
        
        Args:
            soup: BeautifulSoup parsed HTML
            
        Returns:
            Maximum DOM depth
        """
        def get_depth(element):
            if not element.find_all(True, recursive=False):
                return 1
            
            return 1 + max(get_depth(child) for child in element.find_all(True, recursive=False))
        
        body = soup.find('body')
        if body:
            return get_depth(body)
        
        return 0
