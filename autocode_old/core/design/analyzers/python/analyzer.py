"""Python code analyzer.

This module provides functionality to analyze Python code using AST parsing.
"""

import ast
from pathlib import Path
from typing import List, Dict, Any

from ..base_analyzer import BaseAnalyzer, AnalysisResult


class PythonAnalyzer(BaseAnalyzer):
    """Analyzer for Python code using AST parsing."""

    def get_supported_extensions(self) -> List[str]:
        """Get list of supported file extensions.
        
        Returns:
            List of supported Python file extensions
        """
        return ['.py', '.pyi']
    
    def analyze_file(self, file_path: Path) -> AnalysisResult:
        """Analyze a single Python file.
        
        Args:
            file_path: Path to the Python file to analyze
            
        Returns:
            Analysis result with extracted class and function information
        """
        if not self.can_analyze_file(file_path):
            return AnalysisResult(
                status="error",
                errors=[f"Unsupported file type: {file_path.suffix}"]
            )
        
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
                
            # Parse AST
            try:
                tree = ast.parse(content, filename=str(file_path))
            except SyntaxError as e:
                return AnalysisResult(
                    status="error",
                    errors=[f"Syntax error in {file_path}: {str(e)}"]
                )
            
            # Extract classes and functions
            classes = []
            functions = []
            imports = []
            
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    class_info = self._extract_class_info(node, file_path)
                    classes.append(class_info)
                elif isinstance(node, ast.FunctionDef) and node.col_offset == 0:
                    # Only top-level functions
                    function_info = self._extract_function_info(node)
                    functions.append(function_info)
                elif isinstance(node, (ast.Import, ast.ImportFrom)):
                    import_info = self._extract_import_info(node)
                    imports.append(import_info)
            
            # Calculate metrics
            total_loc = len(content.splitlines())
            
            return AnalysisResult(
                status="success",
                data={
                    "file_path": str(file_path),
                    "file_type": "python",
                    "classes": classes,
                    "functions": functions,
                    "imports": imports,
                    "metrics": {
                        "total_classes": len(classes),
                        "total_functions": len(functions),
                        "total_imports": len(imports),
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
    
    def _extract_class_info(self, node: ast.ClassDef, file_path: Path) -> Dict[str, Any]:
        """Extract detailed information from a class node.
        
        Args:
            node: AST ClassDef node
            file_path: Path to the file containing the class
            
        Returns:
            Dictionary with class information
        """
        # Extract methods with detailed information
        methods = []
        for item in node.body:
            if isinstance(item, ast.FunctionDef):
                method_info = self._extract_method_info(item)
                methods.append(method_info)
        
        # Extract class attributes from assignments
        attributes = []
        for item in node.body:
            if isinstance(item, ast.Assign):
                for target in item.targets:
                    if isinstance(target, ast.Name):
                        attr_info = self._extract_attribute_info(target, item)
                        attributes.append(attr_info)
        
        # Extract type-annotated attributes (important for Pydantic models)
        for item in node.body:
            if isinstance(item, ast.AnnAssign) and isinstance(item.target, ast.Name):
                attr_info = self._extract_annotated_attribute_info(item)
                attributes.append(attr_info)
        
        # Extract base classes
        bases = []
        for base in node.bases:
            if isinstance(base, ast.Name):
                bases.append(base.id)
            elif isinstance(base, ast.Attribute):
                bases.append(f"{base.value.id}.{base.attr}" if hasattr(base.value, 'id') else base.attr)
        
        # Extract decorators
        decorators = []
        for decorator in node.decorator_list:
            if isinstance(decorator, ast.Name):
                decorators.append(decorator.id)
            elif isinstance(decorator, ast.Attribute):
                decorators.append(decorator.attr)
        
        return {
            "name": node.name,
            "bases": bases,
            "decorators": decorators,
            "methods": methods,
            "attributes": attributes,
            "file": str(file_path),
            "file_name": file_path.stem,
            "loc": node.end_lineno - node.lineno + 1 if hasattr(node, 'end_lineno') else 0,
            "num_methods": len(methods),
            "num_attributes": len(attributes),
            "line_number": node.lineno
        }
    
    def _extract_function_info(self, node: ast.FunctionDef) -> Dict[str, Any]:
        """Extract information from a function node.
        
        Args:
            node: AST FunctionDef node
            
        Returns:
            Dictionary with function information
        """
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
            "parameters": params,
            "return_type": return_type,
            "decorators": decorators,
            "line_number": node.lineno,
            "loc": node.end_lineno - node.lineno + 1 if hasattr(node, 'end_lineno') else 0
        }
    
    def _extract_import_info(self, node: ast.stmt) -> Dict[str, Any]:
        """Extract import information.
        
        Args:
            node: AST Import or ImportFrom node
            
        Returns:
            Dictionary with import information
        """
        if isinstance(node, ast.Import):
            return {
                "type": "import",
                "modules": [alias.name for alias in node.names],
                "line_number": node.lineno
            }
        elif isinstance(node, ast.ImportFrom):
            return {
                "type": "from_import",
                "module": node.module,
                "names": [alias.name for alias in node.names],
                "level": node.level,
                "line_number": node.lineno
            }
        
        return {}

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

    def _extract_annotated_attribute_info(self, ann_assign_node: ast.AnnAssign) -> Dict[str, Any]:
        """Extract information from a type-annotated attribute (e.g., field: str = "default").
        
        Args:
            ann_assign_node: AST AnnAssign node
            
        Returns:
            Dictionary with attribute information
        """
        attr_name = ann_assign_node.target.id
        
        # Determine visibility
        visibility = "+" if not attr_name.startswith("_") else "-"
        
        # Extract type annotation
        attr_type = self._get_type_annotation(ann_assign_node.annotation)
        
        # Check if it has a default value
        has_default = ann_assign_node.value is not None
        default_value = None
        
        if has_default:
            if isinstance(ann_assign_node.value, ast.Constant):
                default_value = repr(ann_assign_node.value.value)
            elif isinstance(ann_assign_node.value, ast.Name):
                default_value = ann_assign_node.value.id
            elif isinstance(ann_assign_node.value, ast.Call):
                # Handle function calls like Field(default="value")
                if isinstance(ann_assign_node.value.func, ast.Name):
                    default_value = f"{ann_assign_node.value.func.id}(...)"
                elif isinstance(ann_assign_node.value.func, ast.Attribute):
                    default_value = f"{ann_assign_node.value.func.attr}(...)"
        
        return {
            "name": attr_name,
            "visibility": visibility,
            "type": attr_type,
            "has_default": has_default,
            "default_value": default_value
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
