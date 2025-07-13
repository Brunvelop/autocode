"""CSS analyzer for extracting styles and selectors.

This module provides functionality to analyze CSS files and extract
selectors, properties, and style information.
"""

from pathlib import Path
from typing import Dict, Any, List, Optional
import re

from ..base_analyzer import BaseAnalyzer, AnalysisResult


class CSSAnalyzer(BaseAnalyzer):
    """Analyzer for CSS files to extract styles and selectors."""
    
    def __init__(self, project_root: Path, config: Dict[str, Any] = None):
        """Initialize the CSS analyzer.
        
        Args:
            project_root: Project root directory
            config: Configuration dictionary
        """
        super().__init__(project_root, config)
        
        # CSS parsing patterns
        self.patterns = {
            # CSS rules: selector { properties }
            'rules': re.compile(r'([^{}]+)\s*\{([^{}]*)\}', re.MULTILINE | re.DOTALL),
            # Properties within rules
            'properties': re.compile(r'([^:;]+):\s*([^;]+);?', re.MULTILINE),
            # Media queries
            'media_queries': re.compile(r'@media\s+([^{]+)\s*\{', re.MULTILINE),
            # Imports
            'imports': re.compile(r'@import\s+(?:url\()?[\'"]?([^\'"()]+)[\'"]?\)?', re.MULTILINE),
            # Variables (CSS custom properties)
            'variables': re.compile(r'--([^:;]+):\s*([^;]+);?', re.MULTILINE),
            # Comments
            'comments': re.compile(r'/\*.*?\*/', re.DOTALL),
        }
    
    def get_supported_extensions(self) -> List[str]:
        """Get list of supported file extensions.
        
        Returns:
            List of supported CSS extensions
        """
        return ['.css', '.scss', '.sass', '.less']
    
    def analyze_file(self, file_path: Path) -> AnalysisResult:
        """Analyze a single CSS file.
        
        Args:
            file_path: Path to the CSS file to analyze
            
        Returns:
            Analysis result with extracted style information
        """
        if not self.can_analyze_file(file_path):
            return AnalysisResult(
                status="error",
                errors=[f"Unsupported file type: {file_path.suffix}"]
            )
        
        try:
            content = file_path.read_text(encoding='utf-8')
            
            # Remove comments for cleaner parsing
            clean_content = self.patterns['comments'].sub('', content)
            
            # Extract CSS components
            rules = self._extract_rules(clean_content)
            selectors = self._extract_selectors(rules)
            properties = self._extract_all_properties(rules)
            media_queries = self._extract_media_queries(content)
            imports = self._extract_imports(content)
            variables = self._extract_variables(clean_content)
            
            # Calculate metrics
            total_loc = len(content.splitlines())
            
            return AnalysisResult(
                status="success",
                data={
                    "file_path": str(file_path),
                    "file_type": "css",
                    "language": file_path.suffix[1:],  # css, scss, sass, less
                    "rules": rules,
                    "selectors": selectors,
                    "properties": properties,
                    "media_queries": media_queries,
                    "imports": imports,
                    "variables": variables,
                    "metrics": {
                        "total_rules": len(rules),
                        "total_selectors": len(selectors),
                        "unique_properties": len(set(prop["property"] for prop in properties)),
                        "media_queries": len(media_queries),
                        "imports": len(imports),
                        "variables": len(variables),
                        "total_loc": total_loc,
                        "class_selectors": len([s for s in selectors if s["type"] == "class"]),
                        "id_selectors": len([s for s in selectors if s["type"] == "id"]),
                        "element_selectors": len([s for s in selectors if s["type"] == "element"])
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
    
    def _extract_rules(self, content: str) -> List[Dict[str, Any]]:
        """Extract CSS rules from content.
        
        Args:
            content: CSS content
            
        Returns:
            List of CSS rule information
        """
        rules = []
        
        for match in self.patterns['rules'].finditer(content):
            selector_text = match.group(1).strip()
            properties_text = match.group(2).strip()
            
            # Extract properties for this rule
            rule_properties = []
            for prop_match in self.patterns['properties'].finditer(properties_text):
                prop_name = prop_match.group(1).strip()
                prop_value = prop_match.group(2).strip()
                
                rule_properties.append({
                    "property": prop_name,
                    "value": prop_value
                })
            
            rule_info = {
                "selector": selector_text,
                "properties": rule_properties,
                "property_count": len(rule_properties),
                "line_number": self._get_line_number(content, match.start())
            }
            rules.append(rule_info)
        
        return rules
    
    def _extract_selectors(self, rules: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Extract and classify selectors from rules.
        
        Args:
            rules: List of CSS rules
            
        Returns:
            List of selector information
        """
        selectors = []
        
        for rule in rules:
            selector_text = rule["selector"]
            
            # Split multiple selectors (comma-separated)
            individual_selectors = [s.strip() for s in selector_text.split(',')]
            
            for selector in individual_selectors:
                selector_info = {
                    "selector": selector,
                    "type": self._classify_selector(selector),
                    "specificity": self._calculate_specificity(selector),
                    "property_count": rule["property_count"],
                    "line_number": rule["line_number"]
                }
                selectors.append(selector_info)
        
        return selectors
    
    def _extract_all_properties(self, rules: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Extract all CSS properties with usage information.
        
        Args:
            rules: List of CSS rules
            
        Returns:
            List of property information
        """
        properties = []
        
        for rule in rules:
            for prop in rule["properties"]:
                prop_info = {
                    "property": prop["property"],
                    "value": prop["value"],
                    "selector": rule["selector"],
                    "line_number": rule["line_number"],
                    "category": self._categorize_property(prop["property"])
                }
                properties.append(prop_info)
        
        return properties
    
    def _extract_media_queries(self, content: str) -> List[Dict[str, Any]]:
        """Extract media queries from CSS content.
        
        Args:
            content: CSS content
            
        Returns:
            List of media query information
        """
        media_queries = []
        
        for match in self.patterns['media_queries'].finditer(content):
            media_condition = match.group(1).strip()
            
            media_info = {
                "condition": media_condition,
                "type": self._classify_media_query(media_condition),
                "line_number": self._get_line_number(content, match.start())
            }
            media_queries.append(media_info)
        
        return media_queries
    
    def _extract_imports(self, content: str) -> List[Dict[str, Any]]:
        """Extract CSS imports.
        
        Args:
            content: CSS content
            
        Returns:
            List of import information
        """
        imports = []
        
        for match in self.patterns['imports'].finditer(content):
            import_path = match.group(1)
            
            import_info = {
                "path": import_path,
                "type": "external" if import_path.startswith(('http', '//')) else "local",
                "line_number": self._get_line_number(content, match.start())
            }
            imports.append(import_info)
        
        return imports
    
    def _extract_variables(self, content: str) -> List[Dict[str, Any]]:
        """Extract CSS custom properties (variables).
        
        Args:
            content: CSS content
            
        Returns:
            List of variable information
        """
        variables = []
        
        for match in self.patterns['variables'].finditer(content):
            var_name = match.group(1).strip()
            var_value = match.group(2).strip()
            
            var_info = {
                "name": var_name,
                "value": var_value,
                "type": self._classify_variable_value(var_value),
                "line_number": self._get_line_number(content, match.start())
            }
            variables.append(var_info)
        
        return variables
    
    def _classify_selector(self, selector: str) -> str:
        """Classify a CSS selector by type.
        
        Args:
            selector: CSS selector string
            
        Returns:
            Selector type ('class', 'id', 'element', 'attribute', 'pseudo', 'complex')
        """
        selector = selector.strip()
        
        if selector.startswith('#'):
            return "id"
        elif selector.startswith('.'):
            return "class"
        elif '[' in selector and ']' in selector:
            return "attribute"
        elif ':' in selector:
            return "pseudo"
        elif any(combinator in selector for combinator in [' ', '>', '+', '~']):
            return "complex"
        else:
            return "element"
    
    def _calculate_specificity(self, selector: str) -> int:
        """Calculate CSS specificity score (simplified).
        
        Args:
            selector: CSS selector string
            
        Returns:
            Specificity score
        """
        # Simplified specificity calculation
        score = 0
        
        # Count IDs (most specific)
        score += selector.count('#') * 100
        
        # Count classes, attributes, and pseudo-classes
        score += selector.count('.') * 10
        score += selector.count('[') * 10
        score += selector.count(':') * 10
        
        # Count elements
        elements = re.findall(r'\b[a-zA-Z][a-zA-Z0-9]*\b', selector)
        score += len(elements)
        
        return score
    
    def _categorize_property(self, property_name: str) -> str:
        """Categorize a CSS property.
        
        Args:
            property_name: CSS property name
            
        Returns:
            Property category
        """
        layout_props = ['display', 'position', 'top', 'right', 'bottom', 'left', 'float', 'clear', 'flex', 'grid']
        box_model_props = ['width', 'height', 'margin', 'padding', 'border', 'box-sizing']
        typography_props = ['font', 'text', 'line-height', 'letter-spacing', 'word-spacing']
        color_props = ['color', 'background', 'border-color', 'outline-color']
        animation_props = ['animation', 'transition', 'transform']
        
        prop = property_name.lower()
        
        if any(p in prop for p in layout_props):
            return "layout"
        elif any(p in prop for p in box_model_props):
            return "box-model"
        elif any(p in prop for p in typography_props):
            return "typography"
        elif any(p in prop for p in color_props):
            return "color"
        elif any(p in prop for p in animation_props):
            return "animation"
        else:
            return "other"
    
    def _classify_media_query(self, condition: str) -> str:
        """Classify a media query by type.
        
        Args:
            condition: Media query condition
            
        Returns:
            Media query type
        """
        condition = condition.lower()
        
        if 'print' in condition:
            return "print"
        elif 'screen' in condition:
            return "screen"
        elif 'max-width' in condition or 'min-width' in condition:
            return "responsive"
        elif 'orientation' in condition:
            return "orientation"
        else:
            return "other"
    
    def _classify_variable_value(self, value: str) -> str:
        """Classify a CSS variable value by type.
        
        Args:
            value: Variable value
            
        Returns:
            Value type ('color', 'size', 'font', 'other')
        """
        value = value.lower().strip()
        
        if re.match(r'^#[0-9a-f]{3,6}$', value) or value.startswith('rgb') or value.startswith('hsl'):
            return "color"
        elif any(unit in value for unit in ['px', 'em', 'rem', '%', 'vh', 'vw']):
            return "size"
        elif 'font' in value or any(font in value for font in ['arial', 'helvetica', 'serif', 'sans-serif']):
            return "font"
        else:
            return "other"
    
    def _get_line_number(self, content: str, position: int) -> int:
        """Get line number for a position in content.
        
        Args:
            content: Full content
            position: Character position
            
        Returns:
            Line number (1-based)
        """
        return content[:position].count('\n') + 1
