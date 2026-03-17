# AI Flex SDK

AI Flex SDK 是一个基于 Python 的 AI Agent 框架，专为金融分析和股票交易场景设计。它实现了 ReAct 风格的智能体运行时，支持工具调用、MCP 集成、知识库检索、记忆管理和技能系统。

## 目录

- [快速开始](#快速开始)
- [核心概念](#核心概念)
- [Agent 配置指南](#agent-配置指南)
- [工具系统](#工具系统)
- [技能系统](#技能系统)
- [高级功能](#高级功能)
- [API 参考](#api-参考)

## 快速开始

### 安装

```bash
# 使用 UV 安装（推荐）
uv sync

# 或使用 pip
pip install -e .
```

### 基础示例

```python
import asyncio
from sdk.agent import AgentBuilder
from sdk.agent.llm import OpenAILLM, OpenAIModelOptions

async def main():
    # 1. 创建 LLM 实例
    llm = OpenAILLM(
        api_key="your-api-key",
        options=OpenAIModelOptions(model="gpt-4o-mini", temperature=0.2)
    )

    # 2. 使用 Builder 创建 Agent
    agent = (AgentBuilder()
        .with_name("analyst")
        .with_description("数据分析助手")
        .with_llm(llm)
        .with_max_steps(8)
        .with_instructions("你是一个专业的数据分析助手")
        .build())

    # 3. 运行任务
    result = await agent.run("分析AAPL股票的投资价值")

    # 4. 查看结果
    print(f"最终答案: {result.output}")
    for step in result.steps:
        print(f"[{step.type}] {step.content}")

asyncio.run(main())
```

### 环境变量

在项目根目录创建 `.env` 文件：

```bash
OPENAI_API_KEY=sk-xxx
OPENAI_API_BASE=https://api.openai.com/v1  # 可选
OPENAI_MODEL=gpt-4o-mini                   # 可选
```

## 核心概念

### Agent

Agent 是智能体的核心类，封装了 LLM、工具、技能和运行时逻辑。

### AgentBuilder

使用 Builder 模式链式配置 Agent：

```python
agent = (AgentBuilder()
    .with_name("my-agent")
    .with_description("Agent 描述")
    .with_llm(llm)
    .with_max_steps(10)
    .with_instructions("系统提示词")
    .build())
```

### ReAct 运行时

Agent 使用 ReAct（Reasoning + Acting）模式运行：

1. **思考（Thought）**：Agent 分析当前状态
2. **行动（Action）**：Agent 调用工具或子 Agent
3. **观察（Observation）**：Agent 获取行动结果
4. 重复直到完成任务或达到最大步数

### AgentOptions

封装所有 Agent 配置的数据类：

```python
from sdk.agent.core.agent import AgentOptions

options = AgentOptions(
    llm=llm,
    name="my-agent",
    description="Agent 描述",
    max_steps=10,
    instructions="系统提示词"
)
agent = Agent(options)
```

## Agent 配置指南

### LLM 配置

```python
from sdk.agent.llm import OpenAILLM, OpenAIModelOptions

# OpenAI 模型配置
llm_options = OpenAIModelOptions(
    model="gpt-4o-mini",       # 模型名称
    temperature=0.2,            # 温度参数 (0-2)
    max_tokens=2000,            # 最大生成 token 数
    top_p=1.0,                  # nucleus 采样参数
    frequency_penalty=0,        # 频率惩罚
    presence_penalty=0,         # 存在惩罚
    api_base="https://api.openai.com/v1"  # API 端点
)

llm = OpenAILLM(
    api_key="your-api-key",
    options=llm_options
)
```

### Builder 配置方法

| 方法 | 参数 | 说明 |
|------|------|------|
| `with_name()` | `str` | Agent 名称（必需） |
| `with_description()` | `str` | Agent 描述（必需） |
| `with_llm()` | `LLM` | LLM 实例（必需） |
| `with_max_steps()` | `int` | 最大执行步数，默认 5 |
| `with_instructions()` | `str` | 系统提示词 |
| `with_workspace_root()` | `str` | 工作区根目录 |
| `with_tools()` | `list[Tool]` | 工具列表 |
| `with_children()` | `list[Agent]` | 子 Agent 列表 |
| `with_skills()` | `list[Skill]` | 技能列表 |
| `with_skill_sources()` | `list[str]` | 技能源路径列表 |
| `with_mcp_servers()` | `list[McpServerConfig]` | MCP 服务器配置 |
| `with_memory_enabled()` | `bool` | 启用记忆功能 |
| `with_compression_enabled()` | `bool` | 启用上下文压缩 |
| `with_knowledge_base()` | `dict` | 知识库配置 |

### 运行配置

```python
# 基本运行
result = await agent.run("任务描述")

# 带会话 ID 的运行（保持上下文）
result = await agent.run("后续任务", session_id="session-123")

# 流式运行（实时输出）
await agent.run_stream(
    task="任务描述",
    emit=lambda step: print(f"[{step.type}] {step.content}")
)

# 运行结果结构
result.output      # 最终答案
result.steps       # 执行步骤列表
result.session_id  # 会话 ID
result.usage       # Token 使用统计
```

### 会话管理

```python
# 创建新会话
session_id = agent.create_session()

# 获取会话上下文
context = agent.get_session_context(session_id)

# 清除会话
agent.clear_session(session_id)

# 列出所有会话
sessions = agent.list_sessions()

# 终止运行
agent.terminate()

# 重置运行时
agent.reset_runtime()
```

## 工具系统

### Tool 接口

所有工具必须实现 `Tool` 协议：

```python
from sdk.agent.core.interfaces import Tool
from pydantic import validate_call

class MyTool(Tool):
    @property
    def name(self) -> str:
        return "my-tool"

    @property
    def description(self) -> str:
        return "工具描述"

    @property
    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "input": {
                    "type": "string",
                    "description": "输入参数"
                }
            },
            "required": ["input"]
        }

    @validate_call
    async def execute(self, input: str, context=None) -> str:
        # 工具逻辑实现
        return f"处理结果: {input}"
```

### 使用 BaseTool

继承 `BaseTool` 可以简化工具开发：

```python
from sdk.agent.tools.base_tool import BaseTool

class SimpleTool(BaseTool):
    @property
    def name(self) -> str:
        return "simple-tool"

    @property
    def description(self) -> str:
        return "简单工具示例"

    @property
    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "query": {"type": "string"}
            },
            "required": ["query"]
        }

    async def execute(self, query: str, context=None) -> str:
        return f"查询: {query}"
```

### 注册工具

```python
# 通过 Builder 注册
agent = (AgentBuilder()
    .with_tools([my_tool])
    .build())

# 或添加到已存在的 Agent
agent.register_tool(my_tool)
```

### 内置工具

SDK 自动提供以下内置工具：

| 工具名称 | 说明 |
|----------|------|
| `read_file` | 读取文件内容 |
| `write_file` | 写入文件 |
| `edit_file` | 编辑文件 |
| `list_directory` | 列出目录内容 |
| `find_files` | 查找文件 |
| `search_text` | 搜索文本 |
| `shell` | 执行 Shell 命令 |

## 技能系统

### 技能定义

在 `SKILL.md` 文件中定义技能：

```markdown
---
name: stock-analysis
description: 股票分析技能
version: 1.0.0
author: Your Name
allowed_tools:
  - read_file
  - search_text
---

# 股票分析技能

这个技能帮助分析股票数据...

## 使用方法

1. 获取股票数据
2. 分析趋势
3. 生成报告
```

### 加载技能

```python
# 从目录加载技能
agent = (AgentBuilder()
    .with_skill_sources(["./skills", "./custom_skills"])
    .build())

# 直接添加技能实例
from sdk.agent.skills.skill import Skill

skill = Skill.from_file("./skills/my_skill/SKILL.md")
agent = (AgentBuilder()
    .with_skills([skill])
    .build())
```

## 高级功能

### 子 Agent 委托

```python
# 创建子 Agent
data_agent = (AgentBuilder()
    .with_name("data-fetcher")
    .with_description("数据获取专家")
    .with_llm(llm)
    .build())

# 添加到主 Agent
main_agent = (AgentBuilder()
    .with_name("analyst")
    .with_description("分析师")
    .with_llm(llm)
    .with_children([data_agent])
    .build())

# 主 Agent 可以调用子 Agent
result = await main_agent.run("获取并分析 AAPL 数据")
```

### MCP 集成

```python
from sdk.agent.core.interfaces import McpServerConfig

mcp_config = McpServerConfig(
    name="my-mcp",
    command="npx",
    args=["-y", "@modelcontextprotocol/server-fetch"],
    env={"API_KEY": "xxx"}
)

agent = (AgentBuilder()
    .with_mcp_servers([mcp_config])
    .build())
```

### 知识库集成

```python
# RagFlow 知识库配置
kb_config = {
    "type": "ragflow",
    "base_url": "http://localhost:9380",
    "api_key": "ragflow-xxx",
    "dataset_ids": ["dataset-1"]
}

agent = (AgentBuilder()
    .with_knowledge_base(kb_config)
    .build())
```

### 记忆和压缩

```python
agent = (AgentBuilder()
    .with_memory_enabled(True)       # 启用记忆存储
    .with_compression_enabled(True)   # 启用上下文压缩
    .with_max_steps(20)               # 增加最大步数
    .build())
```

## API 参考

### Agent 类

```python
class Agent:
    """智能体核心类"""

    def __init__(self, options: AgentOptions) -> None: ...

    async def run(
        self,
        task: str,
        session_id: str | None = None
    ) -> AgentResult:
        """运行 Agent 任务"""

    async def run_stream(
        self,
        task: str,
        session_id: str | None = None,
        emit: Callable[[Step], None] | None = None
    ) -> None:
        """流式运行任务"""

    def create_session(self) -> str:
        """创建新会话"""

    def get_session_context(self, session_id: str) -> SessionContext:
        """获取会话上下文"""

    def clear_session(self, session_id: str) -> None:
        """清除会话"""

    def list_sessions(self) -> list[str]:
        """列出所有会话"""

    def terminate(self) -> None:
        """终止运行"""

    def reset_runtime(self) -> None:
        """重置运行时"""
```

### AgentBuilder 类

```python
class AgentBuilder:
    """Agent 构建器"""

    def with_name(self, name: str) -> AgentBuilder: ...

    def with_description(self, description: str) -> AgentBuilder: ...

    def with_llm(self, llm: LLM) -> AgentBuilder: ...

    def with_max_steps(self, max_steps: int) -> AgentBuilder: ...

    def with_instructions(self, instructions: str) -> AgentBuilder: ...

    def with_workspace_root(self, workspace_root: str) -> AgentBuilder: ...

    def with_tools(self, tools: list[Tool]) -> AgentBuilder: ...

    def with_children(self, children: list[Agent]) -> AgentBuilder: ...

    def with_skills(self, skills: list[Skill]) -> AgentBuilder: ...

    def with_skill_sources(self, sources: list[str]) -> AgentBuilder: ...

    def with_mcp_servers(self, servers: list[McpServerConfig]) -> AgentBuilder: ...

    def with_memory_enabled(self, enabled: bool) -> AgentBuilder: ...

    def with_compression_enabled(self, enabled: bool) -> AgentBuilder: ...

    def with_knowledge_base(self, config: dict) -> AgentBuilder: ...

    def build(self) -> Agent:
        """构建 Agent 实例"""
```

### AgentResult 类

```python
class AgentResult:
    """Agent 运行结果"""

    output: str              # 最终答案
    steps: list[Step]        # 执行步骤
    session_id: str          # 会话 ID
    usage: TokenUsage        # Token 使用统计

class Step:
    """执行步骤"""
    type: str                # 步骤类型: thought/action/observation
    content: str             # 步骤内容
    timestamp: datetime      # 时间戳
```

### TokenUsage 类

```python
class TokenUsage:
    """Token 使用统计"""

    prompt_tokens: int      # 输入 token 数
    completion_tokens: int  # 输出 token 数
    total_tokens: int       # 总 token 数
```

## 完整示例

```python
import asyncio
from sdk.agent import AgentBuilder
from sdk.agent.llm import OpenAILLM, OpenAIModelOptions
from sdk.agent.core.interfaces import Tool
from pydantic import validate_call

# 自定义工具
class CalculatorTool(Tool):
    @property
    def name(self) -> str:
        return "calculator"

    @property
    def description(self) -> str:
        return "执行数学计算，支持加减乘除"

    @property
    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "expression": {
                    "type": "string",
                    "description": "数学表达式，如 2 + 3"
                }
            },
            "required": ["expression"]
        }

    @validate_call
    async def execute(self, expression: str, context=None) -> str:
        try:
            result = eval(expression)
            return f"计算结果: {result}"
        except Exception as e:
            return f"计算错误: {e}"

async def main():
    # 创建 LLM
    llm = OpenAILLM(
        api_key="your-api-key",
        options=OpenAIModelOptions(
            model="gpt-4o-mini",
            temperature=0.2
        )
    )

    # 创建工具
    calculator = CalculatorTool()

    # 创建 Agent
    agent = (AgentBuilder()
        .with_name("math-assistant")
        .with_description("数学计算助手")
        .with_llm(llm)
        .with_max_steps(10)
        .with_instructions(
            "你是一个专业的数学计算助手。"
            "当用户需要计算时，使用 calculator 工具。"
            "清晰地解释计算过程和结果。"
        )
        .with_tools([calculator])
        .with_memory_enabled(True)
        .build())

    # 运行任务
    result = await agent.run("计算 (15 + 25) * 3 的结果")

    # 输出结果
    print("=" * 50)
    print(f"最终答案: {result.output}")
    print("=" * 50)

    # 输出详细步骤
    for i, step in enumerate(result.steps, 1):
        print(f"\n步骤 {i} [{step.type}]:")
        print(f"  {step.content}")

    # 输出 Token 使用
    print(f"\nToken 使用: {result.usage.total_tokens}")

asyncio.run(main())
```

## 更多资源

- [框架文档](README_FRAMEWORK.md)
- [项目主页](README.md)
- [示例代码](src/agents/)
