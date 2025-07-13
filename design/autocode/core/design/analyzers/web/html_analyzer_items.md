# Items from html_analyzer.py

**Source:** `C:\Users\bruno\Desktop\autocode\autocode\core\design\analyzers\web\html_analyzer.py`  
**Type:** python

**Metrics:**
- Total Classes: 1
- Total Functions: 0
- Total Imports: 5
- Total Loc: 301
- Average Methods Per Class: 9.0

## Classes

### HTMLAnalyzer

**Line:** 15  
**LOC:** 287  

```mermaid
classDiagram
    class HTMLAnalyzer {
        +get_supported_extensions() -> List[str]
        +analyze_file(file_path: Path) -> AnalysisResult
        -_extract_elements(soup: BeautifulSoup) -> List
        -_extract_custom_elements(soup: BeautifulSoup) -> List
        -_extract_form_elements(soup: BeautifulSoup) -> List
        -_extract_scripts(soup: BeautifulSoup) -> List
        -_extract_links(soup: BeautifulSoup) -> List
        -_extract_relationships(soup: BeautifulSoup) -> List
        -_calculate_dom_depth(soup: BeautifulSoup) -> int
    }
    BaseAnalyzer <|-- HTMLAnalyzer

```

