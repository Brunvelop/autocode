"""
test_health.py — Tests unitarios para autocode.core.code.health

Cubre toda la API pública:
- HealthConfig: defaults, overrides
- load_thresholds(): lectura de TOML, fichero ausente, sección ausente, campos desconocidos
- run_health_check(): pass/fail/warning, violations de MI, CC, nesting, rank F, circulares
"""
from __future__ import annotations

from pathlib import Path

import pytest

from autocode.core.code.health import (
    HealthConfig,
    HealthCheckResult,
    HealthViolation,
    load_thresholds,
    run_health_check,
)
from autocode.core.code.models import FileMetrics, FunctionMetrics


# ==============================================================================
# FIXTURES
# ==============================================================================


def _make_function(
    name: str = "my_func",
    file: str = "src/mod.py",
    line: int = 1,
    complexity: int = 1,
    nesting_depth: int = 1,
    rank: str = "A",
    sloc: int = 10,
) -> FunctionMetrics:
    return FunctionMetrics(
        name=name,
        file=file,
        line=line,
        complexity=complexity,
        rank=rank,
        nesting_depth=nesting_depth,
        sloc=sloc,
    )


def _make_file(
    path: str = "src/mod.py",
    mi: float = 80.0,
    sloc: int = 100,
    avg_complexity: float = 2.0,
    functions: list[FunctionMetrics] | None = None,
) -> FileMetrics:
    funcs = functions or [_make_function(file=path)]
    return FileMetrics(
        path=path,
        sloc=sloc,
        maintainability_index=mi,
        avg_complexity=avg_complexity,
        functions=funcs,
    )


@pytest.fixture
def good_metrics() -> list[FileMetrics]:
    """Métricas que pasan todos los umbrales (defaults de HealthConfig)."""
    return [
        _make_file("src/a.py", mi=85.0, sloc=100, avg_complexity=2.0),
        _make_file("src/b.py", mi=75.0, sloc=200, avg_complexity=3.0),
    ]


@pytest.fixture
def bad_mi_metrics() -> list[FileMetrics]:
    """Un archivo con MI por debajo del umbral crítico (20.0 por defecto)."""
    return [
        _make_file("src/good.py", mi=85.0, sloc=100, avg_complexity=2.0),
        _make_file("src/bad.py", mi=10.0, sloc=300, avg_complexity=4.0),
    ]


@pytest.fixture
def borderline_metrics() -> list[FileMetrics]:
    """Archivos en zona de warning (entre critical y warning) → passed=True con warnings."""
    # critical_mi=20, warning_mi=40 → valor en [20, 40) dispara warning, no critical
    return [
        _make_file("src/border.py", mi=25.0, sloc=100, avg_complexity=2.0),
    ]


@pytest.fixture
def high_cc_metrics() -> list[FileMetrics]:
    """Función con CC por encima del umbral crítico."""
    bad_func = _make_function(name="complex_fn", complexity=30, rank="F")
    return [
        _make_file("src/complex.py", mi=60.0, functions=[bad_func]),
    ]


@pytest.fixture
def deep_nesting_metrics() -> list[FileMetrics]:
    """Función con nesting por encima del umbral crítico."""
    deep_func = _make_function(name="nested_fn", nesting_depth=10)
    return [
        _make_file("src/nested.py", mi=60.0, functions=[deep_func]),
    ]


@pytest.fixture
def rank_f_metrics() -> list[FileMetrics]:
    """Función con rank F (CC > 25). Config por defecto max_rank_f=0 → falla."""
    rank_f_func = _make_function(name="huge_fn", complexity=30, rank="F")
    return [
        _make_file("src/huge.py", mi=60.0, functions=[rank_f_func]),
    ]


# ==============================================================================
# TEST HEALTHCONFIG
# ==============================================================================


class TestHealthConfig:
    def test_defaults_are_strict(self):
        """Defaults deben ser los umbrales estrictos documentados."""
        config = HealthConfig()
        assert config.critical_mi == 20.0
        assert config.warning_mi == 40.0
        assert config.critical_function_cc == 25
        assert config.warning_function_cc == 15
        assert config.critical_nesting == 8
        assert config.warning_nesting == 5
        assert config.critical_file_sloc == 1000
        assert config.warning_file_sloc == 500
        assert config.max_rank_f_functions == 0
        assert config.max_circular_deps == 0

    def test_custom_single_override(self):
        """Se puede overridear un campo individual sin tocar el resto."""
        config = HealthConfig(critical_mi=5.0)
        assert config.critical_mi == 5.0
        assert config.warning_mi == 40.0  # default no tocado

    def test_custom_multiple_overrides(self):
        """Se pueden overridear múltiples campos."""
        config = HealthConfig(critical_mi=5.0, max_rank_f_functions=3, max_circular_deps=2)
        assert config.critical_mi == 5.0
        assert config.max_rank_f_functions == 3
        assert config.max_circular_deps == 2
        assert config.warning_mi == 40.0  # default no tocado

    def test_equality(self):
        """Dos HealthConfig con los mismos valores son iguales."""
        assert HealthConfig() == HealthConfig()
        assert HealthConfig(critical_mi=5.0) != HealthConfig()

    def test_exclude_default_is_empty_list(self):
        """exclude debe ser lista vacía por defecto (no compartida entre instancias)."""
        c1 = HealthConfig()
        c2 = HealthConfig()
        assert c1.exclude == []
        # Listas independientes (no comparten referencia)
        c1.exclude.append("tests/*")
        assert c2.exclude == []


# ==============================================================================
# TEST LOAD_THRESHOLDS
# ==============================================================================


class TestLoadThresholds:
    def test_reads_critical_mi_from_toml(self, tmp_path: Path):
        """Lee [tool.codehealth] de un pyproject.toml."""
        toml = tmp_path / "pyproject.toml"
        toml.write_text("[tool.codehealth]\ncritical_mi = 5.0\n")
        config = load_thresholds(project_root=tmp_path)
        assert config.critical_mi == 5.0

    def test_reads_multiple_fields_from_toml(self, tmp_path: Path):
        """Lee múltiples campos de [tool.codehealth]."""
        toml = tmp_path / "pyproject.toml"
        toml.write_text(
            "[tool.codehealth]\ncritical_mi = 5.0\nmax_circular_deps = 2\n"
        )
        config = load_thresholds(project_root=tmp_path)
        assert config.critical_mi == 5.0
        assert config.max_circular_deps == 2
        # Campos no especificados usan defaults
        assert config.warning_mi == 40.0

    def test_missing_file_returns_defaults(self, tmp_path: Path):
        """Si no hay pyproject.toml, devuelve defaults."""
        config = load_thresholds(project_root=tmp_path)
        assert config == HealthConfig()

    def test_missing_section_returns_defaults(self, tmp_path: Path):
        """Si no hay [tool.codehealth], devuelve defaults."""
        toml = tmp_path / "pyproject.toml"
        toml.write_text("[project]\nname = \"foo\"\n")
        config = load_thresholds(project_root=tmp_path)
        assert config == HealthConfig()

    def test_missing_tool_section_returns_defaults(self, tmp_path: Path):
        """Si no hay [tool], devuelve defaults."""
        toml = tmp_path / "pyproject.toml"
        toml.write_text("[project]\nname = \"foo\"\n")
        config = load_thresholds(project_root=tmp_path)
        assert config == HealthConfig()

    def test_ignores_unknown_fields(self, tmp_path: Path):
        """Campos desconocidos en el TOML no causan error."""
        toml = tmp_path / "pyproject.toml"
        toml.write_text(
            "[tool.codehealth]\ncritical_mi = 5.0\nunknown_field = 42\n"
        )
        config = load_thresholds(project_root=tmp_path)
        assert config.critical_mi == 5.0

    def test_no_project_root_uses_cwd(self, tmp_path: Path, monkeypatch):
        """Sin project_root, usa Path.cwd() como fallback."""
        monkeypatch.chdir(tmp_path)
        toml = tmp_path / "pyproject.toml"
        toml.write_text("[tool.codehealth]\ncritical_mi = 7.0\n")
        config = load_thresholds()  # sin project_root
        assert config.critical_mi == 7.0

    def test_reads_exclude_list(self, tmp_path: Path):
        """Lee la lista de exclusiones."""
        toml = tmp_path / "pyproject.toml"
        toml.write_text(
            '[tool.codehealth]\nexclude = ["tests/*", "setup.py"]\n'
        )
        config = load_thresholds(project_root=tmp_path)
        assert config.exclude == ["tests/*", "setup.py"]


# ==============================================================================
# TEST RUN_HEALTH_CHECK
# ==============================================================================


class TestRunHealthCheck:
    # --- Casos de éxito ---

    def test_all_pass_returns_passed_true(self, good_metrics):
        """Métricas buenas → passed=True, sin violations."""
        result = run_health_check(HealthConfig(), good_metrics)
        assert result.passed is True
        assert len(result.violations) == 0

    def test_result_is_health_check_result(self, good_metrics):
        """run_health_check devuelve un HealthCheckResult."""
        result = run_health_check(HealthConfig(), good_metrics)
        assert isinstance(result, HealthCheckResult)

    def test_violations_are_health_violation_instances(self, bad_mi_metrics):
        """Cada violation es un HealthViolation."""
        result = run_health_check(HealthConfig(), bad_mi_metrics)
        assert all(isinstance(v, HealthViolation) for v in result.violations)

    def test_empty_metrics_passes(self):
        """Sin archivos → passed=True, sin violations."""
        result = run_health_check(HealthConfig(), [])
        assert result.passed is True
        assert len(result.violations) == 0

    # --- Violaciones de MI ---

    def test_critical_mi_violation_fails(self, bad_mi_metrics):
        """Archivo con MI bajo el umbral crítico → passed=False."""
        result = run_health_check(HealthConfig(critical_mi=20.0), bad_mi_metrics)
        assert result.passed is False

    def test_critical_mi_violation_rule(self, bad_mi_metrics):
        """Violation de MI tiene rule='mi' y level='critical'."""
        result = run_health_check(HealthConfig(critical_mi=20.0), bad_mi_metrics)
        assert any(v.rule == "mi" and v.level == "critical" for v in result.violations)

    def test_critical_mi_violation_path(self, bad_mi_metrics):
        """Violation de MI incluye el path del archivo afectado."""
        result = run_health_check(HealthConfig(critical_mi=20.0), bad_mi_metrics)
        mi_violations = [v for v in result.violations if v.rule == "mi" and v.level == "critical"]
        paths = {v.path for v in mi_violations}
        assert "src/bad.py" in paths

    def test_warning_mi_only_passes(self, borderline_metrics):
        """Solo warnings de MI → passed=True pero con violations de nivel warning."""
        # borderline: MI=25, critical_mi=20, warning_mi=40 → en zona warning a nivel archivo
        # Bajamos los umbrales del proyecto para que avg_mi=25 no dispare project_mi critical
        result = run_health_check(
            HealthConfig(
                critical_mi=20.0,
                warning_mi=40.0,
                critical_project_avg_mi=10.0,
                warning_project_avg_mi=15.0,
            ),
            borderline_metrics,
        )
        assert result.passed is True
        assert any(v.rule == "mi" and v.level == "warning" for v in result.violations)

    def test_good_mi_no_violations(self, good_metrics):
        """Archivos con MI buena → sin violations de MI."""
        result = run_health_check(HealthConfig(), good_metrics)
        mi_violations = [v for v in result.violations if v.rule == "mi"]
        assert len(mi_violations) == 0

    # --- Violaciones de CC de función ---

    def test_critical_function_cc_fails(self, high_cc_metrics):
        """Función con CC crítica → passed=False."""
        result = run_health_check(HealthConfig(critical_function_cc=25), high_cc_metrics)
        assert result.passed is False

    def test_critical_function_cc_violation_rule(self, high_cc_metrics):
        """Violation de CC tiene rule='function_cc' y level='critical'."""
        result = run_health_check(HealthConfig(critical_function_cc=25), high_cc_metrics)
        assert any(
            v.rule == "function_cc" and v.level == "critical"
            for v in result.violations
        )

    # --- Violaciones de nesting ---

    def test_critical_nesting_fails(self, deep_nesting_metrics):
        """Función con nesting crítico → passed=False."""
        result = run_health_check(HealthConfig(critical_nesting=8), deep_nesting_metrics)
        assert result.passed is False

    def test_critical_nesting_violation_rule(self, deep_nesting_metrics):
        """Violation de nesting tiene rule='nesting' y level='critical'."""
        result = run_health_check(HealthConfig(critical_nesting=8), deep_nesting_metrics)
        assert any(
            v.rule == "nesting" and v.level == "critical"
            for v in result.violations
        )

    # --- Violaciones de rank F ---

    def test_rank_f_functions_fails_when_above_max(self, rank_f_metrics):
        """Funciones rank F por encima del max → passed=False."""
        result = run_health_check(HealthConfig(max_rank_f_functions=0), rank_f_metrics)
        assert result.passed is False

    def test_rank_f_functions_passes_when_within_max(self, rank_f_metrics):
        """Funciones rank F dentro del límite permitido → passed=True.

        Elevamos critical_function_cc y project_cc para aislar el test
        del rank_f rule exclusivamente (complexity=30 no debe disparar otras reglas).
        """
        result = run_health_check(
            HealthConfig(
                max_rank_f_functions=5,
                critical_function_cc=100,
                warning_function_cc=50,
                critical_project_avg_complexity=100.0,
                warning_project_avg_complexity=50.0,
            ),
            rank_f_metrics,
        )
        assert result.passed is True

    def test_rank_f_violation_rule(self, rank_f_metrics):
        """Violation de rank F tiene rule='rank_f'."""
        result = run_health_check(HealthConfig(max_rank_f_functions=0), rank_f_metrics)
        assert any(v.rule == "rank_f" for v in result.violations)

    # --- Violaciones de dependencias circulares ---

    def test_circular_deps_passes_within_limit(self, good_metrics):
        """Circulares dentro del límite → passed=True."""
        coupling_result = ([], [["a", "b"]])  # 1 circular
        result = run_health_check(
            HealthConfig(max_circular_deps=1),
            good_metrics,
            coupling_result=coupling_result,
        )
        assert result.passed is True

    def test_circular_deps_fails_above_limit(self, good_metrics):
        """Circulares por encima del límite → passed=False."""
        coupling_result = ([], [["a", "b"], ["c", "d"]])  # 2 circulares
        result = run_health_check(
            HealthConfig(max_circular_deps=0),
            good_metrics,
            coupling_result=coupling_result,
        )
        assert result.passed is False

    def test_circular_deps_violation_rule(self, good_metrics):
        """Violation de circulares tiene rule='circular_deps'."""
        coupling_result = ([], [["a", "b"]])
        result = run_health_check(
            HealthConfig(max_circular_deps=0),
            good_metrics,
            coupling_result=coupling_result,
        )
        assert any(v.rule == "circular_deps" for v in result.violations)

    def test_no_coupling_result_skips_circular_check(self, good_metrics):
        """Sin coupling_result, no se evalúan circulares."""
        result = run_health_check(HealthConfig(max_circular_deps=0), good_metrics)
        circular_violations = [v for v in result.violations if v.rule == "circular_deps"]
        assert len(circular_violations) == 0

    # --- Summary ---

    def test_summary_contains_key_metrics(self, good_metrics):
        """El summary contiene al menos las métricas clave."""
        result = run_health_check(HealthConfig(), good_metrics)
        assert isinstance(result.summary, dict)
        assert len(result.summary) > 0

    # --- HealthViolation structure ---

    def test_violation_has_required_fields(self, bad_mi_metrics):
        """Cada HealthViolation tiene rule, level, path, value, threshold."""
        result = run_health_check(HealthConfig(critical_mi=20.0), bad_mi_metrics)
        for v in result.violations:
            assert hasattr(v, "rule")
            assert hasattr(v, "level")
            assert hasattr(v, "path")
            assert hasattr(v, "value")
            assert hasattr(v, "threshold")

    def test_violation_level_is_valid(self, bad_mi_metrics):
        """El level de cada violation es 'critical' o 'warning'."""
        result = run_health_check(HealthConfig(critical_mi=20.0), bad_mi_metrics)
        for v in result.violations:
            assert v.level in ("critical", "warning")
