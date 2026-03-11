"""
health.py — Code Health configuration, thresholds, and evaluation engine.

Provides:
- HealthConfig: dataclass with quality thresholds (read from [tool.codehealth])
- load_thresholds(): reads config from consumer's pyproject.toml
- HealthViolation: structured representation of a quality gate violation
- HealthCheckResult: result of evaluating all quality gates
- run_health_check(): evaluates all quality gates, returns structured result

Used by:
- autocode.pytest_plugin (pytest integration)
- autocode.interfaces.cli (health-check command)
- tests/health/conftest.py (health quality gates for autocode itself)
"""
from __future__ import annotations

import tomllib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from autocode.core.code.models import FileMetrics, PackageCoupling


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
# VIOLATION + RESULT
# ==============================================================================


@dataclass
class HealthViolation:
    """Violación estructurada de una quality gate.

    Attributes:
        rule: Identificador de la regla violada.
              Valores: "mi", "function_cc", "nesting", "sloc", "avg_cc",
                       "rank_f", "circular_deps", "project_mi", "project_cc"
        level: Severidad: "critical" (gate falla) o "warning" (aviso)
        path: Archivo o función afectada (path relativo)
        value: Valor medido que viola el umbral
        threshold: Umbral violado
        detail: Información extra (nombre de función, línea, etc.)
    """

    rule: str
    level: str  # "critical" | "warning"
    path: str
    value: float
    threshold: float
    detail: Optional[str] = None


@dataclass
class HealthCheckResult:
    """Resultado de ejecutar todas las quality gates.

    Attributes:
        passed: True si no hay ninguna violation de nivel "critical"
        violations: Lista de todas las violations encontradas (critical + warning)
        summary: Métricas agregadas para display (clave → valor como string)
    """

    passed: bool
    violations: list[HealthViolation]
    summary: dict[str, str]


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
    violations: list[HealthViolation] = []

    # ------------------------------------------------------------------
    # 1. Maintainability Index por archivo
    # ------------------------------------------------------------------
    for fm in file_metrics:
        if fm.maintainability_index < config.critical_mi:
            violations.append(HealthViolation(
                rule="mi",
                level="critical",
                path=fm.path,
                value=fm.maintainability_index,
                threshold=config.critical_mi,
            ))
        elif fm.maintainability_index < config.warning_mi:
            violations.append(HealthViolation(
                rule="mi",
                level="warning",
                path=fm.path,
                value=fm.maintainability_index,
                threshold=config.warning_mi,
            ))

    # ------------------------------------------------------------------
    # 2. SLOC por archivo
    # ------------------------------------------------------------------
    for fm in file_metrics:
        if fm.sloc > config.critical_file_sloc:
            violations.append(HealthViolation(
                rule="sloc",
                level="critical",
                path=fm.path,
                value=float(fm.sloc),
                threshold=float(config.critical_file_sloc),
            ))
        elif fm.sloc > config.warning_file_sloc:
            violations.append(HealthViolation(
                rule="sloc",
                level="warning",
                path=fm.path,
                value=float(fm.sloc),
                threshold=float(config.warning_file_sloc),
            ))

    # ------------------------------------------------------------------
    # 3. CC media por archivo
    # ------------------------------------------------------------------
    for fm in file_metrics:
        if fm.avg_complexity > config.critical_avg_complexity:
            violations.append(HealthViolation(
                rule="avg_cc",
                level="critical",
                path=fm.path,
                value=fm.avg_complexity,
                threshold=config.critical_avg_complexity,
            ))
        elif fm.avg_complexity > config.warning_avg_complexity:
            violations.append(HealthViolation(
                rule="avg_cc",
                level="warning",
                path=fm.path,
                value=fm.avg_complexity,
                threshold=config.warning_avg_complexity,
            ))

    # ------------------------------------------------------------------
    # 4. CC por función
    # ------------------------------------------------------------------
    for fm in file_metrics:
        for func in fm.functions:
            if func.complexity > config.critical_function_cc:
                violations.append(HealthViolation(
                    rule="function_cc",
                    level="critical",
                    path=func.file,
                    value=float(func.complexity),
                    threshold=float(config.critical_function_cc),
                    detail=f"{func.name}() line {func.line}",
                ))
            elif func.complexity > config.warning_function_cc:
                violations.append(HealthViolation(
                    rule="function_cc",
                    level="warning",
                    path=func.file,
                    value=float(func.complexity),
                    threshold=float(config.warning_function_cc),
                    detail=f"{func.name}() line {func.line}",
                ))

    # ------------------------------------------------------------------
    # 5. Nesting depth por función
    # ------------------------------------------------------------------
    for fm in file_metrics:
        for func in fm.functions:
            if func.nesting_depth > config.critical_nesting:
                violations.append(HealthViolation(
                    rule="nesting",
                    level="critical",
                    path=func.file,
                    value=float(func.nesting_depth),
                    threshold=float(config.critical_nesting),
                    detail=f"{func.name}() line {func.line}",
                ))
            elif func.nesting_depth > config.warning_nesting:
                violations.append(HealthViolation(
                    rule="nesting",
                    level="warning",
                    path=func.file,
                    value=float(func.nesting_depth),
                    threshold=float(config.warning_nesting),
                    detail=f"{func.name}() line {func.line}",
                ))

    # ------------------------------------------------------------------
    # 6. Rank F functions (total proyecto)
    # ------------------------------------------------------------------
    all_funcs = [f for fm in file_metrics for f in fm.functions]
    rank_f_funcs = [f for f in all_funcs if f.rank == "F"]
    rank_f_count = len(rank_f_funcs)

    if rank_f_count > config.max_rank_f_functions:
        # Una sola violation a nivel de proyecto, con path vacío
        violations.append(HealthViolation(
            rule="rank_f",
            level="critical",
            path="<project>",
            value=float(rank_f_count),
            threshold=float(config.max_rank_f_functions),
            detail=", ".join(f"{f.name}() [{f.file}:{f.line}]" for f in rank_f_funcs),
        ))

    # ------------------------------------------------------------------
    # 7. Dependencias circulares
    # ------------------------------------------------------------------
    if coupling_result is not None:
        _, circulars = coupling_result
        circular_count = len(circulars)
        if circular_count > config.max_circular_deps:
            violations.append(HealthViolation(
                rule="circular_deps",
                level="critical",
                path="<project>",
                value=float(circular_count),
                threshold=float(config.max_circular_deps),
                detail="; ".join(f"{a} ↔ {b}" for a, b in circulars),
            ))

    # ------------------------------------------------------------------
    # 8. MI media del proyecto
    # ------------------------------------------------------------------
    if file_metrics:
        avg_mi = sum(fm.maintainability_index for fm in file_metrics) / len(file_metrics)
        if avg_mi < config.critical_project_avg_mi:
            violations.append(HealthViolation(
                rule="project_mi",
                level="critical",
                path="<project>",
                value=avg_mi,
                threshold=config.critical_project_avg_mi,
            ))
        elif avg_mi < config.warning_project_avg_mi:
            violations.append(HealthViolation(
                rule="project_mi",
                level="warning",
                path="<project>",
                value=avg_mi,
                threshold=config.warning_project_avg_mi,
            ))

    # ------------------------------------------------------------------
    # 9. CC media del proyecto
    # ------------------------------------------------------------------
    if all_funcs:
        avg_cc = sum(f.complexity for f in all_funcs) / len(all_funcs)
        if avg_cc > config.critical_project_avg_complexity:
            violations.append(HealthViolation(
                rule="project_cc",
                level="critical",
                path="<project>",
                value=avg_cc,
                threshold=config.critical_project_avg_complexity,
            ))
        elif avg_cc > config.warning_project_avg_complexity:
            violations.append(HealthViolation(
                rule="project_cc",
                level="warning",
                path="<project>",
                value=avg_cc,
                threshold=config.warning_project_avg_complexity,
            ))

    # ------------------------------------------------------------------
    # Resultado final
    # ------------------------------------------------------------------
    has_critical = any(v.level == "critical" for v in violations)
    passed = not has_critical

    # Summary para display
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
