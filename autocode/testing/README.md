# Code Health Quality Gates

Sistema de quality gates para medir y proteger la salud del código. Se integra con pytest como plugin y con el CLI de autocode como comando standalone.

## Quick Start

```bash
# Instalar
pip install autocode

# Opción A — pytest plugin (zero config)
pytest --autocode-health

# Opción B — CLI standalone (para CI sin pytest)
autocode health-check
autocode health-check --format json   # output JSON para parsear
autocode health-check --strict        # usa defaults estrictos, ignora pyproject.toml
```

---

## Arquitectura

El sistema se compone de **tres capas** con responsabilidades separadas:

```
autocode/
├── core/code/health.py        ← 1. Motor (lógica de negocio pura)
└── testing/
    ├── plugin.py              ← 2. Integración pytest (fixtures, hooks, flag)
    └── gates.py               ← 3. Tests de quality gates (colectados por el plugin)
```

### Capa 1: `core/code/health.py` — Motor

Lógica pura sin dependencia de pytest. Contiene:

- **`HealthConfig`**: dataclass con todos los umbrales de calidad
- **`load_thresholds()`**: lee `[tool.codehealth]` del `pyproject.toml` del proyecto
- **`run_health_check()`**: evalúa todas las quality gates, devuelve `HealthCheckResult`
- **`HealthViolation`** / **`HealthCheckResult`**: modelos de resultado estructurado

Puede usarse de forma independiente en cualquier código Python:

```python
from autocode.core.code.health import HealthConfig, load_thresholds, run_health_check

config = load_thresholds()   # lee pyproject.toml del cwd
result = run_health_check(config, file_metrics)
print(result.passed)         # True / False
print(result.violations)     # lista de HealthViolation
```

### Capa 2: `testing/plugin.py` — Pytest plugin

Registrado automáticamente vía entry-point `pytest11` cuando autocode está instalado. Proporciona:

- **Flag `--autocode-health`**: activa la colección de gates built-in
- **Marker `health`**: para etiquetar tests como quality gates
- **Fixtures de sesión** (disponibles en todos los tests del proyecto):
  - `health_config` → `HealthConfig` leído del `pyproject.toml` del consumidor
  - `all_file_metrics` → `list[FileMetrics]` de todos los archivos trackeados por git
  - `coupling_result` → `tuple(coupling, circulars)` del análisis de dependencias
- **Hook `pytest_terminal_summary`**: tabla resumen al final del run con `--autocode-health`

### Capa 3: `testing/gates.py` — Quality gate tests

Módulo de tests pytest que se colecta automáticamente cuando se pasa `--autocode-health`. Contiene las tres clases de gates:

- **`TestFileHealth`**: gates a nivel de archivo (MI, SLOC, avg CC)
- **`TestFunctionHealth`**: gates a nivel de función (CC, nesting, rank F)
- **`TestProjectHealth`**: gates agregadas del proyecto (avg MI, avg CC, circulares)

Estos tests usan las fixtures del plugin, por lo que funcionan tanto cuando son colectados por el plugin (consumidor) como cuando son re-exportados desde `tests/health/` (desarrollo de autocode).

---

## Configuración: `[tool.codehealth]`

Añade esta sección en el `pyproject.toml` de tu proyecto para personalizar los umbrales. Todos los campos son opcionales — los no especificados usan los defaults estrictos.

```toml
[tool.codehealth]
# Maintainability Index por archivo (0-100, mayor es mejor)
# critical: el test FALLA | warning: aviso visible en output
critical_mi = 20.0          # default: 20.0
warning_mi = 40.0           # default: 40.0

# Cyclomatic Complexity por función
critical_function_cc = 25   # default: 25
warning_function_cc = 15    # default: 15

# Profundidad de anidamiento por función (if dentro de for dentro de while...)
critical_nesting = 8        # default: 8
warning_nesting = 5         # default: 5

# Líneas de código efectivas (SLOC) por archivo
critical_file_sloc = 1000   # default: 1000
warning_file_sloc = 500     # default: 500

# CC media por archivo (promedio de todas sus funciones)
critical_avg_complexity = 15.0   # default: 15.0
warning_avg_complexity = 10.0    # default: 10.0

# CC media del proyecto (promedio de TODAS las funciones)
critical_project_avg_complexity = 10.0   # default: 10.0
warning_project_avg_complexity = 7.0     # default: 7.0

# MI media del proyecto (promedio de todos los archivos)
critical_project_avg_mi = 30.0   # default: 30.0
warning_project_avg_mi = 50.0    # default: 50.0

# Máximo de funciones con rank F (CC > 25) permitidas en el proyecto
max_rank_f_functions = 0    # default: 0

# Máximo de dependencias circulares entre paquetes permitidas
max_circular_deps = 0       # default: 0

# Globs de archivos a excluir del análisis
exclude = []                # default: []
# Ejemplos: ["tests/*", "setup.py", "autocode/web/**/*.js"]
```

### Estrategia recomendada para proyectos con deuda técnica

Los defaults son estrictos (codebase perfecto). Si tu proyecto tiene deuda técnica, **calibra los umbrales con el estado actual** y sube gradualmente:

```toml
[tool.codehealth]
# Estado actual del proyecto (2026-01-01) — subir cada mes
critical_mi = 5.0            # peor archivo actual: legacy.py = 6.2
critical_function_cc = 40    # peor función actual: process_data() = 38
max_rank_f_functions = 3     # estado actual: 3 funciones rank F
max_circular_deps = 1        # dependencia circular conocida: core ↔ interfaces
```

---

## Quality Gates

### A nivel de archivo

| Gate | Qué mide | Viola si |
|------|----------|----------|
| **Maintainability Index (MI)** | Índice compuesto (0-100) de mantenibilidad. Combina Halstead Volume, Cyclomatic Complexity y líneas de código. Mayor = más mantenible. | `MI < critical_mi` (fallo) / `MI < warning_mi` (aviso) |
| **File SLOC** | Source Lines Of Code — líneas de código efectivas (sin contar comentarios ni líneas vacías). | `SLOC > critical_file_sloc` |
| **File Avg CC** | CC media de todas las funciones del archivo. Detecta archivos "difusos" con muchas funciones moderadamente complejas. | `avg_cc > critical_avg_complexity` |

### A nivel de función

| Gate | Qué mide | Viola si |
|------|----------|----------|
| **Function CC** | Cyclomatic Complexity — número de caminos independientes de ejecución. 1 = trivial, 10 = moderado, 25+ = rank F (muy difícil de testear). | `CC > critical_function_cc` |
| **Function Nesting** | Profundidad máxima de anidamiento (if/for/while/try anidados). Nesting > 5 = difícil de leer; > 8 = refactoring urgente. | `nesting > critical_nesting` |
| **Rank F Functions** | Funciones con CC > 25 (rango F en la escala McCabe). No es un umbral por función sino un **presupuesto total** del proyecto. | `count(rank_F) > max_rank_f_functions` |

### A nivel de proyecto (agregadas)

| Gate | Qué mide | Viola si |
|------|----------|----------|
| **Project Avg MI** | MI media de todos los archivos del proyecto. Tendencia general del codebase. | `avg_MI < critical_project_avg_mi` |
| **Project Avg CC** | CC media de todas las funciones del proyecto. Complejidad acumulada. | `avg_CC > critical_project_avg_complexity` |
| **Circular Dependencies** | Ciclos en el grafo de dependencias entre paquetes (A importa B que importa A). Presupuesto total. | `count(circulars) > max_circular_deps` |

### Diferencia entre critical y warning

| Nivel | Efecto en pytest | Efecto en CLI |
|-------|------------------|---------------|
| **critical** | Test **FALLA** (exit code 1) | Exit code 1 |
| **warning** | Test pasa, aviso en output | Aviso en output |

---

## Modos de ejecución

### `pytest --autocode-health` (recomendado para consumidores)

```bash
pytest --autocode-health          # ejecuta todos los gates
pytest --autocode-health -v       # verbose: muestra cada test
pytest --autocode-health -x       # para en el primer fallo
pytest --autocode-health -k "mi"  # filtra gates por nombre
```

Al final del run muestra una tabla resumen:
```
╔══════════════════════════════════════════════════════╗
║            CODE HEALTH QUALITY GATES                 ║
╠══════════════════════════════════════════════════════╣
║  Files analyzed           42                         ║
║  Avg MI                   67.3 ✅                    ║
║  Avg CC                   2.43 ✅                    ║
║  Rank F functions         0 ✅                       ║
║  Circular deps            0 ✅                       ║
╠══════════════════════════════════════════════════════╣
║  ✅  ALL GATES PASSED                                ║
╚══════════════════════════════════════════════════════╝
```

### `autocode health-check` (standalone, para CI sin pytest)

```bash
autocode health-check                          # tabla en terminal
autocode health-check --format json            # JSON para parsear en CI
autocode health-check --strict                 # usa defaults, ignora pyproject.toml
autocode health-check --project-root /path/to  # especificar raíz del proyecto
```

Exit code 0 = todos los gates pasan. Exit code 1 = hay violations críticas.

### `pytest -m health` (desarrollo de autocode)

Cuando desarrollas en el propio repo de autocode, los tests de health están en `tests/health/test_code_health.py` que re-exporta las clases de `autocode/testing/gates.py`. No requiere el flag `--autocode-health`.

---

## Para contribuidores de autocode

### Relación entre tests/health/ y autocode/testing/

```
tests/health/test_code_health.py
    from autocode.testing.gates import TestFileHealth, TestFunctionHealth, TestProjectHealth
    # thin wrapper: re-exporta las clases para que pytest las colecte en dev
```

Esta doble ruta existe para que:
- **Consumidores** usen `pytest --autocode-health` → colecta desde el paquete instalado
- **Desarrolladores de autocode** usen `pytest -m health` → colecta desde `tests/health/`

Ambos caminos ejecutan exactamente el mismo código de gates.

### Añadir un nuevo quality gate

1. **Añadir el check helper** en `autocode/core/code/health.py`:
   ```python
   def _check_mi_variance(config: HealthConfig, file_metrics: list[FileMetrics]) -> list[HealthViolation]:
       """Comprueba la varianza del MI entre archivos (codebase inconsistente)."""
       ...
   ```

2. **Añadir el campo** en `HealthConfig`:
   ```python
   @dataclass
   class HealthConfig:
       ...
       critical_mi_variance: float = 20.0
   ```

3. **Registrar el check** en `run_health_check()`:
   ```python
   violations.extend(_check_mi_variance(config, file_metrics))
   ```

4. **Añadir el test** en `autocode/testing/gates.py`:
   ```python
   @pytest.mark.health
   class TestFileHealth:
       def test_mi_variance(self, all_file_metrics, health_config):
           """La varianza del MI no debe ser excesiva."""
           ...
   ```

### Correr los health tests en desarrollo

```bash
# Health gates del propio proyecto autocode
pytest -m health -v

# Simulando el workflow de un consumidor
pytest --autocode-health -v

# Solo tests unitarios del sistema de health
pytest tests/unit/core/code/test_health.py tests/unit/test_pytest_plugin.py -v
```
