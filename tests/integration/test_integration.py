"""
Integration tests for autocode interfaces.

Tests the complete integration between registry, API, CLI, and MCP components
to ensure they work together as expected in real-world scenarios.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from fastapi.testclient import TestClient
from click.testing import CliRunner

from autocode.interfaces.registry import (
    register_function, clear_registry, function_count,
    get_function_by_name, get_all_functions
)
from autocode.interfaces.api import create_api_app
from autocode.interfaces.cli import app as cli_app, _register_commands
from autocode.interfaces.mcp import create_mcp_app
from autocode.interfaces.models import GenericOutput


class TestFullIntegration:
    """End-to-end integration tests for all interfaces."""
    
    @pytest.fixture(autouse=True)
    def setup_integration_functions(self):
        """Set up test functions for integration testing."""
        # Register test functions using the decorator
        @register_function(http_methods=["GET", "POST"])
        def integration_add(a: int, b: int = 10) -> GenericOutput:
            """Add two integers for integration testing.
            
            Args:
                a: First integer
                b: Second integer (defaults to 10)
                
            Returns:
                Sum of a and b
            """
            return GenericOutput(result=a + b, success=True)
        
        @register_function(http_methods=["POST"])
        def integration_multiply(x: float, y: float = 2.0) -> GenericOutput:
            """Multiply two floats for integration testing.
            
            Args:
                x: First float
                y: Second float (defaults to 2.0)
                
            Returns:
                Product of x and y
            """
            return GenericOutput(result=x * y, success=True)
        
        @register_function(http_methods=["GET"])
        def integration_greet(name: str = "World") -> GenericOutput:
            """Generate a greeting message.
            
            Args:
                name: Name to greet (defaults to "World")
                
            Returns:
                Dictionary containing greeting
            """
            return GenericOutput(result={"message": f"Hello, {name}!"}, success=True)
        
        # Re-register CLI commands after adding new functions
        _register_commands()
        
        yield
        
        # Cleanup is handled by conftest.py cleanup_registry fixture
    
    @patch('autocode.interfaces.api.load_functions')
    def test_api_integration_with_registered_functions(self, mock_load):
        """Test that API correctly serves registered functions."""
        app = create_api_app()
        client = TestClient(app)
        
        # Test GET endpoint with defaults
        response = client.get("/integration_add?a=5")
        assert response.status_code == 200
        data = response.json()
        assert data["result"] == 15  # 5 + 10 (default)
        
        # Test POST endpoint with all parameters
        response = client.post("/integration_add", json={"a": 3, "b": 7})
        assert response.status_code == 200
        data = response.json()
        assert data["result"] == 10
        
        # Test function that returns GenericOutput with dict result
        response = client.get("/integration_greet?name=Test")
        assert response.status_code == 200
        data = response.json()
        assert data["result"] == {"message": "Hello, Test!"}
        
        # Test POST-only endpoint
        response = client.post("/integration_multiply", json={"x": 4.5, "y": 3.0})
        assert response.status_code == 200
        data = response.json()
        assert data["result"] == 13.5
        
        # Test that GET is not available for POST-only function
        response = client.get("/integration_multiply?x=4.5&y=3.0")
        assert response.status_code == 405  # Method Not Allowed
    
    def test_cli_integration_with_registered_functions(self):
        """Test that CLI correctly exposes registered functions."""
        runner = CliRunner()
        
        # Test list command shows registered functions
        result = runner.invoke(cli_app, ['list'])
        assert result.exit_code == 0
        assert "integration_add" in result.output
        assert "integration_multiply" in result.output
        assert "integration_greet" in result.output
        
        # Test executing registered function via CLI
        result = runner.invoke(cli_app, ['integration_add', '--a', '8', '--b', '2'])
        assert result.exit_code == 0
        assert "10" in result.output
        
        # Test with default parameters
        result = runner.invoke(cli_app, ['integration_add', '--a', '5'])
        assert result.exit_code == 0
        assert "15" in result.output
        
        # Test help for registered function
        result = runner.invoke(cli_app, ['integration_add', '--help'])
        assert result.exit_code == 0
        assert "Add two integers for integration testing" in result.output
        assert "--a" in result.output
        assert "--b" in result.output
    
    @patch('autocode.interfaces.mcp.create_api_app')
    @patch('autocode.interfaces.mcp.FastApiMCP')
    def test_mcp_integration_preserves_api_functionality(self, mock_fastapi_mcp, mock_create_api_app):
        """Test that MCP integration preserves API functionality."""
        # Create actual API app for this test
        mock_create_api_app.side_effect = lambda: create_api_app()
        
        # Mock MCP components
        mock_mcp_instance = Mock()
        mock_fastapi_mcp.return_value = mock_mcp_instance
        
        # Create MCP app
        with patch('autocode.interfaces.api.load_functions'):
            mcp_app = create_mcp_app()
        
        # Test that API functionality is preserved
        client = TestClient(mcp_app)
        
        # Test health endpoint
        response = client.get("/health")
        assert response.status_code == 200
        
        # Test functions endpoint
        response = client.get("/functions")
        assert response.status_code == 200
        
        # Verify MCP was integrated
        mock_fastapi_mcp.assert_called_once()
        mock_mcp_instance.mount.assert_called_once()
    
    def test_registry_function_parameter_inference(self):
        """Test that parameter inference works correctly across interfaces."""
        @register_function()
        def complex_function(
            required_str: str,
            optional_int: int = 42,
            optional_bool: bool = True
        ) -> GenericOutput:
            """Complex function with various parameter types.
            
            Args:
                required_str: A required string parameter
                optional_int: An optional integer parameter
                optional_bool: An optional boolean parameter
            """
            return GenericOutput(result={
                "required_str": required_str,
                "optional_int": optional_int,
                "optional_bool": optional_bool
            }, success=True)
        
        # Verify function was registered correctly using public API
        func_info = get_function_by_name("complex_function")
        assert func_info is not None
        assert func_info.name == "complex_function"
        assert len(func_info.params) == 3
        
        # Check parameter details using schemas
        params = [p.to_schema() for p in func_info.params]
        
        str_param = next(p for p in params if p.name == "required_str")
        assert str_param.required is True
        assert str_param.type_str == "str"
        
        int_param = next(p for p in params if p.name == "optional_int")
        assert int_param.required is False
        assert int_param.default == 42
        
        bool_param = next(p for p in params if p.name == "optional_bool")
        assert bool_param.required is False
        assert bool_param.default is True
    
    @patch('autocode.interfaces.api.load_functions')
    def test_error_handling_across_interfaces(self, mock_load):
        """Test error handling consistency across interfaces."""
        # Register a function that can error
        @register_function()
        def error_prone_function(value: int) -> GenericOutput:
            """Function that errors on negative values."""
            if value < 0:
                raise ValueError("Value cannot be negative")
            return GenericOutput(result=value * 2, success=True)
        
        # Test API error handling
        app = create_api_app()
        client = TestClient(app)
        
        # Should work with positive value
        response = client.post("/error_prone_function", json={"value": 5})
        assert response.status_code == 200
        
        # Should handle error gracefully
        response = client.post("/error_prone_function", json={"value": -1})
        assert response.status_code == 400  # Parameter error
        
        # Re-register CLI commands for new function
        _register_commands()
        
        # Test CLI error handling
        runner = CliRunner()
        
        # Should work with positive value
        result = runner.invoke(cli_app, ['error_prone_function', '--value', '3'])
        assert result.exit_code == 0
        assert "6" in result.output
        
        # Should handle error gracefully
        result = runner.invoke(cli_app, ['error_prone_function', '--value', '-2'])
        assert result.exit_code != 0
    
class TestInterfaceConsistency:
    """Tests to ensure consistent behavior across all interfaces."""
    
    def test_parameter_handling_consistency(self):
        """Test that parameter handling is consistent between API and CLI."""
        @register_function()
        def consistency_test(param1: str, param2: int = 100) -> GenericOutput:
            """Test function for consistency checking."""
            return GenericOutput(result=f"{param1}:{param2}", success=True)
        
        # Test via API
        with patch('autocode.interfaces.api.load_functions'):
            app = create_api_app()
            client = TestClient(app)
            
            # API with defaults
            response = client.post("/consistency_test", json={"param1": "test"})
            assert response.status_code == 200
            data = response.json()
            assert data["result"] == "test:100"
            
            # API with all params
            response = client.post("/consistency_test", json={"param1": "test", "param2": 50})
            assert response.status_code == 200
            data = response.json()
            assert data["result"] == "test:50"
        
        # Re-register CLI commands for new function
        _register_commands()
        
        # Test via CLI
        runner = CliRunner()
        
        # CLI with defaults
        result = runner.invoke(cli_app, ['consistency_test', '--param1', 'test'])
        assert result.exit_code == 0
        assert "test:100" in result.output
        
        # CLI with all params
        result = runner.invoke(cli_app, ['consistency_test', '--param1', 'test', '--param2', '50'])
        assert result.exit_code == 0
        assert "test:50" in result.output
    
    def test_function_metadata_consistency(self):
        """Test that function metadata is consistent across interfaces."""
        @register_function(http_methods=["GET", "POST", "PUT"])
        def metadata_test(x: int, y: str = "default") -> GenericOutput:
            """Test function for metadata consistency.
            
            Args:
                x: An integer parameter
                y: A string parameter with default
            """
            return GenericOutput(result={"x": x, "y": y}, success=True)
        
        # Access function info using public API
        func_info = get_function_by_name("metadata_test")
        assert func_info is not None
        
        # Verify metadata
        assert func_info.name == "metadata_test"
        assert func_info.description == "Test function for metadata consistency."
        assert set(func_info.http_methods) == {"GET", "POST", "PUT"}
        assert len(func_info.params) == 2
        
        # Verify parameter details
        x_param = next(p for p in func_info.params if p.name == "x")
        y_param = next(p for p in func_info.params if p.name == "y")
        
        assert x_param.type == int and x_param.required is True
        assert y_param.type == str and y_param.required is False and y_param.default == "default"


class TestCrossModuleDependencies:
    """Tests for dependencies between different interface modules."""
    
    def test_registry_integration_with_all_interfaces(self):
        """Test that registry changes are reflected in all interfaces."""
        initial_count = function_count()
        
        # Add function dynamically
        @register_function()
        def dynamic_function(value: str) -> GenericOutput:
            """Dynamically added function."""
            return GenericOutput(result=f"Dynamic: {value}", success=True)
        
        # Verify registry was updated using public API
        assert function_count() == initial_count + 1
        func_info = get_function_by_name("dynamic_function")
        assert func_info is not None
        
        # Test that CLI reflects the change
        runner = CliRunner()
        result = runner.invoke(cli_app, ['list'])
        assert "dynamic_function" in result.output
    
    @patch('autocode.interfaces.api.load_functions')
    def test_mcp_and_api_integration(self, mock_load):
        """Test integration between MCP and API components."""
        # Register a test function
        @register_function()
        def mcp_test_function(data: str) -> GenericOutput:
            """Function for MCP testing."""
            return GenericOutput(result={"processed": data.upper()}, success=True)
        
        # Create MCP app
        with patch('autocode.interfaces.mcp.FastApiMCP') as mock_mcp:
            mock_mcp_instance = Mock()
            mock_mcp.return_value = mock_mcp_instance
            
            app = create_mcp_app()
            
            # Verify MCP was initialized with the app
            mock_mcp.assert_called_once()
            call_args = mock_mcp.call_args
            assert call_args[0][0] == app  # First argument should be the app
            
            # Verify app configuration
            assert "MCP Server" in app.title
            assert "MCP integration" in app.description
    
    def test_error_propagation_across_modules(self):
        """Test that errors propagate correctly across module boundaries."""
        # Test that searching for non-existent function returns None
        result = get_function_by_name("nonexistent")
        assert result is None
        
        # Test that API would handle registry errors
        from autocode.interfaces.api import _execute_function as execute_function_with_params
        from autocode.interfaces.models import FunctionInfo
        
        # Create a function info that references nonexistent function
        fake_func = lambda: None  # This won't be called
        fake_func_info = FunctionInfo(
            name="fake",
            func=fake_func,
            description="Fake function",
            params=[]
        )
        
        # This should work (no registry lookup involved in execute_function_with_params)
        result = execute_function_with_params(fake_func_info, {}, "POST")
        # When function returns None (not GenericOutput), API wraps it with warning
        assert result["success"] is False or result["result"] == "None"


class TestRealWorldScenarios:
    """Tests for real-world usage scenarios."""
    
    def test_code_quality_tool_simulation(self):
        """Simulate a real code quality tool being registered and used."""
        @register_function(http_methods=["POST"])
        def analyze_code_quality(
            code: str,
            strict_mode: bool = False,
            max_line_length: int = 88
        ) -> GenericOutput:
            """Analyze code quality metrics.
            
            Args:
                code: Source code to analyze
                strict_mode: Enable strict checking
                max_line_length: Maximum line length allowed
            """
            issues = []
            lines = code.split('\n')
            
            for i, line in enumerate(lines, 1):
                if len(line) > max_line_length:
                    issues.append({
                        "line": i,
                        "type": "line_too_long",
                        "message": f"Line {i} exceeds {max_line_length} characters"
                    })
                
                if strict_mode and line.strip().endswith(' '):
                    issues.append({
                        "line": i,
                        "type": "trailing_whitespace",
                        "message": f"Line {i} has trailing whitespace"
                    })
            
            return GenericOutput(result={
                "total_lines": len(lines),
                "issues": issues,
                "score": max(0, 100 - len(issues) * 10)
            }, success=True)
        
        # Test via API
        with patch('autocode.interfaces.api.load_functions'):
            app = create_api_app()
            client = TestClient(app)
            
            # Note: "line1\nline2\n" splits into ['line1', 'line2', ''] = 3 elements
            test_code = "def test():\n    return 'hello world'"
            
            response = client.post("/analyze_code_quality", json={
                "code": test_code,
                "strict_mode": False,
                "max_line_length": 80
            })
            
            assert response.status_code == 200
            data = response.json()
            assert data["result"]["total_lines"] == 2
            assert data["result"]["score"] >= 0
            assert isinstance(data["result"]["issues"], list)
        
        # Re-register CLI commands for new function
        _register_commands()
        
        # Test via CLI
        runner = CliRunner()
        result = runner.invoke(cli_app, [
            'analyze_code_quality',
            '--code', 'print("hello")',
            '--max-line-length', '10'
        ])
        
        assert result.exit_code == 0
        # Should detect line length issue
        assert "issues" in result.output or "score" in result.output
    
    def test_multiple_tools_coexistence(self):
        """Test that multiple tools can coexist in the registry."""
        # Register multiple tools
        @register_function()
        def format_code(code: str, style: str = "pep8") -> GenericOutput:
            """Format code according to style guide."""
            return GenericOutput(result=f"[{style}] {code.strip()}", success=True)
        
        @register_function()
        def check_imports(code: str) -> GenericOutput:
            """Check import statements in code."""
            import_lines = [line for line in code.split('\n') if line.strip().startswith('import')]
            return GenericOutput(result={"import_count": len(import_lines), "imports": import_lines}, success=True)
        
        @register_function()
        def calculate_complexity(code: str) -> GenericOutput:
            """Calculate cyclomatic complexity."""
            # Simplified complexity calculation
            complexity_keywords = ['if', 'elif', 'for', 'while', 'except', 'and', 'or']
            complexity = 1  # Base complexity
            for keyword in complexity_keywords:
                complexity += code.count(keyword)
            return GenericOutput(result=complexity, success=True)
        
        # Verify all tools are registered using public API
        format_func = get_function_by_name("format_code")
        check_func = get_function_by_name("check_imports")
        calc_func = get_function_by_name("calculate_complexity")
        
        assert format_func is not None
        assert check_func is not None
        assert calc_func is not None
        
        # Re-register CLI commands for new functions
        _register_commands()
        
        # Test that they work independently
        runner = CliRunner()
        
        # Test format_code
        result = runner.invoke(cli_app, ['format_code', '--code', 'x=1'])
        assert result.exit_code == 0
        assert "[pep8]" in result.output
        
        # Test calculate_complexity
        result = runner.invoke(cli_app, ['calculate_complexity', '--code', 'if x: pass'])
        assert result.exit_code == 0
        assert "2" in result.output  # Base(1) + if(1) = 2
