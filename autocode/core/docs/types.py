"""
Domain types for documentation checking module.
These types represent the core entities and value objects for the docs domain.
"""

from pydantic import BaseModel, Field, field_validator
from datetime import datetime
from pathlib import Path
from typing import List, Union, Optional
from enum import Enum


class DocType(str, Enum):
    """Type of documentation file."""
    INDEX = "index"
    MODULE = "module"
    FILE = "file"


class StatusType(str, Enum):
    """Status of documentation relative to code."""
    OUTDATED = "outdated"
    MISSING = "missing"
    UP_TO_DATE = "up_to_date"
    ORPHANED = "orphaned"


class FileInfo(BaseModel):
    """Base information about a file from filesystem."""
    model_config = {"frozen": True}
    
    path: Path
    last_modified: datetime
    size_bytes: int = Field(ge=0)
    
    @property
    def relative_path(self) -> Path:
        """Get relative path from project root when available."""
        return self.path


class CodeFile(FileInfo):
    """Represents a code file in the project."""
    model_config = {"frozen": True}
    
    extension: str
    
    @field_validator('extension')
    @classmethod
    def validate_extension(cls, v: str) -> str:
        if not v.startswith('.'):
            raise ValueError('Extension must start with .')
        return v
    
    @property
    def is_python(self) -> bool:
        """Check if this is a Python file."""
        return self.extension == ".py"
    
    @property
    def is_javascript(self) -> bool:
        """Check if this is a JavaScript/TypeScript file."""
        return self.extension in [".js", ".ts", ".jsx", ".tsx"]


class CodeDirectory(BaseModel):
    """Represents a directory containing code files."""
    model_config = {"frozen": True}
    
    path: Path
    file_count: int = Field(ge=0)
    last_modified: datetime  # From the newest file in the directory
    code_files: List[CodeFile] = Field(default_factory=list)
    
    @property
    def has_python_files(self) -> bool:
        """Check if directory contains Python files."""
        return any(f.is_python for f in self.code_files)
    
    @property
    def has_javascript_files(self) -> bool:
        """Check if directory contains JavaScript/TypeScript files."""
        return any(f.is_javascript for f in self.code_files)


class DocFile(FileInfo):
    """Represents a documentation file."""
    model_config = {"frozen": True}
    
    doc_type: DocType
    mapped_code_path: Optional[Path] = None  # Path to corresponding code
    
    @property
    def is_index_doc(self) -> bool:
        """Check if this is an index documentation file."""
        return self.doc_type == DocType.INDEX
    
    @property
    def is_module_doc(self) -> bool:
        """Check if this is a module documentation file."""
        return self.doc_type == DocType.MODULE
    
    @property
    def is_file_doc(self) -> bool:
        """Check if this is a file documentation."""
        return self.doc_type == DocType.FILE


class DocStatus(BaseModel):
    """Status of documentation for a code entity."""
    model_config = {"frozen": True}
    
    code: Union[CodeFile, CodeDirectory, Path]  # Path for index docs
    doc: Optional[DocFile]
    status: StatusType
    doc_type: DocType
    
    @property
    def needs_attention(self) -> bool:
        """Check if this documentation status requires attention."""
        return self.status != StatusType.UP_TO_DATE
    
    @property
    def is_outdated(self) -> bool:
        """Check if documentation is outdated."""
        return self.status == StatusType.OUTDATED
    
    @property
    def is_missing(self) -> bool:
        """Check if documentation is missing."""
        return self.status == StatusType.MISSING
    
    @property
    def is_orphaned(self) -> bool:
        """Check if documentation is orphaned."""
        return self.status == StatusType.ORPHANED


class DocCheckSummary(BaseModel):
    """Summary statistics for documentation check."""
    model_config = {"frozen": True}
    
    total_files: int = Field(ge=0)
    outdated_count: int = Field(ge=0)
    missing_count: int = Field(ge=0)
    orphaned_count: int = Field(ge=0)
    up_to_date_count: int = Field(ge=0)
    
    @property
    def has_issues(self) -> bool:
        """Check if there are any documentation issues."""
        return (self.outdated_count + self.missing_count + self.orphaned_count) > 0
    
    @property
    def issues_count(self) -> int:
        """Total number of issues."""
        return self.outdated_count + self.missing_count + self.orphaned_count


class DocCheckResult(BaseModel):
    """Result of complete documentation check."""
    model_config = {"frozen": True}
    
    statuses: List[DocStatus]
    summary: DocCheckSummary
    timestamp: datetime = Field(default_factory=datetime.now)
    project_root: Path
    docs_root: Path
    
    @property
    def has_issues(self) -> bool:
        """Check if there are any issues found."""
        return self.summary.has_issues
    
    @property
    def outdated_docs(self) -> List[DocStatus]:
        """Get only outdated documentation."""
        return [s for s in self.statuses if s.is_outdated]
    
    @property
    def missing_docs(self) -> List[DocStatus]:
        """Get only missing documentation."""
        return [s for s in self.statuses if s.is_missing]
    
    @property
    def orphaned_docs(self) -> List[DocStatus]:
        """Get only orphaned documentation."""
        return [s for s in self.statuses if s.is_orphaned]
    
    @property
    def issues(self) -> List[DocStatus]:
        """Get all documentation that needs attention."""
        return [s for s in self.statuses if s.needs_attention]
    
    @classmethod
    def create_summary(cls, statuses: List[DocStatus]) -> DocCheckSummary:
        """Create summary from list of statuses."""
        outdated = sum(1 for s in statuses if s.is_outdated)
        missing = sum(1 for s in statuses if s.is_missing)
        orphaned = sum(1 for s in statuses if s.is_orphaned)
        up_to_date = sum(1 for s in statuses if not s.needs_attention)
        
        return DocCheckSummary(
            total_files=len(statuses),
            outdated_count=outdated,
            missing_count=missing,
            orphaned_count=orphaned,
            up_to_date_count=up_to_date
        )
