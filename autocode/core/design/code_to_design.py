"""Code to Design transformer.

This module provides functionality to analyze Python code and generate
modular Markdown files with Mermaid diagrams.
"""

import ast
from pathlib import Path
from typing import List, Dict, Any

class CodeToDesign:
    """Transformer to generate design diagrams from code."""

    def __init__(self, project_root: Path, config: Dict[str, Any] = None):
        """Initialize the transformer.
        
        Args:
            project_root: Project root directory
            config: Configuration dictionary
        """
        self.project_root = project_root
        self.config = config or {
            "output_dir": "design",
            "language": "python",
            "diagrams": ["classes"]
        }
        self.output_base = self.project_root / self.config["output_dir"]

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
                with open(file_path, "r", encoding="utf-8") as f:
                    tree = ast.parse(f.read(), filename=str(file_path))
                
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

    def generate_mermaid_class_diagram(self, class_info: Dict) -> str:
        """Generate Mermaid class diagram for a single class.
        
        Args:
            class_info: Class information dictionary
            
        Returns:
            Mermaid diagram string
        """
        diagram = "classDiagram\n"
        diagram += f"    class {class_info['name']} {{\n"
        
        # Add attributes with visibility and types
        for attr in class_info['attributes']:
            attr_line = f"        {attr['visibility']}{attr['name']}"
            if attr['type']:
                attr_line += f": {attr['type']}"
            diagram += attr_line + "\n"
        
        # Add methods with visibility, parameters, and return types
        for method in class_info['methods']:
            method_line = f"        {method['visibility']}{method['name']}("
            
            # Add parameters (skip 'self' for readability)
            params = [p for p in method['parameters'] if p['name'] != 'self']
            if params:
                param_strs = []
                for param in params:
                    param_str = param['name']
                    if param.get('type'):
                        param_str += f": {param['type']}"
                    param_strs.append(param_str)
                method_line += ", ".join(param_strs)
            
            method_line += ")"
            
            # Add return type
            if method['return_type']:
                method_line += f" -> {method['return_type']}"
            
            diagram += method_line + "\n"
        
        diagram += "    }\n"
        
        # Add inheritance relationships
        for base in class_info['bases']:
            diagram += f"    {base} <|-- {class_info['name']}\n"
        
        # Add decorators as stereotypes
        for method in class_info['methods']:
            if method['is_property']:
                diagram += f"    {class_info['name']} : <<property>> {method['name']}\n"
            elif method['is_static']:
                diagram += f"    {class_info['name']} : <<static>> {method['name']}\n"
            elif method['is_class']:
                diagram += f"    {class_info['name']} : <<class>> {method['name']}\n"
        
        return diagram

    def generate_visual_index(self, structures: Dict[str, Dict]) -> str:
        """Generate a visual index using Mermaid diagram with clickeable links.
        
        Args:
            structures: Extracted code structures organized by directory
            
        Returns:
            Markdown content with visual index
        """
        # Calculate aggregate metrics
        module_metrics = {}
        total_classes = 0
        total_loc = 0
        
        for module_dir, module_info in structures["modules"].items():
            if module_dir == ".":
                continue
                
            module_classes = len(module_info["classes"])
            module_loc = sum(cls["loc"] for cls in module_info["classes"])
            
            module_metrics[module_dir] = {
                "classes": module_classes,
                "loc": module_loc,
                "files": module_info["classes"]
            }
            
            total_classes += module_classes
            total_loc += module_loc
        
        # Generate visual index content
        content = f"# 🏗️ Autocode Architecture Overview\n\n"
        content += f"**Project Summary:** {total_classes} Classes | {total_loc:,} LOC | {len(module_metrics)} Modules\n\n"
        
        # Generate Mermaid diagram
        content += "```mermaid\n"
        content += "graph TD\n"
        content += '    subgraph "🏗️ Autocode Project"\n'
        
        # Module icons mapping
        module_icons = {
            "autocode\\core": "⚙️ Core",
            "autocode\\api": "🌐 API",
            "autocode\\orchestration": "🔄 Orchestration", 
            "autocode\\web": "🖥️ Web",
            "autocode\\prompts": "📝 Prompts"
        }
        
        node_counter = 0
        
        # Generate subgraphs for each module
        for module_dir, metrics in module_metrics.items():
            if metrics["classes"] == 0:
                continue
                
            icon_name = module_icons.get(module_dir, f"📁 {module_dir.split('\\')[-1]}")
            subgraph_title = f"{icon_name} [{metrics['classes']} Classes | {metrics['loc']} LOC]"
            
            content += f'        subgraph "{subgraph_title}"\n'
            
            # Add class nodes with integrated links
            for cls in metrics["files"]:
                node_id = f"C{node_counter}"
                node_counter += 1
                
                # Generate link path with proper formatting
                if module_dir == ".":
                    link_path = f"{cls['file_name']}_class.md#{cls['name'].lower()}"
                else:
                    # Normalize path separators and add anchor
                    normalized_path = module_dir.replace('\\', '/')
                    link_path = f"{normalized_path}/{cls['file_name']}_class.md#{cls['name'].lower()}"
                
                # Create node with pure visual representation (no embedded links)
                content += f'            {node_id}["{cls["name"]}<br/>LOC: {cls["loc"]}"]\n'
            
            content += "        end\n"
        
        content += "    end\n\n"
        
        # Add basic relationships (simplified)
        content += "    %% Module relationships\n"
        if "autocode\\api" in module_metrics and "autocode\\core" in module_metrics:
            content += "    API --> Core\n"
        if "autocode\\core" in module_metrics and "autocode\\orchestration" in module_metrics:
            content += "    Core --> Orchestration\n"
        if "autocode\\orchestration" in module_metrics and "autocode\\web" in module_metrics:
            content += "    Orchestration --> Web\n"
        
        content += "\n"
        
        content += "```\n\n"
        
        # Add Navigation Hub with functional markdown links
        content += "## 🧭 Navigation Hub\n\n"
        content += "**Direct links to all classes organized by module:**\n\n"
        
        for module_dir, metrics in module_metrics.items():
            if metrics["classes"] == 0:
                continue
                
            icon_name = module_icons.get(module_dir, f"📁 {module_dir.split('\\')[-1]}")
            module_name = module_dir.split("\\")[-1].title()
            
            content += f"### {icon_name} {module_name} ({metrics['classes']} Classes | {metrics['loc']} LOC)\n\n"
            
            # Sort classes by name for consistent ordering
            sorted_classes = sorted(metrics["files"], key=lambda x: x["name"])
            
            for cls in sorted_classes:
                # Generate link path with proper formatting
                if module_dir == ".":
                    link_path = f"{cls['file_name']}_class.md#{cls['name'].lower()}"
                else:
                    # Normalize path separators and add anchor
                    normalized_path = module_dir.replace('\\', '/')
                    link_path = f"{normalized_path}/{cls['file_name']}_class.md#{cls['name'].lower()}"
                
                # Create markdown link with metrics
                content += f"- [{cls['name']}]({link_path}) - LOC: {cls['loc']} | Methods: {cls['num_methods']}\n"
            
            content += "\n"
        
        # Add module details summary
        content += "## Module Details\n\n"
        for module_dir, metrics in module_metrics.items():
            if metrics["classes"] == 0:
                continue
                
            module_name = module_dir.split("\\")[-1].title()
            content += f"### {module_name}\n"
            content += f"- **Classes:** {metrics['classes']}\n"
            content += f"- **Lines of Code:** {metrics['loc']:,}\n"
            content += f"- **Average LOC per Class:** {metrics['loc'] // metrics['classes'] if metrics['classes'] > 0 else 0}\n\n"
        
        return content

    def generate_markdown_files(self, structures: Dict[str, Dict]) -> List[Path]:
        """Generate modular Markdown files maintaining directory structure.
        
        Args:
            structures: Extracted code structures organized by directory
            
        Returns:
            List of generated file paths
        """
        generated_dir = self.output_base
        generated_dir.mkdir(parents=True, exist_ok=True)
        
        generated_files = []
        
        # Generate files for each module
        for module_dir, module_info in structures["modules"].items():
            # Create module directory
            if module_dir == ".":
                target_dir = generated_dir
            else:
                target_dir = generated_dir / module_dir
                target_dir.mkdir(parents=True, exist_ok=True)
            
            # Generate _module.md for each directory (except root)
            if module_dir != ".":
                module_md_path = target_dir / "_module.md"
                module_content = f"# Module: {module_dir}\n\n"
                module_content += f"## Classes in this module\n\n"
                
                for file_name, file_info in module_info["files"].items():
                    if file_info["classes"]:
                        module_content += f"### {file_name}.py\n"
                        for cls in file_info["classes"]:
                            module_content += f"- [{cls['name']}]({file_name}_class.md#{cls['name'].lower()})\n"
                        module_content += "\n"
                
                with open(module_md_path, "w", encoding="utf-8") as f:
                    f.write(module_content)
                generated_files.append(module_md_path)
            
            # Generate individual class files per Python file
            for file_name, file_info in module_info["files"].items():
                if file_info["classes"]:  # Only generate if file has classes
                    file_md_path = target_dir / f"{file_name}_class.md"
                    
                    file_content = f"# Classes from {file_name}.py\n\n"
                    file_content += f"Source: `{file_info['path']}`\n\n"
                    
                    # Generate diagram for each class in the file
                    for cls in file_info["classes"]:
                        file_content += f"## {cls['name']}\n\n"
                        file_content += f"**Metrics:** LOC: {cls['loc']} | Methods: {cls['num_methods']}\n\n"
                        file_content += "```mermaid\n"
                        file_content += self.generate_mermaid_class_diagram(cls)
                        file_content += "\n```\n\n"
                    
                    with open(file_md_path, "w", encoding="utf-8") as f:
                        f.write(file_content)
                    generated_files.append(file_md_path)
        
        # Generate visual index
        index_path = generated_dir / "_index.md"
        index_content = self.generate_visual_index(structures)
        
        with open(index_path, "w", encoding="utf-8") as f:
            f.write(index_content)
        generated_files.append(index_path)
        
        return generated_files

    def generate_design(self, directory: str, pattern: str = "*.py") -> Dict[str, Any]:
        """Main method to generate design from code.
        
        Args:
            directory: Directory to analyze
            pattern: File pattern
            
        Returns:
            Result dictionary with generated files and status
        """
        structures = self.analyze_directory(directory, pattern)
        generated_files = self.generate_markdown_files(structures)
        
        # Count structures
        total_modules = len(structures["modules"])
        total_classes = sum(len(module_info["classes"]) for module_info in structures["modules"].values())
        total_files = sum(len(module_info["files"]) for module_info in structures["modules"].values())
        
        return {
            "status": "success",
            "generated_files": [str(f.relative_to(self.project_root)) for f in generated_files],
            "structure_count": {
                "modules": total_modules,
                "classes": total_classes,
                "files": total_files
            }
        }
