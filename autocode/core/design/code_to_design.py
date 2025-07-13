"""Code to Design transformer.

This module provides functionality to analyze code and generate
modular Markdown files with diagrams using a modular architecture.
"""

import os
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import logging

from .analyzers import AnalyzerFactory
from .diagrams import GeneratorFactory, MarkdownExporter
from .utils import GeneralUtils

logger = logging.getLogger(__name__)


class CodeToDesign:
    """Transformer to generate design diagrams from code."""

    def __init__(self, project_root: Path, config: Dict[str, Any] = None):
        """Initialize the transformer.
        
        Args:
            project_root: Project root directory
            config: Configuration dictionary
        """
        self.project_root = project_root
        self.config = self._normalize_config(config)
        self.output_base = self.project_root / self.config["output_dir"]
        
        # Initialize factories
        self.analyzer_factory = AnalyzerFactory(project_root, config)
        self.generator_factory = GeneratorFactory(config)
        
        # Initialize utilities
        self.utils = GeneralUtils(config)
        
        # Initialize analyzers and generators based on config
        self.analyzers = self._initialize_analyzers()
        self.generators = self._initialize_generators()
    
    def _normalize_config(self, config: Dict[str, Any] = None) -> Dict[str, Any]:
        """Normalize configuration with defaults.
        
        Args:
            config: Input configuration
            
        Returns:
            Normalized configuration dictionary
        """
        default_config = {
            "output_dir": "design",
            "languages": ["python"],
            "diagrams": ["classes"],
            "auto_detect": True,
            "include_metrics": True,
            "generate_index": True,
            "module_icons": {},  # User can provide custom icons
            "file_patterns": {},  # User can provide custom patterns
            "exclude_patterns": ["__pycache__", "*.pyc", ".git", "node_modules"],
            "max_depth": 10,
            "output_formats": ["markdown"]
        }
        
        if config:
            # Handle legacy 'language' parameter
            if "language" in config and "languages" not in config:
                config["languages"] = [config["language"]]
            
            # Ensure languages is a list
            if "languages" in config and isinstance(config["languages"], str):
                config["languages"] = [config["languages"]]
            
            # Merge with defaults
            for key, value in config.items():
                default_config[key] = value
        
        return default_config
    
    def _initialize_analyzers(self) -> Dict[str, Any]:
        """Initialize analyzers based on configuration.
        
        Returns:
            Dictionary of initialized analyzers
        """
        analyzers = {}
        
        if self.config.get("auto_detect", True):
            # Auto-detect analyzers for the project
            logger.info("Auto-detecting analyzers for project...")
            # We'll auto-detect per directory when needed
        else:
            # Use specified languages
            languages = self.config.get("languages", ["python"])
            analyzers = self.analyzer_factory.get_analyzers_for_languages(languages)
        
        return analyzers
    
    def _initialize_generators(self) -> Dict[str, Any]:
        """Initialize generators based on configuration.
        
        Returns:
            Dictionary of initialized generators
        """
        diagram_types = self.config.get("diagrams", ["classes"])
        return self.generator_factory.auto_detect_generators(diagram_types)

    def generate_visual_index(self, analysis_results: Dict[str, Any], 
                             project_name: Optional[str] = None) -> str:
        """Generate a visual index using hierarchical structure.
        
        Args:
            analysis_results: Combined analysis results from all analyzers
            project_name: Name of the project (auto-detected if None)
            
        Returns:
            Markdown content with visual index
        """
        # Build hierarchical tree using the new utilities
        module_tree = self.utils.build_hierarchical_tree(analysis_results)
        
        # Generate summary statistics
        summary_stats = self.utils.generate_summary_stats(module_tree)
        
        # Get project name from config or auto-detect
        if not project_name:
            project_name = self.config.get("project_name", self.project_root.name.title())
        
        # Generate visual index content
        content = f"# 🏗️ {project_name} Architecture Overview\n\n"
        
        # Add summary with generic metrics
        metrics = summary_stats["metrics"]
        content += f"**Project Summary:** "
        content += f"{metrics['total_items']} Items | "
        content += f"{metrics['total_loc']:,} LOC | "
        content += f"{summary_stats['total_nodes']} Modules\n\n"
        
        # Add breakdown by type
        if metrics['classes'] > 0:
            content += f"- **Classes:** {metrics['classes']}\n"
        if metrics['functions'] > 0:
            content += f"- **Functions:** {metrics['functions']}\n"
        if metrics['components'] > 0:
            content += f"- **Components:** {metrics['components']}\n"
        content += "\n"
        
        # Generate Mermaid diagram using mermaid generator if available
        if "mermaid" in self.generators:
            content += "```mermaid\n"
            content += self._generate_architecture_diagram(module_tree, project_name)
            content += "\n```\n\n"
        
        # Add module details
        content += "## Module Details\n\n"
        content += self._generate_module_details_section(module_tree)
        
        return content
    
    def _generate_architecture_diagram(self, module_tree: Dict[str, Any], 
                                     project_name: str) -> str:
        """Generate Mermaid architecture diagram.
        
        Args:
            module_tree: Hierarchical module tree
            project_name: Name of the project
            
        Returns:
            Mermaid diagram content
        """
        diagram = "graph TD\n"
        diagram += f'    subgraph "{project_name}"\n'
        
        # Get module icons
        module_icons = self.utils.get_module_icons()
        
        node_counter = 0
        
        # Generate nodes for each module
        for module_name, module_data in module_tree.items():
            metrics = module_data.get("metrics", {})
            if metrics.get("total_items", 0) == 0:
                continue
            
            # Get icon for module
            icon = module_icons.get(module_name.lower(), f"📁 {module_name.title()}")
            
            # Create node with metrics
            node_id = f"M{node_counter}"
            node_counter += 1
            
            diagram += f'        {node_id}["{icon}\\n{metrics["total_items"]} items"]\n'
            
            # Add children if any
            if module_data.get("children"):
                child_diagram, node_counter = self._generate_child_nodes(
                    module_data["children"], node_id, node_counter, module_icons, 2
                )
                diagram += child_diagram
        
        diagram += "    end\n"
        return diagram
    
    def _generate_child_nodes(self, children: Dict[str, Any], parent_id: str, 
                            node_counter: int, module_icons: Dict[str, str], 
                            indent_level: int) -> Tuple[str, int]:
        """Generate child nodes recursively.
        
        Args:
            children: Child modules
            parent_id: Parent node ID
            node_counter: Current node counter
            module_icons: Module icon mapping
            indent_level: Indentation level
            
        Returns:
            Tuple of (diagram content, updated node counter)
        """
        diagram = ""
        indent = "    " * indent_level
        
        for child_name, child_data in children.items():
            metrics = child_data.get("metrics", {})
            if metrics.get("total_items", 0) == 0:
                continue
            
            # Get icon for child
            icon = module_icons.get(child_name.lower(), f"📁 {child_name.title()}")
            
            # Create child node
            child_id = f"M{node_counter}"
            node_counter += 1
            
            diagram += f'{indent}{child_id}["{icon}\\n{metrics["total_items"]} items"]\n'
            diagram += f'{indent}{parent_id} --> {child_id}\n'
            
            # Add grandchildren if any
            if child_data.get("children"):
                grandchild_diagram, node_counter = self._generate_child_nodes(
                    child_data["children"], child_id, node_counter, module_icons, indent_level + 1
                )
                diagram += grandchild_diagram
        
        return diagram, node_counter
    
    def _generate_module_details_section(self, module_tree: Dict[str, Any]) -> str:
        """Generate module details section.
        
        Args:
            module_tree: Hierarchical module tree
            
        Returns:
            Module details content
        """
        content = ""
        
        def add_module_details(nodes: Dict[str, Any], prefix: str = "", level: int = 3):
            nonlocal content
            for node_name, node in nodes.items():
                metrics = node.get("metrics", {})
                
                if metrics.get("total_items", 0) == 0:
                    continue
                
                header_level = "#" * level
                full_name = f"{prefix}{node_name.title()}" if prefix else node_name.title()
                
                content += f"{header_level} {full_name}\n"
                content += f"- **Total Items:** {metrics['total_items']}\n"
                content += f"- **Files:** {metrics['total_files']}\n"
                content += f"- **Lines of Code:** {metrics['total_loc']:,}\n"
                
                if metrics['classes'] > 0:
                    content += f"- **Classes:** {metrics['classes']}\n"
                if metrics['functions'] > 0:
                    content += f"- **Functions:** {metrics['functions']}\n"
                if metrics['components'] > 0:
                    content += f"- **Components:** {metrics['components']}\n"
                
                if not node.get("is_leaf") and node.get("children"):
                    content += f"- **Submodules:** {len(node['children'])}\n"
                
                content += "\n"
                
                # Recursively add children
                if node.get("children"):
                    add_module_details(node["children"], f"{full_name} > ", level + 1)
        
        add_module_details(module_tree)
        return content

    def generate_markdown_files(self, analysis_results: Dict[str, Any], 
                               output_dir: Optional[Path] = None) -> List[Path]:
        """Generate modular Markdown files maintaining directory structure.
        
        Args:
            analysis_results: Combined analysis results from all analyzers
            output_dir: Custom output directory (defaults to self.output_base)
            
        Returns:
            List of generated file paths
        """
        generated_dir = output_dir if output_dir is not None else self.output_base
        generated_dir.mkdir(parents=True, exist_ok=True)
        
        generated_files = []
        
        # Generate visual index if configured
        if self.config.get("generate_index", True):
            index_path = generated_dir / "_index.md"
            index_content = self.generate_visual_index(analysis_results)
            
            with open(index_path, "w", encoding="utf-8") as f:
                f.write(index_content)
            generated_files.append(index_path)
        
        # Generate files for each module
        modules = analysis_results.get("modules", {})
        for module_dir, module_info in modules.items():
            if module_dir == ".":
                target_dir = generated_dir
            else:
                target_dir = generated_dir / module_dir
                target_dir.mkdir(parents=True, exist_ok=True)
            
            # Generate module-level documentation
            module_files = self._generate_module_files(module_dir, module_info, target_dir)
            generated_files.extend(module_files)
        
        return generated_files
    
    def _generate_module_files(self, module_dir: str, module_info: Dict[str, Any], 
                              target_dir: Path) -> List[Path]:
        """Generate files for a specific module.
        
        Args:
            module_dir: Module directory path
            module_info: Module information
            target_dir: Target output directory
            
        Returns:
            List of generated file paths
        """
        generated_files = []
        
        # Generate _module.md for directories (except root)
        if module_dir != ".":
            module_md_path = target_dir / "_module.md"
            module_content = self._generate_module_overview(module_dir, module_info)
            
            with open(module_md_path, "w", encoding="utf-8") as f:
                f.write(module_content)
            generated_files.append(module_md_path)
        
        # Generate individual item files
        if "analysis_data" in module_info:
            for analysis_data in module_info["analysis_data"]:
                item_files = self._generate_analysis_files(analysis_data, target_dir)
                generated_files.extend(item_files)
        
        return generated_files
    
    def _generate_module_overview(self, module_dir: str, module_info: Dict[str, Any]) -> str:
        """Generate module overview content.
        
        Args:
            module_dir: Module directory path
            module_info: Module information
            
        Returns:
            Module overview markdown content
        """
        content = f"# Module: {module_dir}\n\n"
        
        # Add summary
        if "summary" in module_info:
            summary = module_info["summary"]
            content += f"**Summary:** {summary.get('total_files', 0)} files, "
            content += f"{summary.get('total_items', 0)} items\n\n"
        
        # Add items by file
        if "analysis_data" in module_info:
            content += "## Items in this module\n\n"
            
            for analysis_data in module_info["analysis_data"]:
                file_path = analysis_data.get("file_path", "")
                file_name = Path(file_path).stem if file_path else "unknown"
                
                # Add classes
                classes = analysis_data.get("classes", [])
                if classes:
                    content += f"### {file_name} - Classes\n"
                    for cls in classes:
                        content += f"- [{cls['name']}]({file_name}_items.md#{cls['name'].lower()})\n"
                    content += "\n"
                
                # Add functions
                functions = analysis_data.get("functions", [])
                if functions:
                    content += f"### {file_name} - Functions\n"
                    for func in functions:
                        content += f"- [{func['name']}]({file_name}_items.md#{func['name'].lower()})\n"
                    content += "\n"
                
                # Add components
                components = analysis_data.get("components", [])
                if components:
                    content += f"### {file_name} - Components\n"
                    for comp in components:
                        content += f"- [{comp['name']}]({file_name}_items.md#{comp['name'].lower()})\n"
                    content += "\n"
        
        return content
    
    def _generate_analysis_files(self, analysis_data: Dict[str, Any], 
                                target_dir: Path) -> List[Path]:
        """Generate files for analysis data.
        
        Args:
            analysis_data: Analysis data from an analyzer
            target_dir: Target output directory
            
        Returns:
            List of generated file paths
        """
        generated_files = []
        
        file_path = analysis_data.get("file_path", "")
        file_name = Path(file_path).stem if file_path else "unknown"
        
        # Only generate if there are items to document
        has_items = (analysis_data.get("classes") or 
                    analysis_data.get("functions") or 
                    analysis_data.get("components"))
        
        if has_items:
            item_file_path = target_dir / f"{file_name}_items.md"
            content = self._generate_items_content(analysis_data)
            
            with open(item_file_path, "w", encoding="utf-8") as f:
                f.write(content)
            generated_files.append(item_file_path)
        
        return generated_files
    
    def _generate_items_content(self, analysis_data: Dict[str, Any]) -> str:
        """Generate content for items in a file.
        
        Args:
            analysis_data: Analysis data from an analyzer
            
        Returns:
            Items documentation content
        """
        file_path = analysis_data.get("file_path", "")
        file_type = analysis_data.get("file_type", "unknown")
        
        content = f"# Items from {Path(file_path).name}\n\n"
        content += f"**Source:** `{file_path}`  \n"
        content += f"**Type:** {file_type}\n\n"
        
        # Add metrics if available
        if "metrics" in analysis_data:
            metrics = analysis_data["metrics"]
            content += "**Metrics:**\n"
            for key, value in metrics.items():
                if isinstance(value, (int, float)):
                    content += f"- {key.replace('_', ' ').title()}: {value:,}\n"
            content += "\n"
        
        # Generate content for each item type
        for item_type in ["classes", "functions", "components"]:
            items = analysis_data.get(item_type, [])
            if items:
                content += f"## {item_type.title()}\n\n"
                
                for item in items:
                    item_content = self._generate_item_content(item, item_type)
                    content += item_content
        
        return content
    
    def _generate_item_content(self, item: Dict[str, Any], item_type: str) -> str:
        """Generate content for a specific item.
        
        Args:
            item: Item data
            item_type: Type of item ('classes', 'functions', 'components')
            
        Returns:
            Item documentation content
        """
        name = item.get("name", "Unknown")
        content = f"### {name}\n\n"
        
        # Add basic info
        if "line_number" in item:
            content += f"**Line:** {item['line_number']}  \n"
        
        if "loc" in item:
            content += f"**LOC:** {item['loc']}  \n"
        
        # Add type-specific content
        if item_type == "classes" and "mermaid" in self.generators:
            content += "\n```mermaid\n"
            try:
                content += self.generators["mermaid"].generate_class_diagram(item)
            except Exception:
                content += f"classDiagram\n    class {name} {{\n    }}"
            content += "\n```\n\n"
        
        elif item_type == "functions":
            params = item.get("parameters", [])
            if params:
                param_str = ", ".join(p.get("name", str(p)) for p in params)
                content += f"**Parameters:** {param_str}  \n"
            
            if "return_type" in item:
                content += f"**Returns:** {item['return_type']}  \n"
            content += "\n"
        
        elif item_type == "components":
            if "type" in item:
                content += f"**Type:** {item['type']}  \n"
            
            methods = item.get("methods", [])
            if methods:
                content += f"**Methods:** {len(methods)}  \n"
            content += "\n"
        
        return content

    def generate_design(self, directory: str, 
                       patterns: Optional[List[str]] = None) -> Dict[str, Any]:
        """Main method to generate design from code.
        
        Args:
            directory: Directory to analyze
            patterns: File patterns (if None, auto-detects based on available files)
            
        Returns:
            Result dictionary with generated files and status
        """
        try:
            logger.info(f"Starting design generation for directory: {directory}")
            
            # Auto-detect analyzers for the directory
            if self.config.get("auto_detect", True):
                analyzers = self.analyzer_factory.auto_detect_analyzers(directory)
            else:
                analyzers = self.analyzers
            
            if not analyzers:
                return {
                    "status": "error",
                    "error": f"No suitable analyzers found for directory: {directory}",
                    "generated_files": [],
                    "analysis_results": {}
                }
            
            # Run analysis with all available analyzers
            combined_results = {"modules": {}}
            analyzer_results = {}
            
            for analyzer_name, analyzer in analyzers.items():
                logger.info(f"Running {analyzer_name} analyzer...")
                
                try:
                    result = analyzer.analyze_directory(directory, patterns)
                    
                    if result.is_successful():
                        analyzer_results[analyzer_name] = result
                        # Merge results
                        self._merge_analysis_results(combined_results, result.data)
                        logger.info(f"✅ {analyzer_name} analysis completed successfully")
                    else:
                        logger.warning(f"⚠️ {analyzer_name} analysis failed: {result.errors}")
                
                except Exception as e:
                    logger.error(f"❌ {analyzer_name} analysis error: {str(e)}")
            
            if not analyzer_results:
                return {
                    "status": "error", 
                    "error": "All analyzers failed",
                    "generated_files": [],
                    "analysis_results": {}
                }
            
            # Generate markdown files
            logger.info("Generating markdown files...")
            
            # Calculate output directory based on analyzed directory
            # Remove trailing slash and get directory name
            directory_name = directory.rstrip("/").rstrip("\\")
            if directory_name and directory_name != ".":
                output_dir = self.output_base / directory_name
            else:
                output_dir = self.output_base
            
            generated_files = self.generate_markdown_files(combined_results, output_dir)
            
            # Calculate metrics
            total_items = sum(
                sum(
                    len(analysis.get("classes", [])) + 
                    len(analysis.get("functions", [])) + 
                    len(analysis.get("components", []))
                    for analysis in module_info.get("analysis_data", [])
                )
                for module_info in combined_results["modules"].values()
            )
            
            return {
                "status": "success" if generated_files else "warning",
                "generated_files": [str(f.relative_to(self.project_root)) for f in generated_files],
                "analysis_results": combined_results,
                "analyzer_results": {name: result.data for name, result in analyzer_results.items()},
                "metrics": {
                    "total_items": total_items,
                    "total_files": len(generated_files),
                    "analyzers_used": list(analyzer_results.keys())
                },
                "message": f"Generated {len(generated_files)} design files for {directory}"
            }
            
        except Exception as e:
            logger.error(f"Error generating design for {directory}: {str(e)}")
            return {
                "status": "error",
                "error": str(e),
                "generated_files": [],
                "analysis_results": {}
            }
    
    def _merge_analysis_results(self, combined_results: Dict[str, Any], 
                               new_results: Dict[str, Any]) -> None:
        """Merge analysis results from different analyzers.
        
        Args:
            combined_results: Combined results to merge into
            new_results: New results to merge
        """
        new_modules = new_results.get("modules", {})
        
        for module_path, module_info in new_modules.items():
            if module_path not in combined_results["modules"]:
                combined_results["modules"][module_path] = {
                    "files": {},
                    "analysis_data": [],
                    "summary": {"total_files": 0, "total_items": 0}
                }
            
            # Merge files info
            combined_results["modules"][module_path]["files"].update(
                module_info.get("files", {})
            )
            
            # Add analysis data from the new analyzer
            if "analysis_data" in module_info:
                combined_results["modules"][module_path]["analysis_data"].extend(
                    module_info["analysis_data"]
                )
            
            # Update summary
            combined_summary = combined_results["modules"][module_path]["summary"]
            new_summary = module_info.get("summary", {})
            
            combined_summary["total_files"] = len(
                combined_results["modules"][module_path]["files"]
            )
            combined_summary["total_items"] += new_summary.get("total_items", 0)
    
    def get_analyzer_info(self) -> Dict[str, Any]:
        """Get information about available analyzers.
        
        Returns:
            Dictionary with analyzer information
        """
        return self.analyzer_factory.get_analyzer_info() if hasattr(self.analyzer_factory, 'get_analyzer_info') else {
            "available_analyzers": self.analyzer_factory.get_available_analyzers(),
            "supported_extensions": self.analyzer_factory.get_supported_extensions()
        }
    
    def get_generator_info(self) -> Dict[str, Any]:
        """Get information about available generators.
        
        Returns:
            Dictionary with generator information
        """
        return self.generator_factory.get_generator_info()
    
    def get_system_info(self) -> Dict[str, Any]:
        """Get comprehensive system information.
        
        Returns:
            Dictionary with system information
        """
        return {
            "project_root": str(self.project_root),
            "config": self.config,
            "analyzers": self.get_analyzer_info(),
            "generators": self.get_generator_info(),
            "utilities": {
                "class": self.utils.__class__.__name__,
                "methods": [method for method in dir(self.utils) if not method.startswith('_')]
            }
        }
