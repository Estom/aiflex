# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

PStock is a Python-based AI Agent framework designed for financial analysis and stock trading scenarios. It implements a ReAct-style agent runtime with tool calling, MCP integration, knowledge base retrieval, memory management, and a skills system.

The codebase consists of two main packages:
- **pstock_sdk**: Core agent runtime with programmatic API
- **pstock_framework**: Declarative framework using JSON configuration files

## Common Commands

### Installation and Setup
```bash
# Install dependencies using UV (recommended)
uv sync

# Or using pip
pip install -e .
```

### Running Agents
```bash
# Run an agent with a task
python /home/estom/work/pstock/src/agents/financial_analyst/agent.py "Analyze AAPL stock"

# Interactive mode
python /home/estom/work/pstock/src/agents/financial_analyst/agent.py --interactive

# Quick start menu
./start.sh
```

### Code Quality
```bash
# Linting
uv run ruff check src/

# Format code
uv run ruff format src/

# Type checking
uv run mypy src/
```

### Testing
```bash
# Run all tests
uv run pytest

# Run specific test file
uv run pytest tests/test_agent.py

# With coverage
uv run pytest --cov=pstock_sdk --cov-report=html
```

### Building
```bash
# Build the package
uv build
```

## Architecture

### Package Structure

```
src/
├── pstock_sdk/              # Core SDK
│   ├── agent/
│   │   ├── core/
│   │   │   ├── agent.py         # Agent class and Builder
│   │   │   ├── agent_runtime.py # ReAct runtime (thought-action loop)
│   │   │   └── interfaces.py    # Protocol interfaces
│   │   ├── tools/               # Built-in tools
│   │   ├── llm/                 # LLM abstraction (OpenAI)
│   │   └── skills/              # Skill registry
│   ├── stores/                  # Data storage layer
│   ├── integration/             # RagFlow integration
│   └── utils/                   # Utilities
├── pstock_framework/            # Declarative framework
│   ├── config/                  # Pydantic config models
│   ├── loader/                  # Config loaders
│   └── registry/                # Agent registry
├── agents/                      # Agent definitions
│   └── financial_analyst/       # Example agent
└── pstock_server/               # Server component (in development)
```

### Core Concepts

**ReAct Runtime** (`src/pstock_sdk/agent/core/agent_runtime.py`): Implements the thought-action-observation loop using OpenAI function calling. The runtime cycles through reasoning steps until completion or max steps.

**Agent Builder Pattern** (`src/pstock_sdk/agent/core/agent.py`): Use `AgentBuilder()` to construct agents programmatically:

```python
agent = (AgentBuilder()
    .with_name("my-agent")
    .with_description("Description")
    .with_llm(llm)
    .with_experience_enabled(True)
    .build())
```

**Declarative Configuration** (`src/pstock_framework/`): Agents can be defined using `agent.json` files with automatic discovery of tools, skills, and subagents.

**Tool Protocol** (`src/pstock_sdk/agent/core/interfaces.py`): Tools must implement the `Tool` protocol with `name`, `description`, `input_schema`, and `execute()` method.

**Claude Skills** (`src/agents/*/skills/`): Skills are defined in `SKILL.md` files with YAML frontmatter containing metadata (name, description, allowed_tools).

**Subagent Delegation**: Child agents are automatically wrapped as `AgentAdapterTool` and can be called by parent agents.

### Key Data Flow

1. **Agent Loading** (`pstock_framework`): Scans `agents/` directories, parses `agent.json`, loads prompts, discovers tools/skills/subagents
2. **Tool Registration**: Tools are registered in `ToolRegistry` and converted to OpenAI function schemas
3. **Execution**: `AgentRuntime` runs the ReAct loop, calling tools via function calling
4. **Memory/Experience**: Results can be stored in `ExperienceStore` for future retrieval

## Environment Variables

Required in `.env` file:

```bash
OPENAI_API_KEY=sk-...           # Required for LLM
OPENAI_API_BASE=https://api.openai.com/v1  # Optional: custom API endpoint
OPENAI_MODEL=gpt-4o-mini        # Model to use

# Optional integrations
RAGFLOW_BASE_URL=http://...     # For knowledge base retrieval
RAGFLOW_API_KEY=ragflow-...
BOCHA_API_KEY=...               # For web search
```

## Agent Directory Structure

When creating new agents in `src/agents/`:

```
agent_name/
├── agent.json              # Required: Agent configuration
├── prompt.md               # Optional: System prompt
├── skills/                 # Optional: Claude Skills
│   └── skill_name/
│       └── SKILL.md
├── tools/                  # Optional: Auto-discovered Python tools
│   └── tool_name.py
└── subagents/              # Optional: Child agents
    └── child_agent/
        └── agent.json
```

## Important Patterns

**Tool Auto-Discovery**: Tools in `tools/*.py` are automatically loaded if they:
1. Implement the `Tool` protocol
2. Use `@validate_call` decorator
3. Export a `create_tool()` or `get_tool()` factory function
4. Have a module-level `tool` variable

**Error Handling**: Tool import errors are non-fatal (logged but don't break agent loading). Circular subagent references are detected at load time.

**LLM Inheritance**: Subagents inherit the parent's LLM unless explicitly configured in their `agent.json`.

**Experience System**: When enabled, agents can learn from past runs using `experience_query` and `experience_update` tools.

## Configuration Reference

Key `agent.json` fields:
- `model`: LLM configuration (model, api_key, api_base, temperature, max_tokens)
- `prompt`: System prompt (file reference or inline)
- `tools`: Auto-discovery settings, enable/disable lists
- `skills`: Skill sources, inline definitions
- `subagents`: Named child agents with optional aliases
- `runtime`: max_steps, workspace_root, mcp_servers, experience_enabled, knowledge_base
