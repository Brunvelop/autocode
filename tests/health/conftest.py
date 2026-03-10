"""
conftest.py — Infraestructura para Code Health Quality Gates.

Proporciona:
- HealthConfig: dataclass con umbrales leídos de [tool.codehealth] en pyproject.toml
- Fixtures session-scoped: all_file_metrics, coupling_result, health_config
- Hook pytest_terminal_summary: tabla resumen al final del test run
"""
from __future__ import annotations

import tomllib
from dataclasses import dataclass, field
from pathlib import Path

import pytest

from autocode.core.code.analyzer import analyze_file_metrics
from autocode.core.code.coupling import analyze_coupling
from autocode.core.code.models import FileMetrics, PackageCoupling
from autocode.core.vcs.git import get_tracked_files

_ALL_EXTENSIONS = (".py", ".js", ".mjs", ".jsx")

# Almacén de datos para el hook terminal (poblado por los fixtures)
_health_summary: dict = {}


# ==============================================================================
# CONFIG
# ==============================================================================


@dataclass
class HealthConfig:
    """Umbrales de calidad de código leídos de [tool.codehealth] en pyproject.toml."""

    # Maintainability Index (0-100, mayor es mejor)
    critical_mi: float = 20.0
    warning_mi: float = 40.0
    # CC por función
    critical_function_cc: int = 25
    warning_function_cc: int = 15
    # Nesting depth por función
    critical_nesting: int = 8
    warning_nesting: int = 5
    # SLOC por archivo
    critical_file_sloc: int = 1000
    warning_file_sloc: int = 500
    # CC media por archivo
    critical_avg_complexity: float = 15.0
    warning_avg_complexity: float = 10.0
    # CC media del proyecto (agregado)
    critical_project_avg_complexity: float = 10.0
    warning_project_avg_complexity: float = 7.0
    # MI media del proyecto (agregado)
    critical_project_avg_mi: float = 30.0
    warning_project_avg_mi: float = 50.0
    # Máximo de funciones con rank F (CC > 25) permitidas
    max_rank_f_functions: int = 0
    # Dependencias circulares entre paquetes
    max_circular_deps: int = 0
    # Globs a excluir del análisis
    exclude: list[str] = field(default_factory=list)


def load_thresholds() -> HealthConfig:
    """Lee [tool.codehealth] de pyproject.toml y devuelve HealthConfig tipado."""
    toml_path = Path("pyproject.toml")
    if not toml_path.exists():
        return HealthConfig()

    with open(toml_path, "rb") as f:
        data = tomllib.load(f)

    section = data.get("tool", {}).get("codehealth", {})
    # Solo pasar campos conocidos para evitar TypeError
    known_fields = {f for f in HealthConfig.__dataclass_fields__}
    filtered = {k: v for k, v in section.items() if k in known_fields}
    return HealthConfig(**filtered)


# ==============================================================================
# SESSION-SCOPED FIXTURES
# ==============================================================================


@pytest.fixture(scope="session")
def health_config() -> HealthConfig:
    """Carga los umbrales de [tool.codehealth] de pyproject.toml."""
    return load_thresholds()


@pytest.fixture(scope="session")
def all_file_metrics(health_config: HealthConfig) -> list[FileMetrics]:
    """Analiza TODOS los archivos trackeados por git una sola vez por sesión.

    Excluye los archivos que coincidan con los globs en health_config.exclude.
    Popula _health_summary con métricas agregadas para el hook terminal.
    """
    global _health_summary

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

        _health_summary["Files analyzed"] = f"{len(results)}"
        _health_summary["Avg MI"] = f"{avg_mi:.1f} {mi_icon}"
        _health_summary["Avg CC"] = f"{avg_cc:.2f} {cc_icon}"
        _health_summary["Rank F functions"] = f"{rank_f_count} {rf_icon}"

    return results


@pytest.fixture(scope="session")
def coupling_result(
    health_config: HealthConfig,
) -> tuple[list[PackageCoupling], list[list[str]]]:
    """Analiza el acoplamiento entre paquetes una sola vez por sesión."""
    global _health_summary

    files = get_tracked_files(*_ALL_EXTENSIONS)
    filtered = [
        f for f in files
        if not any(Path(f).match(p) for p in health_config.exclude)
    ]
    coupling, circulars = analyze_coupling(filtered)

    circ_icon = "✅" if len(circulars) <= health_config.max_circular_deps else "❌"
    _health_summary["Circular deps"] = f"{len(circulars)} {circ_icon}"

    return coupling, circulars


# ==============================================================================
# TERMINAL SUMMARY HOOK
# ==============================================================================


def pytest_terminal_summary(terminalreporter, exitstatus, config):
    """Imprime tabla resumen de code health al final del test run."""
    # Solo mostrar si se ejecutaron tests de health
    all_reports = (
        terminalreporter.stats.get("passed", [])
        + terminalreporter.stats.get("failed", [])
        + terminalreporter.stats.get("error", [])
    )
    health_ran = any(
        hasattr(r, "nodeid") and "health" in r.nodeid
        for r in all_reports
    )
    if not health_ran or not _health_summary:
        return

    passed = exitstatus == 0
    overall = "✅  ALL GATES PASSED" if passed else "❌  GATES FAILED"

    width = 54
    separator = "═" * width
    terminalreporter.write_sep("-", "Code Health Summary")
    terminalreporter.write_line(f"╔{separator}╗")
    terminalreporter.write_line(f"║{'  CODE HEALTH QUALITY GATES':^{width}}║")
    terminalreporter.write_line(f"╠{separator}╣")

    for key, value in _health_summary.items():
        content = f"  {key:<26} {value}"
        terminalreporter.write_line(f"║{content:<{width}}║")

    terminalreporter.write_line(f"╠{separator}╣")
    terminalreporter.write_line(f"║{'  ' + overall:<{width}}║")
    terminalreporter.write_line(f"╚{separator}╝")
