"""
autocode.testing — Pytest plugin and built-in quality gate tests.

Provides pytest integration for code health quality gates:
- plugin.py:  pytest plugin (registered via pytest11 entry-point)
- gates.py:   built-in quality gate test classes (collected by the plugin)

Usage in consumer projects:
    pytest --autocode-health
"""
