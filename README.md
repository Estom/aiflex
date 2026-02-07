# PStock SDK

一个功能强大的 Python AI Agent 框架，专为金融分析和股票交易场景设计。实现了 ReAct 风格的智能体运行时，支持工具调用、MCP 集成、知识库检索、记忆管理和技能系统。

## 核心特性

- **ReAct Agent Runtime**: 基于 OpenAI function-calling 的思考-行动循环实现
- **MCP 集成**: 支持 Model Context Protocol 服务器连接和工具调用
- **知识库检索**: 集成 RagFlow 进行 RAG 检索增强
- **记忆管理**: 短期/长期记忆支持，自动记忆合成
- **经验系统**: Agent 可学习和复用历史经验
- **技能系统**: 基于 Markdown 的技能定义和自动加载
- **多智能体**: 支持父子 Agent 委托模式和任务分发
- **内置工具**: 文件操作、Shell、搜索、Todo 管理等丰富工具集
- **声明式配置**: 通过 JSON 和 Markdown 配置 Agent，无需编码

## 环境要求

- Python >= 3.11
- UV 包管理器（推荐）

## 快速开始

### 1. 安装依赖

```bash
# 使用 UV 安装（推荐）
uv sync

# 或使用 pip
pip install -e .
```

### 2. 配置环境变量

```bash
cp .env.example .env
# 编辑 .env 文件，设置 OPENAI_API_KEY
```

### 3. 运行演示

```bash
# 运行金融分析演示
bash demo.sh

# 或使用快速启动脚本
bash start.sh

# 直接运行任务
python run_agent.py "简要分析苹果公司(AAPL)的当前状况"
```

## 项目结构

```
pstock/
├── src/
│   ├── pstock_sdk/              # 核心 SDK
│   │   ├── agent/
│   │   │   ├── core/            # Agent 核心实现
│   │   │   │   ├── agent.py     # Agent 类和 Builder
│   │   │   │   └── agent_runtime.py  # ReAct 运行时
│   │   │   ├── tools/           # 内置工具实现
│   │   │   ├── llm/             # LLM 抽象层
│   │   │   └── skills/          # 技能注册表
│   │   ├── stores/              # 数据存储层
│   │   ├── integration/         # RagFlow 等集成
│   │   └── utils/               # 工具函数
│   └── pstock_framework/        # 声明式框架
│       ├── config/              # Pydantic 配置模型
│       ├── loader/              # 配置加载器
│       └── registry/            # Agent 注册中心
├── tests/                       # 测试代码
├── run_agent.py                 # Agent 运行脚本
├── demo.sh                      # 演示脚本
├── start.sh                     # 快速启动脚本
└── pyproject.toml               # 项目配置
```

## 使用方式

### 方式一：编程式 API

```python
import asyncio
from pstock_sdk import AgentBuilder, OpenAILLM, OpenAIModelOptions

async def main():
    # 初始化 LLM
    llm = OpenAILLM(
        api_key="your-api-key",
        options=OpenAIModelOptions(model="gpt-4o-mini")
    )

    # 创建 Agent
    agent = (
        AgentBuilder()
        .with_name("market-analyst")
        .with_description("股市市场分析智能体")
        .with_instructions("你是一位专业的股市分析师...")
        .with_llm(llm)
        .with_workspace_root("./workspace")
        .with_experience_enabled(True)
        .build()
    )

    # 运行任务
    result = await agent.run("分析今天的市场热点")
    print(result.output)

asyncio.run(main())
```

### 方式二：声明式配置

在 `agents/` 目录下创建 Agent 配置：

**agent.json**
```json
{
  "name": "financial_analyst",
  "version": "1.0.0",
  "description": "AI 金融分析师",
  "model": null,
  "prompt": {
    "file": "prompt.md"
  },
  "skills": {
    "sources": ["skills/"],
    "inline": []
  },
  "tools": {
    "auto_discover": true,
    "enabled": [],
    "disabled": []
  },
  "subagents": [
    {
      "name": "data_fetcher",
      "enabled": true
    }
  ],
  "runtime": {
    "max_steps": 10,
    "experience_enabled": false,
    "knowledge_base": null
  }
}
```

**prompt.md**
```markdown
# Financial Analyst Agent

You are an expert financial analyst with deep knowledge of stock markets.

## Guidelines

1. Always provide data-driven analysis
2. Consider multiple perspectives before making recommendations
3. Use available tools to gather current market data
```

**创建agent.py**

```py
import asyncio
import json
import os
from pathlib import Path

from dotenv import load_dotenv

from pstock_framework import AgentFrameworkLoader
from pstock_sdk import OpenAILLM, OpenAIModelOptions


def print_agent_config(agent) -> None:
    """打印 Agent 的 JSON 格式配置信息"""
    # 获取工具列表
    tools = agent.tool_registry.list()
    tools_list = [
        {"name": tool.name, "description": tool.description}
        for tool in tools
    ]

    # 获取技能列表
    skills = agent.skill_registry.list()
    skills_list = [
        {"name": skill["name"], "description": skill.get("description", "")}
        for skill in skills
    ]

    config = {
        "name": agent.name,
        "description": agent.description,
        "max_steps": agent.config.max_steps,
        "instructions": agent.config.instructions,
        "workspace_root": agent.config.workspace_root,
        "model": {
            "name": agent.llm.model,
            "temperature": agent.llm.temperature,
            "max_tokens": agent.llm.max_tokens,
        },
        "tools_count": len(tools_list),
        "tools": tools_list,
        "skills_count": len(skills_list),
        "skills": skills_list,
        "children_count": len(agent.children),
        "children": [
            {"name": child.name, "description": child.description}
            for child in agent.children
        ],
        "experience_enabled": agent.experience_enabled,
        "mcp_lazy_load": agent.mcp_lazy_load,
        "mcp_servers": agent.mcp_servers,
        "codespace_enabled": agent.codespace_enabled,
        "skill_sources": agent.skill_sources,
    }

    print(json.dumps(config, indent=2, ensure_ascii=False))


async def main():
    # 加载环境变量
    load_dotenv()

    # 从环境变量读取配置
    api_key = os.getenv("OPENAI_API_KEY")
    api_base = os.getenv("OPENAI_API_BASE", "https://api.openai.com/v1")
    model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

    # 初始化 LLM
    llm = OpenAILLM(
        api_key=api_key,
        options=OpenAIModelOptions(model=model, api_base=api_base)
    )

    # 获取当前目录作为 Agent 目录
    agent_dir = Path(__file__).parent.resolve()
    loader = AgentFrameworkLoader(agents_root=agent_dir, default_llm=llm)

    # 加载单个 Agent
    agent = await loader.load()
    print(f"Loaded agent: {agent.name}")

    # 打印 Agent 配置信息
    print("\n" + "=" * 60)
    print("Agent Configuration (JSON):")
    print("=" * 60)
    print_agent_config(agent)
    print("=" * 60 + "\n")

    # 运行任务
    result = await agent.run("Analyze AAPL stock")
    print(f"\nResult:\n{result.output}")


if __name__ == "__main__":
    asyncio.run(main())
```

然后使用运行脚本：

```bash
python agent.py "分析苹果公司(AAPL)的当前状况"
```

## 内置工具

Agent 默认可用的工具：

| 工具名 | 功能 | 说明 |
|--------|------|------|
| `find_files` | 文件搜索 | 按模式搜索文件 |
| `read_file` | 读取文件 | 读取文件内容 |
| `write_file` | 写入文件 | 创建或覆盖文件 |
| `edit_file` | 编辑文件 | 精确替换文件内容 |
| `list_directory` | 列出目录 | 列出目录内容 |
| `search_text` | 文本搜索 | 在文件中搜索文本 |
| `shell` | Shell 命令 | 执行 Shell 命令 |
| `web_search` | Web 搜索 | 搜索网络（需要 API Key） |
| `web_fetch` | URL 获取 | 获取网页内容 |
| `todo_list` | Todo 管理 | 管理待办事项 |
| `knowledge_base_retrieve` | 知识库检索 | RagFlow RAG 检索 |
| `experience_query` | 经验查询 | 查询历史经验 |
| `experience_update` | 经验更新 | 保存新经验 |

## 技能系统

技能是 Agent 的专业知识模块，通过 Markdown 文件定义：

**skills/market_analysis/SKILL.md**
```markdown
---
name: market_analysis
description: 高级市场分析技术
version: 1.0.0
tags: [market, analysis, technical-indicators]
---

# Market Analysis Skill

## Capabilities

- Technical analysis (moving averages, RSI, MACD)
- Trend identification and evaluation
- Support and resistance levels
- Volume analysis
```

Agent 会自动加载配置的技能，并在相关任务中使用。

## 多智能体系统

支持父子 Agent 委托，父 Agent 可以将任务委托给子 Agent：

```
financial_analyst (父)
    └── data_fetcher (子)
```

子 Agent 会被自动包装为工具，父 Agent 可以像调用工具一样调用子 Agent。

## 配置选项

### 环境变量 (.env)

```bash
# OpenAI 配置
OPENAI_API_KEY=sk-...
OPENAI_API_BASE=https://api.openai.com/v1
OPENAI_MODEL=gpt-4o-mini

# RagFlow 知识库（可选）
RAGFLOW_BASE_URL=http://ragflow.example.com:80
RAGFLOW_API_KEY=ragflow-...

# Web 搜索（可选）
BOCHA_API_KEY=your-bocha-api-key

```

### Agent Runtime 配置

```json
{
  "runtime": {
    "max_steps": 30,              // 最大执行步数
    "workspace_root": "./workspace", // 工作目录
    "mcp_lazy_load": false,       // MCP 延迟加载
    "experience_enabled": true,   // 启用经验学习
    "compression_enabled": true,  // 启用记忆压缩
    "knowledge_base": {           // 知识库配置
      "enabled": true,
      "similarity_threshold": 0.7
    }
  }
}
```

## 命令行工具

```bash
# 运行任务
python run_agent.py "你的任务描述"

# 交互式模式
python run_agent.py --interactive

# 使用真实 AI（需要配置 .env）
python run_agent.py "任务" --real-llm

# 快速启动菜单
./start.sh
```

## 开发指南

### 代码质量检查

```bash
# 代码检查
uv run ruff check src/

# 代码格式化
uv run ruff format src/

# 类型检查
uv run mypy src/
```

### 运行测试

```bash
# 运行所有测试
uv run pytest

# 带覆盖率报告
uv run pytest --cov=pstock_sdk --cov-report=html

# 运行特定测试
uv run pytest tests/test_agent.py
```

### 添加自定义工具

```python
from pstock_sdk import BaseTool, ToolDefinition

class MyCustomTool(BaseTool):
    def get_definition(self) -> ToolDefinition:
        return ToolDefinition(
            name="my_tool",
            description="我的自定义工具",
            input_schema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "查询参数"}
                },
                "required": ["query"]
            }
        )

    async def execute(self, args: dict) -> str:
        query = args["query"]
        # 实现工具逻辑
        return f"结果: {query}"
```

## 架构设计

```
┌─────────────────────────────────────────────────────────┐
│                        Agent                             │
├─────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐    │
│  │   Skills    │  │    Tools    │  │  Subagents  │    │
│  └─────────────┘  └─────────────┘  └─────────────┘    │
├─────────────────────────────────────────────────────────┤
│                    Agent Runtime                         │
│  ┌─────────────────────────────────────────────────┐   │
│  │              ReAct Loop                         │   │
│  │  Thought → Action → Observation → Thought → ... │   │
│  └─────────────────────────────────────────────────┘   │
├─────────────────────────────────────────────────────────┤
│                        LLM                               │
│                   (OpenAI / Compatible)                  │
└─────────────────────────────────────────────────────────┘
```