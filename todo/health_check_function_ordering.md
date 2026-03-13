# feat(health): add function ordering convention check to health-check

## ⚠️ Lecciones aprendidas — implementado y revertido

Esta feature fue implementada (commits 77d20d9 → 0f37c9d) y posteriormente **revertida**
porque tiene problemas de diseño fundamentales:

### Problema 1: Es una convención de estilo, no una métrica de salud

El health-check system está diseñado para métricas **cuantitativas y objetivas** (MI, CC, nesting,
SLOC, rank F, circular deps). Estas métricas miden cosas concretas calculadas por Lizard y
tienen umbrales numéricos claros.

El orden de funciones es una **convención de estilo** — subjetiva, contextual, y debatible.
Mezclar ambas en el mismo sistema diluye el propósito de cada uno.

### Problema 2: Falsos positivos estructurales

La implementación solo detecta "público después de privado" a nivel de archivo, sin
distinción de clase. Casos legítimos que generan violaciones:

- Módulos con secciones explícitas: `# PUBLIC API` y `# PRIVATE HELPERS` intercaladas
  por razones de proximidad lógica
- Archivos con múltiples clases donde el orden per-clase es correcto pero el orden
  file-level viola la regla
- Código generado, parsers, y state machines donde el orden refleja la lógica,
  no la visibilidad

Para proyectos reales, la tasa de falsos positivos fue suficientemente alta
como para que los warnings perdieran credibilidad.

### Problema 3: La herramienta correcta ya existe: `ruff`

`ruff` tiene reglas de ordering con soporte per-clase, configurable por tipo
de método (dunder, property, classmethod, staticmethod, etc.):

```toml
# pyproject.toml
[tool.ruff]
select = ["D"]  # o reglas específicas de ordering

# O más específicamente con pylint-style ordering:
select = ["C0"]
```

También existen plugins como `ruff-isort` para imports. Para method ordering
en clases, la regla `D` de pydocstyle o las extensiones de `pylint` (C0202, C0204)
hacen esto con precisión AST real.

```bash
# Uso inmediato, sin implementar nada:
ruff check autocode/ --select D
```

Es estrictamente superior: AST-based, entiende clases, configurable por tipo de método,
auto-fixable (`ruff check --fix`), y no requiere mantenimiento.

---

## Descripción original

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

## Implementación recomendada (si se decide retomar)

### Opción A: Delegar a ruff (recomendado)

Documentar en el README que la convención de ordering se enforza con `ruff`,
no con autocode health-check. Añadir a `pyproject.toml` del proyecto la configuración
de ruff para method ordering.

**Sin código que mantener. Sin falsos positivos. Auto-fixable.**

### Opción B: Implementación per-clase (si se quiere en-house)

Si se decide mantenerlo en el health system, la implementación debe ser **per-clase**,
no per-archivo:

```python
def _check_function_ordering_in_class(
    class_name: str, methods: list[FunctionMetrics]
) -> list[str]:
    """Detecta métodos públicos después de privados DENTRO de una clase."""
    ...
```

Esto requiere que `FileMetrics.functions` incluya información de a qué clase
pertenece cada método (`class_name: str | None`). Actualmente `FunctionMetrics`
no tiene este dato — habría que añadirlo al parser.

## Archivos a tocar (si se implementa per-clase)

- `autocode/core/code/models.py` — añadir `class_name: str | None` a `FunctionMetrics`
- `autocode/core/code/parsers/python_parser.py` — trackear clase contenedora al parsear
- `autocode/core/code/parsers/js_parser.py` — ídem para JS
- `autocode/core/code/health.py` — `_classify_function()`, `_check_function_ordering()`
- `tests/unit/core/code/test_health.py` — tests para la nueva gate

## Notas

- Solo tiene sentido como **opt-in** (`check_function_ordering = false` por defecto)
- Evaluar si `ruff` con reglas de ordering cubre el caso de uso antes de implementar
- Los módulos con sección `# PUBLIC API` / `# PRIVATE HELPERS` en comentarios
  podrían ser excluidos opcionalmente
