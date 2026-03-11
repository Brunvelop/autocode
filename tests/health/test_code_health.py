"""
test_code_health.py — Health gates for THIS project (autocode itself).

The actual gate implementations live in autocode.testing.gates (installable package).
This file re-exports them so that pytest collects them when running:

    pytest -m health           # collected from this file (autocode dev workflow)
    pytest --autocode-health   # collected from autocode/testing/gates.py (consumer workflow)

Fixtures (health_config, all_file_metrics, coupling_result) are provided
automatically by autocode.testing.plugin via the pytest11 entry-point.
"""
from autocode.testing.gates import TestFileHealth, TestFunctionHealth, TestProjectHealth

__all__ = ["TestFileHealth", "TestFunctionHealth", "TestProjectHealth"]
