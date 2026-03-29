"""
Unit tests for AI core domain models.

Tests the Pydantic models:
- ContextUsage
- ChatConfig
- ChatResult
"""
from autocode.core.ai.models import ContextUsage, ChatConfig, ChatResult


class TestContextUsage:
    """Tests for ContextUsage model."""

    def test_default_values(self):
        usage = ContextUsage()
        assert usage.current == 0
        assert usage.max == 0
        assert usage.percentage == 0.0

    def test_custom_values(self):
        usage = ContextUsage(current=1000, max=8000, percentage=12.5)
        assert usage.current == 1000
        assert usage.max == 8000
        assert usage.percentage == 12.5


class TestChatConfig:
    """Tests for ChatConfig model."""

    def test_default_values(self):
        config = ChatConfig()
        assert config.module_kwargs_schemas == {}
        assert config.available_tools == []
        assert config.models == []

    def test_custom_values(self):
        config = ChatConfig(
            module_kwargs_schemas={"ReAct": {"params": []}},
            available_tools=[{"name": "tool_a"}],
            models=[{"id": "gpt-4o"}]
        )
        assert config.module_kwargs_schemas == {"ReAct": {"params": []}}
        assert len(config.available_tools) == 1
        assert len(config.models) == 1


class TestChatResult:
    """Tests for ChatResult model."""

    def test_default_values(self):
        result = ChatResult()
        assert result.response == ""
        assert result.reasoning is None
        assert result.trajectory is None
        assert result.history is None
        assert result.completions is None

    def test_with_response(self):
        result = ChatResult(response="Hello!")
        assert result.response == "Hello!"

    def test_with_all_fields(self):
        result = ChatResult(
            response="Answer",
            reasoning="Step 1: ...",
            trajectory=[{"thought": "thinking"}],
            history=[{"role": "user", "content": "hi"}],
            completions=["A", "B"]
        )
        assert result.response == "Answer"
        assert result.reasoning == "Step 1: ..."
        assert isinstance(result.trajectory, list)
        assert isinstance(result.history, list)
        assert result.completions == ["A", "B"]

    def test_trajectory_accepts_dict(self):
        result = ChatResult(trajectory={"thought_0": "thinking"})
        assert isinstance(result.trajectory, dict)
