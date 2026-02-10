"""
Agent Runtime - Agent 运行时实现

实现 ReAct 循环：思考 -> 行动 -> 观察 -> 最终答案
"""

import json
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from loguru import logger

from .agent_context import AgentContextManager
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


@dataclass
class AgentRuntimeConfig:
    """Agent Runtime 配置"""
    name: str
    description: str
    max_steps: int = 5
    instructions: str | None = None
    workspace_root: str | None = None


class AgentRuntime:
    """
    Agent 运行时

    负责：
    - 构建 system prompt
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
        context_manager: AgentContextManager,
    ):
        self.llm = llm
        self.tool_registry = tool_registry
        self.skill_registry = skill_registry
        self.config = config
        self.context_manager = context_manager
        self._terminated = False

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

    async def run(self, task: str, session_id: str | None = None) -> AgentRunResult:
        """
        运行 Agent 任务

        Args:
            task: 用户任务
            session_id: 会话 ID，如果为 None 则自动生成

        Returns:
            AgentRunResult: 运行结果
        """
        # 获取或创建上下文
        context = self.context_manager.get_context(session_id)

        steps: list[AgentStep] = []
        iteration = 0

        # 记录用户最新提问的历史消息
        await self.context_manager.add_message(session_id, {
            "role": "user",
            "content": task
        })

        # ReAct 循环
        while iteration < self.config.max_steps:
            # 每次循环前重新构建消息列表，获取最新的历史消息（包含系统提示词）
            messages: list[ChatMessage] = await self.context_manager.get_messages(session_id)
            # 检查终止标志-只需要模型开启前执行即可，其他步骤无需打断
            if self._terminated:
                terminated_step = build_agent_step(
                    "terminated",
                    "会话已被终止",
                    "会话终止",
                )
                steps.append(terminated_step)
                self.reset()
                return AgentRunResult(
                    output="[会话已终止]",
                    steps=steps,
                )

            # 调用 LLM
            reply = await self.llm.chat(messages, self.tool_registry.definitions())
            content = reply["message"].get("content")
            tool_calls = reply["message"].get("tool_calls", [])

            # 记录思考步骤
            thought_step = build_agent_step(
                "thought",
                content or "",
                "思考中",
                reply.get("raw"),
            )
            steps.append(thought_step)
            # 记录模型回复历史消息
            await self.context_manager.add_message(session_id, {
                "role": "assistant",
                "content": content,
                "tool_calls": tool_calls,
            })

            # 如果有工具调用
            if tool_calls:
                # 执行每个工具调用
                for call in tool_calls:
                    action_step = self._build_tool_step(call, content)
                    steps.append(action_step)

                    # 执行工具
                    observation = await self._execute_tool(call, context)
                    observation_step = build_agent_step(
                        "observation",
                        observation,
                        f"工具结果 {call['name']}",
                        reply.get("raw"),
                        {"call": call["name"]},
                    )
                    steps.append(observation_step)

                    # 添加工具结果到历史消息
                    await self.context_manager.add_message(session_id, {
                        "role": "tool",
                        "tool_call_id": call["id"],
                        "name": call["name"],
                        "content": observation,
                    })

                iteration += 1
                continue

            # 如果有最终回答
            if content:
                final_step = build_agent_step(
                    "final",
                    content.strip(),
                    "最终回答",
                    reply.get("raw"),
                )
                steps.append(final_step)
                return AgentRunResult(output=content.strip(), steps=steps)

            # 空响应
            empty_step = build_agent_step(
                "error",
                "No response content from model.",
                "回答丢失",
                reply.get("raw"),
            )
            steps.append(empty_step)
            iteration += 1

        # 达到最大步数
        fallback = "Error: Maximum steps reached without a final answer."
        final_step = build_agent_step("error", fallback, "回答错误")
        steps.append(final_step)
        return AgentRunResult(output=fallback, steps=steps)

    async def run_stream(
        self,
        task: str,
        session_id: str | None = None,
        emit: Callable[[AgentStep], None] | None = None,
    ) -> AgentRunResult:
        """
        流式运行 Agent（用于实时输出）

        Args:
            task: 用户任务
            session_id: 会话 ID，如果为 None 则自动生成
            emit: 回调函数，用于发送步骤

        Returns:
            AgentRunResult: 运行结果
        """
        # 获取或创建上下文
        context = self.context_manager.get_context(session_id)
        session_id = context.session_id

        iteration = 0

        # 记录用户最新提问的历史消息
        await self.context_manager.add_message(session_id, {
            "role": "user",
            "content": task
        })

        while iteration < self.config.max_steps:
            # 每次循环前重新构建消息列表，获取最新的历史消息（包含系统提示词）
            messages: list[ChatMessage] = await self.context_manager.get_messages(session_id)
            # 检查终止标志
            if self._terminated:
                terminated_step = build_agent_step(
                    "terminated",
                    "会话已被终止",
                    "会话终止",
                )
                if emit:
                    await emit(terminated_step)
                self.reset()
                return AgentRunResult(output="[会话已终止]")

            reply = await self.llm.chat(messages, self.tool_registry.definitions())
            content = reply["message"].get("content")
            tool_calls = reply["message"].get("tool_calls", [])

            # 发送思考步骤
            agent_step = build_agent_step(
                "thought",
                content or "",
                "思考中",
                reply.get("raw"),
            )
            if emit:
                await emit(agent_step)

            # 记录模型回复历史消息
            await self.context_manager.add_message(session_id, {
                "role": "assistant",
                "content": content,
                "tool_calls": tool_calls,
            })
            
            # 如果有工具调用
            if tool_calls:
                for call in tool_calls:
                    # 发送动作步骤
                    action_step = self._build_tool_step(call, content)
                    if emit:
                        await emit(action_step)

                    # 执行工具
                    observation = await self._execute_tool(call, context)

                    # 发送观察步骤
                    observation_step = build_agent_step(
                        "observation",
                        observation,
                        f"调用结果 {call['name']}",
                        reply.get("raw"),
                        {"call": call["name"]},
                    )
                    if emit:
                        await emit(observation_step)
                    # 记录工具调用历史消息
                    await self.context_manager.add_message(session_id,{
                        "role": "tool",
                        "tool_call_id": call["id"],
                        "name": call["name"],
                        "content": observation,
                    })

                iteration += 1
                continue

            # 最终回答
            if content:
                final_step = build_agent_step(
                    "final",
                    content.strip(),
                    "最终回答",
                    reply.get("raw"),
                )
                if emit:
                    await emit(final_step)
                return AgentRunResult(output=content.strip())

            # 空响应
            empty_step = build_agent_step(
                "error",
                "No response content from model.",
                "回答丢失",
                reply.get("raw"),
            )
            if emit:
                await emit(empty_step)
            iteration += 1

        # 达到最大步数
        fallback = "Error: Maximum steps reached without a final answer."
        final_step = build_agent_step("error", fallback, "回答错误")
        if emit:
            await emit(final_step)
        return AgentRunResult(output=fallback)

    def _build_tool_step(self, call: ToolCall, thought: str | None) -> AgentStep:
        """构建工具调用步骤"""
        try:
            parsed_args = json.loads(call["arguments"])
        except json.JSONDecodeError:
            parsed_args = call["arguments"]

        action_input = json.dumps(parsed_args) if not isinstance(
            parsed_args, str) else parsed_args

        return build_agent_step(
            "action",
            action_input,
            f"调用工具 {call['name']}",
            call,
            {"call": call["name"], "thought": thought},
        )

    async def _execute_tool(self, call: ToolCall, context: AgentContext | None) -> str:
        """执行工具调用"""
        tool = self.tool_registry.get(call["name"])
        if not tool:
            return f"Error: tool {call['name']} not found."

        try:
            args = json.loads(call["arguments"])
        except json.JSONDecodeError:
            args = call["arguments"]

        try:
            return await tool.execute(args, context)
        except Exception as e:
            logger.error(f"Error executing tool {call['name']}: {e}")
            return f"Error executing tool {call['name']}: {e!s}"

    def _get_history_messages(self, context: AgentContext | None) -> list[ChatMessage]:
        """获取历史消息"""
        if not context:
            return []
        return context.history_messages or []
