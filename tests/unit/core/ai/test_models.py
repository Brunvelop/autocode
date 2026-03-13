"""
Unit tests for AI core models.
"""
import pytest
from autocode.core.ai.models import DspyOutput

class TestDspyOutput:
    
    def test_trajectory_normalization_clean(self):
        """Should preserve already clean trajectory."""
        clean_trajectory = [
            {"thought": "Thinking...", "tool": "search"},
            {"thought": "Done", "tool": "finish"}
        ]
        
        output = DspyOutput(
            success=True,
            result={},
            trajectory=clean_trajectory
        )
        
        dump = output.model_dump()
        assert dump["trajectory"] == clean_trajectory

    def test_trajectory_normalization_flat_dspy_react(self):
        """Should normalize flat DSPy ReAct dictionary to list of steps."""
        flat_trajectory = {
            "thought_0": "First thought",
            "tool_name_0": "tool_1",
            "tool_args_0": {"arg": 1},
            "observation_0": "Result 1",
            
            "thought_1": "Second thought",
            "tool_name_1": "tool_2",
            "tool_args_1": {},
            # Missing observation_1 simulates incomplete step or just different structure
        }
        
        output = DspyOutput(
            success=True,
            result={},
            trajectory=flat_trajectory
        )
        
        dump = output.model_dump()
        traj = dump["trajectory"]
        
        assert isinstance(traj, list)
        assert len(traj) == 2
        
        # Check Step 0
        assert traj[0]["thought"] == "First thought"
        assert traj[0]["tool_name"] == "tool_1"
        assert traj[0]["tool_args"] == {"arg": 1}
        assert traj[0]["observation"] == "Result 1"
        
        # Check Step 1
        assert traj[1]["thought"] == "Second thought"
        assert traj[1]["tool_name"] == "tool_2"

    def test_trajectory_normalization_mixed_keys(self):
        """Should handle mixed keys gracefully."""
        # DSPy sometimes includes other metadata keys
        mixed_trajectory = {
            "thought_0": "T0",
            "tool_0": "func", # Sometimes it's tool, sometimes tool_name
            "some_metadata": "ignore_me"
        }
        
        output = DspyOutput(
            success=True,
            result={},
            trajectory=mixed_trajectory
        )
        
        dump = output.model_dump()
        traj = dump["trajectory"]
        
        assert isinstance(traj, list)
        assert len(traj) == 1
        assert traj[0]["thought"] == "T0"
        # The key 'tool_0' should be preserved as 'tool' if we map it, 
        # or just kept as is if we are generic.
        # Let's see how we implement it. Assuming generic suffix stripping.
        assert traj[0].get("tool") == "func" or traj[0].get("tool_name") == "func"

    def test_trajectory_none(self):
        """Should handle None trajectory."""
        output = DspyOutput(
            success=True,
            result={},
            trajectory=None
        )
        assert output.model_dump()["trajectory"] is None


class TestDspyOutputStaticMethods:
    """Tests for DspyOutput static methods (normalize_trajectory, serialize_value)."""
    
    def test_normalize_trajectory_static_with_flat_dict(self):
        """normalize_trajectory works as staticmethod without instance."""
        flat = {
            "thought_0": "First",
            "tool_name_0": "tool1",
            "thought_1": "Second",
            "tool_name_1": "tool2",
        }
        result = DspyOutput.normalize_trajectory(flat)
        assert isinstance(result, list)
        assert len(result) == 2
        assert result[0]["thought"] == "First"
        assert result[1]["tool_name"] == "tool2"
    
    def test_normalize_trajectory_static_with_list(self):
        """normalize_trajectory passes through lists unchanged."""
        trajectory = [{"thought": "step1"}, {"thought": "step2"}]
        result = DspyOutput.normalize_trajectory(trajectory)
        assert result == trajectory
    
    def test_normalize_trajectory_static_with_none(self):
        """normalize_trajectory returns None for None input."""
        assert DspyOutput.normalize_trajectory(None) is None
    
    def test_normalize_trajectory_static_with_non_indexed_dict(self):
        """normalize_trajectory returns dict as-is if no indexed keys."""
        d = {"some_key": "value", "another": 42}
        result = DspyOutput.normalize_trajectory(d)
        assert result == d
    
    def test_serialize_value_static_basic_types(self):
        """serialize_value works as staticmethod with basic types."""
        assert DspyOutput.serialize_value(None) is None
        assert DspyOutput.serialize_value("hello") == "hello"
        assert DspyOutput.serialize_value(42) == 42
        assert DspyOutput.serialize_value(3.14) == 3.14
        assert DspyOutput.serialize_value(True) is True
    
    def test_serialize_value_static_list(self):
        """serialize_value recursively serializes lists."""
        result = DspyOutput.serialize_value([1, "two", [3, 4]])
        assert result == [1, "two", [3, 4]]
    
    def test_serialize_value_static_dict(self):
        """serialize_value recursively serializes dicts."""
        result = DspyOutput.serialize_value({"a": 1, "b": {"c": 2}})
        assert result == {"a": 1, "b": {"c": 2}}
    
    def test_serialize_value_static_object_with_dict(self):
        """serialize_value handles objects with __dict__."""
        class Obj:
            def __init__(self):
                self.name = "test"
                self.value = 42
                self._private = "hidden"
        
        result = DspyOutput.serialize_value(Obj())
        assert result == {"name": "test", "value": 42}
    
    def test_model_dump_uses_static_methods(self):
        """model_dump() still works correctly after refactor to staticmethods."""
        flat_trajectory = {
            "thought_0": "Thinking",
            "tool_name_0": "search",
        }
        output = DspyOutput(
            success=True,
            result={"response": "hello"},
            trajectory=flat_trajectory,
            reasoning="Some reasoning"
        )
        dump = output.model_dump()
        
        # trajectory should be normalized
        assert isinstance(dump["trajectory"], list)
        assert dump["trajectory"][0]["thought"] == "Thinking"
        
        # Other fields should work
        assert dump["success"] is True
        assert dump["result"] == {"response": "hello"}
        assert dump["reasoning"] == "Some reasoning"


class TestSerializeComplexObject:
    """Tests for DspyOutput._serialize_complex_object static method."""

    def test_pydantic_model_dump_path(self):
        """_serialize_complex_object uses model_dump() for Pydantic-like objects."""
        class FakePydantic:
            def model_dump(self):
                return {"field": "value", "number": 7}

        result = DspyOutput._serialize_complex_object(FakePydantic())
        assert result == {"field": "value", "number": 7}

    def test_pydantic_model_dump_failure_falls_back_to_dict(self):
        """_serialize_complex_object falls back to __dict__ if model_dump() raises."""
        class BrokenModelDump:
            def model_dump(self):
                raise RuntimeError("broken")

            def __init__(self):
                self.name = "fallback"
                self.value = 99

        result = DspyOutput._serialize_complex_object(BrokenModelDump())
        assert result == {"name": "fallback", "value": 99}

    def test_object_with_dict_path(self):
        """_serialize_complex_object uses __dict__ for plain objects."""
        class Plain:
            def __init__(self):
                self.x = 1
                self.y = "hello"
                self._private = "hidden"

        result = DspyOutput._serialize_complex_object(Plain())
        assert result == {"x": 1, "y": "hello"}
        assert "_private" not in result

    def test_json_fallback_for_non_dict_objects(self):
        """_serialize_complex_object falls back to json for objects without __dict__."""
        # A tuple goes through the json.dumps/loads path
        result = DspyOutput._serialize_complex_object((1, 2, 3))
        assert result == [1, 2, 3]  # json serializes tuples as arrays

    def test_str_fallback_for_unserializable_objects(self):
        """_serialize_complex_object returns str() as last resort via json default=str."""
        class NoDict:
            __slots__ = []  # disables __dict__, forces json/str fallback path

            def __str__(self):
                return "NoDict-instance"

        result = DspyOutput._serialize_complex_object(NoDict())
        # json.dumps with default=str converts it to a string representation
        assert isinstance(result, str)
        assert "NoDict-instance" in result

    def test_nested_object_via_model_dump_is_recursively_serialized(self):
        """_serialize_complex_object recursively serializes nested objects from model_dump."""
        class Inner:
            def __init__(self):
                self.val = 42

        class Outer:
            def model_dump(self):
                return {"inner": Inner()}  # returns a non-basic value

        result = DspyOutput._serialize_complex_object(Outer())
        # The inner object should be recursively serialized via serialize_value
        assert result == {"inner": {"val": 42}}
