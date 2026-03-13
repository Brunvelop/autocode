# feat(health): add symbol usage analysis to health-check (dead code + hotspots)

## ⚠️ Lecciones aprendidas — implementado y revertido

Esta feature fue implementada completamente (commits 758ecdd → 43b80d7) y posteriormente
**revertida** porque el enfoque tiene problemas fundamentales:

### Problema 1: Regex `\bname\b` genera falsos positivos masivos en proyectos multi-lenguaje

El flujo implementado era:
- `all_file_metrics` extrae símbolos de **todos** los archivos trackeados (`.py` + `.js` + `.mjs` + `.jsx`)
- `build_usage_index()` buscaba referencias solo en `.py`

**Resultado:** 100% de los símbolos JS aparecían con 0 referencias → falso positivo masivo.

La "solución" de escanear también `.js` topaba con otro problema:

| Patrón JS | Problema |
|-----------|---------|
| `connectedCallback()` | Lo llama el browser, no el código → siempre 0 refs |
| `(anonymous)()` | Lizard lo extrae pero no es referenciable por nombre |
| Event handlers en HTML | `.html` no se escanea → falso positivo |
| `customElements.define()` | Tag se usa en HTML, no en JS |

### Problema 2: Los falsos positivos son inherentes a la técnica

La detección por regex no puede distinguir entre:
- Una función realmente muerta
- Una función usada vía `getattr`, `globals()`, o invocación dinámica
- Un entry point registrado en `pyproject.toml` (ej: `app = "cli:app"`)
- Un callback/hook llamado por un framework externo
- Una función pública de librería usada por consumidores externos

Para proyectos reales, la lista `dead_code_exclude_patterns` crece indefinidamente
intentando tapar falsos positivos, destruyendo el valor de la herramienta.

### Problema 3: La herramienta correcta ya existe: `vulture`

`vulture` analiza el AST completo, entiende:
- Decoradores (`@app.route`, `@pytest.fixture`)  
- Clases base y overrides
- `__all__` exports
- Uso vía `getattr` (heurística)
- Confianza configurable por tipo de item

```bash
pip install vulture
vulture autocode/ --min-confidence 80
```

Es estrictamente superior a regex, no requiere mantenimiento, y es Python-only
(lo que evita el problema de los símbolos JS).

---

## Descripción original

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

## Implementación propuesta (revisada)

### Enfoque recomendado: integrar `vulture` como backend

En lugar de reimplementar la detección por regex, wrappear `vulture`:

```python
# autocode/core/code/usage.py
import subprocess
from pathlib import Path

def build_usage_index_vulture(
    project_root: Path,
    min_confidence: int = 80,
    exclude_patterns: list[str] | None = None,
) -> list[SymbolUsage]:
    """Detecta dead code usando vulture (requiere: pip install vulture)."""
    result = subprocess.run(
        ["vulture", str(project_root), f"--min-confidence={min_confidence}"],
        capture_output=True, text=True
    )
    # Parsear output de vulture: "path:line: unused function 'name' (confidence%)"
    ...
```

**Ventajas:**
- Sin falsos positivos de JS (vulture solo analiza Python)
- Sin necesidad de exclusion_patterns para casos comunes
- AST-based → respeta decoradores, `__all__`, herencia

**Limitación:** Añade dependencia de `vulture`. Puede añadirse como optional dep:
```toml
[project.optional-dependencies]
dead-code = ["vulture>=2.10"]
```

### Alternativa más simple: script `make dead-code`

```makefile
dead-code:
    vulture autocode/ --min-confidence 80
```

Sin integración en el health system, sin complejidad. El desarrollador lo corre manualmente
cuando quiere revisar dead code.

## Archivos a tocar (si se implementa con vulture)

- `autocode/core/code/usage.py` — wrapper de vulture (**nuevo archivo, muy simple**)
- `autocode/interfaces/cli.py` — nuevo comando `usage-report` que invoca vulture
- `pyproject.toml` — `[project.optional-dependencies] dead-code = ["vulture>=2.10"]`
- `tests/unit/core/code/test_usage.py` — tests (mockeando el subprocess de vulture)

## Consideraciones y limitaciones conocidas

| Caso | Comportamiento con vulture |
|------|---------------------------|
| `getattr(obj, 'foo')` | Detectable con whitelist de vulture ✅ |
| `from module import foo` | Detectado como uso ✅ |
| Funciones de test (`test_*`) | Vulture las ignora por convención ✅ |
| Dunders (`__init__`, etc.) | Vulture los ignora ✅ |
| Entry points (`main`) | Añadir a `whitelist.py` de vulture ✅ |
| Clases Pydantic (type hints) | Detectadas ✅ |
| Símbolos JS | Vulture es Python-only → sin falsos positivos ✅ |
| Web Component lifecycle | Fuera de scope (JS) → sin falsos positivos ✅ |
