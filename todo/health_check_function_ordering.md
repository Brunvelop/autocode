# feat(health): add function ordering convention check to health-check

## Descripción

Añadir al health-check una nueva quality gate que detecte archivos donde el orden de definición de funciones/métodos no sigue un convenio establecido. El problema más común: mezclar funciones públicas y privadas (`_prefijo`) de forma aleatoria en lugar de agruparlas de forma coherente.

## Convenio a validar (Python)

Orden esperado dentro de un módulo o clase:

```
1. Dunder methods    (__init__, __str__, __repr__, ...)
2. Public methods    (sin prefijo _)
3. Private methods   (prefijo _ o __)
```

Variante aceptable alternativa (también válida si es consistente):
```
1. Dunder methods
2. Private methods primero (helpers del __init__)
3. Public API al final
```

Lo que se considera **violación**: intercalar métodos públicos y privados sin ningún patrón, por ejemplo:
```python
def public_a(): ...
def _private_x(): ...   # ← mal: rompe el bloque público
def public_b(): ...     # ← peor: vuelve a público después de privado
def _private_y(): ...
```

## Comportamiento esperado

```bash
autocode health-check --project-root .
```

```
❌ VIOLATION [warning] function_ordering — mymodule.py
   _helper() at line 45 interrupts public block (public_api() follows at line 67)
```

Configurable en `pyproject.toml`:
```toml
[tool.codehealth]
check_function_ordering = true          # activar/desactivar (default: false, opt-in)
function_ordering_level = "warning"     # "warning" | "critical"
```

## Implementación propuesta

### 1. Datos ya disponibles

`FunctionMetrics` (en `autocode/core/code/models.py`) ya tiene:
- `name: str`
- `line: int`
- `file: str`

Solo falta clasificar cada función como `dunder`, `public` o `private`.

### 2. Nueva función en `health.py`

```python
def _classify_function(name: str) -> str:
    """Clasifica una función como 'dunder', 'private' o 'public'."""
    if name.startswith('__') and name.endswith('__'):
        return 'dunder'
    elif name.startswith('_'):
        return 'private'
    return 'public'

def _check_function_ordering(
    config: HealthConfig, file_metrics: list[FileMetrics]
) -> list[HealthViolation]:
    """Detecta mezclas de funciones públicas y privadas."""
    violations = []
    for fm in file_metrics:
        funcs_sorted = sorted(fm.functions, key=lambda f: f.line)
        categories = [_classify_function(f.name) for f in funcs_sorted]
        
        # Detectar si hay un 'public' después de un 'private' (ignorando dunders)
        last_was_private = False
        for func, cat in zip(funcs_sorted, categories):
            if cat == 'dunder':
                continue
            if cat == 'private':
                last_was_private = True
            elif cat == 'public' and last_was_private:
                violations.append(HealthViolation(
                    rule="function_ordering",
                    level=config.function_ordering_level,
                    path=fm.path,
                    value=float(func.line),
                    threshold=0.0,
                    detail=f"{func.name}() at line {func.line} appears after private methods"
                ))
    return violations
```

### 3. Añadir a `HealthConfig`

```python
check_function_ordering: bool = False
function_ordering_level: str = "warning"  # "warning" | "critical"
```

### 4. Integrar en `run_health_check()`

```python
if config.check_function_ordering:
    violations.extend(_check_function_ordering(config, file_metrics))
```

## Archivos a tocar

- `autocode/core/code/health.py` — nueva función `_check_function_ordering()` + config
- `autocode/core/code/models.py` — posiblemente añadir campo `kind` a `FunctionMetrics`
- `tests/unit/core/code/test_health.py` — tests para la nueva gate
- `autocode/testing/README.md` — documentar nueva opción de config

## Notas

- Empezar como **opt-in** (`check_function_ordering = false` por defecto) para no romper proyectos existentes
- El análisis es por archivo, no por clase — una mejora futura podría ser por clase
- Los módulos con sección `# PUBLIC API` / `# PRIVATE HELPERS` en comentarios podrían ser excluidos opcionalmente
- Para clases, el orden dentro de `__init__` debería tratarse separado del nivel módulo
