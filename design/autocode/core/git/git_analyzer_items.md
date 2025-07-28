# Items from git_analyzer.py

**Source:** `C:\Users\bruno\Desktop\autocode\autocode\core\git\git_analyzer.py`  
**Type:** python

**Metrics:**
- Total Classes: 3
- Total Functions: 0
- Total Imports: 6
- Total Loc: 419
- Average Methods Per Class: 3.6666666666666665

## Classes

### FileChange

**Line:** 13  
**LOC:** 8  

```mermaid
classDiagram
    class FileChange {
        +file: str
        +status: str
        +staged: bool
        +additions: int
        +deletions: int
        +diff: str
    }
    NamedTuple <|-- FileChange

```

### GitStatus

**Line:** 23  
**LOC:** 8  

```mermaid
classDiagram
    class GitStatus {
        +total_files: int
        +modified: int
        +added: int
        +deleted: int
        +untracked: int
        +renamed: int
    }
    NamedTuple <|-- GitStatus

```

### GitAnalyzer

**Line:** 33  
**LOC:** 387  

```mermaid
classDiagram
    class GitAnalyzer {
        -__init__(project_root: Path)
        -_run_git_command(args: List[str]) -> str
        -_get_file_status() -> Dict[str, tuple]
        -_get_file_diff(filepath: str, staged: bool) -> tuple
        -_categorize_status(index_status: Optional[str], worktree_status: Optional[str]) -> str
        -_load_gitignore_patterns() -> Set[str]
        -_should_ignore_file(filepath: str) -> bool
        +get_all_changes() -> List[FileChange]
        +get_repository_status(changes: List[FileChange]) -> GitStatus
        +analyze_changes() -> Dict
        +save_changes_to_file(output_path: Path) -> Dict
    }

```

