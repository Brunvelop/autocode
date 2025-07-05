"""
Documentation indexer for generating structured documentation indices.
"""

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

from ..api.models import DocIndexConfig


class DocIndexer:
    """Generates structured indices of modular documentation."""
    
    def __init__(self, project_root: Path, config: DocIndexConfig, output_override: Optional[str] = None):
        """Initialize documentation indexer.
        
        Args:
            project_root: Path to the project root directory
            config: Documentation index configuration
            output_override: Optional override for output path (from CLI)
        """
        self.project_root = project_root
        self.config = config
        self.output_path = self._resolve_output_path(output_override)
    
    def _resolve_output_path(self, output_override: Optional[str]) -> Path:
        """Resolve the output path based on priority: CLI > config > default.
        
        Args:
            output_override: Optional override from CLI argument
            
        Returns:
            Resolved output path
        """
        if output_override:
            # CLI argument has highest priority
            return Path(output_override)
        
        # Use config value (already has default)
        return self.project_root / self.config.output_path
    
    def extract_purpose(self, content: str) -> str:
        """Extract purpose from documentation content.
        
        Args:
            content: File content to analyze
            
        Returns:
            Extracted purpose or default message if not found
        """
        try:
            # Flexible regex to match both variations:
            # "## 🎯 Propósito del Módulo" and "## 🎯 Propósito"
            pattern = r"## 🎯 Propósito(?:\s+del\s+Módulo)?\s*\n\s*(.+)"
            match = re.search(pattern, content, re.IGNORECASE | re.MULTILINE)
            
            if match:
                purpose = match.group(1).strip()
                # Clean up the purpose text
                # Remove any markdown formatting and extra spaces
                purpose = re.sub(r'\*\*([^*]+)\*\*', r'\1', purpose)  # Remove bold
                purpose = re.sub(r'\*([^*]+)\*', r'\1', purpose)      # Remove italic
                purpose = re.sub(r'`([^`]+)`', r'\1', purpose)        # Remove code
                purpose = ' '.join(purpose.split())                   # Normalize whitespace
                return purpose
            
            return "No purpose found"
            
        except Exception as e:
            return f"Error reading file: {str(e)}"
    
    def _read_file_content(self, file_path: Path) -> str:
        """Safely read file content.
        
        Args:
            file_path: Path to the file to read
            
        Returns:
            File content or error message
        """
        try:
            return file_path.read_text(encoding='utf-8')
        except Exception as e:
            return f"Error reading file: {str(e)}"
    
    def _get_file_last_modified(self, file_path: Path) -> Optional[str]:
        """Get file last modified timestamp.
        
        Args:
            file_path: Path to the file
            
        Returns:
            ISO formatted timestamp or None if error
        """
        try:
            timestamp = file_path.stat().st_mtime
            return datetime.fromtimestamp(timestamp).isoformat()
        except Exception:
            return None
    
    def _scan_directory_structure(self, docs_dir: Path) -> Dict[str, Any]:
        """Recursively scan documentation directory structure.
        
        Args:
            docs_dir: Path to documentation directory
            
        Returns:
            Nested dictionary representing the structure
        """
        if not docs_dir.exists() or not docs_dir.is_dir():
            return {}
        
        result = {}
        
        # Get all items in this directory
        try:
            items = list(docs_dir.iterdir())
        except PermissionError:
            return result
        
        # Separate directories and files
        directories = [item for item in items if item.is_dir() and not item.name.startswith('.')]
        files = [item for item in items if item.is_file() and item.suffix == '.md']
        
        # Check for index file (_index.md)
        index_file = docs_dir / '_index.md'
        if index_file.exists():
            content = self._read_file_content(index_file)
            purpose = self.extract_purpose(content)
            result.update({
                "type": "root" if docs_dir.name == "docs" else "index",
                "index_file": str(index_file.relative_to(self.project_root)),
                "purpose": purpose,
                "last_modified": self._get_file_last_modified(index_file)
            })
        
        # Check for module file (_module.md)
        module_file = docs_dir / '_module.md'
        if module_file.exists():
            content = self._read_file_content(module_file)
            purpose = self.extract_purpose(content)
            result.update({
                "type": "module",
                "module_file": str(module_file.relative_to(self.project_root)),
                "purpose": purpose,
                "last_modified": self._get_file_last_modified(module_file)
            })
        
        # Process subdirectories
        if directories:
            subdirs = {}
            for subdir in sorted(directories):
                subdir_structure = self._scan_directory_structure(subdir)
                if subdir_structure:  # Only include if not empty
                    subdirs[str(subdir.relative_to(self.project_root)) + "/"] = subdir_structure
            
            if subdirs:
                result["subdirectories"] = subdirs
        
        # Process individual documentation files (excluding _index.md and _module.md)
        doc_files = [f for f in files if f.name not in ['_index.md', '_module.md']]
        if doc_files:
            files_dict = {}
            for doc_file in sorted(doc_files):
                content = self._read_file_content(doc_file)
                purpose = self.extract_purpose(content)
                files_dict[str(doc_file.relative_to(self.project_root))] = {
                    "type": "file_doc",
                    "purpose": purpose,
                    "last_modified": self._get_file_last_modified(doc_file)
                }
            
            if files_dict:
                result["files"] = files_dict
        
        return result
    
    def _calculate_statistics(self, structure: Dict[str, Any]) -> Dict[str, int]:
        """Calculate statistics from the documentation structure.
        
        Args:
            structure: Documentation structure dictionary
            
        Returns:
            Statistics dictionary
        """
        stats = {
            "total_files": 0,
            "total_modules": 0,
            "total_directories": 0,
            "total_purposes_found": 0
        }
        
        def count_recursive(node: Dict[str, Any]):
            # Count current node
            if "type" in node:
                if node["type"] in ["module", "root", "index"]:
                    stats["total_modules"] += 1
                if node["type"] == "file_doc":
                    stats["total_files"] += 1
                
                # Count if purpose was found
                purpose = node.get("purpose", "")
                if purpose and purpose != "No purpose found" and not purpose.startswith("Error"):
                    stats["total_purposes_found"] += 1
            
            # Count subdirectories
            if "subdirectories" in node:
                stats["total_directories"] += len(node["subdirectories"])
                for subdir in node["subdirectories"].values():
                    count_recursive(subdir)
            
            # Count files
            if "files" in node:
                stats["total_files"] += len(node["files"])
                for file_info in node["files"].values():
                    purpose = file_info.get("purpose", "")
                    if purpose and purpose != "No purpose found" and not purpose.startswith("Error"):
                        stats["total_purposes_found"] += 1
        
        count_recursive(structure)
        return stats
    
    def _get_project_name(self) -> str:
        """Extract project name from main documentation.
        
        Returns:
            Project name or default
        """
        main_index = self.project_root / "docs" / "_index.md"
        if main_index.exists():
            try:
                content = self._read_file_content(main_index)
                # Look for title in first few lines
                lines = content.split('\n')[:10]
                for line in lines:
                    if line.startswith('# '):
                        # Extract title, remove markdown formatting
                        title = line[2:].strip()
                        title = re.sub(r' - Technical Documentation$', '', title)
                        return title
                    if 'Vidi' in line and ('motor' in line.lower() or 'engine' in line.lower()):
                        return "Vidi - Unified Inference Engine"
            except Exception:
                pass
        
        return "Project Documentation"
    
    def generate_index(self) -> Path:
        """Generate complete documentation index.
        
        Returns:
            Path to the generated index file
        """
        docs_dir = self.project_root / "docs"
        
        if not docs_dir.exists():
            raise FileNotFoundError(f"Documentation directory not found: {docs_dir}")
        
        # Scan the documentation structure
        structure = self._scan_directory_structure(docs_dir)
        
        # Calculate statistics
        stats = self._calculate_statistics(structure)
        
        # Get project name
        project_name = self._get_project_name()
        
        # Build complete index
        index_data = {
            "timestamp": datetime.now().isoformat(),
            "project_name": project_name,
            "config": {
                "output_path": str(self.output_path.relative_to(self.project_root)),
                "generated_by": "autocode-doc-indexer",
                "version": "1.0.0"
            },
            "documentation_stats": stats,
            "structure": {
                str(docs_dir.relative_to(self.project_root)) + "/": structure
            }
        }
        
        # Ensure output directory exists
        self.output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Save to file
        with open(self.output_path, 'w', encoding='utf-8') as f:
            json.dump(index_data, f, indent=2, ensure_ascii=False)
        
        return self.output_path
    
    def get_index_status(self) -> Dict[str, Any]:
        """Get status of the documentation index.
        
        Returns:
            Status information about the index
        """
        if not self.output_path.exists():
            return {
                "exists": False,
                "last_generated": None,
                "size_bytes": 0,
                "stats": {}
            }
        
        try:
            stat = self.output_path.stat()
            last_modified = datetime.fromtimestamp(stat.st_mtime).isoformat()
            
            # Try to read stats from existing index
            with open(self.output_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                stats = data.get("documentation_stats", {})
            
            return {
                "exists": True,
                "last_generated": last_modified,
                "size_bytes": stat.st_size,
                "stats": stats
            }
            
        except Exception as e:
            return {
                "exists": True,
                "last_generated": None,
                "size_bytes": 0,
                "stats": {},
                "error": str(e)
            }
