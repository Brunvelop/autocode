"""Code to Design transformer.

This module provides functionality to analyze code and generate
modular Markdown files with diagrams using a modular architecture.
"""

from pathlib import Path
from typing import List, Dict, Any

from .analyzers import PythonAnalyzer
from .generators import MermaidGenerator
from .utils import (
    build_module_tree, count_modules, generate_mermaid_subgraphs,
    generate_click_declarations, generate_module_details
)


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
        
        # Initialize analyzer and generator based on config
        if self.config["language"] == "python":
            self.analyzer = PythonAnalyzer(project_root, config)
        else:
            raise ValueError(f"Unsupported language: {self.config['language']}")
        
        if "classes" in self.config["diagrams"]:
            self.diagram_generator = MermaidGenerator(config)
        else:
            raise ValueError(f"No supported diagram types in: {self.config['diagrams']}")

    def generate_visual_index(self, structures: Dict[str, Dict]) -> str:
        """Generate a visual index using Mermaid diagram with hierarchical structure.
        
        Args:
            structures: Extracted code structures organized by directory
            
        Returns:
            Markdown content with visual index
        """
        # Build hierarchical tree
        module_tree = build_module_tree(structures)
        
        # Calculate total metrics
        total_classes = sum(node["metrics"]["classes"] for node in module_tree.values())
        total_loc = sum(node["metrics"]["loc"] for node in module_tree.values())
        total_modules = count_modules(module_tree)
        
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
        mermaid_content, node_counter, nodes_info = generate_mermaid_subgraphs(module_tree, module_icons, node_counter, 2)
        content += mermaid_content
        
        content += "    end\n\n"
        
        # Add module relationships
        content += "    %% Module relationships\n"
        content += "    API --> Core\n"
        content += "    Core --> Orchestration\n"
        content += "    Orchestration --> Web\n"
        content += "\n"
        
        # Add interactive click declarations
        click_content = generate_click_declarations(nodes_info)
        content += click_content
        content += "\n"
        
        content += "```\n\n"
        
        # Add module details summary
        content += "## Module Details\n\n"
        details_content = generate_module_details(module_tree)
        content += details_content
        
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
                        file_content += self.diagram_generator.generate_class_diagram(cls)
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
        # Use the analyzer to extract structures
        structures = self.analyzer.analyze_directory(directory, pattern)
        
        # Generate markdown files using the structures
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
