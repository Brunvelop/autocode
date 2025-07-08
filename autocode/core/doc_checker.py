"""
Documentation checker for Vidi project.
Compares modification dates between code files and their documentation.
Follows the modular documentation structure from W_1_generate_modular_docs.md
"""

from pathlib import Path
from typing import List, NamedTuple, Set, Optional
import os


class DocStatus(NamedTuple):
    """Status of a code-documentation pair."""
    code_file: Path
    doc_file: Path
    status: str  # 'outdated', 'missing', 'up_to_date', 'orphaned'
    doc_type: str  # 'file', 'module', 'index'


class DocChecker:
    """Checks documentation status against code files following modular structure."""
    
    def __init__(self, project_root: Path = None, config: Optional['DocsConfig'] = None):
        """Initialize DocChecker with project root directory and optional configuration."""
        self.project_root = project_root or Path.cwd()
        self.docs_dir = self.project_root / "docs"
        self.config = config
    
    def find_code_directories(self) -> List[Path]:
        """Auto-discover directories containing Python code (excluding __init__.py only dirs)."""
        code_dirs = []
        
        # Scan directories in project root
        for item in self.project_root.iterdir():
            if item.is_dir() and not item.name.startswith('.') and item.name != 'docs':
                # Check if directory contains .py files (excluding __init__.py)
                python_files = [f for f in item.rglob("*.py") if f.name != "__init__.py"]
                if python_files:
                    code_dirs.append(item)
        
        return code_dirs
    
    def find_configured_directories(self) -> List[Path]:
        """Find directories based on configuration."""
        if not self.config or not self.config.directories:
            return self.find_code_directories()
        
        code_dirs = []
        for dir_pattern in self.config.directories:
            # Remove trailing slash if present
            dir_pattern = dir_pattern.rstrip('/')
            dir_path = self.project_root / dir_pattern
            
            if dir_path.exists() and dir_path.is_dir():
                # Check if directory contains code files with configured extensions
                code_files = self.get_code_files_in_directory(dir_path)
                if code_files:
                    code_dirs.append(dir_path)
        
        return code_dirs
    
    def should_exclude_file(self, file_path: Path) -> bool:
        """Check if a file should be excluded based on configuration."""
        if not self.config or not self.config.exclude:
            return False
        
        for pattern in self.config.exclude:
            if pattern.endswith('/'):
                # Directory pattern
                if pattern.rstrip('/') in str(file_path):
                    return True
            elif pattern.startswith('*'):
                # Extension pattern
                if file_path.name.endswith(pattern[1:]):
                    return True
            else:
                # Exact filename
                if file_path.name == pattern:
                    return True
        
        return False
    
    def get_supported_extensions(self) -> List[str]:
        """Get list of supported file extensions."""
        if self.config and self.config.file_extensions:
            return self.config.file_extensions
        # Default to Python files for backward compatibility
        return [".py"]
    
    def get_code_files_in_directory(self, directory: Path) -> List[Path]:
        """Get all code files in a directory based on configured extensions."""
        code_files = []
        extensions = self.get_supported_extensions()
        
        for extension in extensions:
            for code_file in directory.rglob(f"*{extension}"):
                # Skip __init__.py files only for Python
                if extension == ".py" and code_file.name == "__init__.py":
                    continue
                # Skip excluded files
                if self.should_exclude_file(code_file):
                    continue
                code_files.append(code_file)
        
        return code_files
    
    def get_all_code_files(self) -> List[Path]:
        """Get all code files from all code directories based on configured extensions."""
        code_files = []
        code_dirs = self.find_configured_directories()
        
        for code_dir in code_dirs:
            code_files.extend(self.get_code_files_in_directory(code_dir))
        
        return code_files
    
    def get_all_python_files(self) -> List[Path]:
        """Get all Python files from all code directories, excluding __init__.py."""
        # Keep for backward compatibility
        return [f for f in self.get_all_code_files() if f.suffix == ".py"]
    
    def get_all_code_directories_with_subdirs(self) -> Set[Path]:
        """Get all directories that contain code files (including subdirectories)."""
        all_dirs = set()
        code_dirs = self.find_configured_directories()
        
        for code_dir in code_dirs:
            # Add the main directory
            all_dirs.add(code_dir)
            
            # Add all subdirectories that contain code files
            code_files = self.get_code_files_in_directory(code_dir)
            for code_file in code_files:
                # Add all parent directories up to the main code directory
                current_dir = code_file.parent
                while current_dir != code_dir.parent and current_dir != self.project_root:
                    all_dirs.add(current_dir)
                    current_dir = current_dir.parent
        
        return all_dirs
    
    def find_all_doc_files(self) -> List[Path]:
        """Find all documentation files in the docs directory."""
        if not self.docs_dir.exists():
            return []
        
        doc_files = []
        for doc_file in self.docs_dir.rglob("*.md"):
            # Skip _index.md as it doesn't map to specific code
            if doc_file.name != "_index.md":
                doc_files.append(doc_file)
        
        return doc_files
    
    def map_doc_to_code_file(self, doc_file: Path) -> Path:
        """Map a documentation file back to its corresponding code file."""
        # Convert docs/autocode/cli.md -> autocode/cli.* (try all supported extensions)
        relative_doc = doc_file.relative_to(self.docs_dir)
        base_path = self.project_root / relative_doc.with_suffix('')
        
        # Try to find the actual code file with supported extensions
        extensions = self.get_supported_extensions()
        for extension in extensions:
            code_path = base_path.with_suffix(extension)
            if code_path.exists():
                return code_path
        
        # If no file found, default to .py for backward compatibility
        return base_path.with_suffix('.py')
    
    def map_module_doc_to_directory(self, doc_file: Path) -> Path:
        """Map a _module.md file back to its corresponding code directory."""
        # Convert docs/autocode/_module.md -> autocode/
        relative_doc = doc_file.relative_to(self.docs_dir)
        # Remove _module.md to get the directory path
        code_path = self.project_root / relative_doc.parent
        return code_path
    
    def find_orphaned_docs(self) -> List[DocStatus]:
        """Find documentation files that no longer have corresponding code."""
        orphaned = []
        doc_files = self.find_all_doc_files()
        
        for doc_file in doc_files:
            if doc_file.name == "_module.md":
                # This is a module documentation file
                code_path = self.map_module_doc_to_directory(doc_file)
                if not code_path.exists() or not code_path.is_dir():
                    orphaned.append(DocStatus(code_path, doc_file, 'orphaned', 'module'))
                else:
                    # Check if directory actually contains code files
                    code_files = self.get_code_files_in_directory(code_path)
                    if not code_files:
                        orphaned.append(DocStatus(code_path, doc_file, 'orphaned', 'module'))
            else:
                # This is a file documentation - need to check all possible extensions
                code_path = self.map_doc_to_code_file(doc_file)
                if not code_path.exists():
                    orphaned.append(DocStatus(code_path, doc_file, 'orphaned', 'file'))
        
        return orphaned
    
    def map_code_file_to_doc(self, code_file: Path) -> Path:
        """Map a code file to its corresponding documentation file."""
        # Convert autocode/doc_checker.py -> docs/autocode/doc_checker.md
        # Convert autocode/web/static/app.js -> docs/autocode/web/static/app.md
        relative_path = code_file.relative_to(self.project_root)
        doc_path = self.docs_dir / relative_path.with_suffix('.md')
        return doc_path
    
    def map_directory_to_module_doc(self, code_dir: Path) -> Path:
        """Map a code directory to its corresponding _module.md file."""
        # Convert autocode/ -> docs/autocode/_module.md
        relative_path = code_dir.relative_to(self.project_root)
        doc_path = self.docs_dir / relative_path / "_module.md"
        return doc_path
    
    def get_index_doc_path(self) -> Path:
        """Get the path to the main _index.md file."""
        return self.docs_dir / "_index.md"
    
    def is_doc_outdated(self, code_path: Path, doc_file: Path) -> str:
        """Check if documentation is outdated compared to code."""
        if not doc_file.exists():
            return 'missing'
        
        # For directories, check against the newest file in that directory
        if code_path.is_dir():
            newest_code_time = 0
            code_files = self.get_code_files_in_directory(code_path)
            for code_file in code_files:
                newest_code_time = max(newest_code_time, code_file.stat().st_mtime)
            
            if newest_code_time == 0:  # No code files found
                return 'up_to_date'
            
            doc_mtime = doc_file.stat().st_mtime
            if newest_code_time > doc_mtime:
                return 'outdated'
        else:
            # For files, compare directly
            code_mtime = code_path.stat().st_mtime
            doc_mtime = doc_file.stat().st_mtime
            if code_mtime > doc_mtime:
                return 'outdated'
        
        return 'up_to_date'
    
    def check_all_docs(self) -> List[DocStatus]:
        """Check documentation status for all code following modular structure."""
        results = []
        
        # 1. Check _index.md (main project documentation)
        index_doc = self.get_index_doc_path()
        # Use project root as reference for _index.md
        index_status = self.is_doc_outdated(self.project_root, index_doc)
        results.append(DocStatus(self.project_root, index_doc, index_status, 'index'))
        
        # 2. Check _module.md for each code directory
        code_directories = self.get_all_code_directories_with_subdirs()
        for code_dir in code_directories:
            module_doc = self.map_directory_to_module_doc(code_dir)
            status = self.is_doc_outdated(code_dir, module_doc)
            results.append(DocStatus(code_dir, module_doc, status, 'module'))
        
        # 3. Check individual file documentation
        code_files = self.get_all_code_files()
        for code_file in code_files:
            doc_file = self.map_code_file_to_doc(code_file)
            status = self.is_doc_outdated(code_file, doc_file)
            results.append(DocStatus(code_file, doc_file, status, 'file'))
        
        # 4. Check for orphaned documentation
        orphaned_docs = self.find_orphaned_docs()
        results.extend(orphaned_docs)
        
        return results
    
    def get_outdated_docs(self) -> List[DocStatus]:
        """Get only the documentation that needs attention (outdated, missing or orphaned)."""
        all_results = self.check_all_docs()
        return [result for result in all_results if result.status in ['outdated', 'missing', 'orphaned']]
    
    def format_results(self, results: List[DocStatus]) -> str:
        """Format results for display."""
        if not results:
            return "✅ All documentation is up to date!"
        
        # Separate by type and status
        outdated = [r for r in results if r.status == 'outdated']
        missing = [r for r in results if r.status == 'missing']
        orphaned = [r for r in results if r.status == 'orphaned']
        
        output = []
        
        if outdated:
            output.append("Documentación desactualizada:")
            for result in outdated:
                if result.doc_type == 'index':
                    output.append(f"- docs/_index.md (documentación principal del proyecto)")
                elif result.doc_type == 'module':
                    relative_code = result.code_file.relative_to(self.project_root)
                    relative_doc = result.doc_file.relative_to(self.project_root)
                    output.append(f"- {relative_code}/ → {relative_doc}")
                else:  # file
                    relative_code = result.code_file.relative_to(self.project_root)
                    relative_doc = result.doc_file.relative_to(self.project_root)
                    output.append(f"- {relative_code} → {relative_doc}")
        
        if missing:
            if outdated:
                output.append("")  # Empty line separator
            output.append("Archivos sin documentación:")
            for result in missing:
                if result.doc_type == 'index':
                    output.append(f"- docs/_index.md (documentación principal)")
                elif result.doc_type == 'module':
                    relative_code = result.code_file.relative_to(self.project_root)
                    output.append(f"- docs/{relative_code}/_module.md (documentación del módulo)")
                else:  # file
                    relative_code = result.code_file.relative_to(self.project_root)
                    output.append(f"- {relative_code}")
        
        if orphaned:
            if outdated or missing:
                output.append("")  # Empty line separator
            output.append("Documentación huérfana (código eliminado):")
            for result in orphaned:
                relative_doc = result.doc_file.relative_to(self.project_root)
                if result.doc_type == 'module':
                    relative_code = result.code_file.relative_to(self.project_root)
                    output.append(f"- {relative_doc} (directorio {relative_code}/ ya no existe)")
                else:  # file
                    relative_code = result.code_file.relative_to(self.project_root)
                    output.append(f"- {relative_doc} (archivo {relative_code} ya no existe)")
        
        output.append("")
        total = len(results)
        output.append(f"Total: {total} archivo{'s' if total != 1 else ''} requiere{'n' if total != 1 else ''} atención")
        
        return "\n".join(output)
