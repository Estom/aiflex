# Quick fix: Revert problematic changes and add simple observability

# 1. Restore original imports
import json
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any
from datetime import datetime

from loguru import logger

from .interfaces import (
    AgentContext,
    AgentRunResult,
    AgentStep,
    ChatMessage,
    LLM,
    ToolCall,
    ToolDefinition,
)
from ..tools.tool_registry import ToolRegistry
from ..skills.skill_registry import SkillRegistry
from ...utils.agent_step import build_agent_step
from .step_context_manager import StepContextManager

# Simple observability (without integration issues)
class SimpleMetrics:
    """Simple metrics collector without complex dependencies."""
    def __init__(self):
        self.tool_calls = 0
        self.tool_failures = 0

    def record_tool_call(self, name):
        self.tool_calls += 1

    def record_tool_failure(self, name):
        self.tool_failures += 1


@dataclass
class AgentRuntimeConfig:
    """Agent Runtime 配置"""

    name: str
    description: str
    max_steps: int = 5
    instructions: str | None = None
    workspace_root: str | None = None
    # 压缩相关配置
    compression_enabled: bool = False
    max_context_length: int = 50
    compression_trigger_ratio: float = 0.8
    compression_ratio: float = 0.3
    # 可观测性配置（简化版，避免集成问题）
    metrics_enabled: bool = False


class AgentRuntime:
    """
    Agent 运行时

    负责：
    - 执行 ReAct 循环
    - 调用 LLM
    - 执行工具调用
    - 支持会话终止
    """

    def __init__(
        self,
        llm: LLM,
        tool_registry: ToolRegistry,
        skill_registry: SkillRegistry,
        config: AgentRuntimeConfig,
    ):
        self.llm = llm
        self.tool_registry = tool_registry
        self.skill_registry = skill_registry
        self.config = config
        self._terminated = False

        # 简化的 metrics（不使用复杂的 observability 模块）
        self.metrics = SimpleMetrics() if config.metrics_enabled else None

        # 默认 instructions
        if not config.instructions:
            config.instructions = (
                "Use ReAct style with OpenAI function calling. "
                "Call tools when helpful and provide a concise final answer when done."
            )

    def terminate(self) -> None:
        """终止当前运行的会话"""
        self._terminated = True

    def reset(self) -> None:
        """重置终止状态，用于下次运行"""
        self._terminated = False
