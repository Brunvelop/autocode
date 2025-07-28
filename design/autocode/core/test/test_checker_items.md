# Items from test_checker.py

**Source:** `C:\Users\bruno\Desktop\autocode\autocode\core\test\test_checker.py`  
**Type:** python

**Metrics:**
- Total Classes: 2
- Total Functions: 0
- Total Imports: 5
- Total Loc: 302
- Average Methods Per Class: 7.5

## Classes

### TestStatus

**Line:** 14  
**LOC:** 6  

```mermaid
classDiagram
    class TestStatus {
        +code_file: Path
        +test_file: Path
        +status: str
        +test_type: str
    }
    NamedTuple <|-- TestStatus

```

### TestChecker

**Line:** 22  
**LOC:** 281  

```mermaid
classDiagram
    class TestChecker {
        -__init__(project_root: Path, config: Optional)
        +find_code_directories() -> List[Path]
        +get_all_python_files() -> List[Path]
        +get_all_code_directories_with_subdirs() -> Set[Path]
        +map_code_file_to_unit_test(code_file: Path) -> Path
        +map_directory_to_integration_test(code_dir: Path) -> Path
        +find_all_test_files() -> List[Path]
        +map_test_to_code_file(test_file: Path) -> Path
        +find_orphaned_tests() -> List[TestStatus]
        +execute_tests() -> tuple[int, str, str]
        +check_all_tests() -> List[TestStatus]
        +parse_pytest_failures(stdout: str, stderr: str) -> List[str]
        +get_test_statuses() -> List[TestStatus]
        +get_missing_and_failing_tests() -> List[TestStatus]
        +format_results(results: List[TestStatus]) -> str
    }

```

