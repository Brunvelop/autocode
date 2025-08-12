"""JavaScript/TypeScript code analyzer.

This module provides functionality to analyze JavaScript and TypeScript code
using regex patterns and simple parsing (could be extended to use AST later).
"""

import re
from pathlib import Path
from typing import Dict, Any, List, Optional

from ..base_analyzer import BaseAnalyzer, AnalysisResult


class JavaScriptAnalyzer(BaseAnalyzer):
    """Analyzer for JavaScript and TypeScript code."""
    
    def __init__(self, project_root: Path, config: Dict[str, Any] = None):
        """Initialize the JavaScript analyzer.
        
        Args:
            project_root: Project root directory
            config: Configuration dictionary
        """
        super().__init__(project_root, config)
        
        # Configurable patterns for better extensibility
        self.patterns = {
            # Class definitions
            'classes': re.compile(r'class\s+(\w+)(?:\s+extends\s+(\w+))?\s*\{', re.MULTILINE),
            # Function definitions
            'functions': re.compile(r'(?:function\s+(\w+)|(?:const|let|var)\s+(\w+)\s*=\s*(?:async\s+)?function|\w+\s*:\s*(?:async\s+)?function)', re.MULTILINE),
            # Arrow functions assigned to variables
            'arrow_functions': re.compile(r'(?:const|let|var)\s+(\w+)\s*=\s*(?:async\s+)?\([^)]*\)\s*=>', re.MULTILINE),
            # Exports
            'exports': re.compile(r'export\s+(?:default\s+)?(?:class|function|const|let|var)\s+(\w+)', re.MULTILINE),
            # Imports
            'imports': re.compile(r'import\s+(?:\{([^}]+)\}|(\w+))\s+from\s+[\'"]([^\'"]+)[\'"]', re.MULTILINE),
            # Methods in classes
            'methods': re.compile(r'(\w+)\s*\([^)]*\)\s*\{', re.MULTILINE),
            # Comments (for JSDoc detection)
            'jsdoc': re.compile(r'/\*\*(.*?)\*/', re.DOTALL),
        }
    
    def get_supported_extensions(self) -> List[str]:
        """Get list of supported file extensions.
        
        Returns:
            List of supported extensions
        """
        return ['.js', '.ts', '.jsx', '.tsx']
    
    def analyze_file(self, file_path: Path) -> AnalysisResult:
        """Analyze a single JavaScript/TypeScript file.
        
        Args:
            file_path: Path to the file to analyze
            
        Returns:
            Analysis result with extracted code information
        """
        if not self.can_analyze_file(file_path):
            return AnalysisResult(
                status="error",
                errors=[f"Unsupported file type: {file_path.suffix}"]
            )
        
        try:
            content = file_path.read_text(encoding='utf-8')
            
            # Extract various code elements
            classes = self._extract_classes(content)
            functions = self._extract_functions(content)
            imports = self._extract_imports(content)
            exports = self._extract_exports(content)
            
            # Calculate metrics
            total_loc = len(content.splitlines())
            
            return AnalysisResult(
                status="success",
                data={
                    "file_path": str(file_path),
                    "file_type": "javascript",
                    "language": file_path.suffix[1:],  # js, ts, jsx, tsx
                    "classes": classes,
                    "functions": functions,
                    "imports": imports,
                    "exports": exports,
                    "metrics": {
                        "total_classes": len(classes),
                        "total_functions": len(functions),
                        "total_imports": len(imports),
                        "total_exports": len(exports),
                        "total_loc": total_loc,
                        "average_methods_per_class": sum(len(c["methods"]) for c in classes) / len(classes) if classes else 0
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
    
    def _extract_classes(self, content: str) -> List[Dict[str, Any]]:
        """Extract class definitions from JavaScript content.
        
        Args:
            content: JavaScript content
            
        Returns:
            List of class information dictionaries
        """
        classes = []
        
        for match in self.patterns['classes'].finditer(content):
            class_name = match.group(1)
            extends_class = match.group(2) if match.lastindex > 1 else None
            
            # Find the class body
            start_pos = match.end()
            class_body = self._extract_class_body(content, start_pos)
            
            # Extract methods from class body
            methods = self._extract_methods_from_class_body(class_body)
            
            class_info = {
                "name": class_name,
                "extends": extends_class,
                "methods": methods,
                "line_number": self._get_line_number(content, match.start()),
                "type": "class"
            }
            classes.append(class_info)
        
        return classes
    
    def _extract_functions(self, content: str) -> List[Dict[str, Any]]:
        """Extract function definitions from JavaScript content.
        
        Args:
            content: JavaScript content
            
        Returns:
            List of function information dictionaries
        """
        functions = []
        
        # Regular function declarations
        func_pattern = re.compile(r'function\s+(\w+)\s*\(([^)]*)\)', re.MULTILINE)
        for match in func_pattern.finditer(content):
            func_name = match.group(1)
            params = [p.strip() for p in match.group(2).split(',') if p.strip()]
            
            functions.append({
                "name": func_name,
                "parameters": params,
                "type": "function",
                "line_number": self._get_line_number(content, match.start())
            })
        
        # Arrow functions assigned to variables
        arrow_pattern = re.compile(r'(?:const|let|var)\s+(\w+)\s*=\s*(?:async\s+)?\(([^)]*)\)\s*=>', re.MULTILINE)
        for match in arrow_pattern.finditer(content):
            func_name = match.group(1)
            params = [p.strip() for p in match.group(2).split(',') if p.strip()]
            
            functions.append({
                "name": func_name,
                "parameters": params,
                "type": "arrow_function",
                "line_number": self._get_line_number(content, match.start())
            })
        
        return functions
    
    def _extract_imports(self, content: str) -> List[Dict[str, Any]]:
        """Extract import statements from JavaScript content.
        
        Args:
            content: JavaScript content
            
        Returns:
            List of import information dictionaries
        """
        imports = []
        
        for match in self.patterns['imports'].finditer(content):
            named_imports = match.group(1)
            default_import = match.group(2)
            module_path = match.group(3)
            
            import_info = {
                "module": module_path,
                "line_number": self._get_line_number(content, match.start())
            }
            
            if named_imports:
                import_info["type"] = "named"
                import_info["imports"] = [imp.strip() for imp in named_imports.split(',')]
            elif default_import:
                import_info["type"] = "default"
                import_info["import"] = default_import
            
            imports.append(import_info)
        
        return imports
    
    def _extract_exports(self, content: str) -> List[Dict[str, Any]]:
        """Extract export statements from JavaScript content.
        
        Args:
            content: JavaScript content
            
        Returns:
            List of export information dictionaries
        """
        exports = []
        
        for match in self.patterns['exports'].finditer(content):
            export_name = match.group(1)
            
            exports.append({
                "name": export_name,
                "type": "default" if "default" in match.group(0) else "named",
                "line_number": self._get_line_number(content, match.start())
            })
        
        return exports
    
    def _extract_class_body(self, content: str, start_pos: int) -> str:
        """Extract the body of a class starting from a position.
        
        Args:
            content: Full content
            start_pos: Starting position after class declaration
            
        Returns:
            Class body content
        """
        brace_count = 0
        body_start = -1
        
        for i, char in enumerate(content[start_pos:], start_pos):
            if char == '{':
                if body_start == -1:
                    body_start = i + 1
                brace_count += 1
            elif char == '}':
                brace_count -= 1
                if brace_count == 0:
                    return content[body_start:i]
        
        return ""
    
    def _extract_methods_from_class_body(self, class_body: str) -> List[Dict[str, Any]]:
        """Extract methods from a class body.
        
        Args:
            class_body: Class body content
            
        Returns:
            List of method information dictionaries
        """
        methods = []
        
        # Method pattern: methodName(params) { or async methodName(params) {
        method_pattern = re.compile(r'(?:async\s+)?(\w+)\s*\(([^)]*)\)\s*\{', re.MULTILINE)
        
        for match in method_pattern.finditer(class_body):
            method_name = match.group(1)
            params = [p.strip() for p in match.group(2).split(',') if p.strip()]
            
            # Skip constructor-like patterns that might not be methods
            if method_name in ['if', 'for', 'while', 'switch']:
                continue
            
            methods.append({
                "name": method_name,
                "parameters": params,
                "is_async": "async" in match.group(0),
                "visibility": "+" if not method_name.startswith("_") else "-"
            })
        
        return methods
    
    def _get_line_number(self, content: str, position: int) -> int:
        """Get line number for a position in content.
        
        Args:
            content: Full content
            position: Character position
            
        Returns:
            Line number (1-based)
        """
        return content[:position].count('\n') + 1
