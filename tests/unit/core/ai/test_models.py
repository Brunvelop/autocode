"""
Unit tests for AI core models and serialization utilities.

Tests the standalone serialization functions (previously DspyOutput static methods):
- normalize_trajectory
- serialize_value
- _serialize_complex_object
"""
import pytest
from autocode.core.ai.models import normalize_trajectory, serialize_value, _serialize_complex_object


class TestNormalizeTrajectory:
    """Tests for normalize_trajectory() standalone function."""

    def test_preserves_already_clean_list_trajectory(self):
        """Should preserve a trajectory that is already a list of steps."""
        clean_trajectory = [
            {"thought": "Thinking...", "tool": "search"},
            {"thought": "Done", "tool": "finish"}
        ]
        result = normalize_trajectory(clean_trajectory)
        assert result == clean_trajectory

    def test_normalizes_flat_dspy_react_dict(self):
        """Should normalize flat DSPy ReAct dictionary to list of steps."""
        flat_trajectory = {
            "thought_0": "First thought",
            "tool_name_0": "tool_1",
            "tool_args_0": {"arg": 1},
            "observation_0": "Result 1",

            "thought_1": "Second thought",
            "tool_name_1": "tool_2",
            "tool_args_1": {},
        }

        result = normalize_trajectory(flat_trajectory)

        assert isinstance(result, list)
        assert len(result) == 2

        # Check Step 0
        assert result[0]["thought"] == "First thought"
        assert result[0]["tool_name"] == "tool_1"
        assert result[0]["tool_args"] == {"arg": 1}
        assert result[0]["observation"] == "Result 1"

        # Check Step 1
        assert result[1]["thought"] == "Second thought"
        assert result[1]["tool_name"] == "tool_2"

    def test_handles_mixed_keys(self):
        """Should handle mixed keys gracefully (generic suffix stripping)."""
        mixed_trajectory = {
            "thought_0": "T0",
            "tool_0": "func",
            "some_metadata": "ignore_me"
        }

        result = normalize_trajectory(mixed_trajectory)

        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0]["thought"] == "T0"
        # 'tool_0' should be normalized to 'tool_name' (it matches tool/tool_name pattern)
        assert result[0].get("tool_name") == "func"

    def test_returns_none_unchanged(self):
        """Should return None as-is."""
        assert normalize_trajectory(None) is None

    def test_non_indexed_dict_returned_unchanged(self):
        """A dict without indexed keys is returned as-is."""
        d = {"some_key": "value", "another": 42}
        result = normalize_trajectory(d)
        assert result == d

    def test_with_flat_dict_two_steps(self):
        """normalize_trajectory works with 2 indexed steps."""
        flat = {
            "thought_0": "First",
            "tool_name_0": "tool1",
            "thought_1": "Second",
            "tool_name_1": "tool2",
        }
        result = normalize_trajectory(flat)
        assert isinstance(result, list)
        assert len(result) == 2
        assert result[0]["thought"] == "First"
        assert result[1]["tool_name"] == "tool2"

    def test_non_dict_non_list_returned_unchanged(self):
        """Strings, ints, etc. are returned as-is."""
        assert normalize_trajectory("some string") == "some string"
        assert normalize_trajectory(42) == 42


class TestSerializeValue:
    """Tests for serialize_value() standalone function."""

    def test_none_returns_none(self):
        assert serialize_value(None) is None

    def test_basic_types_unchanged(self):
        assert serialize_value("hello") == "hello"
        assert serialize_value(42) == 42
        assert serialize_value(3.14) == 3.14
        assert serialize_value(True) is True

    def test_list_is_recursively_serialized(self):
        result = serialize_value([1, "two", [3, 4]])
        assert result == [1, "two", [3, 4]]

    def test_dict_is_recursively_serialized(self):
        result = serialize_value({"a": 1, "b": {"c": 2}})
        assert result == {"a": 1, "b": {"c": 2}}

    def test_object_with_dict_is_serialized(self):
        class Obj:
            def __init__(self):
                self.name = "test"
                self.value = 42
                self._private = "hidden"

        result = serialize_value(Obj())
        assert result == {"name": "test", "value": 42}
        assert "_private" not in result


class TestSerializeComplexObject:
    """Tests for _serialize_complex_object() standalone function."""

    def test_pydantic_model_dump_path(self):
        """Uses model_dump() for Pydantic-like objects."""
        class FakePydantic:
            def model_dump(self):
                return {"field": "value", "number": 7}

        result = _serialize_complex_object(FakePydantic())
        assert result == {"field": "value", "number": 7}

    def test_pydantic_model_dump_failure_falls_back_to_dict(self):
        """Falls back to __dict__ if model_dump() raises."""
        class BrokenModelDump:
            def model_dump(self):
                raise RuntimeError("broken")

            def __init__(self):
                self.name = "fallback"
                self.value = 99

        result = _serialize_complex_object(BrokenModelDump())
        assert result == {"name": "fallback", "value": 99}

    def test_object_with_dict_path(self):
        """Uses __dict__ for plain objects, skipping private attrs."""
        class Plain:
            def __init__(self):
                self.x = 1
                self.y = "hello"
                self._private = "hidden"

        result = _serialize_complex_object(Plain())
        assert result == {"x": 1, "y": "hello"}
        assert "_private" not in result

    def test_json_fallback_for_non_dict_objects(self):
        """Falls back to json for objects without __dict__ (e.g. tuples)."""
        result = _serialize_complex_object((1, 2, 3))
        assert result == [1, 2, 3]  # json serializes tuples as arrays

    def test_str_fallback_for_unserializable_objects(self):
        """Returns str() as last resort via json default=str."""
        class NoDict:
            __slots__ = []  # disables __dict__, forces json/str fallback path

            def __str__(self):
                return "NoDict-instance"

        result = _serialize_complex_object(NoDict())
        assert isinstance(result, str)
        assert "NoDict-instance" in result

    def test_nested_object_via_model_dump_is_recursively_serialized(self):
        """Recursively serializes nested objects from model_dump."""
        class Inner:
            def __init__(self):
                self.val = 42

        class Outer:
            def model_dump(self):
                return {"inner": Inner()}  # returns a non-basic value

        result = _serialize_complex_object(Outer())
        assert result == {"inner": {"val": 42}}
