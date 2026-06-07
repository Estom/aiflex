"""Integration tests for multi-agent collaboration."""

import pytest

from sdk.agent.core.agent import AgentBuilder
from sdk.agent.tools.base_tool import BaseTool


class MockLLM:
    """Mock LLM for testing."""

    def __init__(self):
        self.messages = []

    async def chat(self, messages, tools=None):
        self.messages.extend(messages)
        # Simple mock response
        return {
            "message": {
                "content": "I understand the task.",
                "tool_calls": []
            },
            "raw": "Mock response"
        }


@pytest.mark.asyncio
class TestMultiAgentCollaboration:
    """Tests for multi-agent collaboration."""

    @pytest.fixture
    def mock_llm(self):
        """Create mock LLM."""
        return MockLLM()

    @pytest.fixture
    def child_agent(self, mock_llm):
        """Create a child agent."""
        return (
            AgentBuilder()
            .with_name("data_fetcher")
            .with_description("Fetches data")
            .with_llm(mock_llm)
            .with_max_steps(3)
            .build()
        )

    @pytest.fixture
    def parent_agent(self, mock_llm, child_agent):
        """Create a parent agent with child."""
        return (
            AgentBuilder()
            .with_name("analyst")
            .with_description("Financial analyst")
            .with_llm(mock_llm)
            .with_child(child_agent)
            .with_max_steps(5)
            .build()
        )

    async def test_agent_has_children(self, parent_agent, child_agent):
        """Test that parent agent has children."""
        assert len(parent_agent.children) == 1
        assert parent_agent.children[0].name == child_agent.name

    async def test_child_agent_executable(self, child_agent):
        """Test that child agent can execute tasks."""
        result = await child_agent.run("Test task")
        assert result.output is not None

    async def test_parent_can_delegate(self, parent_agent, mock_llm):
        """Test that parent can delegate to child."""
        # Check that child agent is registered as a tool
        tools = parent_agent.tool_registry.list()
        tool_names = [t.name for t in tools]
        # Child agent name is prefixed with "agent_"
        assert "agent_data_fetcher" in tool_names

    async def test_multi_agent_independence(self, child_agent, mock_llm):
        """Test that agents maintain independent state."""
        # Create two instances with same LLM
        agent1 = (
            AgentBuilder()
            .with_name("agent1")
            .with_description("Agent 1")
            .with_llm(mock_llm)
            .build()
        )
        agent2 = (
            AgentBuilder()
            .with_name("agent2")
            .with_description("Agent 2")
            .with_llm(mock_llm)
            .build()
        )

        # Run both agents
        await agent1.run("Task 1")
        await agent2.run("Task 2")

        # Both should work independently
        assert len(agent1.context_manager.list_sessions()) > 0
        assert len(agent2.context_manager.list_sessions()) > 0


@pytest.mark.asyncio
class TestAgentTools:
    """Tests for agent tool adapter."""

    @pytest.fixture
    def mock_llm(self):
        """Create mock LLM."""
        return MockLLM()

    @pytest.fixture
    def simple_agent(self, mock_llm):
        """Create a simple agent."""
        return (
            AgentBuilder()
            .with_name("test_agent")
            .with_description("Test agent")
            .with_llm(mock_llm)
            .build()
        )

    async def test_agent_has_builtin_tools(self, simple_agent):
        """Test that agent has builtin tools."""
        tools = simple_agent.tool_registry.list()
        tool_names = [t.name for t in tools]

        # Check for some expected tools
        assert "shell" in tool_names
        assert "read_file" in tool_names
        assert "write_file" in tool_names

    async def test_tool_registration(self, simple_agent):
        """Test tool registration."""
        class CustomTool(BaseTool):
            name = "custom_tool"
            description = "A custom tool"

            async def execute(self, input, context=None):
                return "Custom result"

        agent = (
            AgentBuilder()
            .with_name("test_agent")
            .with_description("Test agent")
            .with_llm(simple_agent.llm)
            .with_tool(CustomTool())
            .build()
        )

        tools = agent.tool_registry.list()
        tool_names = [t.name for t in tools]
        assert "custom_tool" in tool_names
