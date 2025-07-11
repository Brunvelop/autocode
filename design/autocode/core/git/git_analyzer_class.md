# Classes from git_analyzer.py

Source: `autocode\core\git\git_analyzer.py`

## FileChange

**Metrics:** LOC: 8 | Methods: 0

```mermaid
classDiagram
    class FileChange {
    }
    NamedTuple <|-- FileChange

```

## GitStatus

**Metrics:** LOC: 8 | Methods: 0

```mermaid
classDiagram
    class GitStatus {
    }
    NamedTuple <|-- GitStatus

```

## GitAnalyzer

**Metrics:** LOC: 387 | Methods: 11

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

