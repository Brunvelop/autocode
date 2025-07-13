# Items from token_counter.py

**Source:** `C:\Users\bruno\Desktop\autocode\autocode\core\ai\token_counter.py`  
**Type:** python

**Metrics:**
- Total Classes: 1
- Total Functions: 1
- Total Imports: 3
- Total Loc: 162
- Average Methods Per Class: 6.0

## Classes

### TokenCounter

**Line:** 11  
**LOC:** 123  

```mermaid
classDiagram
    class TokenCounter {
        -__init__(model: str)
        +count_tokens_in_text(text: str) -> int
        +count_tokens_in_file(file_path: Path) -> int
        +get_token_statistics(file_path: Path) -> Dict
        +estimate_cost(token_count: int, input_cost_per_1k: float, output_cost_per_1k: float) -> Dict
        +check_threshold(token_count: int, threshold: int) -> Dict
    }

```

## Functions

### count_tokens_in_multiple_files

**Line:** 136  
**LOC:** 27  
**Parameters:** file_paths, model  
**Returns:** Dict  

