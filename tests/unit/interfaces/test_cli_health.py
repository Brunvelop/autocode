"""
Tests for the health-check CLI command.

TDD: tests written before implementation.
Verifies that `autocode health-check` runs correctly, produces valid output
in table and JSON formats, and respects --strict mode.
"""
import json

import pytest
from click.testing import CliRunner

from autocode.interfaces.cli import app


class TestHealthCheckCommand:
    """Tests for the `health-check` Click command."""

    def test_command_appears_in_help(self):
        """health-check debe aparecer en el help principal del CLI."""
        runner = CliRunner()
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        assert "health-check" in result.output

    def test_runs_without_crashing(self):
        """health-check debe ejecutar sin excepción no controlada.

        El exit code puede ser 0 (passed) o 1 (violations found), ambos son válidos.
        Lo que NO debe ocurrir es un crash (exit_code 2+ por error de Click,
        o una excepción no capturada).
        """
        runner = CliRunner()
        result = runner.invoke(app, ["health-check"])
        # exit_code 0 = passed, 1 = critical violations — ambos correctos
        # exit_code 2 = Click error (bad param), >1 = crash — inválidos
        assert result.exit_code in (0, 1), (
            f"Unexpected exit code {result.exit_code}. Output:\n{result.output}"
            f"\nException: {result.exception}"
        )

    def test_table_output_is_default(self):
        """Sin --format, la salida debe ser tabla (contiene 'CODE HEALTH')."""
        runner = CliRunner()
        result = runner.invoke(app, ["health-check"])
        assert result.exit_code in (0, 1)
        assert "CODE HEALTH" in result.output

    def test_table_shows_pass_or_fail_status(self):
        """La tabla debe mostrar PASSED o FAILED como resultado final."""
        runner = CliRunner()
        result = runner.invoke(app, ["health-check", "--format", "table"])
        assert result.exit_code in (0, 1)
        assert "PASSED" in result.output or "FAILED" in result.output

    def test_table_shows_summary_metrics(self):
        """La tabla debe mostrar métricas de resumen (Files analyzed, Avg MI…)."""
        runner = CliRunner()
        result = runner.invoke(app, ["health-check", "--format", "table"])
        assert result.exit_code in (0, 1)
        assert "Files analyzed" in result.output

    def test_json_output_is_valid_json(self):
        """--format json debe producir JSON parseable."""
        runner = CliRunner()
        result = runner.invoke(app, ["health-check", "--format", "json"])
        assert result.exit_code in (0, 1)
        # Should not raise
        data = json.loads(result.output)
        assert isinstance(data, dict)

    def test_json_output_has_required_keys(self):
        """JSON debe contener 'passed', 'summary' y 'violations'."""
        runner = CliRunner()
        result = runner.invoke(app, ["health-check", "--format", "json"])
        assert result.exit_code in (0, 1)
        data = json.loads(result.output)
        assert "passed" in data
        assert "summary" in data
        assert "violations" in data

    def test_json_passed_matches_exit_code(self):
        """data['passed']==True ↔ exit_code==0, data['passed']==False ↔ exit_code==1."""
        runner = CliRunner()
        result = runner.invoke(app, ["health-check", "--format", "json"])
        data = json.loads(result.output)
        if data["passed"]:
            assert result.exit_code == 0
        else:
            assert result.exit_code == 1

    def test_json_violations_have_correct_structure(self):
        """Cada violation en el JSON debe tener los campos obligatorios."""
        runner = CliRunner()
        result = runner.invoke(app, ["health-check", "--format", "json"])
        data = json.loads(result.output)
        for violation in data["violations"]:
            assert "rule" in violation
            assert "level" in violation
            assert "path" in violation
            assert "value" in violation
            assert "threshold" in violation
            # detail es opcional (puede ser None)
            assert "detail" in violation

    def test_json_violations_levels_are_valid(self):
        """Cada violation debe tener level 'critical' o 'warning'."""
        runner = CliRunner()
        result = runner.invoke(app, ["health-check", "--format", "json"])
        data = json.loads(result.output)
        for violation in data["violations"]:
            assert violation["level"] in ("critical", "warning"), (
                f"Invalid level: {violation['level']}"
            )

    def test_strict_mode_runs_without_crashing(self):
        """--strict debe ejecutar sin crash usando HealthConfig() por defecto."""
        runner = CliRunner()
        result = runner.invoke(app, ["health-check", "--strict"])
        assert result.exit_code in (0, 1), (
            f"Unexpected exit code {result.exit_code}. Output:\n{result.output}"
        )

    def test_strict_mode_uses_stricter_thresholds(self):
        """--strict debe usar umbrales más estrictos que los del pyproject.toml.

        El pyproject.toml del proyecto tiene umbrales relajados (ej: critical_mi=3.0).
        Con --strict se usan HealthConfig() defaults (critical_mi=20.0), lo que
        podría producir más violations. Al menos verificamos que produce salida válida.
        """
        runner = CliRunner()
        result_default = runner.invoke(app, ["health-check", "--format", "json"])
        result_strict = runner.invoke(app, ["health-check", "--strict", "--format", "json"])

        assert result_strict.exit_code in (0, 1)

        default_data = json.loads(result_default.output)
        strict_data = json.loads(result_strict.output)

        # Con --strict deberíamos tener >= violations que con defaults relajados
        assert len(strict_data["violations"]) >= len(default_data["violations"])

    def test_help_shows_options(self):
        """El help del comando debe mostrar --format, --strict, --project-root."""
        runner = CliRunner()
        result = runner.invoke(app, ["health-check", "--help"])
        assert result.exit_code == 0
        assert "--format" in result.output
        assert "--strict" in result.output
        assert "--project-root" in result.output

    def test_format_choice_validation(self):
        """--format solo acepta 'table' o 'json', otros valores dan error."""
        runner = CliRunner()
        result = runner.invoke(app, ["health-check", "--format", "xml"])
        assert result.exit_code != 0
        assert "Invalid value" in result.output or "invalid choice" in result.output.lower()
