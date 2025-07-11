"""
Tests for code-to-design transformer.
"""

import pytest
from pathlib import Path
from autocode.core.design import CodeToDesign


class TestCodeToDesign:
    """Test the CodeToDesign transformer."""
    
    def test_initialization(self, tmp_path):
        """Test CodeToDesign initialization."""
        transformer = CodeToDesign(tmp_path)
        assert transformer.project_root == tmp_path
        assert transformer.config["output_dir"] == "design"
        assert transformer.config["language"] == "python"
        assert "classes" in transformer.config["diagrams"]
    
    def test_analyze_simple_class(self, tmp_path):
        """Test analyzing a simple Python class."""
        # Create a simple Python file
        py_file = tmp_path / "test.py"
        py_file.write_text("""
class MyClass:
    def __init__(self):
        pass
    
    def method_one(self):
        return True
    
    def method_two(self):
        return False
""")
        
        # Create transformer and analyze
        transformer = CodeToDesign(tmp_path)
        structures = transformer.analyze_directory(".")
        
        # Check results
        assert "modules" in structures
        assert "." in structures["modules"]
        assert len(structures["modules"]["."]["classes"]) == 1
        
        cls = structures["modules"]["."]["classes"][0]
        assert cls["name"] == "MyClass"
        assert "method_one" in cls["methods"]
        assert "method_two" in cls["methods"]
        assert "__init__" in cls["methods"]
        assert cls["file_name"] == "test"
    
    def test_generate_mermaid_diagram(self, tmp_path):
        """Test generating Mermaid class diagram."""
        transformer = CodeToDesign(tmp_path)
        
        class_info = {
            "name": "TestClass",
            "methods": ["method_a", "method_b"],
            "bases": ["BaseClass"]
        }
        
        diagram = transformer.generate_mermaid_class_diagram(class_info)
        
        assert "classDiagram" in diagram
        assert "class TestClass" in diagram
        assert "+method_a()" in diagram
        assert "+method_b()" in diagram
        assert "BaseClass <|-- TestClass" in diagram
    
    def test_generate_design_files(self, tmp_path):
        """Test generating design files from code."""
        # Create a test Python file
        py_file = tmp_path / "sample.py"
        py_file.write_text("""
class Calculator:
    def add(self, a, b):
        return a + b
    
    def subtract(self, a, b):
        return a - b

class BasicCalculator(Calculator):
    def multiply(self, a, b):
        return a * b
""")
        
        # Generate design
        transformer = CodeToDesign(tmp_path)
        result = transformer.generate_design(".")
        
        # Check results
        assert result["status"] == "success"
        assert result["structure_count"]["classes"] == 2
        assert result["structure_count"]["modules"] == 1
        assert result["structure_count"]["files"] == 1
        
        # Check generated files exist
        design_dir = tmp_path / "design" / "generated"
        assert design_dir.exists()
        
        # Check the sample_class.md file (new modular structure)
        sample_class_file = design_dir / "sample_class.md"
        assert sample_class_file.exists()
        content = sample_class_file.read_text()
        assert "# Classes from sample.py" in content
        assert "Source: `sample.py`" in content
        
        # Check Calculator class in the file
        assert "## Calculator" in content
        assert "```mermaid" in content
        assert "classDiagram" in content
        assert "+add()" in content
        assert "+subtract()" in content
        
        # Check BasicCalculator class in the same file
        assert "## BasicCalculator" in content
        assert "Calculator <|-- BasicCalculator" in content
        assert "+multiply()" in content
        
        # Check index file
        index_file = design_dir / "_index.md"
        assert index_file.exists()
        content = index_file.read_text()
        assert "# Generated Design Index" in content
        assert "## Root Level" in content
        assert "sample.py" in content
        assert "sample_class.md" in content
