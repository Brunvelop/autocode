"""
conftest.py — Health tests configuration (backward compatibility shim).

All fixtures (health_config, all_file_metrics, coupling_result) and the
pytest_terminal_summary hook are now provided by autocode.pytest_plugin,
which is auto-registered via the pytest11 entry-point when autocode is
installed.

This file is intentionally empty — no local fixtures needed.

To run health gates:
    pytest -m health                # uses plugin fixtures + tests/health/test_code_health.py
    pytest --autocode-health        # uses plugin fixtures + autocode/health_gates.py (installable)
"""
