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
