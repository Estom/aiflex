"""
PStock Framework - 声明式 Agent 框架

一个基于 JSON 配置文件的声明式 Agent 框架，支持：
- 声明式 agent.json 配置
- Claude Skills 规范（SKILL.md）
- 工具自动发现（tools/*.py）
- 子 Agent 递归加载
- 框架加载器和注册表

基本用法：
```python
from pstock_framework import AgentFrameworkLoader
from pstock_sdk import OpenAILLM

# 初始化
llm = OpenAILLM(api_key="sk-...", options={"model": "gpt-4"})
loader = AgentFrameworkLoader(agents_root="agents/", default_llm=llm)

# 加载所有 Agent
await loader.load_all()

# 获取特定 Agent
agent = loader.get_agent("financial_analyst")
result = await agent.run("Analyze AAPL stock")

# 列出所有 Agent
for name in loader.registry.list_agents():
    print(f"Loaded agent: {name}")
```
"""

__version__ = "0.1.0"

from pathlib import Path
from typing import TYPE_CHECKING, Any

from loguru import logger

if TYPE_CHECKING:
    from pstock_sdk.agent.core.agent import Agent

from .config import (
    AgentConfig,
    ModelConfig,
    PromptConfig,
    RuntimeConfig,
    SkillMetadata,
    SkillsConfig,
    SubagentConfig,
    ToolsConfig,
)
from .exceptions import (
    AgentConfigError,
    CircularReferenceError,
    FrameworkError,
    PromptNotFoundError,
    SkillParseError,
    ToolImportError,
)
from .loader import AgentLoader
from .registry import AgentFrameworkRegistry
from .utils import find_agent_config, find_prompt_file, resolve_agent_dir


class AgentFrameworkLoader:
    """
    Agent 框架加载器

    主入口类，负责扫描 agents_root 并加载所有 Agent。
    """

    def __init__(
        self,
        agents_root: str | Path,
        default_llm: Any,
        default_model: str | None = None,
        default_api_key: str | None = None,
    ):
        """
        初始化框架加载器

        Args:
            agents_root: Agent 根目录
            default_llm: 默认 LLM 实例
            default_model: 默认模型名称
            default_api_key: 默认 API 密钥
        """
        self.agents_root = Path(agents_root).resolve()
        self.default_llm = default_llm
        self.default_model = default_model
        self.default_api_key = default_api_key

        # 创建注册表
        self.registry = AgentFrameworkRegistry()

        # 创建内部加载器
        self._loader = AgentLoader(
            default_llm=default_llm,
            default_model=default_model,
            default_api_key=default_api_key,
        )

    async def load_all(self) -> dict[str, "Agent"]:
        """
        加载所有 Agent

        扫描 agents_root 目录，递归加载所有 agent.json 文件。

        Returns:
            加载的 Agent 字典 {name: agent}
        """
        if not self.agents_root.exists():
            logger.warning(f"Agents root directory not found: {self.agents_root}")
            return {}

        if not self.agents_root.is_dir():
            logger.error(f"Agents root is not a directory: {self.agents_root}")
            return {}

        agents: dict[str, Agent] = {}

        # 遍历所有子目录
        for entry in self.agents_root.iterdir():
            if not entry.is_dir():
                continue

            # 检查是否包含 agent.json
            config_file = find_agent_config(entry)
            if not config_file:
                continue

            try:
                agent = await self._loader.load_agent_from_directory(entry)
                agents[agent.name] = agent
                self.registry.register(agent.name, agent)
                logger.info(f"Loaded agent: {agent.name} from {entry}")
            except Exception as e:
                logger.error(f"Failed to load agent from {entry}: {e}")

        logger.info(f"Loaded {len(agents)} agents from {self.agents_root}")
        return agents

    async def load_agent(self, agent_name: str) -> "Agent | None":
        """
        加载单个 Agent

        Args:
            agent_name: Agent 名称（可以包含路径，如 "trading/analyst"）

        Returns:
            Agent 实例，加载失败返回 None
        """
        agent_dir = resolve_agent_dir(self.agents_root, agent_name)

        if not agent_dir.exists():
            logger.error(f"Agent directory not found: {agent_dir}")
            return None

        try:
            agent = await self._loader.load_agent_from_directory(agent_dir)
            self.registry.register(agent.name, agent)
            logger.info(f"Loaded agent: {agent.name} from {agent_dir}")
            return agent
        except Exception as e:
            logger.error(f"Failed to load agent {agent_name}: {e}")
            return None

    def get_agent(self, name: str) -> "Agent | None":
        """
        获取已加载的 Agent

        Args:
            name: Agent 名称

        Returns:
            Agent 实例，如果不存在则返回 None
        """
        return self.registry.get(name)

    def list_agents(self) -> list[str]:
        """
        列出所有已加载的 Agent

        Returns:
            Agent 名称列表
        """
        return self.registry.list_agents()

    def has_agent(self, name: str) -> bool:
        """
        检查 Agent 是否已加载

        Args:
            name: Agent 名称

        Returns:
            是否已加载
        """
        return self.registry.has_agent(name)

    async def load(self) -> "Agent":
        """
        加载 agents_root 对应的单个 Agent

        当 agents_root 本身就是一个 Agent 目录（包含 agent.json）时，
        直接加载该 Agent。适用于加载单个 Agent 的场景。

        Returns:
            加载的 Agent 实例

        Raises:
            FrameworkError: 加载失败时抛出

        Example:
            ```python
            # agents_root 是单个 Agent 目录
            loader = AgentFrameworkLoader(
                agents_root="agents/financial_analyst",
                default_llm=llm
            )
            agent = await loader.load()
            result = await agent.run("分析 AAPL")
            ```
        """
        if not self.agents_root.exists():
            raise FrameworkError(f"Agent directory not found: {self.agents_root}")

        # 检查是否包含 agent.json
        config_file = find_agent_config(self.agents_root)
        if not config_file:
            raise FrameworkError(f"No agent.json found in: {self.agents_root}")

        try:
            agent = await self._loader.load_agent_from_directory(self.agents_root)
            self.registry.register(agent.name, agent)
            logger.info(f"Loaded agent: {agent.name} from {self.agents_root}")
            return agent
        except Exception as e:
            raise FrameworkError(f"Failed to load agent from {self.agents_root}: {e}") from e


__all__ = [
    # Version
    "__version__",
    # Main loader
    "AgentFrameworkLoader",
    # Registry
    "AgentFrameworkRegistry",
    # Exceptions
    "FrameworkError",
    "AgentConfigError",
    "PromptNotFoundError",
    "CircularReferenceError",
    "ToolImportError",
    "SkillParseError",
    # Config models
    "AgentConfig",
    "ModelConfig",
    "PromptConfig",
    "SkillsConfig",
    "ToolsConfig",
    "SubagentConfig",
    "RuntimeConfig",
    "SkillMetadata",
    # Utils
    "resolve_agent_dir",
    "find_agent_config",
    "find_prompt_file",
]
