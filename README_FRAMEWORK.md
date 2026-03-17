# 🎉 PStock Framework智能体框架 - 运行成功！

## ✅ 当前状态

您的 **PStock 智能体框架**已经成功实现并运行！

### 📦 已完成的组件

✅ **framework** - 声明式智能体框架
✅ **工具系统** - 自动发现和加载
✅ **技能系统** - Claude Skills 支持
✅ **子智能体** - 递归加载和协作
✅ **运行脚本** - 便捷的启动器

## 🚀 快速开始

### 方法 1: 使用启动脚本（推荐）

```bash
python 
```

然后选择你想要的运行模式。

### 方法 2: 直接运行

```bash
# 单次运行
python agent.py "分析苹果公司股票"
```

## 📊 运行示例

### 示例 1: 股票分析

```bash
python /src/agents/financial_analyst/agent.py
```

## 🎯 当前可用的智能体

### financial_analyst（金融分析师）

**功能**:
- 📈 股票价格查询
- 📊 技术指标分析
- 💼 基本面分析
- 🔍 市场趋势判断
- 🎯 投资建议

**工具**:
- `stock_data` - 股票数据工具
- `agent_data_fetcher` - 数据获取子智能体

**技能**:
- `market_analysis` - 高级市场分析技术

**子智能体**:
- `data_fetcher` - 专业的数据获取智能体

## 🔧 配置真实AI

### 创建 .env 文件

```bash
cat > .env << 'EOF'
# OpenAI API
OPENAI_API_KEY=sk-your-key-here
OPENAI_MODEL=gpt-4o-mini

# 或使用其他兼容API
# OPENAI_API_BASE=https://api.deepseek.com/v1
EOF
```

### 使用真实AI运行

```bash
python run_agent.py "分析任务" --real-llm
```

## 📁 项目结构

```
pstock/
├── src/
│   ├── framework/     # ✨ 声明式框架
│   └── sdk/          # 🛠️ SDK 核心
```

## 🎨 创建自己的智能体

### 快速创建一个简单智能体

```bash
# 1. 创建目录
mkdir -p agents/my_agent

# 2. 创建配置
cat > agents/my_agent/agent.json << 'EOF'
{
  "name": "my_agent",
  "version": "1.0.0",
  "description": "我的智能体",
  "model": null,
  "prompt": {
    "system": "你是一个有用的AI助手。"
  }
}
EOF

# 3. 运行
python run_agent.py "测试我的智能体"
```

详细指南请查看: [agents/README.md](agents/README.md)

## 🔥 核心功能

### 1. 声明式配置

使用 JSON 文件配置智能体，无需编码：

```json
{
  "name": "my_agent",
  "description": "智能体描述",
  "model": {"model": "gpt-4"},
  "prompt": {"system": "系统提示词"},
  "tools": {"auto_discover": true},
  "skills": {"sources": ["skills/"]},
  "subagents": [
    {"name": "child_agent", "enabled": true}
  ]
}
```

### 2. 工具自动发现

在 `tools/` 目录放置 Python 文件即可：

```python
# tools/my_tool.py
from sdk.agent.tools.base_tool import BaseTool

class MyTool(BaseTool):
    name = "my_tool"
    description = "工具描述"

    async def execute(self, input, context=None):
        return "执行结果"

tool = MyTool()  # 框架会自动发现
```

### 3. Claude Skills 支持

使用标准 Claude Skills 格式：

```markdown
---
name: my_skill
description: 技能描述
allowed_tools:
  - tool1
  - tool2
---

# 技能说明

详细的使用说明...
```

### 4. 子智能体协作

智能体可以调用其他智能体：

```json
{
  "subagents": [
    {
      "name": "data_fetcher",
      "alias": "fetch_data",
      "enabled": true
    }
  ]
}
```

## 📊 性能特点

- ⚡ **快速加载**: 毫秒级智能体加载
- 🔄 **自动发现**: 零配置工具和技能加载
- 🛡️ **错误容错**: 单个工具失败不影响整体
- 🔁 **循环检测**: 自动防止子智能体循环引用
- 💾 **配置缓存**: 高效的配置管理

## 🧪 测试

```bash
# 运行框架测试
python test_framework.py

# 测试特定智能体
python run_agent.py "测试任务"
```

## 📚 文档

- **[框架实现总结](FRAMEWORK_SUMMARY.md)** - 完整的技术实现细节
- **[运行指南](AGENT_RUNNER_GUIDE.md)** - 详细的使用说明
- **[智能体创建指南](agents/README.md)** - 如何创建新智能体
- **[API 文档](src/sdk/README.md)** - SDK API 参考

## 🎯 下一步

1. **配置真实API** - 体验完整AI能力
2. **创建自定义工具** - 实现真实数据获取
3. **添加更多智能体** - 构建智能体生态
4. **优化提示词** - 提升智能体性能
5. **集成到应用** - 在实际场景中使用

## 💡 使用示例

### 场景 1: 股票分析助手

```bash
python run_agent.py "作为专业的股票分析师，请分析以下方面：
1. 苹果公司当前的基本面状况
2. 技术指标显示的买入/卖出信号
3. 未来12个月的价格预期
4. 主要风险因素
请给出具体的投资建议。"
```

### 场景 2: 投资组合优化

```bash
python run_agent.py "我有一个投资组合：
- 40% 科技股（AAPL, MSFT, GOOGL）
- 30% 金融股（JPM, BAC）
- 20% 医疗股（JNJ, PFE）
- 10% 现金

请分析这个配置是否合理，并给出优化建议。"
```

### 场景 3: 市场研究

```bash
python run_agent.py "研究当前的半导体行业趋势，包括：
1. 行业整体前景
2. 主要公司对比（NVDA, AMD, INTC）
3. 潜在的投资机会
4. 需要注意的风险"
```

## 🆘 获取帮助

- 查看文档: `cat AGENT_RUNNER_GUIDE.md`
- 运行测试: `python test_framework.py`
- 查看示例: `ls agents/financial_analyst/`
- 交互模式: `python run_agent.py --interactive`

## 🎊 总结

你现在拥有：

✅ **完整的智能体框架** - 声明式配置，自动加载
✅ **可运行的示例智能体** - 金融分析师
✅ **便捷的运行工具** - 一键启动
✅ **完善的文档** - 从入门到精通
✅ **扩展性强** - 轻松添加新功能

**开始探索吧！** 🚀

---

*PStock Framework v0.1.0* | *Generated 2026-02-02*


This directory contains declarative agent configurations for the PStock system.

## Agent Structure

Each agent is a directory with the following structure:

```
agent_name/
├── agent.json              # Required: Agent configuration
├── prompt.md               # Optional: System prompt (or use inline in agent.json)
├── skills/                 # Optional: Claude Skills
│   └── skill_name/
│       └── SKILL.md        # Claude Skills format with YAML frontmatter
├── tools/                  # Optional: Auto-discovered Python tools
│   └── tool_name.py        # Tool implementation
└── subagents/              # Optional: Child agents
    └── child_agent/
        └── agent.json
```

## agent.json Format

```json
{
  "name": "agent_name",
  "version": "1.0.0",
  "description": "What this agent does",
  "model": {
    "model": "gpt-4",
    "api_key": "sk-...",
    "temperature": 0.7,
    "max_tokens": 2000
  },
  "prompt": {
    "file": "prompt.md",
    "system": "Optional inline system prompt",
    "variables": {
      "var_name": "value"
    }
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
      "name": "child_agent",
      "alias": "optional_alias",
      "description": "Override description",
      "enabled": true
    }
  ],
  "runtime": {
    "max_steps": 10,
    "workspace_root": null,
    "mcp_lazy_load": false,
    "mcp_servers": [],
    "experience_enabled": false,
    "knowledge_base": null
  }
}
```

## SKILL.md Format

```markdown
---
name: skill_name
description: What this skill does
allowed_tools:
  - tool1
  - tool2
version: "1.0.0"
tags:
  - tag1
  - tag2
author: Your Name
examples:
  - input: "Example input"
    output: "Example output"
---

# Skill Name

Detailed description of what the skill does and how to use it.

## Instructions

Step-by-step instructions for the LLM.
```

## Tool Implementation

Tools are auto-discovered from `tools/*.py` files. They can be:

1. **Tool Protocol implementation**:
```python
from sdk.agent.core.interfaces import Tool

class MyTool(Tool):
    @property
    def name(self) -> str:
        return "my_tool"

    @property
    def description(self) -> str:
        return "What this tool does"

    async def execute(self, input: Any, context: Any = None) -> str:
        return "Result"
```

2. **Function with @validate_call**:
```python
from pydantic import validate_call

@validate_call
def my_tool(param: str) -> str:
    return f"Result: {param}"
```

3. **Factory function**:
```python
def create_tool():
    return MyTool()
```

## Creating a New Agent

1. **Create the directory**:
```bash
mkdir agents/my_agent
cd agents/my_agent
```

2. **Create agent.json**:
```json
{
  "name": "my_agent",
  "version": "1.0.0",
  "description": "My custom agent",
  "model": null,
  "prompt": {
    "system": "You are a helpful assistant."
  }
}
```

3. **Add tools** (optional):
```bash
mkdir tools
cat > tools/my_tool.py << 'EOF'
from sdk.agent.tools.base_tool import BaseTool

class MyTool(BaseTool):
    name = "my_tool"
    description = "Does something useful"

    async def execute(self, input: Any, context: Any = None) -> str:
        return "Done!"

# Auto-discovery will find this
tool = MyTool()
EOF
```

4. **Add skills** (optional):
```bash
mkdir -p skills/my_skill
cat > skills/my_skill/SKILL.md << 'EOF'
---
name: my_skill
description: My custom skill
---

# My Skill

Instructions for the LLM.
EOF
```

5. **Test the agent**:
```python
from framework import AgentFrameworkLoader
from sdk import OpenAILLM

llm = OpenAILLM(api_key="sk-...", options={"model": "gpt-4"})
loader = AgentFrameworkLoader(agents_root="agents/", default_llm=llm)

await loader.load_all()
agent = loader.get_agent("my_agent")
result = await agent.run("Test task")
print(result)
```

## Existing Agents

### financial_analyst
- **Description**: An AI agent specialized in financial analysis and stock market insights
- **Tools**: stock_data (fetches basic stock information)
- **Skills**: market_analysis (advanced market analysis techniques)
- **Subagents**: data_fetcher (fetches financial and market data)

## Configuration Options

### Model Configuration
- `model`: Model name (e.g., "gpt-4", "gpt-4o-mini")
- `api_key`: API key (optional, defaults to global)
- `api_base`: Custom API base URL (optional)
- `temperature`: Sampling temperature (0.0 - 2.0)
- `max_tokens`: Maximum tokens to generate

### Prompt Configuration
- `file`: Path to prompt file (relative to agent.json)
- `system`: Inline system prompt
- `variables`: Key-value pairs for variable substitution

### Tools Configuration
- `auto_discover`: Automatically discover tools from tools/*.py
- `enabled`: Whitelist of tool names to load
- `disabled`: Blacklist of tool names to skip

### Runtime Configuration
- `max_steps`: Maximum reasoning steps (default: 5)
- `workspace_root`: Working directory for file operations
- `mcp_lazy_load`: Enable MCP server lazy loading
- `mcp_servers`: List of MCP server configurations
- `experience_enabled`: Enable learning from past runs
- `knowledge_base`: Knowledge base configuration dict

## Best Practices

1. **Keep prompts focused**: Specific, clear prompts work better
2. **Use subagents for decomposition**: Break complex tasks into smaller subagents
3. **Document your tools**: Clear descriptions help the LLM use them correctly
4. **Version your agents**: Use semantic versioning in agent.json
5. **Test incrementally**: Start with simple tools, add complexity gradually
6. **Handle errors gracefully**: Tools should return helpful error messages
7. **Use skills for expertise**: Skills guide the LLM on how to approach problems

## Troubleshooting

### Agent not loading
- Check agent.json syntax (use a JSON validator)
- Verify all required fields are present
- Check logs for specific error messages

### Tools not discovered
- Ensure tools/*.py files don't start with underscore
- Verify tool implements the Tool Protocol or has factory function
- Check for Python syntax errors in tool files

### Subagents failing
- Check for circular references (A -> B -> A)
- Verify subagent directories contain agent.json
- Ensure subagent names match directory names

### Prompt not loading
- Verify prompt.md path is relative to agent.json
- Check file permissions
- Ensure prompt.md exists if specified in agent.json

## Further Reading

- [PStock SDK Documentation](../src/sdk/README.md)
- [Framework Summary](../FRAMEWORK_SUMMARY.md)
- [Claude Skills Specification](https://docs.anthropic.com/claude/docs/skills-for-claude)
