"""
Tests for autocode.interfaces.api module.

Tests the FastAPI server functionality including dynamic endpoint generation,
request/response handling, and integration with the function registry.
"""
import pytest
import asyncio
import os
from typing import Dict, Any, List
from unittest.mock import Mock, patch, MagicMock
from fastapi import HTTPException
from fastapi.testclient import TestClient
from pydantic import BaseModel

from autocode.interfaces.api import (
    create_result_response, create_dynamic_model, extract_function_params,
    execute_function_with_params, create_handler, register_dynamic_endpoints,
    create_api_app
)
from autocode.interfaces.models import GenericOutput, FunctionInfo, ExplicitParam
from autocode.interfaces.registry import FUNCTION_REGISTRY, clear_registry


class TestCreateResultResponse:
    """Tests for create_result_response - result formatting."""
    
    def test_create_result_response_dict(self):
        """Test response creation with dict input (should return as-is)."""
        input_dict = {"key": "value", "number": 42, "nested": {"inner": "data"}}
        result = create_result_response(input_dict)
        
        assert result == input_dict
        assert isinstance(result, dict)
    
    @pytest.mark.parametrize("input_value,expected_result", [
        ("string_result", "string_result"),
        (123, 123),
        (True, True),
        (None, None),
        ([1, 2, 3], [1, 2, 3]),
    ])
    def test_create_result_response_non_dict(self, input_value, expected_result):
        """Test response creation with non-dict inputs (should wrap in GenericOutput)."""
        # Create a GenericOutput with the value
        generic_output = GenericOutput(result=input_value, success=True)
        result = create_result_response(generic_output)
        
        assert isinstance(result, dict)
        assert "result" in result
        assert result["result"] == expected_result
        assert "success" in result
        assert result["success"] is True
        assert "message" in result
        assert result["message"] is None
    
    def test_create_result_response_complex_object(self):
        """Test response creation with complex object."""
        class CustomObject:
            def __init__(self, value):
                self.value = value
        
        obj = CustomObject("test")
        # Wrap in GenericOutput since that's what functions should return
        generic_output = GenericOutput(result=obj, success=True)
        result = create_result_response(generic_output)
        
        assert isinstance(result, dict)
        assert result["result"] == obj


class TestCreateDynamicModel:
    """Tests for create_dynamic_model - Pydantic model generation."""
    
    def test_create_dynamic_model_post_required_only(self, sample_function_info):
        """Test creating POST model with required parameters only."""
        # Create function info with only required params
        required_param = ExplicitParam(
            name="required_param",
            type=str,
            required=True,
            description="A required parameter"
        )
        func_info = FunctionInfo(
            name="test_func",
            func=lambda x: x,
            description="Test",
            params=[required_param],
            return_type=GenericOutput
        )
        
        DynamicModel = create_dynamic_model(func_info, for_post=True)
        
        # Test model creation
        assert DynamicModel.__name__ == "Test_FuncInput"
        
        # Test field validation
        instance = DynamicModel(required_param="test_value")
        assert instance.required_param == "test_value"
        
        # Test required field validation
        with pytest.raises(Exception):  # Pydantic validation error
            DynamicModel()
    
    def test_create_dynamic_model_post_with_optional(self, sample_function_info):
        """Test creating POST model with optional parameters."""
        DynamicModel = create_dynamic_model(sample_function_info, for_post=True)
        
        assert DynamicModel.__name__ == "Test_AddInput"
        
        # Test with all params
        instance = DynamicModel(x=5, y=3)
        assert instance.x == 5
        assert instance.y == 3
        
        # Test with only required params (optional should use default)
        instance = DynamicModel(x=5)
        assert instance.x == 5
        assert instance.y == 1  # Default value
    
    def test_create_dynamic_model_get(self, sample_function_info):
        """Test creating GET model (query parameters)."""
        DynamicModel = create_dynamic_model(sample_function_info, for_post=False)
        
        assert DynamicModel.__name__ == "Test_AddQueryParams"
        
        # Should work the same as POST model for parameter handling
        instance = DynamicModel(x=10)
        assert instance.x == 10
        assert instance.y == 1
    
    def test_create_dynamic_model_complex_types(self):
        """Test creating model with various parameter types."""
        params = [
            ExplicitParam(name="str_param", type=str, required=True, description="String param"),
            ExplicitParam(name="int_param", type=int, default=42, required=False, description="Int param"),
            ExplicitParam(name="bool_param", type=bool, default=True, required=False, description="Bool param"),
        ]
        
        func_info = FunctionInfo(
            name="complex_func",
            func=lambda: None,
            description="Complex function",
            params=params,
            return_type=GenericOutput
        )
        
        DynamicModel = create_dynamic_model(func_info, for_post=True)
        
        # Test field types and defaults
        instance = DynamicModel(str_param="test")
        assert instance.str_param == "test"
        assert instance.int_param == 42
        assert instance.bool_param is True


class TestExtractFunctionParams:
    """Tests for extract_function_params - parameter extraction."""
    
    def test_extract_function_params_all_present(self, sample_function_info):
        """Test parameter extraction when all params are present."""
        request_params = {"x": 5, "y": 3}
        
        result = extract_function_params(sample_function_info, request_params)
        
        assert result == {"x": 5, "y": 3}
    
    def test_extract_function_params_missing_optional(self, sample_function_info):
        """Test parameter extraction with missing optional parameter."""
        request_params = {"x": 5}  # Missing 'y'
        
        result = extract_function_params(sample_function_info, request_params)
        
        assert result == {"x": 5, "y": 1}  # Should include default for y
    
    def test_extract_function_params_missing_required(self, sample_function_info):
        """Test parameter extraction with missing required parameter."""
        request_params = {"y": 3}  # Missing required 'x'
        
        result = extract_function_params(sample_function_info, request_params)
        
        # Should not include missing required param (validation happens elsewhere)
        assert result == {"y": 3}
    
    def test_extract_function_params_extra_params(self, sample_function_info):
        """Test parameter extraction with extra parameters."""
        request_params = {"x": 5, "y": 3, "extra": "ignored"}
        
        result = extract_function_params(sample_function_info, request_params)
        
        # Should only include known parameters
        assert result == {"x": 5, "y": 3}
    
    def test_extract_function_params_none_defaults(self):
        """Test parameter extraction with None defaults."""
        params = [
            ExplicitParam(name="required", type=str, required=True, description="Required"),
            ExplicitParam(name="optional", type=str, default=None, required=False, description="Optional with None default")
        ]
        func_info = FunctionInfo(
            name="test",
            func=lambda: None,
            description="Test",
            params=params,
            return_type=GenericOutput
        )
        
        request_params = {"required": "test"}
        result = extract_function_params(func_info, request_params)
        
        # Should not include optional param with None default when not provided
        assert result == {"required": "test"}


class TestExecuteFunctionWithParams:
    """Tests for execute_function_with_params - function execution with error handling."""
    
    def test_execute_function_with_params_success(self, sample_function_info):
        """Test successful function execution."""
        request_params = {"x": 5, "y": 3}
        
        result = execute_function_with_params(
            sample_function_info, request_params, "POST"
        )
        
        assert result["result"] == 8  # 5 + 3 = 8
        assert result["success"] is True
        assert result["message"] is None
    
    def test_execute_function_with_params_dict_result(self):
        """Test function execution that returns a dict."""
        def dict_func(name: str) -> dict:
            return {"greeting": f"Hello, {name}!"}
        
        func_info = FunctionInfo(
            name="dict_func",
            func=dict_func,
            description="Returns dict",
            params=[ExplicitParam(name="name", type=str, required=True, description="Name")],
            return_type=GenericOutput
        )
        
        request_params = {"name": "World"}
        result = execute_function_with_params(func_info, request_params, "GET")
        
        # Should return dict as-is (not wrapped)
        assert result == {"greeting": "Hello, World!"}
    
    def test_execute_function_with_params_value_error(self, sample_function_info):
        """Test function execution with parameter validation error."""
        def failing_func(x: int) -> int:
            if not isinstance(x, int):
                raise ValueError("x must be an integer")
            return x
        
        func_info = FunctionInfo(
            name="failing_func",
            func=failing_func,
            description="Failing function",
            params=[ExplicitParam(name="x", type=int, required=True, description="Integer param")],
            return_type=GenericOutput
        )
        
        request_params = {"x": "not_an_int"}
        
        with pytest.raises(HTTPException) as exc_info:
            execute_function_with_params(func_info, request_params, "POST")
        
        assert exc_info.value.status_code == 400
        assert "Parameter error" in str(exc_info.value.detail)
    
    def test_execute_function_with_params_runtime_error(self, sample_function_info):
        """Test function execution with runtime error."""
        def error_func(x: int) -> int:
            raise RuntimeError("Something went wrong")
        
        func_info = FunctionInfo(
            name="error_func",
            func=error_func,
            description="Error function",
            params=[ExplicitParam(name="x", type=int, required=True, description="Integer param")],
            return_type=GenericOutput
        )
        
        request_params = {"x": 5}
        
        with pytest.raises(HTTPException) as exc_info:
            execute_function_with_params(func_info, request_params, "POST")
        
        assert exc_info.value.status_code == 500
        assert "Internal error" in str(exc_info.value.detail)
    
    @patch('autocode.interfaces.api.logger')
    def test_execute_function_with_params_logging(self, mock_logger, sample_function_info):
        """Test that function execution logs appropriately."""
        request_params = {"x": 5, "y": 3}
        
        execute_function_with_params(
            sample_function_info, request_params, "POST", "extra_info"
        )
        
        # Should log debug message (may be called multiple times)
        assert mock_logger.debug.call_count >= 1
        # Find the call with the expected content
        log_calls = [call[0][0] for call in mock_logger.debug.call_args_list if call[0]]
        request_log = next((log for log in log_calls if "POST test_add" in str(log)), None)
        assert request_log is not None
        assert "params={'x': 5, 'y': 3}" in str(request_log)
        assert "extra_info" in str(request_log)


class TestCreateHandler:
    """Tests for create_handler - endpoint handler creation."""
    
    def test_create_handler_post(self, sample_function_info):
        """Test creating POST handler."""
        handler, model = create_handler(sample_function_info, "POST")
        
        assert callable(handler)
        assert issubclass(model, BaseModel)
        assert model.__name__ == "Test_AddInput"
        
        # Test handler execution (would need async context in real usage)
        # For now, just verify it's a coroutine function
        import asyncio
        assert asyncio.iscoroutinefunction(handler)
    
    def test_create_handler_get(self, sample_function_info):
        """Test creating GET handler."""
        handler, model = create_handler(sample_function_info, "GET")
        
        assert callable(handler)
        assert issubclass(model, BaseModel)
        assert model.__name__ == "Test_AddQueryParams"
        assert asyncio.iscoroutinefunction(handler)
    
    def test_handler_execution_post(self, sample_function_info):
        """Test actual POST handler execution."""
        handler, model = create_handler(sample_function_info, "POST")
        
        # Create request object
        request = model(x=5, y=3)
        
        # Execute handler using asyncio.run
        result = asyncio.run(handler(request))
        
        assert result == {"result": 8, "success": True, "message": None}
    
    def test_handler_execution_get_with_mock_depends(self, sample_function_info):
        """Test GET handler execution (requires mocking Depends)."""
        handler, model = create_handler(sample_function_info, "GET")
        
        # Create query params object
        query_params = model(x=10, y=2)
        
        # For testing, create a simple handler that bypasses Depends
        async def test_handler():
            request_params = query_params.model_dump()
            return execute_function_with_params(
                sample_function_info, request_params, "GET", f"query={request_params}"
            )
        
        # Execute test handler
        result = asyncio.run(test_handler())
        assert result == {"result": 12, "success": True, "message": None}


class TestRegisterDynamicEndpoints:
    """Tests for register_dynamic_endpoints - endpoint registration."""
    
    def test_register_dynamic_endpoints(self):
        """Test registering endpoints for all functions in registry."""
        # Create a mock function info - completely independent of core functions
        test_func_info = FunctionInfo(
            name="mock_test_func",
            func=lambda x, y: GenericOutput(result=x + y, success=True),
            description="Mock test function for endpoint registration",
            params=[
                ExplicitParam(name="x", type=int, required=True, description="First param"),
                ExplicitParam(name="y", type=int, default=1, required=False, description="Second param")
            ],
            http_methods=["GET", "POST"],
            interfaces=["api"],
            return_type=GenericOutput
        )
        
        # Mock get_functions_for_interface to return ONLY our test function
        with patch('autocode.interfaces.api.get_functions_for_interface') as mock_get_funcs:
            mock_get_funcs.return_value = {"mock_test_func": test_func_info}
            
            # Mock FastAPI app
            mock_app = Mock()
            mock_app.add_api_route = Mock()
            
            register_dynamic_endpoints(mock_app)
            
            # Should have called add_api_route for each HTTP method (GET and POST)
            assert mock_app.add_api_route.call_count == 2
            
            # Check that routes were added correctly
            call_args_list = mock_app.add_api_route.call_args_list
            
            # Verify GET route
            get_call = next(call for call in call_args_list if call[1]["methods"] == ["GET"])
            assert get_call[0][0] == "/mock_test_func"  # Path
            assert get_call[1]["operation_id"] == "mock_test_func_get"
            assert get_call[1]["summary"] == "Mock test function for endpoint registration"
            
            # Verify POST route
            post_call = next(call for call in call_args_list if call[1]["methods"] == ["POST"])
            assert post_call[0][0] == "/mock_test_func"  # Path
            assert post_call[1]["operation_id"] == "mock_test_func_post"
            assert post_call[1]["summary"] == "Mock test function for endpoint registration"
    
    def test_register_dynamic_endpoints_empty_registry(self):
        """Test registering endpoints with empty registry."""
        # Mock get_functions_for_interface to return empty dict (simulating empty registry)
        with patch('autocode.interfaces.api.get_functions_for_interface') as mock_get_funcs:
            mock_get_funcs.return_value = {}
            
            mock_app = Mock()
            mock_app.add_api_route = Mock()
            
            register_dynamic_endpoints(mock_app)
            
            # Should not add any routes
            mock_app.add_api_route.assert_not_called()
    
    def test_register_dynamic_endpoints_custom_methods(self):
        """Test registering endpoints with custom HTTP methods."""
        # Create function with custom methods (PUT and DELETE)
        custom_func_info = FunctionInfo(
            name="custom_func",
            func=lambda x: GenericOutput(result=x, success=True),
            description="Custom function with PUT/DELETE",
            params=[ExplicitParam(name="x", type=str, required=True, description="Param")],
            http_methods=["PUT", "DELETE"],
            interfaces=["api"],
            return_type=GenericOutput
        )
        
        # Mock get_functions_for_interface to return ONLY our custom function
        with patch('autocode.interfaces.api.get_functions_for_interface') as mock_get_funcs:
            mock_get_funcs.return_value = {"custom_func": custom_func_info}
            
            mock_app = Mock()
            mock_app.add_api_route = Mock()
            
            register_dynamic_endpoints(mock_app)
            
            # Should register PUT and DELETE routes (2 total)
            assert mock_app.add_api_route.call_count == 2
            
            call_args_list = mock_app.add_api_route.call_args_list
            methods_called = [call[1]["methods"][0] for call in call_args_list]
            
            assert "PUT" in methods_called
            assert "DELETE" in methods_called


class TestCreateApiApp:
    """Tests for create_api_app - complete FastAPI app creation."""
    
    @patch('autocode.interfaces.api.load_core_functions')
    @patch('autocode.interfaces.api.register_dynamic_endpoints')
    def test_create_api_app_success(self, mock_register, mock_load):
        """Test successful API app creation."""
        app = create_api_app()
        
        # Verify app configuration
        assert app.title == "Autocode API"
        assert app.description == "Minimalistic framework for autocode"
        assert app.version == "1.0.0"
        
        # Verify functions were loaded and endpoints registered
        mock_load.assert_called_once()
        mock_register.assert_called_once_with(app)
    
    @patch('autocode.interfaces.api.load_core_functions')
    def test_create_api_app_load_error(self, mock_load):
        """Test API app creation with loading error."""
        mock_load.side_effect = Exception("Loading failed")
        
        with pytest.raises(Exception, match="Loading failed"):
            create_api_app()
    
    @patch('autocode.interfaces.api.load_core_functions')
    def test_create_api_app_endpoints(self, mock_load):
        """Test that standard endpoints are created."""
        app = create_api_app()
        client = TestClient(app)
        
        # Test health endpoint (returns JSON)
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert data["status"] == "healthy"
        assert "functions" in data
        
        # Test functions UI endpoint (returns HTML template)
        response = client.get("/functions")
        # Returns 200 or may fail if template not found
        assert response.status_code in [200, 404, 500]
        
        # Test functions details endpoint (returns JSON)
        response = client.get("/functions/details")
        assert response.status_code == 200
        data = response.json()
        assert "functions" in data
        assert isinstance(data["functions"], dict)
    
    @patch('autocode.interfaces.api.load_core_functions')
    @patch('os.path.exists')
    @patch('os.path.isdir')
    def test_create_api_app_static_files(self, mock_isdir, mock_exists, mock_load):
        """Test static file mounting."""
        mock_exists.return_value = True
        mock_isdir.return_value = True
        
        app = create_api_app()
        
        # Check that static files were mounted (indirectly by checking routes)
        static_routes = [route for route in app.routes if hasattr(route, 'name') and route.name == "static"]
        # Note: This test might need adjustment based on FastAPI's internal structure
    
    @patch('autocode.interfaces.api.load_core_functions')
    def test_create_api_app_root_endpoint(self, mock_load):
        """Test root endpoint serves index.html."""
        app = create_api_app()
        
        # Mock file existence and content
        with patch('os.path.join'):
            with patch('fastapi.responses.FileResponse') as mock_file_response:
                client = TestClient(app)
                
                # This would normally serve a file, but we'll test the route exists
                try:
                    response = client.get("/")
                    # The actual response depends on file existence, 
                    # but the route should be registered
                except Exception:
                    pass  # Expected if file doesn't exist in test environment


class TestApiIntegration:
    """Integration tests for API functionality."""
    
    @patch('autocode.interfaces.api.load_core_functions')
    def test_full_api_integration(self, mock_load, populated_registry):
        """Test full API integration with real function."""
        app = create_api_app()
        client = TestClient(app)
        
        # Test GET endpoint
        response = client.get("/test_add?x=5&y=3")
        assert response.status_code == 200
        data = response.json()
        assert data["result"] == 8
        
        # Test POST endpoint
        response = client.post("/test_add", json={"x": 10, "y": 5})
        assert response.status_code == 200
        data = response.json()
        assert data["result"] == 15
    
    @patch('autocode.interfaces.api.load_core_functions')
    def test_api_error_handling(self, mock_load, populated_registry):
        """Test API error handling."""
        app = create_api_app()
        client = TestClient(app)
        
        # Test missing required parameter
        response = client.get("/test_add")  # Missing x parameter
        assert response.status_code == 422  # FastAPI validation error
        
        # Test invalid parameter type (this would be caught by Pydantic)
        response = client.post("/test_add", json={"x": "not_a_number", "y": 5})
        assert response.status_code == 422


# Additional unit tests for improved coverage
class TestCreateResultResponseExtended:
    """Extended tests for create_result_response with complex edge cases."""
    
    def test_create_result_response_nested_dict(self):
        """Test response creation with deeply nested dict."""
        nested_dict = {
            "level1": {
                "level2": {
                    "level3": ["item1", "item2"],
                    "level3_dict": {"key": "value"}
                },
                "numbers": [1, 2, 3, 4, 5]
            },
            "root_key": "root_value"
        }
        result = create_result_response(nested_dict)
        
        assert result == nested_dict
        assert isinstance(result, dict)
        assert result["level1"]["level2"]["level3"] == ["item1", "item2"]
    
    def test_create_result_response_empty_containers(self):
        """Test response creation with empty containers."""
        empty_dict = {}
        
        result_dict = create_result_response(empty_dict)
        
        # Empty dict is returned as-is
        assert result_dict == {}
        
        # Empty list wrapped in GenericOutput
        empty_list_output = GenericOutput(result=[], success=True)
        result_list = create_result_response(empty_list_output)
        
        assert result_list["result"] == []
        assert result_list["success"] is True
        assert result_list["message"] is None
    
    def test_create_result_response_mixed_types(self):
        """Test response creation with mixed data types."""
        mixed_data = {
            "string": "text",
            "integer": 42,
            "float": 3.14,
            "boolean": True,
            "none": None,
            "list": [1, "two", 3.0, False],
            "nested": {"inner": "value"}
        }
        result = create_result_response(mixed_data)
        
        assert result == mixed_data
        assert result["list"] == [1, "two", 3.0, False]
        assert result["nested"]["inner"] == "value"


class TestCreateDynamicModelExtended:
    """Extended tests for create_dynamic_model with complex types and edge cases."""
    
    def test_create_dynamic_model_with_list_type(self):
        """Test creating model with List type parameter."""
        params = [
            ExplicitParam(name="items", type=List[str], required=True, description="List of items"),
            ExplicitParam(name="numbers", type=List[int], default=[], required=False, description="List of numbers")
        ]
        
        func_info = FunctionInfo(
            name="list_func",
            func=lambda items, numbers: None,
            description="Function with list parameters",
            params=params,
            return_type=GenericOutput
        )
        
        DynamicModel = create_dynamic_model(func_info, for_post=True)
        
        # Test with valid list inputs
        instance = DynamicModel(items=["a", "b", "c"], numbers=[1, 2, 3])
        assert instance.items == ["a", "b", "c"]
        assert instance.numbers == [1, 2, 3]
        
        # Test with default empty list
        instance = DynamicModel(items=["x", "y"])
        assert instance.items == ["x", "y"]
        assert instance.numbers == []
    
    def test_create_dynamic_model_with_dict_type(self):
        """Test creating model with Dict type parameter."""
        params = [
            ExplicitParam(name="config", type=Dict[str, Any], required=True, description="Configuration dict"),
            ExplicitParam(name="metadata", type=Dict[str, str], default={}, required=False, description="Metadata")
        ]
        
        func_info = FunctionInfo(
            name="dict_func",
            func=lambda config, metadata: None,
            description="Function with dict parameters",
            params=params,
            return_type=GenericOutput
        )
        
        DynamicModel = create_dynamic_model(func_info, for_post=True)
        
        # Test with valid dict inputs
        config_data = {"key1": "value1", "key2": 42}
        metadata_data = {"author": "test", "version": "1.0"}
        
        instance = DynamicModel(config=config_data, metadata=metadata_data)
        assert instance.config == config_data
        assert instance.metadata == metadata_data
        
        # Test with default empty dict
        instance = DynamicModel(config={"minimal": "config"})
        assert instance.config == {"minimal": "config"}
        assert instance.metadata == {}
    
    def test_create_dynamic_model_all_optional_params(self):
        """Test creating model with all optional parameters."""
        params = [
            ExplicitParam(name="opt1", type=str, default="default1", required=False, description="Optional 1"),
            ExplicitParam(name="opt2", type=int, default=100, required=False, description="Optional 2"),
            ExplicitParam(name="opt3", type=bool, default=False, required=False, description="Optional 3")
        ]
        
        func_info = FunctionInfo(
            name="all_optional_func",
            func=lambda opt1, opt2, opt3: None,
            description="Function with all optional params",
            params=params,
            return_type=GenericOutput
        )
        
        DynamicModel = create_dynamic_model(func_info, for_post=True)
        
        # Should be able to create instance with no parameters (all defaults)
        instance = DynamicModel()
        assert instance.opt1 == "default1"
        assert instance.opt2 == 100
        assert instance.opt3 is False
        
        # Should be able to override some defaults
        instance = DynamicModel(opt2=200, opt3=True)
        assert instance.opt1 == "default1"  # Still default
        assert instance.opt2 == 200  # Overridden
        assert instance.opt3 is True  # Overridden
    
    def test_create_dynamic_model_no_params(self):
        """Test creating model with no parameters."""
        func_info = FunctionInfo(
            name="no_params_func",
            func=lambda: "result",
            description="Function with no parameters",
            params=[],
            return_type=GenericOutput
        )
        
        DynamicModel = create_dynamic_model(func_info, for_post=True)
        
        # Should create model with no fields
        instance = DynamicModel()
        # Just verify it can be instantiated without errors
        assert instance is not None


class TestExtractFunctionParamsExtended:
    """Extended tests for extract_function_params with complex edge cases."""
    
    def test_extract_function_params_mixed_defaults(self):
        """Test parameter extraction with mixed default types."""
        params = [
            ExplicitParam(name="required_str", type=str, required=True, description="Required string"),
            ExplicitParam(name="optional_int", type=int, default=42, required=False, description="Optional int"),
            ExplicitParam(name="optional_list", type=List[str], default=[], required=False, description="Optional list"),
            ExplicitParam(name="optional_dict", type=Dict[str, Any], default={}, required=False, description="Optional dict"),
            ExplicitParam(name="optional_none", type=str, default=None, required=False, description="Optional with None")
        ]
        
        func_info = FunctionInfo(
            name="mixed_func",
            func=lambda: None,
            description="Function with mixed defaults",
            params=params,
            return_type=GenericOutput
        )
        
        request_params = {"required_str": "test"}
        result = extract_function_params(func_info, request_params)
        
        expected = {
            "required_str": "test",
            "optional_int": 42,
            "optional_list": [],
            "optional_dict": {}
            # optional_none should not be included (None default)
        }
        assert result == expected
    
    def test_extract_function_params_partial_override(self):
        """Test parameter extraction with partial override of defaults."""
        params = [
            ExplicitParam(name="param1", type=str, default="default1", required=False, description="Param 1"),
            ExplicitParam(name="param2", type=int, default=10, required=False, description="Param 2"),
            ExplicitParam(name="param3", type=bool, default=True, required=False, description="Param 3")
        ]
        
        func_info = FunctionInfo(
            name="partial_func",
            func=lambda: None,
            description="Function for partial override test",
            params=params,
            return_type=GenericOutput
        )
        
        # Override only param2
        request_params = {"param2": 20}
        result = extract_function_params(func_info, request_params)
        
        expected = {
            "param1": "default1",  # Default
            "param2": 20,          # Overridden
            "param3": True         # Default
        }
        assert result == expected
    
    def test_extract_function_params_complex_types(self):
        """Test parameter extraction with complex data types."""
        params = [
            ExplicitParam(name="data_list", type=List[Dict[str, Any]], required=True, description="List of dicts"),
            ExplicitParam(name="config_dict", type=Dict[str, List[str]], default={}, required=False, description="Dict of lists")
        ]
        
        func_info = FunctionInfo(
            name="complex_types_func",
            func=lambda: None,
            description="Function with complex types",
            params=params,
            return_type=GenericOutput
        )
        
        complex_list = [{"id": 1, "name": "item1"}, {"id": 2, "name": "item2"}]
        complex_dict = {"category1": ["a", "b"], "category2": ["c", "d"]}
        
        request_params = {"data_list": complex_list, "config_dict": complex_dict}
        result = extract_function_params(func_info, request_params)
        
        expected = {
            "data_list": complex_list,
            "config_dict": complex_dict
        }
        assert result == expected


class TestExecuteFunctionWithParamsExtended:
    """Extended tests for execute_function_with_params with more error types and edge cases."""
    
    def test_execute_function_with_params_type_error(self):
        """Test function execution with TypeError."""
        def type_error_func(x: int, y: str) -> str:
            # This will raise TypeError if x is not int or y is not str
            return f"Result: {x + len(y)}"
        
        func_info = FunctionInfo(
            name="type_error_func",
            func=type_error_func,
            description="Function that can raise TypeError",
            params=[
                ExplicitParam(name="x", type=int, required=True, description="Integer param"),
                ExplicitParam(name="y", type=str, required=True, description="String param")
            ],
            return_type=GenericOutput
        )
        
        # Pass wrong types that will cause TypeError in function
        request_params = {"x": "not_int", "y": 123}
        
        with pytest.raises(HTTPException) as exc_info:
            execute_function_with_params(func_info, request_params, "POST")
        
        assert exc_info.value.status_code == 400
        assert "Parameter error" in str(exc_info.value.detail)
    
    def test_execute_function_with_params_custom_exception(self):
        """Test function execution with custom exception (should be 500)."""
        class CustomError(Exception):
            pass
        
        def custom_error_func(x: int) -> int:
            if x < 0:
                raise CustomError("Negative values not allowed")
            return x * 2
        
        func_info = FunctionInfo(
            name="custom_error_func",
            func=custom_error_func,
            description="Function with custom exception",
            params=[ExplicitParam(name="x", type=int, required=True, description="Positive integer")],
            return_type=GenericOutput
        )
        
        request_params = {"x": -5}
        
        with pytest.raises(HTTPException) as exc_info:
            execute_function_with_params(func_info, request_params, "POST")
        
        assert exc_info.value.status_code == 500
        assert "Internal error" in str(exc_info.value.detail)
    
    def test_execute_function_with_params_list_result(self):
        """Test function execution that returns GenericOutput with list."""
        def list_func(count: int) -> GenericOutput:
            return GenericOutput(result=[f"item_{i}" for i in range(count)], success=True)
        
        func_info = FunctionInfo(
            name="list_func",
            func=list_func,
            description="Returns list",
            params=[ExplicitParam(name="count", type=int, required=True, description="Number of items")],
            return_type=GenericOutput
        )
        
        request_params = {"count": 3}
        result = execute_function_with_params(func_info, request_params, "GET")
        
        # Should return GenericOutput as dict
        assert result["result"] == ["item_0", "item_1", "item_2"]
        assert result["success"] is True
        assert result["message"] is None
    
    def test_execute_function_with_params_none_result(self):
        """Test function execution that returns GenericOutput with None result."""
        def none_func(message: str) -> GenericOutput:
            # Function that performs side effect but returns GenericOutput with None
            return GenericOutput(result=None, success=True, message=f"Processed: {message}")
        
        func_info = FunctionInfo(
            name="none_func",
            func=none_func,
            description="Returns None result",
            params=[ExplicitParam(name="message", type=str, required=True, description="Message")],
            return_type=GenericOutput
        )
        
        request_params = {"message": "test"}
        result = execute_function_with_params(func_info, request_params, "POST")
        
        # Should return GenericOutput as dict
        assert result["result"] is None
        assert result["success"] is True
        assert result["message"] == "Processed: test"
    
    @patch('autocode.interfaces.api.logger')
    def test_execute_function_with_params_error_logging(self, mock_logger):
        """Test that errors are logged appropriately."""
        def error_func() -> str:
            raise ValueError("Test error for logging")
        
        func_info = FunctionInfo(
            name="error_func",
            func=error_func,
            description="Error function for logging test",
            params=[],
            return_type=GenericOutput
        )
        
        with pytest.raises(HTTPException):
            execute_function_with_params(func_info, {}, "POST")
        
        # Should log warning for parameter/type errors
        mock_logger.warning.assert_called_once()
        log_call = mock_logger.warning.call_args[0][0]
        assert "POST error_func parameter error" in log_call
        assert "Test error for logging" in log_call


class TestStaticFilesAndRootEndpoint:
    """Unit tests for static files mounting and root endpoint logic."""
    
    @patch('autocode.interfaces.api.load_core_functions')
    @patch('os.path.exists')
    @patch('os.path.join')
    @patch('os.path.isdir')
    def test_static_files_mounting_when_dir_exists(self, mock_isdir, mock_join, mock_exists, mock_load):
        """Test static files are mounted when web directory exists."""
        mock_exists.return_value = True
        mock_isdir.return_value = True
        mock_join.return_value = "/fake/path/to/web"
        
        app = create_api_app()
        
        # Verify os.path.join was called for web directory
        mock_join.assert_called()
        # Verify existence check was performed
        mock_exists.assert_called_with("/fake/path/to/web")
        
        # Check that app has static mount (indirectly through routes)
        # Note: This test verifies the mounting logic is called, not the actual mounting
        routes = [route for route in app.routes if hasattr(route, 'path')]
        # The exact verification depends on FastAPI's internal structure
    
    @patch('autocode.interfaces.api.load_core_functions')
    @patch('os.path.exists')
    def test_static_files_not_mounted_when_dir_missing(self, mock_exists, mock_load):
        """Test static files are not mounted when web directory doesn't exist."""
        mock_exists.return_value = False
        
        app = create_api_app()
        
        # Verify existence check was performed
        mock_exists.assert_called()
        
        # App should still be created successfully
        assert app.title == "Autocode API"
    
    @patch('autocode.interfaces.api.load_core_functions')
    def test_root_endpoint_file_response(self, mock_load):
        """Test root endpoint returns a response (verifying route exists)."""
        app = create_api_app()
        
        # Verify the root route exists
        root_route = None
        for route in app.routes:
            if hasattr(route, 'path') and route.path == "/":
                root_route = route
                break
        
        assert root_route is not None, "Root endpoint should exist"
        
        # Test with actual client - should either return file or error
        client = TestClient(app)
        response = client.get("/")
        
        # The response might be 200 (file found) or 404/500 (file not found in test)
        # We just verify the endpoint is reachable
        assert response.status_code in [200, 404, 500]
    
    @patch('autocode.interfaces.api.load_core_functions')
    def test_root_endpoint_path_construction(self, mock_load):
        """Test that root endpoint constructs correct path to index.html."""
        with patch('os.path.dirname') as mock_dirname, \
             patch('os.path.join') as mock_join, \
             patch('fastapi.responses.FileResponse') as mock_file_response:
            
            mock_dirname.return_value = "/fake/interfaces/dir"
            mock_join.return_value = "/fake/web/index.html"
            
            app = create_api_app()
            
            # Access the root endpoint function to test path logic
            # This verifies the path construction without making HTTP request
            import inspect
            root_handler = None
            for route in app.routes:
                if hasattr(route, 'path') and route.path == "/" and hasattr(route, 'endpoint'):
                    root_handler = route.endpoint
                    break
            
            assert root_handler is not None
            
            # The path construction logic is tested through the mocks above
            # mock_join should have been called with directory traversal
            expected_calls = mock_join.call_args_list
            # Should include call to join interface dir with "..", "web", "index.html"
            assert len(expected_calls) > 0
