"""
Test checker for Vidi project.
Detects missing tests and validates existing ones following modular structure.
Maps code files to their expected test files but does not create them.
"""

from pathlib import Path
from typing import List, NamedTuple, Set, Optional
import subprocess
import sys
import os


class TestStatus(NamedTuple):
    """Status of a code-test pair."""
    code_file: Path
    test_file: Path
    status: str  # 'missing', 'failing', 'passing', 'orphaned'
    test_type: str  # 'unit', 'integration'


class TestChecker:
    """Checks test status against code files following modular structure."""
    
    def __init__(self, project_root: Path = None, config: Optional['TestConfig'] = None):
        """Initialize TestChecker with project root directory and optional configuration."""
        self.project_root = project_root or Path.cwd()
        self.tests_dir = self.project_root / "tests"
        self.config = config
    
    def find_code_directories(self) -> List[Path]:
        """Auto-discover directories containing Python code (excluding __init__.py only dirs)."""
        code_dirs = []
        
        # Scan directories in project root
        for item in self.project_root.iterdir():
            if item.is_dir() and not item.name.startswith('.') and item.name not in ['docs', 'tests', 'logs', 'outputs']:
                # Check if directory contains .py files (excluding __init__.py)
                python_files = [f for f in item.rglob("*.py") if f.name != "__init__.py"]
                if python_files:
                    code_dirs.append(item)
        
        return code_dirs
    
    def get_all_python_files(self) -> List[Path]:
        """Get all Python files from all code directories, excluding __init__.py."""
        python_files = []
        code_dirs = self.find_code_directories()
        
        for code_dir in code_dirs:
            for py_file in code_dir.rglob("*.py"):
                # Skip __init__.py files
                if py_file.name == "__init__.py":
                    continue
                python_files.append(py_file)
        
        return python_files
    
    def get_all_code_directories_with_subdirs(self) -> Set[Path]:
        """Get all directories that contain Python code (including subdirectories)."""
        all_dirs = set()
        code_dirs = self.find_code_directories()
        
        for code_dir in code_dirs:
            # Add the main directory
            all_dirs.add(code_dir)
            
            # Add all subdirectories that contain .py files
            for py_file in code_dir.rglob("*.py"):
                if py_file.name != "__init__.py":
                    # Add all parent directories up to the main code directory
                    current_dir = py_file.parent
                    while current_dir != code_dir.parent and current_dir != self.project_root:
                        all_dirs.add(current_dir)
                        current_dir = current_dir.parent
        
        return all_dirs
    
    def map_code_file_to_unit_test(self, code_file: Path) -> Path:
        """Map a code file to its corresponding unit test file."""
        # Convert vidi/inference/engine.py -> tests/vidi/inference/test_engine.py
        relative_path = code_file.relative_to(self.project_root)
        test_filename = f"test_{code_file.stem}.py"
        test_path = self.tests_dir / relative_path.parent / test_filename
        return test_path
    
    def map_directory_to_integration_test(self, code_dir: Path) -> Path:
        """Map a code directory to its corresponding integration test file."""
        # Convert vidi/inference/ -> tests/vidi/inference/test_inference_integration.py
        relative_path = code_dir.relative_to(self.project_root)
        test_filename = f"test_{code_dir.name}_integration.py"
        test_path = self.tests_dir / relative_path / test_filename
        return test_path
    
    def find_all_test_files(self) -> List[Path]:
        """Find all test files in the tests directory."""
        if not self.tests_dir.exists():
            return []
        
        test_files = []
        for test_file in self.tests_dir.rglob("test_*.py"):
            test_files.append(test_file)
        
        return test_files
    
    def map_test_to_code_file(self, test_file: Path) -> Path:
        """Map a test file back to its corresponding code file."""
        # Convert tests/vidi/inference/test_engine.py -> vidi/inference/engine.py
        relative_test = test_file.relative_to(self.tests_dir)
        
        # Handle integration tests
        if test_file.name.endswith("_integration.py"):
            # This is an integration test - maps to directory
            # tests/vidi/inference/test_inference_integration.py -> vidi/inference/
            code_path = self.project_root / relative_test.parent
            return code_path
        else:
            # This is a unit test - maps to file
            # Remove 'test_' prefix
            code_filename = test_file.name[5:]  # Remove 'test_'
            code_path = self.project_root / relative_test.parent / code_filename
            return code_path
    
    def find_orphaned_tests(self) -> List[TestStatus]:
        """Find test files that no longer have corresponding code."""
        orphaned = []
        test_files = self.find_all_test_files()
        
        for test_file in test_files:
            code_path = self.map_test_to_code_file(test_file)
            
            if test_file.name.endswith("_integration.py"):
                # Integration test - check if directory exists and has Python files
                if not code_path.exists() or not code_path.is_dir():
                    orphaned.append(TestStatus(code_path, test_file, 'orphaned', 'integration'))
                else:
                    # Check if directory actually contains Python files (excluding __init__.py)
                    python_files = [f for f in code_path.rglob("*.py") if f.name != "__init__.py"]
                    if not python_files:
                        orphaned.append(TestStatus(code_path, test_file, 'orphaned', 'integration'))
            else:
                # Unit test - check if file exists
                if not code_path.exists():
                    orphaned.append(TestStatus(code_path, test_file, 'orphaned', 'unit'))
        
        return orphaned
    
    def execute_tests(self) -> tuple[int, str, str]:
        """Execute pytest and return results."""
        if not self.tests_dir.exists():
            return 0, "No tests directory found", ""
        
        # Check if there are any test files
        test_files = self.find_all_test_files()
        if not test_files:
            return 0, "No test files found", ""
        
        try:
            # Run pytest with basic options
            result = subprocess.run(
                [sys.executable, "-m", "pytest", str(self.tests_dir), "-v", "--tb=short"],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=300  # 5 minutes timeout
            )
            
            return result.returncode, result.stdout, result.stderr
        
        except subprocess.TimeoutExpired:
            return 1, "", "Test execution timed out (5 minutes)"
        except FileNotFoundError:
            return 1, "", "pytest not found. Please install pytest: uv add --dev pytest"
        except Exception as e:
            return 1, "", f"Error executing tests: {str(e)}"
    
    def check_all_tests(self) -> List[TestStatus]:
        """Check test status for all code following modular structure."""
        results = []
        
        # 1. Check unit tests for each Python file
        python_files = self.get_all_python_files()
        for code_file in python_files:
            test_file = self.map_code_file_to_unit_test(code_file)
            if test_file.exists():
                status = 'passing'  # Assume passing, will be updated by execute_tests
            else:
                status = 'missing'
            results.append(TestStatus(code_file, test_file, status, 'unit'))
        
        # 2. Check integration tests for each code directory
        code_directories = self.get_all_code_directories_with_subdirs()
        for code_dir in code_directories:
            test_file = self.map_directory_to_integration_test(code_dir)
            if test_file.exists():
                status = 'passing'  # Assume passing, will be updated by execute_tests
            else:
                status = 'missing'
            results.append(TestStatus(code_dir, test_file, status, 'integration'))
        
        # 3. Check for orphaned tests
        orphaned_tests = self.find_orphaned_tests()
        results.extend(orphaned_tests)
        
        # 4. Execute existing tests to check if they pass
        if any(r.status == 'passing' for r in results):
            exit_code, stdout, stderr = self.execute_tests()
            if exit_code != 0:
                # Parse pytest output to identify failing tests
                failing_tests = self.parse_pytest_failures(stdout, stderr)
                # Update status of failing tests
                for result in results:
                    if result.status == 'passing' and str(result.test_file) in failing_tests:
                        # Create new TestStatus with updated status
                        updated_result = TestStatus(
                            result.code_file, 
                            result.test_file, 
                            'failing', 
                            result.test_type
                        )
                        # Replace in results list
                        index = results.index(result)
                        results[index] = updated_result
        
        return results
    
    def parse_pytest_failures(self, stdout: str, stderr: str) -> List[str]:
        """Parse pytest output to identify failing test files."""
        failing_tests = []
        
        # Look for FAILED patterns in stdout
        for line in stdout.split('\n'):
            if 'FAILED' in line:
                # Extract test file path from pytest output
                # Format: "tests/path/to/test_file.py::TestClass::test_method FAILED"
                parts = line.split('::')
                if parts and parts[0].strip().startswith('tests/'):
                    test_file = parts[0].strip()
                    if test_file not in failing_tests:
                        failing_tests.append(test_file)
        
        return failing_tests
    
    def get_test_statuses(self) -> List[TestStatus]:
        """Get all test statuses (alias for check_all_tests for daemon compatibility)."""
        return self.check_all_tests()
    
    def get_missing_and_failing_tests(self) -> List[TestStatus]:
        """Get only the tests that need attention (missing, failing, or orphaned)."""
        all_results = self.check_all_tests()
        return [result for result in all_results if result.status in ['missing', 'failing', 'orphaned']]
    
    def format_results(self, results: List[TestStatus]) -> str:
        """Format results for display."""
        if not results:
            return "✅ All tests exist and are passing!"
        
        # Separate by status and type
        missing = [r for r in results if r.status == 'missing']
        failing = [r for r in results if r.status == 'failing']
        orphaned = [r for r in results if r.status == 'orphaned']
        
        output = []
        
        if missing:
            output.append("Tests faltantes:")
            for result in missing:
                if result.test_type == 'unit':
                    relative_code = result.code_file.relative_to(self.project_root)
                    relative_test = result.test_file.relative_to(self.project_root)
                    output.append(f"- {relative_code} → {relative_test}")
                else:  # integration
                    relative_code = result.code_file.relative_to(self.project_root)
                    relative_test = result.test_file.relative_to(self.project_root)
                    output.append(f"- {relative_code}/ → {relative_test}")
        
        if failing:
            if missing:
                output.append("")  # Empty line separator
            output.append("Tests fallando:")
            for result in failing:
                relative_test = result.test_file.relative_to(self.project_root)
                output.append(f"- {relative_test}")
        
        if orphaned:
            if missing or failing:
                output.append("")  # Empty line separator
            output.append("Tests huérfanos (código eliminado):")
            for result in orphaned:
                relative_test = result.test_file.relative_to(self.project_root)
                if result.test_type == 'integration':
                    relative_code = result.code_file.relative_to(self.project_root)
                    output.append(f"- {relative_test} (directorio {relative_code}/ ya no existe)")
                else:  # unit
                    relative_code = result.code_file.relative_to(self.project_root)
                    output.append(f"- {relative_test} (archivo {relative_code} ya no existe)")
        
        output.append("")
        total = len(results)
        output.append(f"Total: {total} test{'s' if total != 1 else ''} requiere{'n' if total != 1 else ''} atención")
        
        return "\n".join(output)
