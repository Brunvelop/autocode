"""
Autocode pytest plugin — Code Health Quality Gates.

Auto-registered via pytest11 entry-point when autocode is installed.

Usage (consumer project):
    pytest --autocode-health          # Run built-in quality gates
    pytest --autocode-health -v       # Verbose output
    pytest -m health                  # Run only health-marked tests

Configuration (consumer's pyproject.toml):
    [tool.codehealth]
    critical_mi = 10.0
    warning_mi = 30.0
    # ... see HealthConfig for all options

How it works:
    - Registers --autocode-health CLI flag
    - Registers 'health' marker
    - Provides session-scoped fixtures: health_config, all_file_metrics, coupling_result
    - When --autocode-health is active: collects built-in gate tests from gates.py
    - Prints a summary table at the end of the run (only when --autocode-health active)
"""
from __future__ import annotations

from pathlib import Path
from typing import Optional

import pytest

from autocode.core.code.analyzer import analyze_file_metrics
from autocode.core.code.coupling import analyze_coupling
from autocode.core.code.health import HealthConfig, load_thresholds
from autocode.core.code.models import FileMetrics, PackageCoupling
from autocode.core.vcs.git import get_tracked_files

_ALL_EXTENSIONS = (".py", ".js", ".mjs", ".jsx")

# Almacén de datos para el hook terminal (poblado por los fixtures del plugin)
_plugin_health_summary: dict = {}


# ==============================================================================
# OPTION + MARKER REGISTRATION
# ==============================================================================


def pytest_addoption(parser):
    """Registra el flag --autocode-health en el CLI de pytest."""
    group = parser.getgroup("autocode", "Autocode health quality gates")
    group.addoption(
        "--autocode-health",
        action="store_true",
        default=False,
        help=(
            "Run autocode code health quality gates against the project. "
            "Reads thresholds from [tool.codehealth] in pyproject.toml."
        ),
    )


def pytest_configure(config):
    """Registra el marker 'health'."""
    config.addinivalue_line(
        "markers",
        "health: Code health quality gate tests (run with --autocode-health or -m health)",
    )


def _collect_items_recursive(collector) -> list:
    """Recorre el árbol de collectors y extrae los test Items hoja."""
    items = []
    for thing in collector.collect():
        if isinstance(thing, pytest.Item):
            items.append(thing)
        elif hasattr(thing, "collect"):
            items.extend(_collect_items_recursive(thing))
    return items


def pytest_collection_modifyitems(session, config, items):
    """Inyecta los tests de gates.py después de la colección normal.

    Se usa este hook —en lugar de modificar config.args en pytest_configure—
    porque pytest 9.x excluye los paths dentro de .venv/ vía norecursedirs
    aunque estén añadidos explícitamente a config.args. Al construir el Module
    directamente aquí, ese filtro no aplica y los items se añaden al resultado
    final de colección independientemente de dónde viva el archivo instalado.

    Si los tests ya están presentes (p.ej. el consumidor creó su propio
    tests/test_health.py re-exportando las clases de gates.py), no se duplican.
    """
    if not config.getoption("autocode_health", default=False):
        return

    gates_path = Path(__file__).parent / "gates.py"
    if not gates_path.exists():
        return

    gates_str = str(gates_path)

    # Evitar duplicados: si ya hay items de gates.py (p.ej. via tests/test_health.py
    # que re-exporta las clases), no añadir de nuevo.
    if any(gates_str in str(getattr(item, "path", "")) for item in items):
        return

    module = pytest.Module.from_parent(session, path=gates_path)
    items.extend(_collect_items_recursive(module))


# ==============================================================================
# SESSION-SCOPED FIXTURES
# ==============================================================================


@pytest.fixture(scope="session")
def health_config(request) -> HealthConfig:
    """Carga los umbrales de [tool.codehealth] del pyproject.toml del proyecto.

    Lee desde el directorio donde se ejecuta pytest (Path.cwd()),
    que para consumidores será la raíz de su propio proyecto.
    """
    return load_thresholds(project_root=Path.cwd())


@pytest.fixture(scope="session")
def all_file_metrics(health_config: HealthConfig) -> list[FileMetrics]:
    """Analiza TODOS los archivos trackeados por git una sola vez por sesión.

    Excluye los archivos que coincidan con los globs en health_config.exclude.
    Popula el summary interno del plugin para el hook terminal.

    Returns:
        Lista de FileMetrics de todos los archivos analizados.
    """
    global _plugin_health_summary

    files = get_tracked_files(*_ALL_EXTENSIONS)
    results: list[FileMetrics] = []

    for fpath in files:
        if any(Path(fpath).match(pattern) for pattern in health_config.exclude):
            continue
        try:
            content = Path(fpath).read_text(encoding="utf-8")
            fm = analyze_file_metrics(fpath, content)
            results.append(fm)
        except Exception:
            pass

    # Calcular agregados para el resumen terminal
    if results:
        all_funcs = [f for fm in results for f in fm.functions]
        avg_mi = sum(fm.maintainability_index for fm in results) / len(results)
        avg_cc = sum(f.complexity for f in all_funcs) / len(all_funcs) if all_funcs else 0.0
        rank_f_count = sum(1 for f in all_funcs if f.rank == "F")

        mi_icon = "✅" if avg_mi >= health_config.warning_project_avg_mi else "⚠️"
        cc_icon = "✅" if avg_cc <= health_config.warning_project_avg_complexity else "⚠️"
        rf_icon = "✅" if rank_f_count == 0 else "❌"

        _plugin_health_summary["Files analyzed"] = f"{len(results)}"
        _plugin_health_summary["Avg MI"] = f"{avg_mi:.1f} {mi_icon}"
        _plugin_health_summary["Avg CC"] = f"{avg_cc:.2f} {cc_icon}"
        _plugin_health_summary["Rank F functions"] = f"{rank_f_count} {rf_icon}"

    return results


@pytest.fixture(scope="session")
def coupling_result(
    health_config: HealthConfig,
) -> tuple[list[PackageCoupling], list[list[str]]]:
    """Analiza el acoplamiento entre paquetes una sola vez por sesión.

    Returns:
        Tupla (coupling, circulars) donde:
        - coupling: list[PackageCoupling] — dependencias entre paquetes
        - circulars: list[list[str]] — ciclos detectados
    """
    global _plugin_health_summary

    files = get_tracked_files(*_ALL_EXTENSIONS)
    filtered = [
        f for f in files
        if not any(Path(f).match(p) for p in health_config.exclude)
    ]
    coupling, circulars = analyze_coupling(filtered)

    circ_icon = "✅" if len(circulars) <= health_config.max_circular_deps else "❌"
    _plugin_health_summary["Circular deps"] = f"{len(circulars)} {circ_icon}"

    return coupling, circulars


# ==============================================================================
# TERMINAL SUMMARY HOOK
# ==============================================================================


def pytest_terminal_summary(terminalreporter, exitstatus, config):
    """Imprime tabla resumen de code health al final del run.

    Solo se activa cuando --autocode-health fue pasado explícitamente,
    evitando conflicto con el hook de tests/health/conftest.py cuando
    se ejecuta pytest -m health directamente.
    """
    if not config.getoption("autocode_health", default=False):
        return

    if not _plugin_health_summary:
        return

    passed = exitstatus == 0
    overall = "✅  ALL GATES PASSED" if passed else "❌  GATES FAILED"

    width = 54
    separator = "═" * width
    terminalreporter.write_sep("-", "Code Health Summary")
    terminalreporter.write_line(f"╔{separator}╗")
    terminalreporter.write_line(f"║{'  CODE HEALTH QUALITY GATES':^{width}}║")
    terminalreporter.write_line(f"╠{separator}╣")

    for key, value in _plugin_health_summary.items():
        content = f"  {key:<26} {value}"
        terminalreporter.write_line(f"║{content:<{width}}║")

    terminalreporter.write_line(f"╠{separator}╣")
    terminalreporter.write_line(f"║{'  ' + overall:<{width}}║")
    terminalreporter.write_line(f"╚{separator}╝")
