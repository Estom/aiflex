"""Performance benchmark tests for Agent."""

import asyncio
import time

import pytest

from sdk.agent.core.agent import AgentBuilder


class MockLLM:
    """Mock LLM with configurable latency."""

    def __init__(self, latency_ms: int = 10):
        self.latency = latency_ms / 1000.0  # Convert to seconds
        self.call_count = 0

    async def chat(self, messages, tools=None):
        self.call_count += 1
        # Simulate network latency
        await asyncio.sleep(self.latency)
        return {
            "message": {
                "role": "assistant",
                "content": "Benchmark response",
                "tool_calls": []
            },
            "raw": "Mock benchmark response"
        }


class LatencyTracker:
    """Track execution time."""

    def __init__(self):
        self.start_time = None
        self.end_time = None
        self.duration_ms = None

    def start(self):
        """Start tracking."""
        self.start_time = time.perf_counter()

    def stop(self):
        """Stop tracking and calculate duration."""
        self.end_time = time.perf_counter()
        self.duration_ms = (self.end_time - self.start_time) * 1000


@pytest.mark.asyncio
class TestAgentBenchmark:
    """Benchmark tests for Agent performance."""

    @pytest.fixture
    def fast_llm(self):
        """Create fast mock LLM (10ms)."""
        return MockLLM(latency_ms=10)

    @pytest.fixture
    def slow_llm(self):
        """Create slow mock LLM (100ms)."""
        return MockLLM(latency_ms=100)

    @pytest.fixture
    def agent(self, fast_llm):
        """Create benchmark agent."""
        return (
            AgentBuilder()
            .with_name("benchmark_agent")
            .with_description("Benchmark Agent")
            .with_llm(fast_llm)
            .with_max_steps(5)
            .build()
        )

    async def test_single_run_performance(self, agent, fast_llm):
        """Benchmark single agent run."""
        tracker = LatencyTracker()
        tracker.start()

        result = await agent.run("Benchmark task", "session-1")

        tracker.stop()

        # Should complete quickly
        assert result.output is not None
        assert tracker.duration_ms < 500  # Should be < 500ms
        assert fast_llm.call_count == 1  # One LLM call

    async def test_multiple_runs_performance(self, agent, fast_llm):
        """Benchmark multiple sequential runs."""
        runs = 10
        durations = []

        for i in range(runs):
            tracker = LatencyTracker()
            tracker.start()

            await agent.run(f"Task {i}", f"session-{i}")

            tracker.stop()
            durations.append(tracker.duration_ms)

        # Calculate statistics
        avg_duration = sum(durations) / len(durations)
        max_duration = max(durations)
        min_duration = min(durations)

        # All runs should be fast
        assert avg_duration < 500
        assert max_duration < 500

        # Fastest run
        fastest_run = durations.index(min_duration)
        assert fastest_run >= 0

    async def test_tool_call_overhead(self, agent, fast_llm):
        """Benchmark overhead of tool calls."""
        # Agent with one tool call should take longer than just LLM response
        # because of tool execution

        # Measure just LLM response time
        llm_tracker = LatencyTracker()
        llm_tracker.start()

        await fast_llm.chat([{"role": "user", "content": "Test"}])

        llm_tracker.stop()
        llm_only_time = llm_tracker.duration_ms

        # Measure full agent run
        agent_tracker = LatencyTracker()
        agent_tracker.start()

        await agent.run("Test task", "benchmark-session")

        agent_tracker.stop()
        agent_time = agent_tracker.duration_ms

        # Agent time should be close to LLM time (for simple tasks)
        # May be slightly higher due to overhead
        assert agent_time >= llm_only_time * 0.9  # Allow some overhead
        assert agent_time < llm_only_time * 3  # But not too much overhead

    async def test_context_memory_usage(self, agent, fast_llm):
        """Test that context memory doesn't grow unbounded."""
        session_id = "memory-benchmark"

        initial_call_count = fast_llm.call_count

        # Run multiple turns
        for i in range(10):
            await agent.run(f"Turn {i}", session_id)

        final_call_count = fast_llm.call_count
        total_calls = final_call_count - initial_call_count

        # Should have exactly 10 LLM calls
        assert total_calls == 10

        # Clear session
        agent.clear_session(session_id)

    async def test_latency_impact(self, slow_llm):
        """Test impact of LLM latency on overall performance."""
        agent = (
            AgentBuilder()
            .with_name("slow_agent")
            .with_description("Slow Agent")
            .with_llm(slow_llm)
            .with_max_steps(2)
            .build()
        )

        tracker = LatencyTracker()
        tracker.start()

        await agent.run("Task with slow LLM", "slow-session")

        tracker.stop()

        # Should take about 100ms (LLM latency) + overhead
        assert tracker.duration_ms >= 100  # At least LLM latency
        assert tracker.duration_ms < 300  # But not too much overhead

    async def test_concurrent_sessions_performance(self, fast_llm):
        """Benchmark creating and managing multiple sessions."""
        agent = (
            AgentBuilder()
            .with_name("multi-session-agent")
            .with_description("Multi Session Agent")
            .with_llm(fast_llm)
            .with_max_steps(2)
            .build()
        )

        tracker = LatencyTracker()
        tracker.start()

        # Create and run 5 sessions concurrently
        tasks = [agent.run(f"Task {i}", f"session-{i}") for i in range(5)]
        await asyncio.gather(*tasks)

        tracker.stop()

        # Should complete all sessions
        assert tracker.duration_ms < 1500  # 5 sessions * ~100-200ms each
        assert fast_llm.call_count == 5  # One call per session
