## Análisis del estado actual para release 0.1

He revisado el proyecto completo. Aquí va mi diagnóstico y plan propuesto:

---

### 📊 Estado actual

| Aspecto | Estado | Detalle |
|---------|--------|---------|
| **Python LOC** | ~10,000 | 29 archivos .py en autocode/ |
| **JS LOC** | ~17,400 | 62 archivos .js en web/ |
| **Tests Python** | 523 tests, **2 failing** | `test_serve_command_unified` (host '0.0.0.0' vs '127.0.0.1'), `test_mcp_integration` (mount not called) |
| **Tests JS** | ~17 test HTML files | Tests manuales en navegador, sin runner automatizado |
| **Coverage config** | 80% mínimo | Configurado en pytest.ini |
| **Versión pyproject.toml** | **0.3.0** ⚠️ | Debería ser 0.1.0 para la release |

---

### 🔍 Diagnóstico por área

#### 1. 📚 Documentación
- **README.md está desactualizado**: La arquitectura mostrada referencia módulos que ya no existen (`doc_checker.py`, `test_checker.py`, `git_analyzer.py`, `opencode_executor.py`, `token_counter.py`, `api/server.py`, `orchestration/daemon.py`...). La sección de Features, Quick Start, Architecture, API Reference — todo apunta a una versión anterior del software.
- **DCC bien mantenidos**: autocode.md, core.md, interfaces.md, elements.md son excelentes y actualizados. Faltan DCCs para los módulos nuevos: `planning` y `code`.
- **ARCHITECTURE.md** de interfaces y elements: actualizados y útiles.
- **READMEs** de ai/ y workflow/: el de AI es muy extenso (casi tutorial), podría simplificarse. El de workflow está bien.
- **Falta**: No hay documentación del módulo `code` (metrics, architecture, structure, parsers).

#### 2. 🧪 Tests
- **2 tests fallando**:
  - `test_serve_command_unified`: El test espera `host='127.0.0.1'` pero el código usa `'0.0.0.0'`. Fix simple: alinear test o código.
  - `test_mcp_integration_preserves_api_functionality`: Test espera que `mount` se llame pero la implementación de MCP ya no usa mount. El test está desactualizado respecto al código.
- **521 tests pasando** — buena base.
- **Sin tests para**: módulo `code` completo (solo `test_architecture.py` con 3 tests básicos). Faltan tests de `metrics.py`, `structure.py`, parsers, `reviewer.py`.

#### 3. 🔧 Revisión de código
El código en general está **bien estructurado y limpio**. Observaciones:
- **Helper `_git()` duplicado** en `metrics.py` y `planner.py` — podría extraerse a `vcs/` o `utils/`.
- **`_top_packages_cache`** en metrics.py usa `global` — no es thread-safe.
- **metrics.py** es largo (~400 LOC) pero bien organizado con secciones claras.
- **models.py** del módulo `code` es muy largo (~350 LOC) porque contiene todos los modelos (code structure + metrics + architecture). Podría dividirse pero KISS dice que no es urgente.
- **README del AI module** es demasiado largo (~500 líneas) — más un tutorial que documentación de referencia.

#### 4. 📐 Métricas de código para JS
- Las métricas actuales (`metrics.py`, `architecture.py`) **solo analizan archivos .py**.
- El JS parser existe para estructura pero no calcula CC, MI, nesting, etc.
- Para la 0.1 hay dos opciones:
  - **Opción A**: Extender `_analyze_content` y las métricas para JS (considerable esfuerzo)
  - **Opción B**: Documentar que las métricas son solo Python por ahora y añadir JS en 0.2 (pragmático)
  - **Opción C**: Métricas básicas para JS — LOC/SLOC/functions count (lo que ya se puede extraer del JS parser) sin CC/MI complejos

#### 5. 🤔 ¿Qué hacer con DCC?
Los DCCs son **un diferenciador valioso** del proyecto. Mi recomendación:
- **Mantenerlos**, son excelentes y están bien pensados.
- **Completar los que faltan**: `planning` y `code`.
- **Mantener el README de DCC** que explica el concepto — es buena documentación del propio formato.
- Opcionalmente: mencionar DCC en el README principal como feature del proyecto.

---

### 📋 Plan de acción propuesto para release 0.1

#### Fase 1: Tests verdes ✅
1. Fix `test_serve_command_unified` (host mismatch)
2. Fix `test_mcp_integration_preserves_api_functionality` (mount mock desactualizado)
3. Verificar coverage ≥80%

#### Fase 2: Documentación 📚
4. **Reescribir README.md** — actualizar a la arquitectura real actual
5. Actualizar versión en `pyproject.toml` a `0.1.0`
6. Crear DCC para `planning` module
7. Crear DCC para `code` module  
8. Simplificar README del AI module (de tutorial a referencia concisa)

#### Fase 3: Limpieza de código 🧹
9. Extraer `_git()` helper duplicado a un lugar compartido
10. Revisar archivo por archivo — eliminar dead code, mejorar docstrings, KISS
11. Limpiar el global `_top_packages_cache` en metrics.py

#### Fase 4: Métricas JS 📊
12. Decidir alcance (Opción A/B/C) e implementar
13. Asegurar que quality gates en pytest.ini se cumplen

#### Fase 5: Release 🚀
14. Tag 0.1.0 + CHANGELOG básico

---



# 📊 Análisis Completo del Sistema de Métricas de Código

## 1. Visión General de la Arquitectura

El sistema de métricas tiene **3 capas** claramente separadas:

```
┌─────────────────────────────────────────────────────────────────────┐
│                        FRONTEND (LitElement + D3.js)                │
│                                                                     │
│  ┌─────────────────┐  ┌──────────────┐  ┌───────────────────────┐  │
│  │ architecture/    │  │ git-graph/   │  │ code-explorer/        │  │
│  │  index.js        │  │  metrics-    │  │  index.js             │  │
│  │  (5 tabs:        │  │  dashboard   │  │  code-metrics.js      │  │
│  │  files,code,     │  │  metrics-    │  │  (barra resumen)      │  │
│  │  treemap,deps,   │  │  chart       │  │                       │  │
│  │  metrics)        │  │              │  │                       │  │
│  │  treemap.js      │  │              │  │                       │  │
│  │  graph.js        │  │              │  │                       │  │
│  └────────┬─────────┘  └──────┬───────┘  └───────────┬───────────┘  │
│           │                   │                      │              │
│  ─────────┴───────────────────┴──────────────────────┴──────────    │
│        AutoFunctionController.executeFunction(name, params)         │
│        → fetch(`/${funcName}`) → JSON                               │
│                  (auto-element-generator.js)                        │
└──────────────────────────────┬──────────────────────────────────────┘
                               │ HTTP (GET/POST)
┌──────────────────────────────┴──────────────────────────────────────┐
│                      INTERFACES (FastAPI)                           │
│                                                                     │
│  registry.py: @register_function(http_methods, interfaces)          │
│  api.py: crea endpoints dinámicos desde registry                    │
│  models.py: GenericOutput, FunctionInfo, ParamSchema                │
└──────────────────────────────┬──────────────────────────────────────┘
                               │ function call
┌──────────────────────────────┴──────────────────────────────────────┐
│                    CORE: autocode/core/code/                        │
│                                                                     │
│  ┌─────────────┐  ┌──────────────┐  ┌───────────────────────────┐  │
│  │ metrics.py   │  │architecture.py│  │ structure.py             │  │
│  │ (4 endpoints)│  │(1 endpoint)   │  │ (2 endpoints)            │  │
│  └──────┬───────┘  └──────┬────────┘  └──────────┬───────────────┘  │
│         │                 │                      │                  │
│  ┌──────┴─────────────────┴──────────────────────┴───────────────┐  │
│  │                    models.py (~350 LOC)                        │  │
│  │  CodeNode, CodeGraph, CodeStructureResult                     │  │
│  │  FunctionMetrics, FileMetrics, PackageCoupling                │  │
│  │  MetricsSnapshot, MetricsComparison, MetricsHistory           │  │
│  │  ArchitectureNode, ArchitectureSnapshot, FileDependency       │  │
│  └───────────────────────────────────────────────────────────────┘  │
│                                                                     │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │              parsers/ (strategy pattern)                       │  │
│  │  base.py → BaseParser (ABC: parse_flat() → List[CodeNode])    │  │
│  │  python_parser.py → PythonParser (ast)                        │  │
│  │  js_parser.py → JSParser (regex)                              │  │
│  │  __init__.py → get_parser(ext) → PARSERS registry             │  │
│  └───────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 2. Los 7 Endpoints Registrados

| Endpoint | Módulo | HTTP | Interfaces | Qué devuelve |
|----------|--------|------|------------|---------------|
| `generate_code_metrics` | metrics.py | GET | api, mcp | `MetricsSnapshotOutput` → MetricsComparison (snapshot actual + deltas vs anterior) |
| `get_metrics_snapshots` | metrics.py | GET | api, mcp | Lista de snapshots guardados (resumen) |
| `get_commit_metrics` | metrics.py | GET | api, mcp | `CommitMetricsOutput` → before/after de archivos cambiados en un commit |
| `get_metrics_history` | metrics.py | GET | api, mcp | `MetricsHistoryOutput` → serie temporal para gráficas |
| `get_architecture_snapshot` | architecture.py | GET | api (no mcp) | `ArchitectureSnapshotOutput` → jerarquía + dependencias |
| `get_code_structure` | structure.py | GET | api (no mcp) | `CodeStructureOutput` → grafo de nodos de código |
| `get_code_summary` | structure.py | GET | api, mcp | `CodeSummaryOutput` → texto plano tipo tree (para LLMs) |

---

## 3. Flujo de Datos Detallado

### 3.1 metrics.py — Análisis de complejidad

```
generate_code_metrics()
  ├── _get_tracked_py_files()          → git ls-files *.py
  ├── Para cada archivo:
  │     └── _analyze_content(content, path)   ← SOLO PYTHON (ast.parse)
  │           ├── _count_line_types()          → SLOC, comments, blanks
  │           ├── _extract_function_metrics()   → CC, nesting por función
  │           │     ├── _cyclomatic_complexity() → 1 + decision points
  │           │     ├── _nesting_depth()         → max profundidad control flow
  │           │     └── _cc_rank()               → A-F (≤5=A, >25=F)
  │           └── _maintainability_index()      → MI = f(HV, CC, LOC)
  │                                               (simplified SEI formula)
  ├── Aggregates (avg_cc, avg_mi, distribution)
  ├── _analyze_coupling()              → Ce/Ca/Instability por paquete
  │     └── Detecta circular deps
  ├── _save_snapshot()                 → .autocode/metrics/{short_hash}.json
  └── _compare_snapshots()             → deltas vs snapshot anterior
```

**Punto clave**: `_analyze_content()` usa `ast.parse()` → **solo Python**. No hay equivalente para JS.

**Fórmulas:**
- **CC** = 1 + (if + elif + for + while + except + with + assert) + (and/or contribuyen len-1) + (comprehension ifs+1)
- **MI** = max(0, (171 - 5.2·ln(HV) - 0.23·CC - 16.2·ln(LOC)) × 100/171) donde HV ≈ SLOC × log2(SLOC)
- **Instability** = Ce / (Ce + Ca)

### 3.2 architecture.py — Jerarquía + dependencias

```
get_architecture_snapshot()
  ├── _build_architecture_nodes(py_files)    ← reutiliza _analyze_content de metrics.py
  │     └── Crea ArchitectureNode por directorio + archivo (con MI, CC, LOC)
  ├── _propagate_metrics(nodes, root)        ← bottom-up LOC-weighted averages
  ├── _resolve_file_dependencies(py_files)   ← AST: import/from resolution
  │     ├── _build_module_to_file_map()       → dotted name → file path
  │     ├── _is_internal_module()             → filtra stdlib/third-party
  │     └── Detección circular (A→B y B→A)
  └── Retorna ArchitectureSnapshot con nodes + deps + circulars
```

**Punto clave**: Importa `_analyze_content`, `_get_tracked_py_files`, `_git` directamente de metrics.py.

### 3.3 structure.py — Estructura de código

```
get_code_structure()
  ├── get_git_tree()                   → archivos trackeados
  ├── Filtra por extensión: .py, .js, .mjs, .jsx
  ├── Para cada archivo:
  │     └── get_parser(ext).parse_flat()   ← SÍ soporta Python + JS
  │           ├── PythonParser → ast → CodeNode(class/function/method/import)
  │           └── JSParser → regex → CodeNode(class/function/method/import)
  └── Retorna CodeGraph (adjacency list)
```

**Punto clave**: `structure.py` YA parsea JS vía JSParser, pero solo extrae estructura (nombres, líneas), NO calcula CC/MI/nesting.

---

## 4. Frontend — Quién consume qué

### 4.1 `<architecture-dashboard>` (architecture/index.js)
- **5 tabs**: Files, Code, Treemap, Dependencies, Metrics
- **Llama a**: `get_architecture_snapshot` → summary cards (MI, CC, SLOC, archivos)
- **Tab Treemap** → `<architecture-treemap>` (D3 treemap): rectángulos ∝ SLOC, color = MI
- **Tab Dependencies** → `<architecture-graph>` (D3 force): nodos = archivos, links = imports
- **Tab Metrics** → `<metrics-dashboard hide-summary>` (embebido, sin summary cards duplicadas)
- **Tab Files** → `<file-explorer>` (su propia carga)
- **Tab Code** → `<code-explorer>` (su propia carga)

### 4.2 `<metrics-dashboard>` (git-graph/metrics-dashboard.js)
- **Llama a**: `generate_code_metrics`
- **Muestra**: Summary cards (SLOC, archivos, funciones, clases, CC media, MI media) con deltas
- **Embeds**: `<metrics-chart>` para evolución temporal
- **Tablas**: Top funciones complejas, Peor MI, Acoplamiento

### 4.3 `<metrics-chart>` (git-graph/metrics-chart.js)
- **Llama a**: `get_metrics_history`
- **Muestra**: Multi-line chart D3 con métricas toggleables (SLOC, CC, MI, ranks, etc.)
- **Interacción**: Toggle métricas, hover tooltip, auto-resize

### 4.4 `<code-explorer>` (code-explorer/index.js)
- **Llama a**: `get_code_structure`
- **Muestra**: Árbol de código (Python + JS) con `<code-metrics>` (barra resumen: archivos, LOC, funciones, clases, lenguajes)

### 4.5 `<code-metrics>` (code-explorer/code-metrics.js)
- **No llama a API** — recibe props de `<code-explorer>`
- **Muestra**: Badges de lenguaje (🐍 python, 🟨 javascript), conteos

---

## 5. Modelos de Datos — Mapa completo

```
GenericOutput (base)
  ├── CodeStructureOutput     → result: CodeStructureResult → CodeGraph → [CodeNode]
  ├── CodeSummaryOutput       → result: str (texto plano)
  ├── MetricsSnapshotOutput   → result: MetricsComparison
  │     ├── before: MetricsSnapshot?
  │     └── after: MetricsSnapshot
  │           ├── files: [FileMetrics]
  │           │     └── functions: [FunctionMetrics]
  │           ├── coupling: [PackageCoupling]
  │           └── circular_deps: [[str]]
  ├── MetricsSnapshotListOutput → result: [dict]
  ├── CommitMetricsOutput     → result: CommitMetrics → [CommitFileMetrics]
  ├── MetricsHistoryOutput    → result: MetricsHistory → [MetricsHistoryPoint]
  └── ArchitectureSnapshotOutput → result: ArchitectureSnapshot
        ├── nodes: [ArchitectureNode]
        ├── dependencies: [FileDependency]
        └── circular_dependencies: [[str]]
```

**FileMetrics.language** es `Literal["python", "javascript"]` — ya preparado para JS.

---

## 6. Lo que SOLO funciona con Python vs lo que ya soporta JS

| Componente | Python | JavaScript | Notas |
|-----------|--------|------------|-------|
| **structure.py** / parsers | ✅ PythonParser (ast) | ✅ JSParser (regex) | Ambos devuelven CodeNode con estructura |
| **metrics.py** / `_analyze_content` | ✅ ast.parse → CC, MI, nesting | ❌ No existe equivalente | **Este es el gap** |
| **metrics.py** / `_get_tracked_py_files` | ✅ `git ls-files *.py` | ❌ Solo .py | Fácil de extender |
| **metrics.py** / coupling analysis | ✅ ast imports | ❌ No analiza imports JS | JSParser ya extrae imports |
| **architecture.py** | ✅ Usa _analyze_content | ❌ Solo .py | Hereda la limitación |
| **Frontend treemap/graph** | ✅ Muestra métricas | 🟡 Preparado | Los modelos tienen `language` field |
| **Frontend code-explorer** | ✅ Estructura | ✅ Estructura | Ya muestra archivos JS |
| **Frontend metrics-dashboard** | ✅ Dashboard completo | 🟡 Mostraría JS si hubiera datos | Solo necesita datos del backend |

---

## 7. Patrones de diseño identificados

1. **Strategy Pattern** (parsers): `BaseParser` → `PythonParser` / `JSParser`, registry por extensión
2. **Registry Pattern** (interfaces): `@register_function` → auto-discovery → dynamic FastAPI endpoints
3. **Adjacency List** (models): Todos los grafos usan `parent_id` en vez de children anidados (evita recursión en OpenAPI)
4. **Snapshot Pattern** (metrics): Persistencia en `.autocode/metrics/` → comparación temporal
5. **Controller Pattern** (frontend): `AutoFunctionController` desacopla lógica de UI

---

## 8. Gap Analysis para integración de lizard

### Lo que lizard nos da:
- `lizard.analyze_file("file.js")` → para cada función: `name`, `nloc` (SLOC), `cyclomatic_complexity`, `token_count`, `length`, `start_line`, `end_line`, `top_nesting_level`, `parameter_count`
- También analiza Python (podríamos unificar, pero KISS dice mantener ast para Python por ahora porque ya funciona y tiene coupling)

### Puntos de integración:

**A) `metrics.py` — Crear `_analyze_js_content(content, path) → FileMetrics`**
- Usar lizard para CC, nesting, SLOC per function
- Calcular MI con la misma fórmula `_maintainability_index(sloc, avg_cc, total_loc)` que ya existe
- Contar comments/blanks con heurística simple (// y /* */) ya que lizard no da eso directamente

**B) `metrics.py` — Ampliar `_get_tracked_py_files()` → `_get_tracked_files()`**
- Añadir `git ls-files *.js *.mjs *.jsx` 
- O mejor: `_get_tracked_files(extensions=[".py", ".js", ".mjs", ".jsx"])`

**C) `metrics.py` — Router en `_build_current_snapshot()`**
- Para cada archivo: if `.py` → `_analyze_content()`, if `.js` → `_analyze_js_content()`
- O unificar en un dispatcher

**D) `architecture.py` — Incluir archivos JS en el snapshot**
- Cambiar `_get_tracked_py_files()` → incluir JS
- El análisis de dependencias JS podría reutilizar los imports que JSParser ya extrae

**E) Coupling para JS** — Decisión:
- **Opción simple**: No analizar coupling de JS por ahora (solo CC/MI/nesting)
- **Opción extendida**: Reutilizar JSParser para extraer imports y analizar coupling similar

### Lo que NO necesita cambios:
- **Frontend**: Ya preparado. `FileMetrics.language` acepta "javascript". Los dashboards renderizan lo que el backend envíe.
- **Models**: `FileMetrics` ya tiene `language: Optional[Language]` con `Language = Literal["python", "javascript"]`
- **Registry/API/Interfaces**: Nada que cambiar, los endpoints son los mismos
- **Parsers**: JSParser seguiría siendo para estructura (CodeNode), lizard sería para métricas (FileMetrics)

---

## 9. Resumen de archivos involucrados

### Backend (necesitan cambios para JS):
| Archivo | LOC | Cambio necesario |
|---------|-----|-----------------|
| `autocode/core/code/metrics.py` | ~400 | Añadir `_analyze_js_content()`, ampliar `_get_tracked_files()` |
| `autocode/core/code/architecture.py` | ~290 | Incluir archivos JS en snapshot |
| `pyproject.toml` | - | Añadir `lizard` a dependencies |

### Backend (sin cambios):
| Archivo | LOC | Por qué no cambia |
|---------|-----|-------------------|
| `autocode/core/code/models.py` | ~350 | Ya preparado (Language incluye "javascript") |
| `autocode/core/code/structure.py` | ~300 | Ya parsea JS vía JSParser |
| `autocode/core/code/parsers/*` | ~400 | JSParser sigue para estructura, lizard para métricas |
| `autocode/interfaces/*` | ~400 | Endpoints no cambian |

### Frontend (sin cambios):
| Archivo | LOC | Por qué no cambia |
|---------|-----|-------------------|
| `architecture/index.js` | ~350 | Renderiza lo que el backend envíe |
| `architecture/architecture-treemap.js` | ~280 | Usa SLOC/MI del nodo, agnóstico al lenguaje |
| `architecture/architecture-graph.js` | ~440 | Usa deps del snapshot, agnóstico |
| `git-graph/metrics-dashboard.js` | ~220 | Consume MetricsComparison, agnóstico |
| `git-graph/metrics-chart.js` | ~310 | Consume MetricsHistory, agnóstico |
| `code-explorer/code-metrics.js` | ~70 | Ya muestra badges de lenguaje JS |

---


Genial, con las métricas reales del proyecto y toda la lectura del código ya tengo un análisis completo. Vamos punto por punto:

---

## 1. 🎨 Frontend: Diagnóstico y Nuevo Diseño

### El problema actual

```
index.html
  └── <git-graph>              ← Actúa como APP SHELL (no debería)
        ├── commit-list (left)
        └── detail-panel (right)
              ├── <commit-detail>
              └── <architecture-dashboard>  ← Toggle con botón 🗂️
                    ├── 📁 Files → <file-explorer>
                    ├── 🧬 Code → <code-explorer>
                    ├── 🗺️ Treemap
                    ├── 🔗 Dependencies
                    └── 📊 Metrics → <metrics-dashboard>  ← ¡Vive en git-graph/!
```

**Problemas concretos:**
1. **`<git-graph>` es el app shell** — mezcla responsabilidad de "vista principal de la app" con "visualizador de commits". Todo se anida dentro de git-graph.
2. **`<metrics-dashboard>` vive en `git-graph/`** pero se usa en `architecture/`. La carpeta no refleja la realidad.
3. **`<architecture-dashboard>` es un nombre mentiroso** — Files y Code no son "arquitectura". Es realmente un "Code Dashboard".
4. **Summary cards duplicadas** — architecture-dashboard muestra MI/CC/SLOC de `get_architecture_snapshot`, y metrics-dashboard muestra los mismos datos de `generate_code_metrics`. De ahí el hack `hide-summary`.
5. **Dos endpoints calculan lo mismo** — `get_architecture_snapshot` calcula MI/CC/SLOC y `generate_code_metrics` también. Son dos pasadas sobre los mismos archivos.

### Diseño propuesto

```
index.html
  ├── navbar (como está)
  ├── <git-graph>              ← Solo commits, ya no es app shell
  │     ├── commit-list
  │     └── commit-detail / plan-detail
  └── <code-dashboard>         ← Componente principal independiente
        ├── Summary cards (una sola fuente de datos)
        ├── 📁 Files → <file-explorer>
        ├── 🧬 Code → <code-explorer>  
        ├── 🗺️ Treemap → <treemap-view>
        ├── 🔗 Dependencies → <dependency-graph>
        └── 📊 Metrics → <metrics-panel>
                           └── <metrics-chart>
```

**Layout de la página:** Split horizontal — git-graph a la izquierda (colapsable), code-dashboard a la derecha. O tabs de nivel superior (🌳 Git | 📊 Code). Esto es una decisión de UX que podemos decidir.

**Reorganización de carpetas:**
```
elements/
  ├── git-graph/           ← Solo git: commits, plans, graph layout
  │     ├── index.js       (limpio, ya no es app shell)
  │     ├── commit-node.js
  │     ├── commit-detail.js
  │     ├── commit-plan-node.js
  │     └── commit-plan-detail.js
  ├── dashboard/           ← Nuevo: el código dashboard
  │     ├── index.js       (tabs + summary cards)
  │     ├── treemap-view.js
  │     ├── dependency-graph.js
  │     ├── metrics-panel.js
  │     └── metrics-chart.js
  ├── file-explorer/       (sin cambios)
  ├── code-explorer/       (sin cambios)
  └── chat/                (sin cambios)
```

---

## 2. 🧬 GenericOutput: Análisis de tradeoffs

```python
# Patrón actual
class GenericOutput(BaseModel):
    result: Any = Field(...)
    success: bool = True
    message: str | None = None

class ArchitectureSnapshotOutput(GenericOutput):
    result: Optional[ArchitectureSnapshot] = None  # ← Solo cambia el tipo
```

### Hay **dos usos distintos** del patrón:

**A) Type-narrowing puro (boilerplate)** — `code/models.py`, `planning/models.py`:
```python
class MetricsSnapshotOutput(GenericOutput):
    result: Optional[MetricsComparison] = None  # 3 líneas, 0 comportamiento nuevo

class CommitPlanOutput(GenericOutput):
    result: Optional[CommitPlan] = None  # idem
```
Son ~10 clases que solo cambian el tipo de `result`. No añaden nada más.

**B) Extensión real** — `ai/models.py DspyOutput`:
```python
class DspyOutput(GenericOutput):
    result: Any = ...
    reasoning: Optional[str] = None      # ← Campo nuevo
    completions: Optional[List[str]] = None  # ← Campo nuevo
    trajectory: ...                      # ← Campo nuevo
    history: ...                         # ← Campo nuevo
```
Esto SÍ justifica herencia — añade campos y comportamiento (serialize_value, normalize_trajectory).

### Mi veredicto: **El patrón está bien, pero se puede simplificar**

**Opción A (conservadora, KISS):** Dejarlo como está. Son 3 líneas por output, funciona con FastAPI/OpenAPI, es explícito. El overhead es bajo.

**Opción B (limpiar):** Usar `Generic[T]` para los wrappers puros, mantener herencia para los extendidos:
```python
from typing import Generic, TypeVar
T = TypeVar('T')

class Output(BaseModel, Generic[T]):
    result: T | None = None
    success: bool = True
    message: str | None = None

# Uso directo — elimina 10 clases wrapper:
def get_architecture_snapshot() -> Output[ArchitectureSnapshot]: ...
def generate_code_metrics() -> Output[MetricsComparison]: ...

# DspyOutput sigue heredando porque AÑADE campos:
class DspyOutput(Output[Any]):
    reasoning: Optional[str] = None
    ...
```

**Riesgo:** Pydantic v2 soporta Generic bien, pero hay que verificar que FastAPI genere el OpenAPI schema correcto con `Output[ArchitectureSnapshot]`. En mi experiencia funciona, pero hay edge cases.

**Mi recomendación:** Opción A por ahora (KISS), y si en el futuro el boilerplate molesta, migrar a Generic[T]. No es un problema urgente.

---

## 3. 🔧 Backend: Diagnóstico basado en métricas reales

### Los datos nos dicen esto:

| Archivo | MI | Avg CC | SLOC | Problema principal |
|---------|-----|--------|------|-------------------|
| `metrics.py` | 13.5 | 6.67 | 546 | Hace demasiado: análisis + coupling + snapshots + comparación + commit analysis |
| `executor.py` | 14.0 | 7.92 | 520 | `stream_execute_plan` CC=21 |
| `planner.py` | 19.4 | 5.92 | 349 | `update_commit_plan` CC=21 |
| `log.py` | 20.7 | 6.78 | 313 | Funciones complejas |
| `dspy_utils.py` | 21.4 | 6.64 | 297 | `generate_with_dspy` CC=32 (¡Rank F!) |
| `structure.py` | 22.5 | 10.43 | 264 | Avg CC más alto del proyecto |

**Funciones F-rank (CC>25):**
- `generate_with_dspy` CC=32 — God function
- `stream_chat` CC=26
- `_analyze_coupling` CC=26
- (+ un test CC=28 que no cuenta)

**Dependencia circular:** `autocode.core ↔ autocode.interfaces` — architecture.py importa `_analyze_content` de metrics.py que importa de registry.py

### ¿Puede lizard unificarlo todo?

| Lo que lizard da | Lo que NO da |
|---|---|
| ✅ CC por función (Python + JS + TS) | ❌ Maintainability Index |
| ✅ SLOC por función | ❌ Coupling (Ce/Ca/Instability) |
| ✅ Nesting depth | ❌ Import resolution |
| ✅ Token count, parameter count | ❌ Circular dependency detection |
| ✅ Multi-lenguaje automático | ❌ Comment/blank counts |
| | ❌ Class detection |

**Conclusión: Lizard reemplaza `_cyclomatic_complexity()` + `_nesting_depth()` + `_extract_function_metrics()` pero NO reemplaza coupling/deps/MI.** La estrategia correcta es:

1. **Lizard como motor de CC/nesting** — reemplaza nuestro AST custom para CC. Inmediatamente gana soporte JS.
2. **Mantener AST para coupling** — lizard no puede hacer análisis de imports.
3. **Calcular MI nosotros** — con los datos que lizard nos da (CC + SLOC) aplicamos nuestra fórmula.

### Plan de refactoring backend

**Prioridad 1 — Quick wins:**
- [ ] Extraer `_git()` a `autocode/core/vcs/utils.py` (duplicado en metrics.py y planner.py)
- [ ] Limpiar `_top_packages_cache` global → parámetro o `@lru_cache`
- [ ] Integrar lizard para CC/nesting (reemplaza `_cyclomatic_complexity`, `_nesting_depth`, `_extract_function_metrics`)
- [ ] Con lizard, meter JS en `_build_current_snapshot()` automáticamente

**Prioridad 2 — Splits (si metrics.py crece más):**
- [ ] Extraer coupling analysis de metrics.py → `coupling.py` (~80 LOC)
- [ ] Extraer snapshot persistence → `snapshots.py` (~80 LOC)
- [ ] Esto dejaría metrics.py en ~350 LOC más manejable

**Prioridad 3 — Reducir CC de funciones F-rank:**
- [ ] `generate_with_dspy` (CC=32) — Splitear en subfunciones
- [ ] `stream_chat` (CC=26) — Splitear
- [ ] `_analyze_coupling` (CC=26) — Extraer inner loops

---

## Resumen: ¿Qué haríamos y en qué orden?

1. **Backend primero** — Integrar lizard, extraer `_git()`, limpiar metrics.py. Esto da soporte JS como efecto secundario.
2. **Frontend después** — Reorganizar componentes: sacar git-graph como app shell, crear code-dashboard limpio, mover metrics donde toca.
3. **GenericOutput** — Dejarlo como está (KISS). No merece la pena refactorizar ahora.