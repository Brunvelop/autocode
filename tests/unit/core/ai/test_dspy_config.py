"""
Tests for DSPy configuration and introspection utilities.
"""
import json
import pytest
from autocode.core.ai.dspy_utils import get_all_module_kwargs_schemas, get_module_kwargs_schema

def test_module_kwargs_serialization():
    """
    Test that module kwargs schemas are JSON serializable.
    This is crucial for the API endpoint /get_chat_config.
    """
    schemas = get_all_module_kwargs_schemas()
    
    try:
        json_output = json.dumps(schemas)
        assert json_output is not None
        assert len(json_output) > 0
    except TypeError as e:
        pytest.fail(f"Serialization failed: {e}")

def test_tools_param_excluded():
    """
    Test that 'tools' parameter is excluded from the schema for ReAct.
    """
    # Specifically check ReAct since it has a 'tools' parameter in __init__
    schema = get_module_kwargs_schema('ReAct')
    
    # Check new structure
    assert 'params' in schema
    assert 'supports_tools' in schema
    assert schema['supports_tools'] is True
    
    param_names = [p['name'] for p in schema['params']]
    assert 'tools' not in param_names, "'tools' parameter should be excluded from schema params list"
