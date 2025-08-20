"""
Tests for the hello_world core function.
"""
import pytest
from autocode.autocode.core.hello.hello_world import hello_world


class TestHelloWorld:
    """Test cases for hello_world function."""

    def test_hello_world_default(self):
        """Test hello_world with default parameter."""
        result = hello_world()
        assert result == "Hello, World!"

    def test_hello_world_with_name(self):
        """Test hello_world with custom name."""
        result = hello_world("Bruno")
        assert result == "Hello, Bruno!"

    def test_hello_world_with_empty_string(self):
        """Test hello_world with empty string."""
        result = hello_world("")
        assert result == "Hello, !"

    def test_hello_world_with_special_characters(self):
        """Test hello_world with special characters in name."""
        result = hello_world("José María")
        assert result == "Hello, José María!"

    def test_hello_world_with_numbers(self):
        """Test hello_world with numbers in name."""
        result = hello_world("User123")
        assert result == "Hello, User123!"

    def test_hello_world_with_long_name(self):
        """Test hello_world with a very long name."""
        long_name = "A" * 100
        result = hello_world(long_name)
        expected = f"Hello, {long_name}!"
        assert result == expected

    def test_hello_world_return_type(self):
        """Test that hello_world returns a string."""
        result = hello_world("Test")
        assert isinstance(result, str)

    def test_hello_world_format_consistency(self):
        """Test that the format is consistent across different inputs."""
        names = ["Alice", "Bob", "Charlie"]
        for name in names:
            result = hello_world(name)
            assert result.startswith("Hello, ")
            assert result.endswith("!")
            assert name in result


# Test function directly (not in a class)
def test_hello_world_functional():
    """Functional test of hello_world."""
    assert hello_world() == "Hello, World!"
    assert hello_world("Python") == "Hello, Python!"


# Parametrized test for multiple inputs
@pytest.mark.parametrize("name,expected", [
    ("World", "Hello, World!"),
    ("Alice", "Hello, Alice!"),
    ("Bob", "Hello, Bob!"),
    ("123", "Hello, 123!"),
    ("", "Hello, !"),
])
def test_hello_world_parametrized(name, expected):
    """Parametrized test for multiple name inputs."""
    assert hello_world(name) == expected
