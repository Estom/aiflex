"""
PStock SDK - AI Stock Trading & Analysis System Agent SDK

一个功能强大的 Python Agent 框架，支持：
- ReAct Agent Runtime
- 工具调用
- MCP 集成
- 知识库检索（RagFlow）
- 记忆和经验管理
- 技能系统
"""

__version__ = "0.1.0"

# Core runtime and interfaces
from .agent.core.agent import Agent, AgentBuilder, AgentOptions
from .agent.core.agent_runtime import AgentRuntime, AgentRuntimeConfig
from .agent.core.interfaces import (
    AgentContext,
    AgentRunResult,
    AgentStep,
    ChatHistoryMessage,
    ChatMessage,
    LLM,
    LLMResponse,
    Skill,
    Tool,
    ToolCall,
    ToolDefinition,
)

# Registries
from .agent.tools.tool_registry import ToolRegistry
from .agent.skills.skill_registry import SkillRegistry

# Tools
from .agent.tools.base_tool import BaseTool
from .agent.tools.agent_adapter_tool import AgentAdapterTool, AgentDescriptor
from .agent.tools.knowledge_base_retrieve_tool import KnowledgeBaseRetrieveTool
from .agent.tools.experience_query_tool import ExperienceQueryTool
from .agent.tools.experience_update_tool import ExperienceUpdateTool
from .agent.tools.find_files_tool import FindFilesTool
from .agent.tools.list_directory_tool import ListDirectoryTool
from .agent.tools.read_file_tool import ReadFileTool
from .agent.tools.write_file_tool import WriteFileTool
from .agent.tools.edit_file_tool import EditFileTool
from .agent.tools.search_text_tool import SearchTextTool
from .agent.tools.shell_tool import ShellTool

# LLMs and models
from .agent.llm.openai_llm import OpenAILLM, OpenAIModelOptions

# Config and stores
from .stores.agent_config_store import (
    AgentConfig,
    AgentRuntimeOptions,
    InMemoryAgentConfigStore,
    KnowledgeBaseAgentConfig,
    KnowledgeBaseRetrievalConfig,
)
from .stores.mcp_config_store import InMemoryMcpConfigStore, McpServerConfig
from .stores.memory_store import InMemoryMemoryStore, MemoryRecord, MemorySlotConfig
from .stores.experience_store import ExperienceRecord, ExperienceStore, InMemoryExperienceStore

# Integration
from .integration.ragflow_client import (
    RagFlowClient,
    RagFlowChunk,
    RagFlowConfig,
    RetrieveChunksRequest,
    RetrieveChunksResult,
    resolve_ragflow_config,
)

# Utilities
from .utils.agent_step import build_agent_step
from .utils.logger import logger, setup_logger

__all__ = [
    # Version
    "__version__",
    # Core
    "Agent",
    "AgentBuilder",
    "AgentOptions",
    "AgentRuntime",
    "AgentRuntimeConfig",
    # Interfaces
    "AgentContext",
    "AgentRunResult",
    "AgentStep",
    "ChatHistoryMessage",
    "ChatMessage",
    "LLM",
    "LLMResponse",
    "Skill",
    "Tool",
    "ToolCall",
    "ToolDefinition",
    # Registries
    "ToolRegistry",
    "SkillRegistry",
    # Tools
    "BaseTool",
    "AgentAdapterTool",
    "AgentDescriptor",
    "KnowledgeBaseRetrieveTool",
    "ExperienceQueryTool",
    "ExperienceUpdateTool",
    "FindFilesTool",
    "ListDirectoryTool",
    "ReadFileTool",
    "WriteFileTool",
    "EditFileTool",
    "SearchTextTool",
    "ShellTool",
    # LLM
    "OpenAILLM",
    "OpenAIModelOptions",
    # Stores
    "AgentConfig",
    "AgentRuntimeOptions",
    "InMemoryAgentConfigStore",
    "KnowledgeBaseAgentConfig",
    "KnowledgeBaseRetrievalConfig",
    "InMemoryMcpConfigStore",
    "McpServerConfig",
    "InMemoryMemoryStore",
    "MemoryRecord",
    "MemorySlotConfig",
    "ExperienceRecord",
    "ExperienceStore",
    "InMemoryExperienceStore",
    # Integration
    "RagFlowClient",
    "RagFlowChunk",
    "RagFlowConfig",
    "RetrieveChunksRequest",
    "RetrieveChunksResult",
    "resolve_ragflow_config",
    # Utils
    "build_agent_step",
    "logger",
    "setup_logger",
]
