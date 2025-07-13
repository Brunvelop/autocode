# Items from generator_factory.py

**Source:** `C:\Users\bruno\Desktop\autocode\autocode\core\design\diagrams\generator_factory.py`  
**Type:** python

**Metrics:**
- Total Classes: 2
- Total Functions: 2
- Total Imports: 6
- Total Loc: 231
- Average Methods Per Class: 8.0

## Classes

### GeneratorRegistry

**Line:** 16  
**LOC:** 36  

```mermaid
classDiagram
    class GeneratorRegistry {
        -__init__()
        +register_generator(name: str, generator_class: Type[BaseGenerator], formats: List[str]) -> Any
        +get_generator(name: str) -> Optional
        +get_generator_for_format(format_name: str) -> Optional
        +list_generators() -> List[str]
        +get_supported_formats() -> List[str]
    }

```

### GeneratorFactory

**Line:** 69  
**LOC:** 163  

```mermaid
classDiagram
    class GeneratorFactory {
        -__init__(config: Dict[str, Any])
        -_register_builtin_generators() -> Any
        +create_generator(generator_type: str) -> Optional[BaseGenerator]
        +create_generator_for_format(format_name: str) -> Optional[BaseGenerator]
        +get_generators_for_types(generator_types: List[str]) -> Dict[str, BaseGenerator]
        +auto_detect_generators(diagram_types: List[str]) -> Dict[str, BaseGenerator]
        +get_available_generators() -> List[str]
        +get_supported_formats() -> List[str]
        +supports_diagram_type(diagram_type: str) -> bool
        +get_generator_info() -> Dict[str, Any]
    }

```

## Functions

### register_generator

**Line:** 58  
**LOC:** 4  
**Parameters:** name, generator_class, formats  
**Returns:** Any  

### get_registry

**Line:** 64  
**LOC:** 3  
**Returns:** GeneratorRegistry  

