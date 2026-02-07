# PStock Agents Directory

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
from pstock_sdk.agent.core.interfaces import Tool

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
from pstock_sdk.agent.tools.base_tool import BaseTool

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
from pstock_framework import AgentFrameworkLoader
from pstock_sdk import OpenAILLM

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

- [PStock SDK Documentation](../src/pstock_sdk/README.md)
- [Framework Summary](../FRAMEWORK_SUMMARY.md)
- [Claude Skills Specification](https://docs.anthropic.com/claude/docs/skills-for-claude)
