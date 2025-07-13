# Items from opencode_executor.py

**Source:** `C:\Users\bruno\Desktop\autocode\autocode\core\ai\opencode_executor.py`  
**Type:** python

**Metrics:**
- Total Classes: 1
- Total Functions: 1
- Total Imports: 8
- Total Loc: 267
- Average Methods Per Class: 12.0

## Classes

### OpenCodeExecutor

**Line:** 15  
**LOC:** 226  

```mermaid
classDiagram
    class OpenCodeExecutor {
        -__init__(project_root: Path, config_file: Optional[Path])
        -_load_config() -> Dict[str, Any]
        -_get_default_config() -> Dict[str, Any]
        +is_opencode_available() -> bool
        +list_prompts() -> List[str]
        +get_prompts_info() -> Dict[str, str]
        +execute_opencode(prompt: str) -> Tuple[int, str, str]
        +execute_with_prompt_file(prompt_name: str) -> Tuple[int, str, str]
        +format_output(exit_code: int, stdout: str, stderr: str, json_output: bool, verbose: bool) -> str
        -_format_json_output(exit_code: int, stdout: str, stderr: str) -> str
        -_format_text_output(exit_code: int, stdout: str, stderr: str, verbose: bool) -> str
        -_get_timestamp() -> str
    }

```

## Functions

### validate_opencode_setup

**Line:** 243  
**LOC:** 25  
**Parameters:** project_root  
**Returns:** Tuple[bool, str]  

