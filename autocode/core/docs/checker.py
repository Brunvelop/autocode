"""
Pure business logic for documentation checking.
This module contains the core algorithms without I/O dependencies.
"""

from pathlib import Path
from datetime import datetime
from typing import List, Optional, Dict, Set

from .types import (
    CodeFile, 
    CodeDirectory, 
    DocFile, 
    DocStatus, 
    DocCheckResult, 
    DocCheckSummary,
    StatusType, 
    DocType
)
from .io import (
    discover_code_files,
    discover_code_directories,
    discover_doc_files,
    find_orphaned_docs,
    map_code_file_to_doc_path,
    map_directory_to_module_doc_path,
    get_index_doc_path,
    file_exists
)
from ..config.types import DocsConfig


def determine_doc_status(
    code_last_modified: datetime,
    doc_file: Optional[DocFile]
) -> StatusType:
    """
    Determine the status of documentation relative to code.
    Pure function with no side effects.
    """
    if doc_file is None:
        return StatusType.MISSING
    
    if code_last_modified > doc_file.last_modified:
        return StatusType.OUTDATED
    
    return StatusType.UP_TO_DATE


def check_file_documentation(
    code_file: CodeFile,
    doc_files_map: Dict[Path, DocFile],
    project_root: Path,
    docs_root: Path
) -> DocStatus:
    """Check documentation status for a single code file."""
    doc_path = map_code_file_to_doc_path(code_file, project_root, docs_root)
    doc_file = doc_files_map.get(doc_path)
    
    status = determine_doc_status(code_file.last_modified, doc_file)
    
    return DocStatus(
        code=code_file,
        doc=doc_file,
        status=status,
        doc_type=DocType.FILE
    )


def check_module_documentation(
    code_directory: CodeDirectory,
    doc_files_map: Dict[Path, DocFile],
    project_root: Path,
    docs_root: Path
) -> DocStatus:
    """Check documentation status for a code directory (module)."""
    doc_path = map_directory_to_module_doc_path(code_directory, project_root, docs_root)
    doc_file = doc_files_map.get(doc_path)
    
    status = determine_doc_status(code_directory.last_modified, doc_file)
    
    return DocStatus(
        code=code_directory,
        doc=doc_file,
        status=status,
        doc_type=DocType.MODULE
    )


def check_index_documentation(
    project_root: Path,
    docs_root: Path,
    doc_files_map: Dict[Path, DocFile],
    code_files: List[CodeFile]
) -> DocStatus:
    """Check documentation status for the main index file."""
    index_doc_path = get_index_doc_path(docs_root)
    doc_file = doc_files_map.get(index_doc_path)
    
    # For index docs, use the most recent code file modification time
    if code_files:
        latest_code_time = max(f.last_modified for f in code_files)
    else:
        latest_code_time = datetime.now()
    
    status = determine_doc_status(latest_code_time, doc_file)
    
    return DocStatus(
        code=project_root,  # Index docs reference the whole project
        doc=doc_file,
        status=status,
        doc_type=DocType.INDEX
    )


def create_orphaned_doc_statuses(orphaned_docs: List[DocFile]) -> List[DocStatus]:
    """Create DocStatus objects for orphaned documentation."""
    orphaned_statuses = []
    
    for doc_file in orphaned_docs:
        # For orphaned docs, we don't have the actual code reference
        # so we create a dummy path based on the doc file
        if doc_file.doc_type == DocType.MODULE:
            # For module docs, create a directory path
            code_ref = doc_file.path.parent / "dummy_module"
        else:
            # For file docs, create a file path
            code_ref = doc_file.path.with_suffix('.dummy')
        
        status = DocStatus(
            code=code_ref,
            doc=doc_file,
            status=StatusType.ORPHANED,
            doc_type=doc_file.doc_type
        )
        orphaned_statuses.append(status)
    
    return orphaned_statuses


def analyze_documentation_status(
    code_files: List[CodeFile],
    code_directories: List[CodeDirectory],
    doc_files: List[DocFile],
    orphaned_docs: List[DocFile],
    project_root: Path,
    docs_root: Path
) -> List[DocStatus]:
    """
    Analyze documentation status for all code entities.
    Pure function that orchestrates the checking logic.
    """
    # Create lookup map for doc files
    doc_files_map = {doc.path: doc for doc in doc_files}
    
    all_statuses = []
    
    # 1. Check index documentation
    index_status = check_index_documentation(
        project_root, docs_root, doc_files_map, code_files
    )
    all_statuses.append(index_status)
    
    # 2. Check module documentation for each directory
    for code_directory in code_directories:
        module_status = check_module_documentation(
            code_directory, doc_files_map, project_root, docs_root
        )
        all_statuses.append(module_status)
    
    # 3. Check file documentation for each code file
    for code_file in code_files:
        file_status = check_file_documentation(
            code_file, doc_files_map, project_root, docs_root
        )
        all_statuses.append(file_status)
    
    # 4. Add orphaned documentation statuses
    orphaned_statuses = create_orphaned_doc_statuses(orphaned_docs)
    all_statuses.extend(orphaned_statuses)
    
    return all_statuses


def check_documentation(
    project_root: Path,
    config: DocsConfig
) -> DocCheckResult:
    """
    Main function to check documentation status.
    Coordinates I/O operations and pure business logic.
    """
    # Setup paths
    docs_root = project_root / config.docs_directory
    
    # 1. Discover all code files
    code_files = discover_code_files(
        project_root=project_root,
        directories=config.directories,
        file_extensions=config.file_extensions,
        exclude_patterns=config.exclude
    )
    
    # 2. Group code files into directories
    code_directories = discover_code_directories(project_root, code_files)
    
    # 3. Discover all documentation files
    doc_files = discover_doc_files(docs_root)
    
    # 4. Find orphaned documentation
    orphaned_docs = find_orphaned_docs(
        doc_files=doc_files,
        project_root=project_root,
        docs_root=docs_root,
        code_files=code_files,
        code_directories=code_directories
    )
    
    # 5. Analyze documentation status (pure logic)
    statuses = analyze_documentation_status(
        code_files=code_files,
        code_directories=code_directories,
        doc_files=doc_files,
        orphaned_docs=orphaned_docs,
        project_root=project_root,
        docs_root=docs_root
    )
    
    # 6. Create summary
    summary = DocCheckResult.create_summary(statuses)
    
    # 7. Build final result
    result = DocCheckResult(
        statuses=statuses,
        summary=summary,
        timestamp=datetime.now(),
        project_root=project_root,
        docs_root=docs_root
    )
    
    return result


def get_issues_only(result: DocCheckResult) -> List[DocStatus]:
    """
    Filter documentation check result to show only issues.
    Convenience function for CLI/API integration.
    """
    return result.issues


def count_issues_by_type(statuses: List[DocStatus]) -> Dict[str, int]:
    """
    Count issues by type for summary reporting.
    Pure function for statistics.
    """
    counts = {
        'outdated': 0,
        'missing': 0,
        'orphaned': 0,
        'up_to_date': 0
    }
    
    for status in statuses:
        if status.is_outdated:
            counts['outdated'] += 1
        elif status.is_missing:
            counts['missing'] += 1
        elif status.is_orphaned:
            counts['orphaned'] += 1
        else:
            counts['up_to_date'] += 1
    
    return counts


def filter_by_doc_type(statuses: List[DocStatus], doc_type: DocType) -> List[DocStatus]:
    """Filter statuses by documentation type."""
    return [s for s in statuses if s.doc_type == doc_type]


def filter_by_status_type(statuses: List[DocStatus], status_type: StatusType) -> List[DocStatus]:
    """Filter statuses by status type."""
    return [s for s in statuses if s.status == status_type]


def has_documentation_issues(result: DocCheckResult) -> bool:
    """
    Check if there are any documentation issues.
    Simple predicate function.
    """
    return result.has_issues
