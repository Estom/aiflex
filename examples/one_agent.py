#!/usr/bin/env python
"""
PStock 完整功能智能体示例

创建一个使用所有 PStock SDK Agent 功能的智能体。

功能列表：
1. ReAct 框架 - 思考-行动-观察循环
2. 工具调用 - 多个自定义工具
3. 上下文管理 - 压缩和截断
4. 多会话支持 - 独立对话会话
5. 多轮对话 - 历史记录管理
6. 多智能体 - 子 Agent 协作
7. 记忆功能 - 记忆槽和自动生成
8. 对话终止 - 运行时终止能力
9. 流式输出 - 实时步骤展示
"""

from pstock_sdk.agent.tools.todo_tool import TodoTool
from pstock_sdk.agent.tools.search_text_tool import SearchTextTool
from pstock_sdk.agent.tools.find_files_tool import FindFilesTool
from pstock_sdk.agent.tools.shell_tool import ShellTool
from pstock_sdk.agent.tools.edit_file_tool import EditFileTool
from pstock_sdk.agent.tools.list_directory_tool import ListDirectoryTool
from pstock_sdk.agent.tools.write_file_tool import WriteFileTool
from pstock_sdk.agent.tools.read_file_tool import ReadFileTool
from pstock_sdk.agent.tools.web_search_tool import WebSearchTool
import asyncio
import os
from typing import Any

from dotenv import load_dotenv

from pstock_sdk.agent.core.agent import Agent, AgentBuilder
from pstock_sdk.agent.core.interfaces import AgentContext, AgentStep, Skill, Tool, ToolDefinition
from pstock_sdk.agent.mcp.mcp_config import McpServerConfig
from pstock_sdk.agent.memory.memory import MemoryRecord, MemorySlotConfig
from pstock_sdk.agent.llm.openai_llm import OpenAILLM, OpenAIModelOptions
from pstock_server import registry
from pstock_server.server import AgentServer

load_dotenv()


# =============================================================================
# 自定义工具
# =============================================================================

class DatabaseQueryTool(Tool):
    """模拟数据库查询工具"""

    def __init__(self):
        self._name = "db_query"
        self._description = "查询数据库信息"

    @property
    def name(self) -> str:
        return self._name

    @property
    def description(self) -> str:
        return self._description

    @property
    def display_name(self) -> str | None:
        return "数据库查询"

    @property
    def parameters(self) -> dict[str, Any] | None:
        return {
            "type": "object",
            "properties": {
                "table": {
                    "type": "string",
                    "description": "表名",
                },
                "condition": {
                    "type": "string",
                    "description": "查询条件",
                },
            },
            "required": ["table"],
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
        table = input.get("table", "")
        condition = input.get("condition", "")
        return f"从 {table} 表中查询结果：找到 {len(condition)} 条匹配记录"


class DataAnalysisTool(Tool):
    """模拟数据分析工具"""

    def __init__(self):
        self._name = "data_analysis"
        self._description = "分析数据并生成报告"

    @property
    def name(self) -> str:
        return self._name

    @property
    def description(self) -> str:
        return self._description

    @property
    def display_name(self) -> str | None:
        return "数据分析"

    @property
    def parameters(self) -> dict[str, Any] | None:
        return {
            "type": "object",
            "properties": {
                "data": {
                    "type": "string",
                    "description": "待分析的数据",
                },
            },
            "required": ["data"],
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
        data = input.get("data", "")
        return f"数据分析完成：{data} -> 趋势：上升，增长率：15%"


# =============================================================================
# 子 Agent
# =============================================================================


def create_research_agent(llm) -> Agent:
    """创建研究专家子 Agent"""
    return (
        AgentBuilder()
        .with_name("research-specialist")
        .with_description("网络搜索和信息收集专家")
        .with_llm(llm)
        .with_max_steps(5)
        .with_instructions("你是搜索专家，专注于从网络获取准确、最新的信息。")
        .with_tools([WebSearchTool()])
        .build()
    )


def create_analyst_agent(llm) -> Agent:
    """创建数据分析师子 Agent"""
    return (
        AgentBuilder()
        .with_name("analyst-specialist")
        .with_description("数据分析专家，擅长数据处理和报告生成")
        .with_llm(llm)
        .with_max_steps(5)
        .with_instructions("你是数据分析专家，专注于处理数据并生成有价值的洞察。")
        .with_tools([DatabaseQueryTool(), DataAnalysisTool()])
        .build()
    )


# =============================================================================
# 完整功能 Agent
# =============================================================================


def create_full_featured_agent() -> Agent:
    """
    创建一个使用所有功能的完整 Agent
    """
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY 环境变量未设置")

    llm = OpenAILLM(
        api_key=api_key,
        options=OpenAIModelOptions(
            model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            api_base=os.getenv("OPENAI_API_BASE", "https://api.openai.com/v1"),
            temperature=0.2,
        ),
    )

    # 定义记忆槽
    memory_slots = [
        MemorySlotConfig(
            name="user_profile",
            description="用户基本信息：姓名、职业、兴趣等",
            type="short_term",
        ),
        MemorySlotConfig(
            name="conversation_history",
            description="对话历史摘要：用户关心的话题、讨论过的问题",
            type="short_term",
        ),
        MemorySlotConfig(
            name="user_preferences",
            description="用户偏好：回答风格、专业领域偏好",
            type="long_term",
        ),
    ]

    # 创建子 Agent
    research_agent = create_research_agent(llm)
    analyst_agent = create_analyst_agent(llm)

    # 创建mcp config
    # 注意：如果 API key 无效，请设置 enabled=False 禁用 MCP 功能

    mcp_server_config = McpServerConfig(
        name="web_search_mcp_aliyun",
        baseUrl="https://dashscope.aliyuncs.com/api/v1/mcps/WebSearch/sse",
        apiKey="sk-eb893e7ed312495fbf074856731d8047",
        description="这是一个联网搜索的mcp服务器",
        enabled=True,  # 暂时禁用，待配置有效 API key 后启用
    )
    
    # 创建知识库配置
    knowledge_base_config = {
        "datasetIds": ["b288d410eeb311f0a205626a91af775a"]
    }
    
    # 读取skills
    weather_skill = Skill(
        name="report_weather",
        description="如何展示天气情况",
        path="myskill/weather/SKILL.md"
    )

    # 创建主控 Agent
    agent = (
        AgentBuilder()
        .with_name("full-featured-assistant")
        .with_description(
            "全功能智能助手 - 集成了搜索、分析、记忆、协作等所有能力"
        )
        # ==================== LLM 配置 ====================
        .with_llm(llm)
        .with_max_steps(20)

        # ==================== 系统指令 ====================
        .with_instructions(
            "你是一个功能强大的 AI 助手。你可以：\n"
            "1. 使用网络搜索工具查找最新信息\n"
            "2. 使用数据库工具查询历史数据\n"
            "3. 使用数据分析工具处理信息\n"
            "4. 使用文件操作工具管理文件\n"
            "5. 委托给专业子 Agent 完成复杂任务\n"
            "6. 记住用户的重要信息\n"
            "\n"
            "请专业、准确地回答用户问题。"
        )

        # ==================== 工具配置 ====================
        .with_tools([
            TodoTool(),
            ReadFileTool(),
            WriteFileTool(),
            ListDirectoryTool(),
            EditFileTool(),
            ShellTool(),
            FindFilesTool(),
            SearchTextTool()
        ])

        .with_workspace_root("/home/estom/work/pstock/examples/workspace")


        # ==================== 子 Agent 配置 ====================
        # .with_children([research_agent, analyst_agent])

        # ==================== 上下文管理配置 ====================
        .with_max_history_rounds(3)

        # ==================== 上下文压缩配置 ====================
        .with_compression_enabled(True)
        .with_max_context_length(80)
        .with_compression_trigger_ratio(0.75)
        .with_compression_ratio(0.35)

        # ==================== 记忆功能配置 ====================
        .with_memory_enabled(True)
        .with_memory_slots(memory_slots)

        # ==================== mcp配置 ====================
        .with_mcp_servers([mcp_server_config])

        # ==================== 知识库 ====================
        .with_knowledge_base(knowledge_base_config)

        # ==================== agent skills ====================
        .with_skill(weather_skill)
        .with_skill_sources(["/home/estom/work/pstock/examples/skills",])

        .build()
    )

    return agent


# =============================================================================
# 演示所有功能
# =============================================================================


async def demonstrate_all_features():
    """演示所有功能"""
    print("=" * 70)
    print(" " * 18 + "PStock 全功能 Agent 演示")
    print("=" * 70)

    # 检查 API Key
    if not os.getenv("OPENAI_API_KEY"):
        print("\n错误: 请设置 OPENAI_API_KEY 环境变量")
        return

    # 创建 Agent
    print("\n[1/7] 创建全功能 Agent...")
    agent = create_full_featured_agent()
    print(f"  ✓ Agent 名称: {agent.name}")
    print(f"  ✓ 工作目录: {agent.workspace_root}")
    print(f"  ✓ 工具数量: {len(agent.tool_registry.list())}")
    print(f"  ✓ 子 Agent 数量: {len(agent.children)}")
    print(f"  ✓ 记忆槽数量: {len(agent.context_manager.memory_slots)}")
    print(f"  ✓ 上下文压缩: {agent.context_manager.compression_enabled}")
    print(f"  ✓ 技能数量: {len(agent.skill_registry.list())}")
    print(f"  ✓ MCP 服务器数量: {len(agent.mcp_servers)}")


def serve_agent():
    """演示所有功能"""
    print("=" * 70)
    print(" " * 18 + "PStock 全功能 Agent 演示")
    print("=" * 70)

    # 检查 API Key
    if not os.getenv("OPENAI_API_KEY"):
        print("\n错误: 请设置 OPENAI_API_KEY 环境变量")
        return

    # 创建 Agent
    print("\n[1/7] 创建全功能 Agent...")
    agent = create_full_featured_agent()
    print(f"  ✓ Agent 名称: {agent.name}")
    print(f"  ✓ 工作目录: {agent.workspace_root}")
    print(f"  ✓ 工具数量: {len(agent.tool_registry.list())}")
    print(f"  ✓ 子 Agent 数量: {len(agent.children)}")
    print(f"  ✓ 记忆槽数量: {len(agent.context_manager.memory_slots)}")
    print(f"  ✓ 上下文压缩: {agent.context_manager.compression_enabled}")
    print(f"  ✓ 技能数量: {len(agent.skill_registry.list())}")
    print(f"  ✓ MCP服务器数量: {len(agent.mcp_servers)}")
    
    registry.register(agent)
    # Create server
    server = AgentServer(registry)
    # Run server with command line arguments
    server.run()

# =============================================================================
# 主函数
# =============================================================================


def main():
    """主函数"""
    # asyncio.run(demonstrate_all_features())
    serve_agent()


if __name__ == "__main__":
    main()
