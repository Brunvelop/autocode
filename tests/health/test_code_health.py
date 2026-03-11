"""
test_code_health.py — Health gates for THIS project (autocode itself).

The actual gate implementations live in autocode.health_gates (installable package).
This file re-exports them so that pytest collects them when running:

    pytest -m health           # collected from this file (autocode dev workflow)
    pytest --autocode-health   # collected from autocode/health_gates.py (consumer workflow)

Fixtures (health_config, all_file_metrics, coupling_result) are provided
automatically by autocode.pytest_plugin via the pytest11 entry-point.
"""
from autocode.health_gates import TestFileHealth, TestFunctionHealth, TestProjectHealth

__all__ = ["TestFileHealth", "TestFunctionHealth", "TestProjectHealth"]
