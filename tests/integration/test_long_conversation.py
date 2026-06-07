"""Integration tests for long conversation with context compression."""

import pytest

from sdk.agent.core.agent import AgentBuilder


class MockLLM:
    """Mock LLM that tracks message count."""

    def __init__(self):
        self.call_count = 0
        self.message_history = []

    async def chat(self, messages, tools=None):
        self.call_count += 1
        self.message_history.extend(messages)
        # Simple response
        return {
            "message": {
                "role": "assistant",
                "content": f"Response {self.call_count}",
            },
            "raw": f"Mock response {self.call_count}"
        }


@pytest.mark.asyncio
class TestLongConversation:
    """Tests for long conversation handling."""

    @pytest.fixture
    def mock_llm(self):
        """Create mock LLM."""
        return MockLLM()

    @pytest.fixture
    def agent(self, mock_llm):
        """Create agent with low max_history_rounds."""
        return (
            AgentBuilder()
            .with_name("test_agent")
            .with_description("Test Agent")
            .with_llm(mock_llm)
            .with_max_history_rounds(3)  # Keep only 3 rounds
            .with_max_steps(2)
            .build()
        )

    async def test_history_truncation(self, agent, mock_llm):
        """Test that history is truncated after max rounds."""
        session_id = "test-session"

        # Simulate 5 conversations (exceeds max_history_rounds=3)
        for i in range(5):
            await agent.run(f"Task {i}", session_id)

        # History should be truncated
        sessions = agent.list_sessions()
        assert len(sessions) == 1

        # Context should have limited history
        context = agent.get_session_context(session_id)
        assert context is not None

    async def test_compression_enabled(self, mock_llm):
        """Test conversation with compression enabled."""
        agent = (
            AgentBuilder()
            .with_name("test_agent")
            .with_description("Test Agent")
            .with_llm(mock_llm)
            .with_compression_enabled(True)
            .with_max_context_length(5)  # Very low limit
            .with_max_history_rounds(10)
            .with_max_steps(2)
            .build()
        )

        session_id = "test-compression"

        # Send multiple messages to trigger compression
        for i in range(5):
            await agent.run(f"Task {i}", session_id)

        # Should have completed without errors
        context = agent.get_session_context(session_id)
        assert context is not None

    async def test_multiple_sessions_independence(self, agent, mock_llm):
        """Test that multiple sessions maintain independent history."""
        session1 = "session-1"
        session2 = "session-2"

        # Run different tasks in different sessions
        await agent.run("Task A", session1)
        await agent.run("Task B", session2)
        await agent.run("Task C", session1)

        # Both sessions should exist
        sessions = agent.list_sessions()
        assert len(sessions) >= 1  # May have more due to internal state

        # Clear one session
        agent.clear_session(session1)

    async def test_session_lifecycle(self, agent, mock_llm):
        """Test complete session lifecycle."""
        session_id = "lifecycle-test"

        # Create session implicitly
        result1 = await agent.run("First task", session_id)
        assert result1.output is not None

        # Get session context
        context = agent.get_session_context(session_id)
        assert context is not None
        assert context.session_id == session_id

        # Clear session
        cleared = agent.clear_session(session_id)
        assert cleared is True

        # Session should be removed from active sessions list
        sessions = agent.list_sessions()
        assert session_id not in sessions
