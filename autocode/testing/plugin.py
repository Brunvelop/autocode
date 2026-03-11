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
    """Registra el marker 'health' y, si --autocode-health está activo, añade las gates."""
    config.addinivalue_line(
        "markers",
        "health: Code health quality gate tests (run with --autocode-health or -m health)",
    )

    # Cuando --autocode-health está activo, inyectamos la ruta de gates.py
    # en los args de colección para que pytest la encuentre y llame a pytest_collect_file.
    # Usamos try/except porque pytest_configure puede llamarse antes de parsear opciones
    # (por ejemplo durante el discovery de plugins en etapa temprana).
    try:
        if config.getoption("autocode_health"):
            gates_path = Path(__file__).parent / "gates.py"
            if gates_path.exists():
                gates_str = str(gates_path)
                if gates_str not in (config.args or []):
                    config.args = list(config.args or []) + [gates_str]
    except (ValueError, AttributeError):
        # Opción no registrada aún (llamada early) — se procesa en pytest_collection_start
        pass


# ==============================================================================
# FILE COLLECTION (para --autocode-health)
# ==============================================================================


def pytest_collect_file(parent, file_path):
    """Cuando --autocode-health está activo, colecta el módulo de built-in gates.

    Este hook actúa como "gatekeeper": solo devuelve el módulo si el archivo
    es exactamente gates.py del paquete. El resto de archivos se ignoran.
    """
    if not parent.config.getoption("autocode_health", default=False):
        return None

    gates_path = Path(__file__).parent / "gates.py"
    if not gates_path.exists():
        return None

    if file_path == gates_path:
        return pytest.Module.from_parent(parent, path=file_path)

    return None


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
