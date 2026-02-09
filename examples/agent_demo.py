#!/usr/bin/env python
"""
PStock Agent 完整功能示例

本示例展示了 PStock SDK Agent 的所有功能特性：

1. ReAct 框架 - 思考-行动-观察循环
2. 工具调用 - 内置工具和自定义工具
3. 上下文管理 - 上下文压缩和截断
4. 多会话支持 - 独立的对话会话
5. 多轮对话 - 带历史记录的连续对话
6. 多智能体协作 - 子 Agent 委托
7. 记忆功能 - 记忆槽和记忆生成
8. 对话终止 - 运行时终止能力
9. 流式输出 - 实时步骤输出

Prerequisites:
    - 设置 OPENAI_API_KEY 环境变量或在 .env 文件中配置

Usage:
    python examples/agent_demo.py
"""

import asyncio
import os
from typing import Any

from dotenv import load_dotenv

from pstock_sdk.agent.core.agent import Agent, AgentBuilder
from pstock_sdk.agent.core.interfaces import AgentContext, Tool, ToolDefinition
from pstock_sdk.agent.memory.memory import MemoryRecord, MemorySlotConfig
from pstock_sdk.agent.llm.openai_llm import OpenAILLM, OpenAIModelOptions

load_dotenv()


# =============================================================================
# 自定义工具示例
# =============================================================================


class WeatherTool(Tool):
    """模拟天气查询工具"""

    def __init__(self):
        self._name = "get_weather"
        self._description = "获取指定城市的天气信息"
        # 模拟天气数据
        self._weather_data = {
            "北京": "晴天，温度 25°C",
            "上海": "多云，温度 22°C",
            "深圳": "阵雨，温度 28°C",
        }

    @property
    def name(self) -> str:
        return self._name

    @property
    def description(self) -> str:
        return self._description

    @property
    def display_name(self) -> str | None:
        return "天气查询"

    @property
    def parameters(self) -> dict[str, Any] | None:
        return {
            "type": "object",
            "properties": {
                "city": {
                    "type": "string",
                    "description": "城市名称",
                    "enum": ["北京", "上海", "深圳"],
                },
            },
            "required": ["city"],
        }

    def get_definition(self) -> ToolDefinition:
        return {
            "type": "function",
            "function": {
                "name": self._name,
                "description": self._description,
                "parameters": self.parameters,
            },
        }

    async def execute(self, input: Any, context: AgentContext | None = None) -> str:
        city = input.get("city")
        if city in self._weather_data:
            return f"{city}的天气：{self._weather_data[city]}"
        return f"抱歉，没有查询到{city}的天气信息"


class CalculatorTool(Tool):
    """模拟计算器工具"""

    def __init__(self):
        self._name = "calculator"
        self._description = "执行基本数学运算"

    @property
    def name(self) -> str:
        return self._name

    @property
    def description(self) -> str:
        return self._description

    @property
    def display_name(self) -> str | None:
        return "计算器"

    @property
    def parameters(self) -> dict[str, Any] | None:
        return {
            "type": "object",
            "properties": {
                "expression": {
                    "type": "string",
                    "description": "数学表达式，例如: 2 + 2 或 10 * 5",
                },
            },
            "required": ["expression"],
        }

    def get_definition(self) -> ToolDefinition:
        return {
            "type": "function",
            "function": {
                "name": self._name,
                "description": self._description,
                "parameters": self.parameters,
            },
        }

    async def execute(self, input: Any, context: AgentContext | None = None) -> str:
        try:
            # 注意：生产环境中应该使用更安全的方式计算表达式
            expression = input.get("expression", "")
            result = eval(expression, {"__builtins__": {}}, {})
            return f"计算结果: {result}"
        except Exception as e:
            return f"计算错误: {str(e)}"


# =============================================================================
# 功能 1: 基础 Agent 创建 (ReAct 框架)
# =============================================================================


def create_basic_agent() -> Agent:
    """
    创建一个基础 Agent，演示 ReAct 框架
    """
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY 环境变量未设置")

    llm = OpenAILLM(
        api_key=api_key,
        options=OpenAIModelOptions(
            model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            api_base=os.getenv("OPENAI_API_BASE", "https://api.openai.com/v1"),
        ),
    )

    agent = (
        AgentBuilder()
        .with_name("assistant")
        .with_description("AI 助手，使用 ReAct 框架思考并回答问题")
        .with_llm(llm)
        .with_max_steps(5)
        .with_instructions(
            "你是一个友好的 AI 助手。使用 ReAct 思考方式："
            "1. 理解用户的问题\n"
            "2. 思考如何回答\n"
            "3. 如果需要工具，调用工具\n"
            "4. 给出最终答案"
        )
        .build()
    )

    return agent


# =============================================================================
# 功能 2 & 3: 带工具和上下文管理的 Agent
# =============================================================================


def create_agent_with_tools_and_context() -> Agent:
    """
    创建带工具调用和上下文管理的 Agent
    """
    api_key = os.getenv("OPENAI_API_KEY")
    llm = OpenAILLM(
        api_key=api_key,
        options=OpenAIModelOptions(
            model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            api_base=os.getenv("OPENAI_API_BASE"),
        ),
    )

    agent = (
        AgentBuilder()
        .with_name("helper")
        .with_description("多功能助手 Agent")
        .with_llm(llm)
        .with_max_steps(10)
        # 添加工具
        .with_tools([WeatherTool(), CalculatorTool()])
        # 上下文管理配置
        .with_max_history_rounds(10)
        # 启用上下文压缩
        .with_compression_enabled(True)
        .with_max_context_length(50)
        .with_compression_trigger_ratio(0.8)
        .with_compression_ratio(0.3)
        .build()
    )

    return agent


# =============================================================================
# 功能 4 & 5: 多会话和多轮对话
# =============================================================================


async def demo_multi_session_conversation():
    """演示多会话和多轮对话功能"""
    print("\n" + "=" * 50)
    print("功能演示: 多会话和多轮对话")
    print("=" * 50)

    agent = create_agent_with_tools_and_context()

    # 会话 1: 与用户 A 的对话
    print("\n--- 会话 1: 与用户 A 的对话 ---")
    session_a = "user-a-session"

    result1 = await agent.run_with_context("我叫张三，住在北京", session_a)
    print(f"用户A: 我叫张三，住在北京")
    print(f"助手: {result1.output}")

    result2 = await agent.run_with_context("我住在哪里？", session_a)
    print(f"用户A: 我住在哪里？")
    print(f"助手: {result2.output}")

    # 会话 2: 与用户 B 的对话（独立会话）
    print("\n--- 会话 2: 与用户 B 的对话 ---")
    session_b = "user-b-session"

    result3 = await agent.run_with_context("我叫李四，住在上海", session_b)
    print(f"用户B: 我叫李四，住在上海")
    print(f"助手: {result3.output}")

    # 再次回到会话 1
    print("\n--- 回到会话 1 ---")
    result4 = await agent.run_with_context("我叫什么名字？", session_a)
    print(f"用户A: 我叫什么名字？")
    print(f"助手: {result4.output}")

    # 查看会话列表
    sessions = agent.list_sessions()
    print(f"\n当前活跃会话: {sessions}")


# =============================================================================
# 功能 6: 记忆功能
# =============================================================================


def create_agent_with_memory() -> Agent:
    """创建带记忆功能的 Agent"""
    api_key = os.getenv("OPENAI_API_KEY")
    llm = OpenAILLM(
        api_key=api_key,
        options=OpenAIModelOptions(
            model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            api_base=os.getenv("OPENAI_API_BASE"),
        ),
    )

    # 定义记忆槽
    memory_slots = [
        MemorySlotConfig(name="user_profile", description="用户画像信息", type="short_term"),
        MemorySlotConfig(name="preferences", description="用户偏好设置", type="short_term"),
        MemorySlotConfig(name="interaction_history", description="交互历史摘要", type="long_term"),
    ]

    agent = (
        AgentBuilder()
        .with_name("memory-assistant")
        .with_description("带记忆功能的智能助手")
        .with_llm(llm)
        .with_max_steps(5)
        # 启用记忆功能
        .with_memory_enabled(True)
        .with_memory_slots(memory_slots)
        .build()
    )

    return agent


async def demo_memory_function():
    """演示记忆功能"""
    print("\n" + "=" * 50)
    print("功能演示: 记忆功能")
    print("=" * 50)

    agent = create_agent_with_memory()
    session_id = "memory-demo-session"

    # 第一轮对话
    print("\n--- 第一轮对话 ---")
    result1 = await agent.run_with_context(
        "我叫王五，是一名软件工程师，喜欢编程和阅读",
        session_id,
    )
    print(f"用户: 我叫王五，是一名软件工程师，喜欢编程和阅读")
    print(f"助手: {result1.output}")

    # 查看记忆状态
    manager = agent.get_context_manager()
    memories = manager._load_memories(session_id)
    print(f"\n当前记忆记录数: {len(memories)}")
    for memory in memories:
        print(f"  - {memory.name}: {memory.content}")


# =============================================================================
# 功能 7: 多智能体协作
# =============================================================================


def create_multi_agent_system() -> Agent:
    """创建多智能体系统"""
    api_key = os.getenv("OPENAI_API_KEY")
    llm = OpenAILLM(
        api_key=api_key,
        options=OpenAIModelOptions(
            model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            api_base=os.getenv("OPENAI_API_BASE"),
        ),
    )

    # 创建子 Agent - 数据分析师
    data_analyst = (
        AgentBuilder()
        .with_name("data-analyst")
        .with_description("数据分析专家，擅长处理和分析数据")
        .with_llm(llm)
        .with_max_steps(5)
        .with_instructions("你是数据分析专家，专注于收集、整理和分析数据。")
        .build()
    )

    # 创建子 Agent - 报告生成器
    report_writer = (
        AgentBuilder()
        .with_name("report-writer")
        .with_description("报告撰写专家，擅长生成专业报告")
        .with_llm(llm)
        .with_max_steps(3)
        .with_instructions("你是报告撰写专家，专注于生成清晰、专业的报告。")
        .build()
    )

    # 创建主控 Agent
    coordinator = (
        AgentBuilder()
        .with_name("coordinator")
        .with_description("协调者 Agent，可以委托任务给子 Agent")
        .with_llm(llm)
        .with_max_steps(15)
        .with_instructions(
            "你是项目协调者。当需要数据分析时，委托给 data-analyst。"
            "当需要生成报告时，委托给 report-writer。"
            "整合各个子 Agent 的结果，给用户最终答案。"
        )
        .with_children([data_analyst, report_writer])
        .build()
    )

    return coordinator


async def demo_multi_agent():
    """演示多智能体协作"""
    print("\n" + "=" * 50)
    print("功能演示: 多智能体协作")
    print("=" * 50)

    coordinator = create_multi_agent_system()

    print("\n可用子 Agent:")
    for child in coordinator.children:
        print(f"  - {child.name}: {child.description}")

    # 运行一个需要协作的任务
    print("\n--- 协作任务 ---")
    result = await coordinator.run("帮我分析一下北京和上海的天气差异，并生成一份简要报告")
    print(f"用户: 帮我分析一下北京和上海的天气差异，并生成一份简要报告")
    print(f"助手: {result.output}")

    # 显示执行步骤
    print("\n执行步骤:")
    for i, step in enumerate(result.steps, 1):
        print(f"  {i}. [{step.type}] {step.display_name or ''}")


# =============================================================================
# 功能 8: 对话终止
# =============================================================================


async def demo_conversation_termination():
    """演示对话终止功能"""
    print("\n" + "=" * 50)
    print("功能演示: 对话终止")
    print("=" * 50)

    agent = create_basic_agent()

    print("\n--- 正常运行 ---")
    print("输入 'exit' 可随时终止对话")

    for i in range(3):
        user_input = input(f"\n第 {i+1} 轮对话 (输入 'exit' 终止): ").strip()

        if user_input.lower() == 'exit':
            print("正在终止对话...")
            agent.terminate()
            result = await agent.run("")
            print(f"助手: {result.output}")
            break

        result = await agent.run(user_input)
        print(f"助手: {result.output}")

    print("\n--- 检查终止状态 ---")
    print(f"Runtime terminated flag: {agent.runtime._terminated}")

    # 重置状态
    agent.runtime.reset()
    print(f"重置后 terminated flag: {agent.runtime._terminated}")


# =============================================================================
# 功能 9: 流式输出
# =============================================================================


async def demo_stream_output():
    """演示流式输出功能"""
    print("\n" + "=" * 50)
    print("功能演示: 流式输出")
    print("=" * 50)

    agent = create_agent_with_tools_and_context()
    context = agent.context_manager.get_context("stream-demo")

    print("\n--- 流式执行任务 ---")
    task = "查询北京的天气，然后计算 25 + 37 的结果"

    print(f"用户: {task}")
    print("\n执行步骤:")

    steps_output = []

    def emit_step(step):
        """收集并显示执行步骤（同步回调）"""
        step_info = f"[{step.type}] {step.display_name or step.type}: {step.content[:50]}..."
        print(f"  {step_info}")
        steps_output.append(step)

    result = await agent.runtime.run_stream(task, context, emit_step)

    print(f"\n最终答案: {result.output}")
    print(f"总步骤数: {len(steps_output)}")


# =============================================================================
# 完整功能演示
# =============================================================================


async def demo_all_features():
    """运行所有功能演示"""
    print("\n" + "=" * 70)
    print(" " * 15 + "PStock Agent 完整功能演示")
    print("=" * 70)

    # 检查 API Key
    if not os.getenv("OPENAI_API_KEY"):
        print("\n错误: 请设置 OPENAI_API_KEY 环境变量")
        print("示例: export OPENAI_API_KEY=sk-xxx")
        return

    # 功能 1 & 2 & 3: 基础 Agent、工具调用、上下文管理
    print("\n【功能 1-3】基础 Agent 创建、工具调用、上下文管理")
    agent = create_agent_with_tools_and_context()
    print(f"✓ 创建 Agent: {agent.name}")
    print(f"✓ 工具数量: {len(agent.tool_registry.list())}")
    print(f"✓ 上下文压缩: {agent.context_manager.compression_enabled}")

    # 快速测试
    result = await agent.run("你好，请介绍一下你自己")
    print(f"\n测试对话:")
    print(f"  用户: 你好，请介绍一下你自己")
    print(f"  助手: {result.output}")

    # 功能 4 & 5: 多会话和多轮对话
    await demo_multi_session_conversation()

    # 功能 6: 记忆功能
    await demo_memory_function()

    # 功能 7: 多智能体协作
    await demo_multi_agent()

    # 功能 8: 对话终止 (交互式，跳过自动演示)
    print("\n" + "=" * 50)
    print("功能演示: 对话终止")
    print("=" * 50)
    print("(交互式演示，已跳过自动运行)")
    print("使用 demo_conversation_termination() 可交互式体验")

    # 功能 9: 流式输出
    await demo_stream_output()

    print("\n" + "=" * 70)
    print(" " * 25 + "功能演示完成！")
    print("=" * 70)


# =============================================================================
# 交互式模式
# =============================================================================


async def interactive_mode():
    """交互式对话模式"""
    print("\n" + "=" * 50)
    print("交互式对话模式")
    print("=" * 50)
    print("输入 'quit' 或 'exit' 退出")

    # 使用功能最全的 Agent
    agent = create_agent_with_tools_and_context()
    session_id = "interactive-session"

    print(f"\n已启动: {agent.name}")
    print(f"可用工具: {[tool.name for tool in agent.tool_registry.list()]}")

    while True:
        try:
            user_input = input("\n你: ").strip()

            if user_input.lower() in ['quit', 'exit', '退出']:
                print("再见！")
                break

            if not user_input:
                continue

            result = await agent.run_with_context(user_input, session_id)
            print(f"助手: {result.output}")

            # 显示步骤（可选）
            if len(result.steps) > 1:
                print(f"\n[执行了 {len(result.steps)} 个步骤]")

        except KeyboardInterrupt:
            print("\n\n对话被中断")
            break
        except Exception as e:
            print(f"\n错误: {e}")


# =============================================================================
# 主函数
# =============================================================================


def main():
    """主函数"""
    import sys

    if len(sys.argv) > 1:
        command = sys.argv[1].lower()

        if command in ['interactive', 'i']:
            asyncio.run(interactive_mode())
        elif command in ['terminate', 't']:
            asyncio.run(demo_conversation_termination())
        elif command in ['stream', 's']:
            asyncio.run(demo_stream_output())
        elif command in ['all']:
            asyncio.run(demo_all_features())
        else:
            print("未知命令")
            print("可用命令:")
            print("  python agent_demo.py all        # 运行所有功能演示")
            print("  python agent_demo.py interactive # 交互式对话")
            print("  python agent_demo.py stream     # 流式输出演示")
            print("  python agent_demo.py terminate  # 对话终止演示")
    else:
        # 默认运行所有演示
        asyncio.run(demo_all_features())


if __name__ == "__main__":
    main()
