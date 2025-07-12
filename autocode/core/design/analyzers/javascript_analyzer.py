"""JavaScript/HTML analyzer for UI components.

This module provides functionality to analyze JavaScript and HTML files
to extract component structure, hierarchy, and relationships.
"""

import re
import json
from pathlib import Path
from typing import Dict, List, Any, Optional
from bs4 import BeautifulSoup

from .base_analyzer import BaseAnalyzer


class JavaScriptAnalyzer(BaseAnalyzer):
    """Analyzer for JavaScript and HTML files to extract UI components."""
    
    def __init__(self, project_root: Path, config: Dict[str, Any] = None):
        """Initialize the JavaScript analyzer.
        
        Args:
            project_root: Project root directory
            config: Configuration dictionary
        """
        super().__init__(project_root, config)
        self.component_patterns = {
            # Web Components
            'custom_elements': re.compile(r'customElements\.define\s*\(\s*[\'"]([^\'\"]+)[\'"]', re.MULTILINE),
            # Class-based components
            'class_components': re.compile(r'class\s+(\w+)\s+extends\s+HTMLElement', re.MULTILINE),
            # Function components (simple pattern)
            'function_components': re.compile(r'function\s+(\w+Component)\s*\(', re.MULTILINE),
            # Template literals with HTML
            'template_literals': re.compile(r'`([^`]*<[^>]+>[^`]*)`', re.MULTILINE | re.DOTALL),
            # DOM queries
            'dom_queries': re.compile(r'(?:document\.)?(?:querySelector|getElementById|getElementsBy\w+)\s*\(\s*[\'"]([^\'\"]+)[\'"]', re.MULTILINE),
        }

    def get_supported_extensions(self) -> List[str]:
        """Get list of supported file extensions.
        
        Returns:
            List of supported extensions
        """
        return ['.js', '.html', '.css', '.ts']

    def analyze_file(self, file_path: Path) -> Dict[str, Any]:
        """Analyze a single JavaScript or HTML file.
        
        Args:
            file_path: Path to the file to analyze
            
        Returns:
            Dictionary containing extracted component information
        """
        try:
            content = file_path.read_text(encoding='utf-8')
            
            if file_path.suffix == '.html':
                return self._analyze_html_file(file_path, content)
            elif file_path.suffix in ['.js', '.ts']:
                return self._analyze_js_file(file_path, content)
            elif file_path.suffix == '.css':
                return self._analyze_css_file(file_path, content)
            else:
                return self._create_empty_analysis(file_path)
                
        except Exception as e:
            return {
                'file_path': str(file_path),
                'error': str(e),
                'components': [],
                'elements': [],
                'relationships': []
            }

    def _analyze_html_file(self, file_path: Path, content: str) -> Dict[str, Any]:
        """Analyze HTML file for component structure.
        
        Args:
            file_path: Path to HTML file
            content: File content
            
        Returns:
            Analysis results
        """
        try:
            soup = BeautifulSoup(content, 'html.parser')
            
            # Extract custom elements and components
            components = []
            elements = []
            relationships = []
            
            # Find all elements with IDs or classes
            for element in soup.find_all(True):
                element_info = {
                    'tag': element.name,
                    'id': element.get('id'),
                    'classes': element.get('class', []),
                    'attributes': dict(element.attrs),
                    'text_content': element.get_text(strip=True)[:100] if element.get_text(strip=True) else None,
                    'line_number': getattr(element, 'sourceline', 0)
                }
                
                # Check if it's a custom element (contains hyphens)
                if '-' in element.name:
                    components.append({
                        'name': element.name,
                        'type': 'custom_element',
                        'props': element_info['attributes'],
                        'children': [child.name for child in element.find_all(True, recursive=False)],
                        'line_number': element_info['line_number']
                    })
                
                elements.append(element_info)
                
                # Build parent-child relationships
                parent = element.parent
                if parent and parent.name != '[document]':
                    relationships.append({
                        'parent': parent.name,
                        'child': element.name,
                        'parent_id': parent.get('id'),
                        'child_id': element.get('id')
                    })
            
            # Extract inline JavaScript components
            scripts = soup.find_all('script')
            for script in scripts:
                if script.string:
                    js_analysis = self._analyze_js_content(script.string)
                    components.extend(js_analysis['components'])
                    
            return {
                'file_path': str(file_path),
                'file_type': 'html',
                'components': components,
                'elements': elements,
                'relationships': relationships,
                'metrics': {
                    'total_elements': len(elements),
                    'custom_elements': len([c for c in components if c['type'] == 'custom_element']),
                    'total_components': len(components)
                }
            }
            
        except Exception as e:
            return self._create_error_analysis(file_path, e)

    def _analyze_js_file(self, file_path: Path, content: str) -> Dict[str, Any]:
        """Analyze JavaScript file for component definitions.
        
        Args:
            file_path: Path to JS file
            content: File content
            
        Returns:
            Analysis results
        """
        return self._analyze_js_content(content, file_path)

    def _analyze_js_content(self, content: str, file_path: Optional[Path] = None) -> Dict[str, Any]:
        """Analyze JavaScript content for component definitions.
        
        Args:
            content: JavaScript content
            file_path: Optional file path
            
        Returns:
            Analysis results
        """
        components = []
        elements = []
        relationships = []
        
        # Find custom element definitions
        custom_elements = self.component_patterns['custom_elements'].findall(content)
        for element_name in custom_elements:
            components.append({
                'name': element_name,
                'type': 'custom_element_definition',
                'props': [],
                'children': [],
                'line_number': self._get_line_number(content, element_name)
            })
        
        # Find class-based components
        class_components = self.component_patterns['class_components'].findall(content)
        for class_name in class_components:
            components.append({
                'name': class_name,
                'type': 'class_component',
                'props': self._extract_props_from_class(content, class_name),
                'children': [],
                'line_number': self._get_line_number(content, class_name)
            })
        
        # Find function components
        function_components = self.component_patterns['function_components'].findall(content)
        for func_name in function_components:
            components.append({
                'name': func_name,
                'type': 'function_component',
                'props': self._extract_props_from_function(content, func_name),
                'children': [],
                'line_number': self._get_line_number(content, func_name)
            })
        
        # Find DOM queries and interactions
        dom_queries = self.component_patterns['dom_queries'].findall(content)
        for query in dom_queries:
            elements.append({
                'selector': query,
                'type': 'dom_query',
                'line_number': self._get_line_number(content, query)
            })
        
        # Find template literals with HTML
        templates = self.component_patterns['template_literals'].findall(content)
        for template in templates:
            html_elements = self._extract_elements_from_template(template)
            elements.extend(html_elements)
        
        return {
            'file_path': str(file_path) if file_path else 'inline',
            'file_type': 'javascript',
            'components': components,
            'elements': elements,
            'relationships': relationships,
            'metrics': {
                'total_components': len(components),
                'custom_elements': len([c for c in components if 'custom_element' in c['type']]),
                'function_components': len([c for c in components if c['type'] == 'function_component']),
                'class_components': len([c for c in components if c['type'] == 'class_component'])
            }
        }

    def _analyze_css_file(self, file_path: Path, content: str) -> Dict[str, Any]:
        """Analyze CSS file for component styles.
        
        Args:
            file_path: Path to CSS file
            content: File content
            
        Returns:
            Analysis results
        """
        # Extract CSS selectors that might relate to components
        selectors = re.findall(r'\.([a-zA-Z][a-zA-Z0-9_-]*)', content)
        id_selectors = re.findall(r'#([a-zA-Z][a-zA-Z0-9_-]*)', content)
        
        return {
            'file_path': str(file_path),
            'file_type': 'css',
            'components': [],
            'elements': [],
            'style_selectors': {
                'classes': list(set(selectors)),
                'ids': list(set(id_selectors))
            },
            'metrics': {
                'class_selectors': len(set(selectors)),
                'id_selectors': len(set(id_selectors))
            }
        }

    def _extract_props_from_class(self, content: str, class_name: str) -> List[str]:
        """Extract properties from a class component.
        
        Args:
            content: JavaScript content
            class_name: Name of the class
            
        Returns:
            List of property names
        """
        # Simple pattern to find properties
        class_pattern = rf'class\s+{class_name}.*?{{(.*?)(?=class|\Z)'
        match = re.search(class_pattern, content, re.DOTALL)
        if match:
            class_body = match.group(1)
            props = re.findall(r'this\.(\w+)', class_body)
            return list(set(props))
        return []

    def _extract_props_from_function(self, content: str, func_name: str) -> List[str]:
        """Extract parameters from a function component.
        
        Args:
            content: JavaScript content
            func_name: Name of the function
            
        Returns:
            List of parameter names
        """
        func_pattern = rf'function\s+{func_name}\s*\(\s*([^)]*)\s*\)'
        match = re.search(func_pattern, content)
        if match:
            params = match.group(1)
            if params.strip():
                return [p.strip() for p in params.split(',')]
        return []

    def _extract_elements_from_template(self, template: str) -> List[Dict[str, Any]]:
        """Extract HTML elements from template literal.
        
        Args:
            template: Template literal content
            
        Returns:
            List of element information
        """
        elements = []
        try:
            # Parse HTML in template literal
            soup = BeautifulSoup(template, 'html.parser')
            for element in soup.find_all(True):
                elements.append({
                    'tag': element.name,
                    'id': element.get('id'),
                    'classes': element.get('class', []),
                    'type': 'template_element'
                })
        except:
            pass
        return elements

    def _get_line_number(self, content: str, search_text: str) -> int:
        """Get line number of text in content.
        
        Args:
            content: Full content
            search_text: Text to find
            
        Returns:
            Line number (1-based)
        """
        lines = content.split('\n')
        for i, line in enumerate(lines):
            if search_text in line:
                return i + 1
        return 0

    def _create_empty_analysis(self, file_path: Path) -> Dict[str, Any]:
        """Create empty analysis result.
        
        Args:
            file_path: Path to file
            
        Returns:
            Empty analysis dictionary
        """
        return {
            'file_path': str(file_path),
            'file_type': 'unknown',
            'components': [],
            'elements': [],
            'relationships': [],
            'metrics': {}
        }

    def _create_error_analysis(self, file_path: Path, error: Exception) -> Dict[str, Any]:
        """Create error analysis result.
        
        Args:
            file_path: Path to file
            error: Exception that occurred
            
        Returns:
            Error analysis dictionary
        """
        return {
            'file_path': str(file_path),
            'error': str(error),
            'components': [],
            'elements': [],
            'relationships': [],
            'metrics': {}
        }

    def analyze_directory(self, directory: str, pattern: str = "*.{js,html,css}") -> Dict[str, Any]:
        """Analyze directory for UI components.
        
        Args:
            directory: Directory to analyze
            pattern: File pattern to match
            
        Returns:
            Analysis results organized by directory structure
        """
        target_dir = self.project_root / directory
        if not target_dir.exists():
            return {"error": f"Directory {directory} not found", "modules": {}}

        # Support multiple extensions
        extensions = ['.js', '.html', '.css', '.ts']
        all_files = []
        for ext in extensions:
            all_files.extend(target_dir.rglob(f"*{ext}"))

        # Organize by module structure
        modules = {}
        
        for file_path in all_files:
            # Get relative path from target directory
            rel_path = file_path.relative_to(target_dir)
            module_path = str(rel_path.parent) if rel_path.parent != Path('.') else "."
            
            if module_path not in modules:
                modules[module_path] = {
                    "files": {},
                    "components": [],
                    "total_elements": 0
                }
            
            # Analyze the file
            analysis = self.analyze_file(file_path)
            
            # Store in module structure
            modules[module_path]["files"][rel_path.stem] = analysis
            modules[module_path]["components"].extend(analysis.get('components', []))
            modules[module_path]["total_elements"] += analysis.get('metrics', {}).get('total_elements', 0)

        return {
            "modules": modules,
            "summary": {
                "total_modules": len(modules),
                "total_files": len(all_files),
                "total_components": sum(len(m["components"]) for m in modules.values())
            }
        }
