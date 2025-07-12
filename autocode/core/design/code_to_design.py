"""Code to Design transformer.

This module provides functionality to analyze code and generate
modular Markdown files with diagrams using a modular architecture.
"""

import os
from pathlib import Path
from typing import List, Dict, Any

from .analyzers import PythonAnalyzer, JavaScriptAnalyzer
from .generators import MermaidGenerator, ComponentTreeGenerator
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
            "languages": ["python"],
            "diagrams": ["classes"]
        }
        self.output_base = self.project_root / self.config["output_dir"]
        
        # Initialize available analyzers and generators
        self.analyzers = {}
        self.generators = {}
        
        # Support for multiple languages
        languages = self.config.get("languages", [self.config.get("language", "python")])
        if isinstance(languages, str):
            languages = [languages]
            
        # Initialize analyzers for supported languages
        if "python" in languages:
            self.analyzers["python"] = PythonAnalyzer(project_root, config)
        if any(lang in languages for lang in ["javascript", "html", "css"]):
            self.analyzers["web"] = JavaScriptAnalyzer(project_root, config)
        
        # Initialize generators for supported diagram types
        diagrams = self.config.get("diagrams", ["classes"])
        if "classes" in diagrams:
            self.generators["classes"] = MermaidGenerator(config)
        if "components" in diagrams:
            self.generators["components"] = ComponentTreeGenerator(config)
        
        # Fallback for backward compatibility
        if not self.analyzers:
            self.analyzers["python"] = PythonAnalyzer(project_root, config)
        if not self.generators:
            self.generators["classes"] = MermaidGenerator(config)

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
                        # Use the appropriate generator for class diagrams
                        if "classes" in self.generators:
                            file_content += self.generators["classes"].generate_class_diagram(cls)
                        else:
                            file_content += "classDiagram\n    class " + cls['name'] + " {\n    }"
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

    def generate_component_tree(self, directory: str = "autocode/web") -> Dict[str, Any]:
        """Generate component tree diagram for UI components.
        
        Args:
            directory: Directory to analyze for UI components
            
        Returns:
            Result dictionary with diagram and analysis data
        """
        # Initialize JavaScript analyzer and component tree generator
        js_analyzer = JavaScriptAnalyzer(self.project_root)
        tree_generator = ComponentTreeGenerator()
        
        # Analyze the directory for UI components
        analysis_data = js_analyzer.analyze_directory(directory)
        
        if "error" in analysis_data:
            return {
                "status": "error",
                "error": analysis_data["error"],
                "diagram": None,
                "summary": None
            }
        
        # Generate the component tree diagram
        diagram = tree_generator.generate_component_tree_diagram(analysis_data)
        summary = tree_generator.generate_component_summary(analysis_data)
        
        return {
            "status": "success",
            "diagram": diagram,
            "summary": summary,
            "analysis_data": analysis_data,
            "metrics": {
                "total_components": analysis_data.get("summary", {}).get("total_components", 0),
                "total_files": analysis_data.get("summary", {}).get("total_files", 0),
                "total_modules": analysis_data.get("summary", {}).get("total_modules", 0)
            }
        }

    def generate_design(self, directory: str, pattern: str = None) -> Dict[str, Any]:
        """Main method to generate design from code.
        
        Args:
            directory: Directory to analyze
            pattern: File pattern (if None, auto-detects based on available files)
            
        Returns:
            Result dictionary with generated files and status
        """
        generated_files = []
        all_structures = {"modules": {}}
        total_structure_count = 0
        
        # Auto-detect what types of files exist in the directory
        dir_path = self.project_root / directory
        if not dir_path.exists():
            return {
                "status": "error",
                "error": f"Directory not found: {directory}",
                "generated_files": [],
                "structure_count": 0
            }
        
        # Check for Python files
        python_files = list(dir_path.rglob("*.py"))
        web_files = list(dir_path.rglob("*.html")) + list(dir_path.rglob("*.js")) + list(dir_path.rglob("*.css"))
        
        # Generate Python class diagrams if Python files exist and analyzer available
        if python_files and "python" in self.analyzers and "classes" in self.generators:
            print(f"🐍 Analyzing Python files in {directory}...")
            try:
                python_pattern = pattern if pattern and "*.py" in pattern else "*.py"
                python_structures = self.analyzers["python"].analyze_directory(directory, python_pattern)
                
                # Generate markdown files for Python classes
                python_generated = self.generate_markdown_files(python_structures)
                generated_files.extend(python_generated)
                
                # Merge structures
                for module_dir, module_info in python_structures["modules"].items():
                    if module_dir not in all_structures["modules"]:
                        all_structures["modules"][module_dir] = {"files": {}, "classes": []}
                    all_structures["modules"][module_dir]["files"].update(module_info["files"])
                    all_structures["modules"][module_dir]["classes"].extend(module_info["classes"])
                
                total_structure_count += sum(len(module_info["classes"]) for module_info in python_structures["modules"].values())
                print(f"✅ Generated {len(python_generated)} Python design files")
                
            except Exception as e:
                print(f"⚠️  Warning: Python analysis failed: {e}")
        
        # Generate Web component diagrams if web files exist and analyzer available
        if web_files and "web" in self.analyzers and "components" in self.generators:
            print(f"🌐 Analyzing web files in {directory}...")
            try:
                # Generate component tree for web files
                web_analysis = self.analyzers["web"].analyze_directory(directory)
                
                if "error" not in web_analysis:
                    # Generate component tree diagram
                    diagram = self.generators["components"].generate_component_tree_diagram(web_analysis)
                    summary = self.generators["components"].generate_component_summary(web_analysis)
                    
                    # Create component tree markdown file
                    component_dir = self.output_base / directory.replace("/", os.sep if os.sep != "/" else "/")
                    component_dir.mkdir(parents=True, exist_ok=True)
                    component_file = component_dir / "component_tree.md"
                    
                    component_content = f"# Web Components - {directory}\n\n"
                    component_content += f"## Component Tree\n\n"
                    component_content += f"```mermaid\n{diagram}\n```\n\n"
                    component_content += f"## Summary\n\n{summary}\n"
                    
                    with open(component_file, "w", encoding="utf-8") as f:
                        f.write(component_content)
                    generated_files.append(component_file)
                    
                    total_structure_count += web_analysis.get("summary", {}).get("total_components", 0)
                    print(f"✅ Generated component tree for web files")
                else:
                    print(f"⚠️  Warning: Web analysis failed: {web_analysis['error']}")
                    
            except Exception as e:
                print(f"⚠️  Warning: Web analysis failed: {e}")
        
        # If no files were found for any analyzer
        if not python_files and not web_files:
            print(f"⚠️  No supported files found in {directory}")
        
        return {
            "status": "success" if generated_files else "warning",
            "generated_files": [str(f.relative_to(self.project_root)) for f in generated_files],
            "structure_count": total_structure_count,
            "message": f"Generated {len(generated_files)} design files for {directory}"
        }
