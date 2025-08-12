"""
I/O operations for documentation checking module.
These functions handle filesystem interactions without business logic.
"""

import os
from pathlib import Path
from datetime import datetime
from typing import List, Set, Optional
from fnmatch import fnmatch

from .types import CodeFile, CodeDirectory, DocFile, DocType, FileInfo
from ..config.types import DocsConfig


def get_file_info(file_path: Path) -> FileInfo:
    """Get basic file information from filesystem."""
    stat = file_path.stat()
    return FileInfo(
        path=file_path,
        last_modified=datetime.fromtimestamp(stat.st_mtime),
        size_bytes=stat.st_size
    )


def should_exclude_path(path: Path, exclude_patterns: List[str]) -> bool:
    """Check if a path should be excluded based on patterns."""
    path_str = str(path)
    name = path.name
    
    for pattern in exclude_patterns:
        # Directory pattern (ends with /)
        if pattern.endswith('/'):
            if pattern.rstrip('/') in path_str:
                return True
        # Glob pattern (starts with *)
        elif pattern.startswith('*'):
            if fnmatch(name, pattern):
                return True
        # Exact filename match
        elif name == pattern:
            return True
    
    return False


def discover_code_files(
    project_root: Path,
    directories: List[str],
    file_extensions: List[str],
    exclude_patterns: List[str]
) -> List[CodeFile]:
    """Discover all code files in the specified directories."""
    code_files = []
    
    for directory in directories:
        dir_path = project_root / directory.rstrip('/')
        
        if not dir_path.exists() or not dir_path.is_dir():
            continue
        
        # Recursively find files with specified extensions
        for extension in file_extensions:
            for file_path in dir_path.rglob(f"*{extension}"):
                # Skip if file should be excluded
                if should_exclude_path(file_path, exclude_patterns):
                    continue
                
                # Create CodeFile instance
                try:
                    file_info = get_file_info(file_path)
                    code_file = CodeFile(
                        path=file_info.path,
                        last_modified=file_info.last_modified,
                        size_bytes=file_info.size_bytes,
                        extension=extension
                    )
                    code_files.append(code_file)
                except (OSError, PermissionError):
                    # Skip files that can't be read
                    continue
    
    return code_files


def discover_code_directories(
    project_root: Path,
    code_files: List[CodeFile]
) -> List[CodeDirectory]:
    """Group code files into directories."""
    # Group files by directory
    dir_files_map = {}
    
    for code_file in code_files:
        # Get all parent directories up to project root
        current_dir = code_file.path.parent
        
        while current_dir != project_root.parent and current_dir != project_root:
            if current_dir not in dir_files_map:
                dir_files_map[current_dir] = []
            dir_files_map[current_dir].append(code_file)
            current_dir = current_dir.parent
    
    # Create CodeDirectory instances
    code_directories = []
    for dir_path, files in dir_files_map.items():
        # Find the most recent modification time
        latest_time = max(f.last_modified for f in files)
        
        code_dir = CodeDirectory(
            path=dir_path,
            file_count=len(files),
            last_modified=latest_time,
            code_files=files
        )
        code_directories.append(code_dir)
    
    return code_directories


def discover_doc_files(docs_root: Path) -> List[DocFile]:
    """Discover all documentation files in the docs directory."""
    if not docs_root.exists() or not docs_root.is_dir():
        return []
    
    doc_files = []
    
    for md_file in docs_root.rglob("*.md"):
        try:
            file_info = get_file_info(md_file)
            
            # Determine doc type based on filename
            if md_file.name == "_index.md":
                doc_type = DocType.INDEX
            elif md_file.name == "_module.md":
                doc_type = DocType.MODULE
            else:
                doc_type = DocType.FILE
            
            doc_file = DocFile(
                path=file_info.path,
                last_modified=file_info.last_modified,
                size_bytes=file_info.size_bytes,
                doc_type=doc_type
            )
            doc_files.append(doc_file)
            
        except (OSError, PermissionError):
            # Skip files that can't be read
            continue
    
    return doc_files


def find_orphaned_docs(
    doc_files: List[DocFile],
    project_root: Path,
    docs_root: Path,
    code_files: List[CodeFile],
    code_directories: List[CodeDirectory]
) -> List[DocFile]:
    """Find documentation files that don't have corresponding code."""
    orphaned = []
    
    # Create sets for quick lookup
    code_file_paths = {f.path for f in code_files}
    code_dir_paths = {d.path for d in code_directories}
    
    for doc_file in doc_files:
        if doc_file.doc_type == DocType.INDEX:
            # Index docs always have the project root as reference
            continue
        
        elif doc_file.doc_type == DocType.MODULE:
            # Check if corresponding directory exists and has code
            mapped_dir = map_module_doc_to_directory(doc_file.path, project_root, docs_root)
            if mapped_dir not in code_dir_paths:
                orphaned.append(doc_file)
        
        else:  # FILE doc
            # Check if corresponding code file exists
            mapped_files = map_file_doc_to_code_files(
                doc_file.path,
                project_root,
                docs_root,
                [".py", ".js", ".html", ".css", ".ts", ".jsx", ".tsx"]  # All possible extensions
            )
            if not any(f in code_file_paths for f in mapped_files):
                orphaned.append(doc_file)
    
    return orphaned


def map_code_file_to_doc_path(
    code_file: CodeFile,
    project_root: Path,
    docs_root: Path
) -> Path:
    """Map a code file to its corresponding documentation path."""
    # Convert autocode/doc_checker.py -> docs/autocode/doc_checker.md
    relative_path = code_file.path.relative_to(project_root)
    doc_path = docs_root / relative_path.with_suffix('.md')
    return doc_path


def map_directory_to_module_doc_path(
    directory: CodeDirectory,
    project_root: Path,
    docs_root: Path
) -> Path:
    """Map a code directory to its corresponding _module.md path."""
    # Convert autocode/ -> docs/autocode/_module.md
    relative_path = directory.path.relative_to(project_root)
    doc_path = docs_root / relative_path / "_module.md"
    return doc_path


def map_file_doc_to_code_files(
    doc_path: Path,
    project_root: Path,
    docs_root: Path,
    extensions: List[str]
) -> List[Path]:
    """Map a documentation file to possible code file paths."""
    # Convert docs/autocode/doc_checker.md -> [autocode/doc_checker.py, .js, etc.]
    relative_doc = doc_path.relative_to(docs_root)
    base_path = project_root / relative_doc.with_suffix('')
    
    possible_paths = []
    for extension in extensions:
        possible_paths.append(base_path.with_suffix(extension))
    
    return possible_paths


def map_module_doc_to_directory(
    doc_path: Path,
    project_root: Path,
    docs_root: Path
) -> Path:
    """Map a _module.md file to its corresponding directory."""
    # Convert docs/autocode/_module.md -> autocode/
    relative_doc = doc_path.relative_to(docs_root)
    # Remove _module.md to get directory path
    directory_path = project_root / relative_doc.parent
    return directory_path


def get_index_doc_path(docs_root: Path) -> Path:
    """Get the path to the main _index.md file."""
    return docs_root / "_index.md"


def file_exists(path: Path) -> bool:
    """Check if a file exists."""
    return path.exists() and path.is_file()


def directory_exists(path: Path) -> bool:
    """Check if a directory exists."""
    return path.exists() and path.is_dir()
