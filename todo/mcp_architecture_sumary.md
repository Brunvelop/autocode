# Plan detallado: `get_architecture_summary`

---

## 1. Objetivo

Crear una función `get_architecture_summary` que devuelva un **string compacto en texto plano** con la estructura de arquitectura del proyecto + métricas de calidad, optimizado para consumo por LLMs. Registrada con `interfaces=["api", "mcp"]`.

---

## 2. Firma de la función

```python
@register_function(http_methods=["GET"], interfaces=["api", "mcp"])
def get_architecture_summary(
    path: str = ".",
    depth: int = -1,
    show_functions: bool = False,
) -> CodeSummaryOutput:
    """
    Obtiene un resumen compacto de la arquitectura del código con métricas de calidad.

    Versión ligera de get_architecture_snapshot, optimizada para LLMs.
    Devuelve un árbol tipo 'tree' con métricas de calidad (MI, CC, SLOC)
    por directorio y archivo, hotspots y dependencias circulares.

    Args:
        path: Path relativo al directorio a analizar (default: directorio actual)
        depth: Profundidad máxima del árbol (-1 para ilimitado)
        show_functions: Si incluir nodos de función/método/clase en el árbol
    """
```

**Output model:** Reutiliza `CodeSummaryOutput` (ya existe en `models.py`), que devuelve `result: Optional[str]`.

---

## 3. Implementación interna

La función **NO llama** a `get_architecture_snapshot()` (que siempre analiza todo el proyecto). En su lugar, reutiliza las funciones internas privadas existentes directamente:

```python
def get_architecture_summary(path=".", depth=-1, show_functions=False):
    try:
        # 1. Git metadata
        commit_hash = git("rev-parse", "HEAD")
        commit_short = git("rev-parse", "--short", "HEAD")
        branch = git("rev-parse", "--abbrev-ref", "HEAD")

        # 2. Get tracked files (filtrados por path si path != ".")
        all_files = get_tracked_files(*_ALL_EXTENSIONS)
        if path != ".":
            prefix = path.rstrip("/")
            all_files = [f for f in all_files if f.startswith(prefix)]

        # 3. Build hierarchy con métricas (reutiliza _build_architecture_nodes)
        nodes = _build_architecture_nodes(all_files)
        root_id = "."
        _propagate_metrics(nodes, root_id)

        # 4. Resolver dependencias (reutiliza _resolve_file_dependencies)
        dependencies, circular_deps = _resolve_file_dependencies(all_files)

        # 5. Aplicar depth filter para el texto (no en el análisis)
        # 6. Renderizar texto compacto
        lines = []
        lines.append(_render_header(commit_short, branch, nodes, path))
        lines.append("")
        lines.extend(_render_architecture_tree(
            nodes, root_id, path, depth, show_functions
        ))
        
        hotspot_lines = _render_hotspots(nodes)
        if hotspot_lines:
            lines.append("")
            lines.extend(hotspot_lines)
        
        dep_lines = _render_deps_summary(dependencies, circular_deps)
        if dep_lines:
            lines.append("")
            lines.extend(dep_lines)

        summary_text = "\n".join(lines)
        file_nodes = [n for n in nodes if n.type == "file"]
        return CodeSummaryOutput(
            success=True,
            result=summary_text,
            message=f"Arquitectura: {len(file_nodes)} archivos, "
                    f"{sum(n.sloc for n in file_nodes)} SLOC"
        )
    except Exception as e:
        return CodeSummaryOutput(success=False, message=str(e))
```

---

## 4. Helpers a implementar

### 4.1 `_render_header(commit_short, branch, nodes, path)`

```
📊 Architecture (abc123d @ main)
42 files, 8.5k SLOC, MI=71.2, CC=3.8, 120 fn, 18 cls
```

Calcula los agregados globales desde los `file_nodes`. Usa formato abreviado (`8.5k`).

### 4.2 `_render_architecture_tree(nodes, root_id, path, depth, show_functions)`

Construye el árbol tipo `tree` con indent visual (`├──`, `└──`, `│   `).

**Para directorios:** nombre + métricas agregadas
```
├── autocode/core/ (4.8k SLOC, MI=67.2, CC=4.5)
```

**Para archivos (show_functions=False):** nombre + métricas + counts inline + indicador de alerta
```
│   ├── architecture.py (340 SLOC, MI=68.0, CC=3.1, 10f, 2c)
│   ├── executor.py (280 SLOC, MI=42.3, CC=12.1, 6f) 🔴
```

**Para archivos (show_functions=True):** nombre + métricas, luego hijos indentados
```
│   ├── executor.py (280 SLOC, MI=42.3, CC=12.1) 🔴
│   │   ├── 🔷 PlanExecutor (200 SLOC, CC=7.2, 4m)
│   │   │   ├── execute() CC=12 C 🔴
│   │   │   ├── validate() CC=5 A
│   │   │   └── _apply_step() CC=8 B
│   │   └── run_plan() CC=6 B
```

**Indicadores de alerta:**
- `🔴` → MI < 40 o CC > 15
- `⚠️` → MI < 60 o CC > 10

**Depth filter:** solo renderiza nodos hasta `depth` niveles desde `path`. El cálculo de métricas se hace sobre todos los nodos (para que los agregados de directorio sean correctos), pero el rendering se corta a la profundidad indicada.

### 4.3 `_render_hotspots(nodes)`

Muestra los 5-10 archivos con peor MI o mayor CC. Solo aparece si hay archivos problemáticos (MI < 60 o CC > 8).

```
⚠️ Hotspots:
  🔴 core/ai/pipelines.py — MI=42.3, CC=12.1 (6f)
  🔴 core/planning/executor.py — MI=48.7, CC=8.9 (4f)
  ⚠️ interfaces/api.py — MI=55.2, CC=7.3 (8f)
```

Ordenados por MI ascendente (peores primero). Max 10 entradas.

### 4.4 `_render_deps_summary(dependencies, circular_deps)`

Resumen compacto de dependencias. Solo aparece si hay dependencias.

```
🔗 Dependencies: 85 internal imports
⛔ Circular (2):
  architecture.py ↔ models.py
  executor.py ↔ planner.py
```

Si no hay circulares, solo muestra el count. Si no hay deps, no muestra nada.

---

## 5. Cambios en archivos

### `autocode/core/code/architecture.py`
- **Añadir** la función registrada `get_architecture_summary`
- **Añadir** 4 helpers privados:
  - `_render_header`
  - `_render_architecture_tree`  (recursiva, con `_render_tree_node`)
  - `_render_hotspots`
  - `_render_deps_summary`
- **Import adicional:** `from autocode.core.code.models import CodeSummaryOutput`

### `tests/unit/core/code/test_architecture.py`
- **Añadir** nueva sección `L) ARCHITECTURE SUMMARY TESTS`
- Tests:
  1. `test_summary_returns_success_with_text` — output básico exitoso
  2. `test_summary_contains_header_with_commit_info` — header con commit+branch
  3. `test_summary_contains_file_metrics` — archivos con MI, CC, SLOC en el texto
  4. `test_summary_contains_hotspots_when_low_mi` — sección hotspots aparece
  5. `test_summary_no_hotspots_when_all_healthy` — no hotspots si todo OK
  6. `test_summary_contains_circular_deps` — sección circulares
  7. `test_summary_show_functions_includes_function_names` — show_functions=True incluye funciones
  8. `test_summary_show_functions_false_omits_functions` — show_functions=False no incluye funciones
  9. `test_summary_depth_limits_tree` — depth limita la profundidad renderizada
  10. `test_summary_error_returns_failure` — error graceful
  11. `test_summary_empty_project` — proyecto sin archivos

---

## 6. Estimación de tokens del output

| Proyecto | show_functions=False | show_functions=True |
|---|---|---|
| Pequeño (10 archivos) | ~400 tokens | ~800 tokens |
| Mediano (50 archivos, como autocode) | ~1.5k tokens | ~4k tokens |
| Grande (200 archivos) | ~5k tokens | ~15k tokens |

Comparado con `get_architecture_snapshot` JSON que fácilmente genera 50k-200k tokens para un proyecto mediano.

---

## 7. Lo que NO cambia

- `get_architecture_snapshot` sigue igual (frontend-only, `interfaces=["api"]`)
- No se modifica ningún modelo existente
- No se modifica el frontend
- Se reutiliza `CodeSummaryOutput` de models.py (ya existe)

---

¿Apruebas este plan? Si es así, toggle a Act mode y lo implemento.
