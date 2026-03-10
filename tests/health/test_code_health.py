"""
test_code_health.py — Code Health Quality Gates.

Cada test = una regla que itera todo el codebase internamente, recolecta
violaciones y:
  - Imprime aviso en stdout para violaciones borderline (warning threshold)
  - Hace assert sobre las violaciones críticas listando TODAS en el mensaje

Ejecutar solo las quality gates:
    pytest -m health -v --no-header -p no:warnings

Excluir en ciclo de desarrollo rápido:
    pytest -m "not health"
"""
from __future__ import annotations

import pytest

from tests.health.conftest import HealthConfig
from autocode.core.code.models import FileMetrics


# ==============================================================================
# HELPERS DE FORMATO
# ==============================================================================


def _fmt_file_violations(violations: list[dict], metric: str, threshold, unit: str = "") -> str:
    sep = "─" * 62
    lines = [
        f"\n{sep}",
        f"  ❌ {metric} — umbral crítico: {threshold}{unit}",
        sep,
    ]
    for v in violations:
        lines.append(f"    • {v['path']:<50} {v['value']}{unit}")
    lines.append(sep)
    lines.append(f"  Total: {len(violations)} archivo(s) violando el umbral")
    return "\n".join(lines)


def _fmt_func_violations(violations: list[dict], metric: str, threshold) -> str:
    sep = "─" * 62
    lines = [
        f"\n{sep}",
        f"  ❌ {metric} — umbral crítico: {threshold}",
        sep,
    ]
    for v in violations:
        lines.append(f"    • {v['file']}:{v['line']}  {v['name']}()  =  {v['value']}")
    lines.append(sep)
    lines.append(f"  Total: {len(violations)} función(es) violando el umbral")
    return "\n".join(lines)


# ==============================================================================
# REGLAS A NIVEL DE ARCHIVO
# ==============================================================================


@pytest.mark.health
class TestFileHealth:
    """Quality gates a nivel de archivo individual."""

    def test_maintainability_index(
        self, all_file_metrics: list[FileMetrics], health_config: HealthConfig
    ):
        """Ningún archivo debe tener MI por debajo del umbral crítico."""
        critical: list[dict] = []
        warnings_list: list[str] = []

        for fm in all_file_metrics:
            if fm.maintainability_index < health_config.critical_mi:
                critical.append({"path": fm.path, "value": f"{fm.maintainability_index:.1f}"})
            elif fm.maintainability_index < health_config.warning_mi:
                warnings_list.append(f"{fm.path} (MI={fm.maintainability_index:.1f})")

        if warnings_list:
            print(
                f"\n⚠️  MI warning (<{health_config.warning_mi}): "
                + ", ".join(warnings_list)
            )

        assert not critical, _fmt_file_violations(
            critical, "Maintainability Index", health_config.critical_mi
        )

    def test_file_sloc(
        self, all_file_metrics: list[FileMetrics], health_config: HealthConfig
    ):
        """Ningún archivo debe exceder el SLOC máximo crítico."""
        critical: list[dict] = []
        warnings_list: list[str] = []

        for fm in all_file_metrics:
            if fm.sloc > health_config.critical_file_sloc:
                critical.append({"path": fm.path, "value": fm.sloc})
            elif fm.sloc > health_config.warning_file_sloc:
                warnings_list.append(f"{fm.path} ({fm.sloc} SLOC)")

        if warnings_list:
            print(
                f"\n⚠️  SLOC warning (>{health_config.warning_file_sloc}): "
                + ", ".join(warnings_list)
            )

        assert not critical, _fmt_file_violations(
            critical, "File SLOC", health_config.critical_file_sloc, " lines"
        )

    def test_file_avg_complexity(
        self, all_file_metrics: list[FileMetrics], health_config: HealthConfig
    ):
        """Ningún archivo debe exceder la CC media máxima crítica."""
        critical: list[dict] = []
        warnings_list: list[str] = []

        for fm in all_file_metrics:
            if fm.avg_complexity > health_config.critical_avg_complexity:
                critical.append({"path": fm.path, "value": f"{fm.avg_complexity:.2f}"})
            elif fm.avg_complexity > health_config.warning_avg_complexity:
                warnings_list.append(f"{fm.path} (CC={fm.avg_complexity:.2f})")

        if warnings_list:
            print(
                f"\n⚠️  Avg CC warning (>{health_config.warning_avg_complexity}): "
                + ", ".join(warnings_list)
            )

        assert not critical, _fmt_file_violations(
            critical, "File Avg Cyclomatic Complexity", health_config.critical_avg_complexity
        )


# ==============================================================================
# REGLAS A NIVEL DE FUNCIÓN
# ==============================================================================


@pytest.mark.health
class TestFunctionHealth:
    """Quality gates a nivel de función individual."""

    def test_function_complexity(
        self, all_file_metrics: list[FileMetrics], health_config: HealthConfig
    ):
        """Ninguna función debe superar la CC crítica."""
        critical: list[dict] = []
        warning_count = 0

        for fm in all_file_metrics:
            for func in fm.functions:
                entry = {
                    "file": func.file,
                    "line": func.line,
                    "name": func.name,
                    "value": func.complexity,
                }
                if func.complexity > health_config.critical_function_cc:
                    critical.append(entry)
                elif func.complexity > health_config.warning_function_cc:
                    warning_count += 1

        if warning_count:
            print(
                f"\n⚠️  CC warning (>{health_config.warning_function_cc}): "
                f"{warning_count} función(es) con CC alta pero por debajo del crítico"
            )

        assert not critical, _fmt_func_violations(
            critical, "Function Cyclomatic Complexity", health_config.critical_function_cc
        )

    def test_function_nesting(
        self, all_file_metrics: list[FileMetrics], health_config: HealthConfig
    ):
        """Ninguna función debe superar la profundidad de anidamiento crítica."""
        critical: list[dict] = []
        warning_count = 0

        for fm in all_file_metrics:
            for func in fm.functions:
                entry = {
                    "file": func.file,
                    "line": func.line,
                    "name": func.name,
                    "value": func.nesting_depth,
                }
                if func.nesting_depth > health_config.critical_nesting:
                    critical.append(entry)
                elif func.nesting_depth > health_config.warning_nesting:
                    warning_count += 1

        if warning_count:
            print(
                f"\n⚠️  Nesting warning (>{health_config.warning_nesting}): "
                f"{warning_count} función(es) con nesting alto pero por debajo del crítico"
            )

        assert not critical, _fmt_func_violations(
            critical, "Function Nesting Depth", health_config.critical_nesting
        )

    def test_no_rank_f_functions(
        self, all_file_metrics: list[FileMetrics], health_config: HealthConfig
    ):
        """El número de funciones con rank F (CC > 25) no debe superar el máximo permitido."""
        rank_f = [
            {
                "file": func.file,
                "line": func.line,
                "name": func.name,
                "value": func.complexity,
            }
            for fm in all_file_metrics
            for func in fm.functions
            if func.rank == "F"
        ]

        if rank_f:
            print(
                f"\n{'⚠️' if len(rank_f) <= health_config.max_rank_f_functions else '❌'}"
                f"  Rank F functions: {len(rank_f)} "
                f"(máx permitido: {health_config.max_rank_f_functions})"
            )

        assert len(rank_f) <= health_config.max_rank_f_functions, (
            _fmt_func_violations(rank_f, "Rank F functions (CC > 25)", 25)
            + f"\n  Máximo permitido: {health_config.max_rank_f_functions} "
            f"— actual: {len(rank_f)}"
        )


# ==============================================================================
# REGLAS A NIVEL DE PROYECTO (AGREGADAS)
# ==============================================================================


@pytest.mark.health
class TestProjectHealth:
    """Quality gates sobre métricas agregadas del proyecto."""

    def test_project_avg_mi(
        self, all_file_metrics: list[FileMetrics], health_config: HealthConfig
    ):
        """MI media del proyecto debe estar por encima del umbral crítico."""
        if not all_file_metrics:
            pytest.skip("No hay archivos para analizar")

        avg_mi = sum(fm.maintainability_index for fm in all_file_metrics) / len(all_file_metrics)

        if avg_mi < health_config.warning_project_avg_mi:
            print(
                f"\n⚠️  MI media del proyecto ({avg_mi:.1f}) "
                f"por debajo del umbral de warning ({health_config.warning_project_avg_mi})"
            )

        assert avg_mi >= health_config.critical_project_avg_mi, (
            f"MI media del proyecto {avg_mi:.1f} "
            f"< umbral crítico {health_config.critical_project_avg_mi}\n"
            f"  El codebase necesita refactoring urgente."
        )

    def test_project_avg_complexity(
        self, all_file_metrics: list[FileMetrics], health_config: HealthConfig
    ):
        """CC media del proyecto debe estar por debajo del umbral crítico."""
        all_funcs = [f for fm in all_file_metrics for f in fm.functions]
        if not all_funcs:
            pytest.skip("No hay funciones para analizar")

        avg_cc = sum(f.complexity for f in all_funcs) / len(all_funcs)

        if avg_cc > health_config.warning_project_avg_complexity:
            print(
                f"\n⚠️  CC media del proyecto ({avg_cc:.2f}) "
                f"por encima del umbral de warning ({health_config.warning_project_avg_complexity})"
            )

        assert avg_cc <= health_config.critical_project_avg_complexity, (
            f"CC media del proyecto {avg_cc:.2f} "
            f"> umbral crítico {health_config.critical_project_avg_complexity}\n"
            f"  Demasiadas funciones complejas acumuladas en el proyecto."
        )

    def test_no_circular_dependencies(self, coupling_result, health_config: HealthConfig):
        """No debe haber dependencias circulares entre paquetes."""
        _, circulars = coupling_result

        assert len(circulars) <= health_config.max_circular_deps, (
            f"Se detectaron {len(circulars)} dependencia(s) circular(es) "
            f"(máx permitido: {health_config.max_circular_deps}):\n"
            + "\n".join(f"  • {a} ↔ {b}" for a, b in circulars)
        )
