"""
health.py — Code Health configuration, thresholds, and evaluation engine.

Provides:
- HealthConfig: dataclass with quality thresholds (read from [tool.codehealth])
- load_thresholds(): reads config from consumer's pyproject.toml
- HealthViolation: structured representation of a quality gate violation
- HealthCheckResult: result of evaluating all quality gates
- run_health_check(): evaluates all quality gates, returns structured result

Used by:
- autocode.testing.plugin (pytest integration via pytest11 entry-point)
- autocode.interfaces.cli (health-check command)
- tests/health/test_code_health.py (health quality gates for autocode itself)
"""
import tomllib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from refract import register_function

from autocode.core.code.models import FileMetrics, PackageCoupling, HealthViolation, HealthCheckResult


# ==============================================================================
# CONFIG
# ==============================================================================


@dataclass
class HealthConfig:
    """Umbrales de calidad de código leídos de [tool.codehealth] en pyproject.toml.

    Defaults calibrados para ser estrictos. Los consumidores pueden relajarlos
    en su propio [tool.codehealth] según el estado de su codebase.
    """

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


# ==============================================================================
# LOAD THRESHOLDS
# ==============================================================================


def load_thresholds(project_root: Optional[Path] = None) -> HealthConfig:
    """Lee [tool.codehealth] del pyproject.toml del proyecto.

    Args:
        project_root: Directorio raíz del proyecto donde buscar pyproject.toml.
                      Si es None, usa Path.cwd().

    Returns:
        HealthConfig con los valores del TOML, usando defaults para los no especificados.
        Si no existe el archivo o la sección, devuelve HealthConfig() con defaults.
    """
    root = project_root if project_root is not None else Path.cwd()
    toml_path = root / "pyproject.toml"

    if not toml_path.exists():
        return HealthConfig()

    with open(toml_path, "rb") as f:
        data = tomllib.load(f)

    section = data.get("tool", {}).get("codehealth", {})
    if not section:
        return HealthConfig()

    # Solo pasar campos conocidos para evitar TypeError con campos desconocidos
    known_fields = set(HealthConfig.__dataclass_fields__)
    filtered = {k: v for k, v in section.items() if k in known_fields}
    return HealthConfig(**filtered)


# ==============================================================================
# PRIVATE CHECK HELPERS
# ==============================================================================


def _check_mi(config: HealthConfig, file_metrics: list[FileMetrics]) -> list[HealthViolation]:
    """Comprueba el Maintainability Index por archivo."""
    violations = []
    for fm in file_metrics:
        if fm.maintainability_index < config.critical_mi:
            level, threshold = "critical", config.critical_mi
        elif fm.maintainability_index < config.warning_mi:
            level, threshold = "warning", config.warning_mi
        else:
            continue
        violations.append(HealthViolation(
            rule="mi", level=level, path=fm.path,
            value=fm.maintainability_index, threshold=threshold,
        ))
    return violations


def _check_sloc(config: HealthConfig, file_metrics: list[FileMetrics]) -> list[HealthViolation]:
    """Comprueba el SLOC por archivo."""
    violations = []
    for fm in file_metrics:
        if fm.sloc > config.critical_file_sloc:
            level, threshold = "critical", float(config.critical_file_sloc)
        elif fm.sloc > config.warning_file_sloc:
            level, threshold = "warning", float(config.warning_file_sloc)
        else:
            continue
        violations.append(HealthViolation(
            rule="sloc", level=level, path=fm.path,
            value=float(fm.sloc), threshold=threshold,
        ))
    return violations


def _check_avg_complexity(
    config: HealthConfig, file_metrics: list[FileMetrics]
) -> list[HealthViolation]:
    """Comprueba la CC media por archivo."""
    violations = []
    for fm in file_metrics:
        if fm.avg_complexity > config.critical_avg_complexity:
            level, threshold = "critical", config.critical_avg_complexity
        elif fm.avg_complexity > config.warning_avg_complexity:
            level, threshold = "warning", config.warning_avg_complexity
        else:
            continue
        violations.append(HealthViolation(
            rule="avg_cc", level=level, path=fm.path,
            value=fm.avg_complexity, threshold=threshold,
        ))
    return violations


def _check_function_cc(
    config: HealthConfig, file_metrics: list[FileMetrics]
) -> list[HealthViolation]:
    """Comprueba la CC por función."""
    violations = []
    for fm in file_metrics:
        for func in fm.functions:
            if func.complexity > config.critical_function_cc:
                level, threshold = "critical", float(config.critical_function_cc)
            elif func.complexity > config.warning_function_cc:
                level, threshold = "warning", float(config.warning_function_cc)
            else:
                continue
            violations.append(HealthViolation(
                rule="function_cc", level=level, path=func.file,
                value=float(func.complexity), threshold=threshold,
                detail=f"{func.name}() line {func.line}",
            ))
    return violations


def _check_nesting(
    config: HealthConfig, file_metrics: list[FileMetrics]
) -> list[HealthViolation]:
    """Comprueba la profundidad de anidamiento por función."""
    violations = []
    for fm in file_metrics:
        for func in fm.functions:
            if func.nesting_depth > config.critical_nesting:
                level, threshold = "critical", float(config.critical_nesting)
            elif func.nesting_depth > config.warning_nesting:
                level, threshold = "warning", float(config.warning_nesting)
            else:
                continue
            violations.append(HealthViolation(
                rule="nesting", level=level, path=func.file,
                value=float(func.nesting_depth), threshold=threshold,
                detail=f"{func.name}() line {func.line}",
            ))
    return violations


def _check_rank_f(
    config: HealthConfig, all_funcs: list
) -> list[HealthViolation]:
    """Comprueba el número total de funciones con rank F en el proyecto."""
    rank_f_funcs = [f for f in all_funcs if f.rank == "F"]
    if len(rank_f_funcs) <= config.max_rank_f_functions:
        return []
    return [HealthViolation(
        rule="rank_f", level="critical", path="<project>",
        value=float(len(rank_f_funcs)),
        threshold=float(config.max_rank_f_functions),
        detail=", ".join(f"{f.name}() [{f.file}:{f.line}]" for f in rank_f_funcs),
    )]


def _check_circular_deps(
    config: HealthConfig,
    coupling_result: tuple[list[PackageCoupling], list[list[str]]],
) -> list[HealthViolation]:
    """Comprueba las dependencias circulares entre paquetes."""
    _, circulars = coupling_result
    if len(circulars) <= config.max_circular_deps:
        return []
    return [HealthViolation(
        rule="circular_deps", level="critical", path="<project>",
        value=float(len(circulars)),
        threshold=float(config.max_circular_deps),
        detail="; ".join(f"{a} ↔ {b}" for a, b in circulars),
    )]


def _check_project_mi(
    config: HealthConfig, file_metrics: list[FileMetrics]
) -> list[HealthViolation]:
    """Comprueba la MI media del proyecto."""
    if not file_metrics:
        return []
    avg_mi = sum(fm.maintainability_index for fm in file_metrics) / len(file_metrics)
    if avg_mi < config.critical_project_avg_mi:
        level, threshold = "critical", config.critical_project_avg_mi
    elif avg_mi < config.warning_project_avg_mi:
        level, threshold = "warning", config.warning_project_avg_mi
    else:
        return []
    return [HealthViolation(
        rule="project_mi", level=level, path="<project>",
        value=avg_mi, threshold=threshold,
    )]


def _check_project_cc(
    config: HealthConfig, all_funcs: list
) -> list[HealthViolation]:
    """Comprueba la CC media del proyecto."""
    if not all_funcs:
        return []
    avg_cc = sum(f.complexity for f in all_funcs) / len(all_funcs)
    if avg_cc > config.critical_project_avg_complexity:
        level, threshold = "critical", config.critical_project_avg_complexity
    elif avg_cc > config.warning_project_avg_complexity:
        level, threshold = "warning", config.warning_project_avg_complexity
    else:
        return []
    return [HealthViolation(
        rule="project_cc", level=level, path="<project>",
        value=avg_cc, threshold=threshold,
    )]


# ==============================================================================
# RUN HEALTH CHECK
# ==============================================================================


def run_health_check(
    config: HealthConfig,
    file_metrics: list[FileMetrics],
    coupling_result: Optional[tuple[list[PackageCoupling], list[list[str]]]] = None,
) -> HealthCheckResult:
    """Evalúa TODAS las quality gates y devuelve un resultado estructurado.

    Evalúa en orden:
    1. Maintainability Index por archivo (critical + warning)
    2. SLOC por archivo (critical + warning)
    3. CC media por archivo (critical + warning)
    4. CC por función (critical + warning)
    5. Nesting depth por función (critical + warning)
    6. Rank F functions (total vs max permitido)
    7. Dependencias circulares (si se proporciona coupling_result)
    8. MI media del proyecto (critical + warning)
    9. CC media del proyecto (critical + warning)

    Args:
        config: Umbrales de calidad a aplicar
        file_metrics: Lista de FileMetrics de todos los archivos a evaluar
        coupling_result: Tupla (coupling, circulars) de analyze_coupling().
                         Si es None, se omite la evaluación de circulares.

    Returns:
        HealthCheckResult con passed=True si no hay violations críticas.
    """
    all_funcs = [f for fm in file_metrics for f in fm.functions]
    rank_f_count = sum(1 for f in all_funcs if f.rank == "F")

    violations: list[HealthViolation] = []
    violations.extend(_check_mi(config, file_metrics))
    violations.extend(_check_sloc(config, file_metrics))
    violations.extend(_check_avg_complexity(config, file_metrics))
    violations.extend(_check_function_cc(config, file_metrics))
    violations.extend(_check_nesting(config, file_metrics))
    violations.extend(_check_rank_f(config, all_funcs))
    if coupling_result is not None:
        violations.extend(_check_circular_deps(config, coupling_result))
    violations.extend(_check_project_mi(config, file_metrics))
    violations.extend(_check_project_cc(config, all_funcs))

    passed = not any(v.level == "critical" for v in violations)
    summary = _build_summary(config, file_metrics, all_funcs, rank_f_count, coupling_result)
    return HealthCheckResult(passed=passed, violations=violations, summary=summary)


def _build_summary(
    config: HealthConfig,
    file_metrics: list[FileMetrics],
    all_funcs: list,
    rank_f_count: int,
    coupling_result: Optional[tuple] = None,
) -> dict[str, str]:
    """Construye el dict de métricas agregadas para display en terminal."""
    summary: dict[str, str] = {}

    summary["Files analyzed"] = str(len(file_metrics))

    if file_metrics:
        avg_mi = sum(fm.maintainability_index for fm in file_metrics) / len(file_metrics)
        mi_icon = "✅" if avg_mi >= config.warning_project_avg_mi else "⚠️"
        summary["Avg MI"] = f"{avg_mi:.1f} {mi_icon}"

    if all_funcs:
        avg_cc = sum(f.complexity for f in all_funcs) / len(all_funcs)
        cc_icon = "✅" if avg_cc <= config.warning_project_avg_complexity else "⚠️"
        summary["Avg CC"] = f"{avg_cc:.2f} {cc_icon}"

    rf_icon = "✅" if rank_f_count <= config.max_rank_f_functions else "❌"
    summary["Rank F functions"] = f"{rank_f_count} {rf_icon}"

    if coupling_result is not None:
        _, circulars = coupling_result
        circ_count = len(circulars)
        circ_icon = "✅" if circ_count <= config.max_circular_deps else "❌"
        summary["Circular deps"] = f"{circ_count} {circ_icon}"

    return summary


# ==============================================================================
# REFRACTED FUNCTION — API + MCP interface
# ==============================================================================


@register_function(http_methods=["GET"], interfaces=["api", "mcp", "cli"])
def get_health_check(strict: bool = False, project_root: str = ".") -> HealthCheckResult:
    """Run code health quality gates against a project.

    Analyzes all files tracked by git and checks them against quality thresholds
    defined in [tool.codehealth] of pyproject.toml (or strict defaults with strict=True).

    Args:
        strict: Use strict default thresholds, ignoring any [tool.codehealth] in pyproject.toml.
        project_root: Root directory of the project to analyze.
    """
    from autocode.core.code.analyzer import analyze_file_metrics
    from autocode.core.code.coupling import analyze_coupling
    from autocode.core.vcs.git import get_tracked_files

    _ALL_EXTENSIONS = (".py", ".js", ".mjs", ".jsx")
    root = Path(project_root).resolve()
    config = HealthConfig() if strict else load_thresholds(root)
    files = get_tracked_files(*_ALL_EXTENSIONS, cwd=str(root))

    file_metrics = []
    for fpath in files:
        if any(Path(fpath).match(pattern) for pattern in config.exclude):
            continue
        try:
            content = (root / fpath).read_text(encoding="utf-8")
            file_metrics.append(analyze_file_metrics(fpath, content))
        except Exception:
            pass

    coupling = analyze_coupling(files)
    return run_health_check(config, file_metrics, coupling_result=coupling)
