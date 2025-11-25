"""
Tests for autocode.interfaces.models module.

Tests the Pydantic models that define input/output contracts for functions
registered in the registry, ensuring data validation and type safety.
"""
import pytest
from typing import Any
from pydantic import ValidationError

from autocode.interfaces.models import (
    ExplicitParam, FunctionInfo, ExplicitInput, GenericOutput
)


class TestExplicitParam:
    """Tests for ExplicitParam model - parameter definitions for registry functions."""
    
    def test_explicit_param_creation_required(self):
        """Test creating required parameter without default."""
        param = ExplicitParam(
            name="test_param",
            type=int,
            required=True,
            description="A test parameter"
        )
        
        assert param.name == "test_param"
        assert param.type == int
        assert param.default is None
        assert param.required is True
        assert param.description == "A test parameter"
    
    def test_explicit_param_creation_optional(self):
        """Test creating optional parameter with default value."""
        param = ExplicitParam(
            name="optional_param",
            type=str,
            default="default_value",
            required=False,
            description="An optional parameter"
        )
        
        assert param.name == "optional_param"
        assert param.type == str
        assert param.default == "default_value"
        assert param.required is False
        assert param.description == "An optional parameter"
    
    @pytest.mark.parametrize("param_type", [int, str, float, bool, list, dict, Any])
    def test_explicit_param_supports_various_types(self, param_type):
        """Test that ExplicitParam supports various Python types."""
        param = ExplicitParam(
            name="test",
            type=param_type,
            required=True,
            description="Test param"
        )
        
        assert param.type == param_type
    
    def test_explicit_param_validation_required_fields(self):
        """Test that required fields are validated."""
        with pytest.raises(ValidationError):
            ExplicitParam()  # Missing required fields
        
        with pytest.raises(ValidationError):
            ExplicitParam(name="test")  # Missing other required fields


class TestFunctionInfo:
    """Tests for FunctionInfo model - complete function metadata for registry."""
    
    def test_function_info_creation_minimal(self, sample_function):
        """Test creating FunctionInfo with minimal required fields."""
        func_info = FunctionInfo(
            name="test_func",
            func=sample_function,
            description="Test function"
        )
        
        assert func_info.name == "test_func"
        assert func_info.func == sample_function
        assert func_info.description == "Test function"
        assert func_info.params == []  # Default empty list
        assert func_info.http_methods == ["GET", "POST"]  # Default methods
    
    def test_function_info_creation_complete(self, sample_function):
        """Test creating FunctionInfo with all fields specified."""
        params = [
            ExplicitParam(name="x", type=int, required=True, description="First param"),
            ExplicitParam(name="y", type=str, default="test", required=False, description="Second param")
        ]
        
        func_info = FunctionInfo(
            name="complete_func",
            func=sample_function,
            description="Complete test function",
            params=params,
            http_methods=["GET", "POST", "PUT"]
        )
        
        assert func_info.name == "complete_func"
        assert func_info.func == sample_function
        assert func_info.description == "Complete test function"
        assert len(func_info.params) == 2
        assert func_info.params[0].name == "x"
        assert func_info.params[1].name == "y"
        assert func_info.http_methods == ["GET", "POST", "PUT"]
    
    def test_function_info_callable_validation(self):
        """Test that FunctionInfo validates callable functions."""
        # This should work
        func_info = FunctionInfo(
            name="test",
            func=lambda x: x,
            description="Test lambda"
        )
        assert callable(func_info.func)
        
        # Test with regular function
        def test_func():
            return "test"
        
        func_info = FunctionInfo(
            name="test",
            func=test_func,
            description="Test function"
        )
        assert callable(func_info.func)
    
    def test_function_info_validation_required_fields(self):
        """Test that required fields are validated."""
        with pytest.raises(ValidationError):
            FunctionInfo()  # Missing all required fields
        
        with pytest.raises(ValidationError):
            FunctionInfo(name="test")  # Missing func and description


class TestExplicitInput:
    """Tests for ExplicitInput model - generic input handling."""
    
    def test_explicit_input_creation_empty(self):
        """Test creating ExplicitInput with default empty params."""
        input_model = ExplicitInput()
        
        assert input_model.params == {}
    
    def test_explicit_input_creation_with_params(self):
        """Test creating ExplicitInput with parameters."""
        params = {"x": 5, "y": "test", "z": True}
        input_model = ExplicitInput(params=params)
        
        assert input_model.params == params
    
    @pytest.mark.parametrize("params", [
        {"single": 1},
        {"multiple": 1, "params": "test", "here": True},
        {"nested": {"inner": "value"}},
        {"list_param": [1, 2, 3]},
    ])
    def test_explicit_input_various_param_types(self, params):
        """Test ExplicitInput with various parameter types."""
        input_model = ExplicitInput(params=params)
        assert input_model.params == params


class TestGenericOutput:
    """Tests for GenericOutput model - standardized response format."""
    
    def test_generic_output_minimal(self):
        """Test creating GenericOutput with just result."""
        output = GenericOutput(result="test_result")
        
        assert output.result == "test_result"
        assert output.success is True  # Default value
        assert output.message is None  # Default value
    
    def test_generic_output_complete(self):
        """Test creating GenericOutput with all fields."""
        output = GenericOutput(
            result={"data": "test"},
            success=False,
            message="Operation failed"
        )
        
        assert output.result == {"data": "test"}
        assert output.success is False
        assert output.message == "Operation failed"
    
    @pytest.mark.parametrize("result", [
        "string_result",
        123,
        {"dict": "result"},
        [1, 2, 3],
        True,
        None,
    ])
    def test_generic_output_various_result_types(self, result):
        """Test GenericOutput with various result types."""
        output = GenericOutput(result=result)
        assert output.result == result
        assert output.success is True
    
    def test_generic_output_dict_conversion(self):
        """Test that GenericOutput can be converted to dict."""
        output = GenericOutput(
            result="test",
            success=True,
            message="Success"
        )
        
        output_dict = output.model_dump()
        expected = {
            "result": "test",
            "success": True,
            "message": "Success"
        }
        
        assert output_dict == expected
    
    def test_generic_output_validation_required_fields(self):
        """Test that result field is required."""
        with pytest.raises(ValidationError):
            GenericOutput()  # Missing required result field


class TestModelsIntegration:
    """Integration tests for models working together."""
    
    def test_function_info_with_explicit_params(self, sample_function):
        """Test FunctionInfo containing ExplicitParam instances."""
        params = [
            ExplicitParam(name="x", type=int, required=True, description="First"),
            ExplicitParam(name="y", type=str, default="default", required=False, description="Second")
        ]
        
        func_info = FunctionInfo(
            name="integrated_test",
            func=sample_function,
            description="Integration test function",
            params=params
        )
        
        # Verify the integration
        assert len(func_info.params) == 2
        assert all(isinstance(p, ExplicitParam) for p in func_info.params)
        
        # Verify param details
        x_param = func_info.params[0]
        y_param = func_info.params[1]
        
        assert x_param.name == "x" and x_param.required is True
        assert y_param.name == "y" and y_param.required is False and y_param.default == "default"
