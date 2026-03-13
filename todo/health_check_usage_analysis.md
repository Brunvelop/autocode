# feat(health): add symbol usage analysis to health-check (dead code + hotspots)

## Descripción

Añadir al health-check (y como comando independiente) análisis de **uso de símbolos** a nivel de proyecto:

1. **Dead code** — funciones/clases definidas pero nunca referenciadas en el proyecto
2. **Hotspots** — las N funciones/clases más referenciadas (para entender el core del proyecto)
3. **Underused** — funciones/clases referenciadas muy pocas veces (candidatas a simplificar o eliminar)

## Comportamiento esperado

### Como quality gate (opt-in)

```bash
autocode health-check --project-root .
```

```
⚠️  VIOLATION [warning] dead_code — autocode/core/utils/openrouter.py
    format_headers() defined at line 23, 0 references found in project

⚠️  VIOLATION [warning] dead_code — autocode/core/code/snapshots.py
    SnapshotManager.prune() defined at line 89, 0 references found in project
```

### Como reporte independiente (nuevo comando o subcomando)

```bash
autocode usage-report --project-root . --top 10
```

```
📊 Symbol Usage Report

🔴 Dead code (0 references):
   format_headers()           autocode/core/utils/openrouter.py:23
   SnapshotManager.prune()    autocode/core/code/snapshots.py:89

🟡 Underused (1-2 references):
   calculate_coupling()       autocode/core/code/coupling.py:45    (1 ref)
   load_thresholds()          autocode/core/code/health.py:62      (2 refs)

🔥 Hotspots (most referenced):
   run_health_check()         autocode/core/code/health.py:180     (12 refs)
   generate_with_dspy()       autocode/core/ai/dspy_utils.py:215   (9 refs)
   FileMetrics                autocode/core/code/models.py:45      (8 refs)
```

## Configuración en pyproject.toml

```toml
[tool.codehealth]
check_dead_code = false              # activar dead code gate (default: false, opt-in)
dead_code_level = "warning"         # "warning" | "critical"
dead_code_min_refs = 0              # umbral: < N referencias = dead code
dead_code_exclude_patterns = [      # excluir símbolos que empiezan por estos patrones
    "test_",                        # funciones de test
    "__",                           # dunders
    "main",                         # entry points
]
```

## Implementación propuesta

### Enfoque: búsqueda de referencias por nombre (sin AST completo)

La aproximación más pragmática es **búsqueda por nombre en el source**, no un análisis de flujo completo. Acepta falsos negativos (ej: uso vía `getattr`) pero es rápido y no requiere deps nuevas.

### 1. Nuevo módulo `autocode/core/code/usage.py`

```python
"""
usage.py — Symbol usage analysis across a Python project.

Provides:
- SymbolUsage: dataclass con nombre, origen y conteo de referencias
- build_usage_index(project_root): escanea todos los .py y cuenta referencias
"""
import re
from pathlib import Path
from dataclasses import dataclass
from typing import Optional


@dataclass
class SymbolUsage:
    name: str               # nombre del símbolo
    defined_in: str         # archivo donde está definido
    defined_line: int       # línea de definición
    reference_count: int    # cuántas veces aparece referenciado fuera de su definición
    references: list[str]   # lista de "file:line" donde se referencia


def build_usage_index(
    project_root: Path,
    symbols: list[dict],        # [{"name": "foo", "file": "...", "line": 42}, ...]
    exclude_patterns: list[str] = None,
) -> list[SymbolUsage]:
    """
    Para cada símbolo en `symbols`, cuenta cuántas veces aparece
    referenciado en los .py del proyecto (excluyendo su propia definición).
    
    Estrategia: regex simple `\bname\b` en todos los archivos .py,
    ignorando líneas de definición (def name / class name).
    """
    ...
```

### 2. Nueva función en `health.py`

```python
def _check_dead_code(
    config: HealthConfig,
    file_metrics: list[FileMetrics],
    project_root: Path,
) -> list[HealthViolation]:
    """Detecta funciones/clases sin ninguna referencia en el proyecto."""
    from autocode.core.code.usage import build_usage_index
    
    # Extraer todos los símbolos del proyecto
    symbols = [
        {"name": f.name, "file": f.file, "line": f.line}
        for fm in file_metrics
        for f in fm.functions
    ]
    
    usage_index = build_usage_index(
        project_root,
        symbols,
        exclude_patterns=config.dead_code_exclude_patterns
    )
    
    violations = []
    for usage in usage_index:
        if usage.reference_count <= config.dead_code_min_refs:
            violations.append(HealthViolation(
                rule="dead_code",
                level=config.dead_code_level,
                path=usage.defined_in,
                value=float(usage.reference_count),
                threshold=float(config.dead_code_min_refs),
                detail=f"{usage.name}() line {usage.defined_line}, {usage.reference_count} references"
            ))
    return violations
```

### 3. Nuevo comando CLI `usage-report`

En `autocode/interfaces/cli.py`, añadir:

```python
@app.command("usage-report")
def usage_report(
    project_root: str = typer.Option(".", help="Directorio raíz del proyecto"),
    top: int = typer.Option(10, help="Top N símbolos más/menos usados"),
    output_format: str = typer.Option("table", help="table | json"),
):
    """Analiza el uso de símbolos: dead code, hotspots y underused."""
    ...
```

### 4. Añadir a `HealthConfig`

```python
check_dead_code: bool = False
dead_code_level: str = "warning"
dead_code_min_refs: int = 0
dead_code_exclude_patterns: list[str] = field(default_factory=lambda: [
    "test_", "__", "main", "setup", "teardown"
])
```

## Consideraciones y limitaciones conocidas

| Caso | Comportamiento |
|------|---------------|
| `getattr(obj, 'foo')` | Falso negativo (no detecta uso) |
| `from module import foo` | Contado como referencia ✅ |
| Funciones de test (`test_*`) | Excluidas por defecto |
| Dunders (`__init__`, etc.) | Excluidos por defecto |
| Entry points (`main`) | Excluido por defecto |
| Clases Pydantic (usadas como type hints) | Detectadas ✅ (aparecen como `ClassName`) |
| Funciones usadas solo en templates/HTML | Falso positivo posible |

## Archivos a tocar

- `autocode/core/code/usage.py` — nuevo módulo de análisis de uso (**nuevo archivo**)
- `autocode/core/code/health.py` — nueva gate `_check_dead_code()` + config
- `autocode/core/code/models.py` — posiblemente añadir `SymbolUsage` a los modelos
- `autocode/interfaces/cli.py` — nuevo comando `usage-report`
- `autocode/interfaces/api.py` — nuevo endpoint `GET /code/usage`
- `tests/unit/core/code/test_usage.py` — tests unitarios (**nuevo archivo**)

## Fases de implementación recomendadas

### Fase 1 (MVP): Reporte offline, sin gate
- Implementar `usage.py` con la lógica de búsqueda por regex
- Añadir comando CLI `usage-report` que imprime tabla
- Sin tocar `health.py` todavía

### Fase 2: Integración en health-check
- Añadir `_check_dead_code()` a `health.py` como opt-in gate
- Añadir config a `HealthConfig`
- Tests

### Fase 3: Endpoint API + visualización
- Exponer `/code/usage` en la API
- Integrar en el treemap del code-dashboard (colorear por usage frequency)
