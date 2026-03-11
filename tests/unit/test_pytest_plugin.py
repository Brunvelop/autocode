"""
test_pytest_plugin.py — Tests for autocode.pytest_plugin

Covers:
- Option registration (--autocode-health flag via pytest_addoption)
- Marker registration (health marker via pytest_configure)
- Session fixtures provided by the plugin:
    - health_config  → HealthConfig
    - all_file_metrics → list[FileMetrics]
    - coupling_result  → tuple(coupling, circulars)

Note: these tests run using the plugin fixtures directly (not the
tests/health/conftest.py fixtures, which are scoped to tests/health/).
"""
from __future__ import annotations

import pytest

from autocode.core.code.health import HealthConfig
from autocode.core.code.models import FileMetrics, PackageCoupling


# ==============================================================================
# PLUGIN REGISTRATION
# ==============================================================================


class TestPluginRegistration:
    """Verifica que el plugin registra correctamente opciones y markers."""

    def test_health_marker_registered(self, pytestconfig):
        """El marker 'health' debe estar registrado en la configuración de pytest."""
        markers = pytestconfig.getini("markers")
        assert any("health" in m for m in markers), (
            "Marker 'health' no está registrado. "
            "El plugin debe llamar a config.addinivalue_line() en pytest_configure."
        )

    def test_autocode_health_option_registered(self, pytestconfig):
        """El flag --autocode-health debe estar registrado como opción CLI."""
        # Si la opción no estuviera registrada, getoption lanzaría ValueError
        val = pytestconfig.getoption("autocode_health")
        # El valor es False por defecto cuando el flag no se pasa
        assert val is False or val is True, (
            "La opción --autocode-health no está registrada en el parser de pytest."
        )

    def test_autocode_health_default_is_false(self, pytestconfig):
        """El flag --autocode-health es False por defecto (sin pasar el flag)."""
        val = pytestconfig.getoption("autocode_health")
        assert val is False


# ==============================================================================
# PLUGIN FIXTURES
# ==============================================================================


class TestPluginFixtures:
    """Verifica que las fixtures del plugin devuelven los tipos correctos."""

    def test_health_config_fixture_type(self, health_config):
        """Fixture health_config devuelve una instancia de HealthConfig."""
        assert isinstance(health_config, HealthConfig), (
            f"health_config debe ser HealthConfig, got {type(health_config)}"
        )

    def test_health_config_has_all_fields(self, health_config):
        """Fixture health_config tiene todos los campos esperados."""
        assert hasattr(health_config, "critical_mi")
        assert hasattr(health_config, "warning_mi")
        assert hasattr(health_config, "critical_function_cc")
        assert hasattr(health_config, "max_rank_f_functions")
        assert hasattr(health_config, "max_circular_deps")
        assert hasattr(health_config, "exclude")

    def test_all_file_metrics_fixture_type(self, all_file_metrics):
        """Fixture all_file_metrics devuelve una lista."""
        assert isinstance(all_file_metrics, list), (
            f"all_file_metrics debe ser list, got {type(all_file_metrics)}"
        )

    def test_all_file_metrics_contains_file_metrics(self, all_file_metrics):
        """Todos los elementos de all_file_metrics son FileMetrics."""
        if all_file_metrics:
            for fm in all_file_metrics:
                assert isinstance(fm, FileMetrics), (
                    f"Elemento debe ser FileMetrics, got {type(fm)}"
                )

    def test_all_file_metrics_not_empty_in_tracked_repo(self, all_file_metrics):
        """En un repo con archivos trackeados, all_file_metrics no debe ser vacío."""
        # autocode tiene archivos .py trackeados, así que esto debería ser True
        assert len(all_file_metrics) > 0, (
            "all_file_metrics está vacío. "
            "En el repo de autocode debe haber archivos .py trackeados por git."
        )

    def test_coupling_result_fixture_type(self, coupling_result):
        """Fixture coupling_result devuelve una tupla de dos elementos."""
        assert isinstance(coupling_result, tuple), (
            f"coupling_result debe ser tuple, got {type(coupling_result)}"
        )
        assert len(coupling_result) == 2, (
            f"coupling_result debe tener 2 elementos, got {len(coupling_result)}"
        )

    def test_coupling_result_first_element_is_list(self, coupling_result):
        """Primer elemento de coupling_result es una lista (coupling)."""
        coupling, _ = coupling_result
        assert isinstance(coupling, list), (
            f"coupling debe ser list, got {type(coupling)}"
        )

    def test_coupling_result_second_element_is_list(self, coupling_result):
        """Segundo elemento de coupling_result es una lista (circulares)."""
        _, circulars = coupling_result
        assert isinstance(circulars, list), (
            f"circulars debe ser list, got {type(circulars)}"
        )
