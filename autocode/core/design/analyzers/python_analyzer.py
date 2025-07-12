"""Python code analyzer.

This module provides functionality to analyze Python code using AST parsing.
"""

import ast
from pathlib import Path
from typing import List, Dict, Any

from .base_analyzer import BaseAnalyzer


class PythonAnalyzer(BaseAnalyzer):
    """Analyzer for Python code using AST parsing."""

    def get_supported_extensions(self) -> list[str]:
        """Get list of supported file extensions.
        
        Returns:
            List of supported Python file extensions
        """
        return ['.py', '.pyi']

    def analyze_directory(self, directory: str, pattern: str = "*.py") -> Dict[str, Dict]:
        """Analyze all Python files in a directory maintaining structure.
        
        Args:
            directory: Relative directory to analyze
            pattern: File pattern
            
        Returns:
            Dictionary of extracted structures organized by directory
        """
        dir_path = self.project_root / directory
        structures = {"modules": {}}
        
        for file_path in dir_path.rglob(pattern):
            if file_path.is_file() and file_path.suffix == ".py":
                # Get relative path and module info
                rel_path = file_path.relative_to(self.project_root)
                module_dir = str(rel_path.parent)
                file_name = file_path.stem
                
                # Initialize module structure if needed
                if module_dir not in structures["modules"]:
                    structures["modules"][module_dir] = {
                        "files": {},
                        "classes": []
                    }
                
                # Parse file
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        tree = ast.parse(f.read(), filename=str(file_path))
                except (SyntaxError, UnicodeDecodeError) as e:
                    # Skip files that can't be parsed
                    continue
                
                file_classes = []
                for node in ast.walk(tree):
                    if isinstance(node, ast.ClassDef):
                        # Extract methods with detailed information
                        methods = []
                        for item in node.body:
                            if isinstance(item, ast.FunctionDef):
                                method_info = self._extract_method_info(item)
                                methods.append(method_info)
                        
                        # Extract class attributes
                        attributes = []
                        for item in node.body:
                            if isinstance(item, ast.Assign):
                                for target in item.targets:
                                    if isinstance(target, ast.Name):
                                        attr_info = self._extract_attribute_info(target, item)
                                        attributes.append(attr_info)
                        
                        class_info = {
                            "name": node.name,
                            "bases": [base.id for base in node.bases if hasattr(base, "id")],
                            "methods": methods,
                            "attributes": attributes,
                            "file": str(rel_path),
                            "module": module_dir,
                            "file_name": file_name,
                            "loc": node.end_lineno - node.lineno + 1 if hasattr(node, 'end_lineno') else 0,
                            "num_methods": len(methods)
                        }
                        file_classes.append(class_info)
                        structures["modules"][module_dir]["classes"].append(class_info)
                
                # Store file info
                structures["modules"][module_dir]["files"][file_name] = {
                    "path": str(rel_path),
                    "classes": file_classes
                }
        
        return structures

    def _extract_method_info(self, node: ast.FunctionDef) -> Dict[str, Any]:
        """Extract detailed information from a method node.
        
        Args:
            node: AST FunctionDef node
            
        Returns:
            Dictionary with method information
        """
        # Determine visibility
        visibility = "+" if not node.name.startswith("_") else "-"
        
        # Extract parameters
        params = []
        for arg in node.args.args:
            param_info = {"name": arg.arg}
            if arg.annotation:
                param_info["type"] = self._get_type_annotation(arg.annotation)
            params.append(param_info)
        
        # Extract return type
        return_type = None
        if node.returns:
            return_type = self._get_type_annotation(node.returns)
        
        # Check for decorators
        decorators = []
        for decorator in node.decorator_list:
            if isinstance(decorator, ast.Name):
                decorators.append(decorator.id)
            elif isinstance(decorator, ast.Attribute):
                decorators.append(decorator.attr)
        
        return {
            "name": node.name,
            "visibility": visibility,
            "parameters": params,
            "return_type": return_type,
            "decorators": decorators,
            "is_property": "property" in decorators,
            "is_static": "staticmethod" in decorators,
            "is_class": "classmethod" in decorators
        }

    def _extract_attribute_info(self, target: ast.Name, assign_node: ast.Assign) -> Dict[str, Any]:
        """Extract information from a class attribute assignment.
        
        Args:
            target: AST Name node (attribute name)
            assign_node: AST Assign node
            
        Returns:
            Dictionary with attribute information
        """
        # Determine visibility
        visibility = "+" if not target.id.startswith("_") else "-"
        
        # Try to extract type from annotation or value
        attr_type = None
        if hasattr(assign_node, 'type_comment') and assign_node.type_comment:
            attr_type = assign_node.type_comment
        elif isinstance(assign_node.value, ast.Constant):
            attr_type = type(assign_node.value.value).__name__
        elif isinstance(assign_node.value, ast.List):
            attr_type = "list"
        elif isinstance(assign_node.value, ast.Dict):
            attr_type = "dict"
        
        return {
            "name": target.id,
            "visibility": visibility,
            "type": attr_type
        }

    def _get_type_annotation(self, annotation: ast.expr) -> str:
        """Extract type annotation as string.
        
        Args:
            annotation: AST annotation node
            
        Returns:
            Type annotation as string
        """
        if isinstance(annotation, ast.Name):
            return annotation.id
        elif isinstance(annotation, ast.Attribute):
            return f"{annotation.value.id}.{annotation.attr}" if hasattr(annotation.value, 'id') else annotation.attr
        elif isinstance(annotation, ast.Subscript):
            # Handle generic types like List[str], Dict[str, int]
            if isinstance(annotation.value, ast.Name):
                base_type = annotation.value.id
                if isinstance(annotation.slice, ast.Name):
                    return f"{base_type}[{annotation.slice.id}]"
                elif isinstance(annotation.slice, ast.Tuple):
                    elements = []
                    for elt in annotation.slice.elts:
                        if isinstance(elt, ast.Name):
                            elements.append(elt.id)
                    return f"{base_type}[{', '.join(elements)}]"
            return str(annotation.value.id) if hasattr(annotation.value, 'id') else "Any"
        else:
            return "Any"
