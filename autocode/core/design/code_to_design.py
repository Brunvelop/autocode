"""Code to Design transformer.

This module provides functionality to analyze Python code and generate
modular Markdown files with Mermaid diagrams.
"""

import ast
from pathlib import Path
from typing import List, Dict, Any, Tuple

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

    def _build_module_tree(self, structures: Dict[str, Dict]) -> Dict[str, Any]:
        """Build a hierarchical tree structure from flat module data.
        
        Args:
            structures: Extracted code structures organized by directory
            
        Returns:
            Hierarchical tree structure with aggregated metrics
        """
        tree = {}
        
        # First pass: Create the tree structure
        for module_dir, module_info in structures["modules"].items():
            if module_dir == ".":
                continue
                
            # Split path into parts
            parts = module_dir.replace('\\', '/').split('/')
            
            # Navigate/create tree structure
            current_level = tree
            path_so_far = []
            
            for part in parts:
                path_so_far.append(part)
                full_path = '/'.join(path_so_far)
                
                if part not in current_level:
                    current_level[part] = {
                        "name": part,
                        "full_path": full_path,
                        "original_path": module_dir,
                        "children": {},
                        "classes": [],
                        "metrics": {"classes": 0, "loc": 0, "files": 0},
                        "is_leaf": False
                    }
                
                current_level = current_level[part]["children"]
        
        # Second pass: Add data to leaf nodes only
        for module_dir, module_info in structures["modules"].items():
            if module_dir == ".":
                continue
                
            # Navigate to the correct node
            leaf_parts = module_dir.replace('\\', '/').split('/')
            leaf_node = tree
            for i, part in enumerate(leaf_parts):
                if i == len(leaf_parts) - 1:
                    # Last part - this is our target node
                    leaf_node = leaf_node[part]
                else:
                    # Navigate to children
                    leaf_node = leaf_node[part]["children"]
            
            # Only set as leaf if it has no children (which means it's a terminal node)
            if not leaf_node["children"]:
                leaf_node["is_leaf"] = True
                leaf_node["classes"] = module_info["classes"]
                leaf_node["metrics"] = {
                    "classes": len(module_info["classes"]),
                    "loc": sum(cls["loc"] for cls in module_info["classes"]),
                    "files": len(module_info["files"])
                }
                leaf_node["original_path"] = module_dir
        
        # Calculate aggregate metrics for parent nodes
        self._calculate_aggregate_metrics(tree)
        
        return tree
    
    def _calculate_aggregate_metrics(self, tree: Dict[str, Any]) -> None:
        """Calculate aggregate metrics for all nodes in the tree.
        
        Args:
            tree: Module tree structure
        """
        for node_name, node in tree.items():
            if node["is_leaf"]:
                continue
                
            # Recursively calculate for children first
            if node["children"]:
                self._calculate_aggregate_metrics(node["children"])
                
                # Sum metrics from all children
                total_classes = 0
                total_loc = 0
                total_files = 0
                
                for child_name, child in node["children"].items():
                    total_classes += child["metrics"]["classes"]
                    total_loc += child["metrics"]["loc"]
                    total_files += child["metrics"]["files"]
                
                node["metrics"] = {
                    "classes": total_classes,
                    "loc": total_loc,
                    "files": total_files
                }

    def generate_visual_index(self, structures: Dict[str, Dict]) -> str:
        """Generate a visual index using Mermaid diagram with hierarchical structure.
        
        Args:
            structures: Extracted code structures organized by directory
            
        Returns:
            Markdown content with visual index
        """
        # Build hierarchical tree
        module_tree = self._build_module_tree(structures)
        
        # Calculate total metrics
        total_classes = sum(node["metrics"]["classes"] for node in module_tree.values())
        total_loc = sum(node["metrics"]["loc"] for node in module_tree.values())
        total_modules = self._count_modules(module_tree)
        
        # Generate visual index content
        content = f"# 🏗️ Autocode Architecture Overview\n\n"
        content += f"**Project Summary:** {total_classes} Classes | {total_loc:,} LOC | {total_modules} Modules\n\n"
        
        # Generate Mermaid diagram
        content += "```mermaid\n"
        content += "graph TD\n"
        content += '    subgraph "🏗️ Autocode Project"\n'
        
        # Module icons mapping
        module_icons = {
            "autocode": "🏗️ Autocode",
            "core": "⚙️ Core",
            "api": "🌐 API",
            "orchestration": "🔄 Orchestration", 
            "web": "🖥️ Web",
            "prompts": "📝 Prompts",
            "ai": "🤖 AI",
            "design": "🎨 Design",
            "docs": "📚 Docs",
            "git": "🔧 Git",
            "test": "🧪 Test"
        }
        
        node_counter = 0
        
        # Generate hierarchical subgraphs with node information
        mermaid_content, node_counter, nodes_info = self._generate_mermaid_subgraphs(module_tree, module_icons, node_counter, 2)
        content += mermaid_content
        
        content += "    end\n\n"
        
        # Add module relationships
        content += "    %% Module relationships\n"
        content += "    API --> Core\n"
        content += "    Core --> Orchestration\n"
        content += "    Orchestration --> Web\n"
        content += "\n"
        
        # Add interactive click declarations
        click_content = self._generate_click_declarations(nodes_info)
        content += click_content
        content += "\n"
        
        content += "```\n\n"
        
        # Add module details summary
        content += "## Module Details\n\n"
        details_content = self._generate_module_details(module_tree)
        content += details_content
        
        return content
    
    def _count_modules(self, tree: Dict[str, Any]) -> int:
        """Count total modules in the tree.
        
        Args:
            tree: Module tree structure
            
        Returns:
            Total number of modules
        """
        count = 0
        for node in tree.values():
            count += 1
            if node["children"]:
                count += self._count_modules(node["children"])
        return count
    
    def _generate_mermaid_subgraphs(self, tree: Dict[str, Any], 
                                   module_icons: Dict[str, str], node_counter: int, 
                                   indent_level: int) -> Tuple[str, int, List[Dict[str, Any]]]:
        """Generate Mermaid subgraphs recursively.
        
        Args:
            tree: Module tree structure
            module_icons: Icon mapping for modules
            node_counter: Current node counter
            indent_level: Indentation level
            
        Returns:
            Tuple of (generated content, updated node counter, node info list)
        """
        content = ""
        indent = "    " * indent_level
        nodes_info = []
        
        for node_name, node in tree.items():
            icon_name = module_icons.get(node_name, f"📁 {node_name}")
            metrics = node["metrics"]
            
            if metrics["classes"] == 0:
                continue
                
            subgraph_title = f"{icon_name} [{metrics['classes']} Classes | {metrics['loc']} LOC]"
            content += f'{indent}subgraph "{subgraph_title}"\n'
            
            if node["is_leaf"]:
                # Add class nodes for leaf modules
                for cls in node["classes"]:
                    node_id = f"C{node_counter}"
                    node_counter += 1
                    content += f'{indent}    {node_id}["{cls["name"]}<br/>LOC: {cls["loc"]}"]\n'
                    
                    # Store node info for link generation
                    nodes_info.append({
                        "node_id": node_id,
                        "class_name": cls["name"],
                        "file_name": cls["file_name"],
                        "module_path": node["original_path"],
                        "loc": cls["loc"],
                        "num_methods": cls["num_methods"]
                    })
            else:
                # Recursively add children
                child_content, node_counter, child_nodes = self._generate_mermaid_subgraphs(
                    node["children"], module_icons, node_counter, indent_level + 1
                )
                content += child_content
                nodes_info.extend(child_nodes)
            
            content += f'{indent}end\n'
        
        return content, node_counter, nodes_info
    
    def _generate_click_declarations(self, nodes_info: List[Dict[str, Any]]) -> str:
        """Generate Mermaid click declarations for interactive nodes.
        
        Args:
            nodes_info: List of node information dictionaries
            
        Returns:
            Generated click declarations content
        """
        content = "    %% Interactive links to class documentation\n"
        
        for node_info in nodes_info:
            node_id = node_info["node_id"]
            class_name = node_info["class_name"]
            file_name = node_info["file_name"]
            module_path = node_info["module_path"].replace('\\', '/')
            loc = node_info["loc"]
            num_methods = node_info["num_methods"]
            
            # Generate link path
            link_path = f"{module_path}/{file_name}_class.md#{class_name.lower()}"
            
            # Generate tooltip with metrics
            tooltip = f"{class_name} - LOC: {loc} | Methods: {num_methods}"
            
            # Add click declaration
            content += f'    click {node_id} "{link_path}" "{tooltip}"\n'
        
        return content
    
    def _generate_navigation_hub(self, tree: Dict[str, Any], 
                               module_icons: Dict[str, str], level: int = 0) -> str:
        """Generate navigation hub recursively.
        
        Args:
            tree: Module tree structure
            module_icons: Icon mapping for modules
            level: Current hierarchy level
            
        Returns:
            Generated navigation content
        """
        content = ""
        
        for node_name, node in tree.items():
            icon_name = module_icons.get(node_name, f"📁 {node_name}")
            metrics = node["metrics"]
            
            if metrics["classes"] == 0:
                continue
                
            # Generate header with appropriate level
            header_level = "#" * (3 + level)
            content += f"{header_level} {icon_name} {node_name.title()} ({metrics['classes']} Classes | {metrics['loc']} LOC)\n\n"
            
            if node["is_leaf"]:
                # Add class links for leaf modules
                sorted_classes = sorted(node["classes"], key=lambda x: x["name"])
                
                for cls in sorted_classes:
                    # Generate link path
                    normalized_path = node["original_path"].replace('\\', '/')
                    link_path = f"{normalized_path}/{cls['file_name']}_class.md#{cls['name'].lower()}"
                    
                    # Create markdown link with metrics
                    content += f"- [{cls['name']}]({link_path}) - LOC: {cls['loc']} | Methods: {cls['num_methods']}\n"
                
                content += "\n"
            else:
                # Recursively add children
                child_content = self._generate_navigation_hub(node["children"], module_icons, level + 1)
                content += child_content
        
        return content
    
    def _generate_module_details(self, tree: Dict[str, Any]) -> str:
        """Generate module details section.
        
        Args:
            tree: Module tree structure
            
        Returns:
            Generated module details content
        """
        content = ""
        
        def add_module_details(nodes: Dict[str, Any], prefix: str = ""):
            nonlocal content
            for node_name, node in nodes.items():
                metrics = node["metrics"]
                
                if metrics["classes"] == 0:
                    continue
                    
                full_name = f"{prefix}{node_name.title()}" if prefix else node_name.title()
                content += f"### {full_name}\n"
                content += f"- **Classes:** {metrics['classes']}\n"
                content += f"- **Lines of Code:** {metrics['loc']:,}\n"
                content += f"- **Average LOC per Class:** {metrics['loc'] // metrics['classes'] if metrics['classes'] > 0 else 0}\n"
                
                if not node["is_leaf"]:
                    content += f"- **Submodules:** {len(node['children'])}\n"
                
                content += "\n"
                
                # Recursively add children
                if node["children"]:
                    add_module_details(node["children"], f"{full_name} > ")
        
        add_module_details(tree)
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
