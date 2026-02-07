"""
Agent - 智能体实现

Agent 是框架的核心类，负责：
- 管理工具、技能、子 Agent、MCP 服务器
- 初始化和配置
- 运行任务
"""

import asyncio
import os
from collections.abc import Callable
from pathlib import Path
from typing import Any

from loguru import logger

from ...integration.ragflow_client import RagFlowClient
from ..mcp.mcp_config import McpServerConfig
from ..memory.memory import MemorySlotConfig
from ..skills.skill_registry import SkillRegistry
from ..tools.agent_adapter_tool import AgentAdapterTool
from ..tools.edit_file_tool import EditFileTool
from ..tools.find_files_tool import FindFilesTool
from ..tools.knowledge_base_retrieve_tool import KnowledgeBaseRetrieveTool
from ..tools.lazy_mcp_adapter_tool import LazyMcpAdapterTool
from ..tools.list_directory_tool import ListDirectoryTool
from ..tools.read_file_tool import ReadFileTool
from ..tools.search_text_tool import SearchTextTool
from ..tools.shell_tool import ShellTool
from ..tools.tool_registry import ToolRegistry
from ..tools.write_file_tool import WriteFileTool
from .agent_context import AgentContextManager
from .agent_runtime import AgentRuntime, AgentRuntimeConfig
from .interfaces import (
    LLM,
    AgentContext,
    AgentRunResult,
    AgentStep,
    Skill,
    Tool,
)


class AgentOptions:
    """Agent 配置选项"""

    def __init__(
        self,
        llm: LLM,
        name: str,
        description: str,
        max_steps: int = 5,
        instructions: str | None = None,
        workspace_root: str | None = None,
        tools: list[Tool] | None = None,
        children: list["Agent"] | None = None,
        skills: list[Skill] | None = None,
        skill_sources: list[str] | None = None,
        mcp_servers: list[McpServerConfig] | None = None,
        mcp_lazy_load: bool = False,
        knowledge_base: dict[str, Any] | None = None,
        max_history_rounds: int = 10,
        memory_enabled: bool = False,
        memory_slots: list[MemorySlotConfig] | None = None,
        compression_enabled: bool = False,
        max_context_length: int = 50,
        compression_trigger_ratio: float = 0.8,
        compression_ratio: float = 0.3,
    ):
        # 模型参数
        self.llm = llm
        # 基本信息
        self.name = name
        self.description = description
        self.max_steps = max_steps
        # 系统提示词
        self.instructions = instructions
        # 工作空间根目录
        self.workspace_root = workspace_root
        # 工具
        self.tools = tools or []
        # 子 Agent
        self.children = children or []
        # 技能或者技能地址
        self.skills = skills or []
        self.skill_sources = skill_sources or []
        # mcp 服务器配置
        self.mcp_servers = mcp_servers or []
        self.mcp_lazy_load = mcp_lazy_load
        # 知识库配置
        self.knowledge_base = knowledge_base
        # 最大历史轮数、记忆、压缩等上下文参数
        self.max_history_rounds = max_history_rounds
        self.memory_enabled = memory_enabled
        self.memory_slots = memory_slots or []
        self.compression_enabled = compression_enabled
        self.max_context_length = max_context_length
        self.compression_trigger_ratio = compression_trigger_ratio
        self.compression_ratio = compression_ratio


class Agent:
    """
    智能体类

    Agent 是框架的核心类，负责：
    - 管理工具、技能、子 Agent
    - 初始化 MCP 服务器
    - 加载技能文件
    - 运行任务
    """

    def __init__(self, options: AgentOptions):
        """
        初始化 Agent

        Args:
            options: Agent 配置选项
        """
        self.name = options.name
        self.description = options.description

        # 配置
        self.config = AgentRuntimeConfig(
            name=options.name,
            description=options.description,
            max_steps=options.max_steps,
            instructions=options.instructions,
            workspace_root=options.workspace_root,
        )

        # LLM
        self.llm = options.llm

        # 注册表
        self.tool_registry = ToolRegistry()
        self.skill_registry = SkillRegistry()

        # 子 Agent
        self.children: list[Agent] = options.children

        # MCP 配置
        self.mcp_servers: list[McpServerConfig] = options.mcp_servers
        self.mcp_lazy_load: bool = options.mcp_lazy_load

        # 知识库
        self.knowledge_base: dict[str, Any] | None = options.knowledge_base

        # 上下文管理器（支持记忆和压缩功能）
        self.context_manager = AgentContextManager(
            max_history_rounds=options.max_history_rounds,
            memory_enabled=options.memory_enabled,
            memory_slots=options.memory_slots,
            compression_enabled=options.compression_enabled,
            max_context_length=options.max_context_length,
            compression_trigger_ratio=options.compression_trigger_ratio,
            compression_ratio=options.compression_ratio,
            llm=options.llm,
        )

        # Codespace 标记
        self.workspace_root: str = options.workspace_root

        # 技能源
        self.skill_sources: list[str] = options.skill_sources

        # 初始化标记
        self._initialized = False
        self._initializing: asyncio.Task | None = None

        # 注册内置工具和工具
        self._register_builtin_tools()
        self._register_tools(options.tools)
        self._register_skills(options.skills)
        self._register_skill_source(options.skill_sources)

        # 创建 Runtime
        self.runtime = AgentRuntime(
            self.llm,
            self.tool_registry,
            self.skill_registry,
            self.config,
        )

    async def run(self, task: str, context: AgentContext | None = None) -> AgentRunResult:
        """
        运行 Agent 任务

        Args:
            task: 用户任务
            context: 运行时上下文

        Returns:
            AgentRunResult: 运行结果
        """
        await self._ensure_initialized()
        return await self.runtime.run(task, context)

    async def run_stream(
        self,
        task: str,
        context: AgentContext,
        emit: callable,  # (AgentStep) -> None
    ) -> AgentRunResult:
        """
        流式运行 Agent

        Args:
            task: 用户任务
            context: 运行时上下文
            emit: 回调函数

        Returns:
            AgentRunResult: 运行结果
        """
        await self._ensure_initialized()
        return await self.runtime.run_stream(task, context, emit)

    async def run_with_context(
        self,
        task: str,
        session_id: str | None = None,
    ) -> AgentRunResult:
        """
        使用上下文管理器运行 Agent 任务

        自动管理会话上下文，包括历史消息的保存和轮次限制。

        Args:
            task: 用户任务
            session_id: 会话 ID，如果为 None 则自动生成

        Returns:
            AgentRunResult: 运行结果，包含 session_id
        """
        await self._ensure_initialized()

        # 获取或创建上下文
        context = self.context_manager.get_or_create_context(session_id)

        # 运行任务
        result = await self.runtime.run(task, context)

        # 更新上下文（添加对话到历史）
        await self.context_manager.update_context(
            context.session_id,
            user_message=task,
            assistant_response=result.output,
        )

        return result

    async def run_stream_with_context(
        self,
        task: str,
        session_id: str | None = None,
        emit: Callable[..., Any] | None = None,
    ) -> AgentRunResult:
        """
        使用上下文管理器流式运行 Agent

        自动管理会话上下文，包括历史消息的保存和轮次限制。

        Args:
            task: 用户任务
            session_id: 会话 ID，如果为 None 则自动生成
            emit: 流式输出回调函数 (AgentStep) -> None

        Returns:
            AgentRunResult: 运行结果，包含 session_id
        """
        await self._ensure_initialized()

        # 收集步骤用于流式输出
        steps_buffer: list[AgentStep] = []

        async def collect_steps(step: AgentStep) -> None:
            """收集执行步骤"""
            steps_buffer.append(step)
            if emit:
                await emit(step)

        # 获取或创建上下文
        context = self.context_manager.get_or_create_context(session_id)

        # 运行任务
        result = await self.runtime.run_stream(task, context, collect_steps)

        # 更新上下文（添加对话到历史）
        await self.context_manager.update_context(
            context.session_id,
            user_message=task,
            assistant_response=result.output,
        )

        return result

    def get_context_manager(self) -> AgentContextManager:
        """
        获取上下文管理器

        Returns:
            AgentContextManager: 上下文管理器实例
        """
        return self.context_manager

    def get_session_context(self, session_id: str) -> AgentContext | None:
        """
        获取指定会话的上下文

        Args:
            session_id: 会话 ID

        Returns:
            AgentContext | None: 上下文对象，如果不存在则返回 None
        """
        return self.context_manager.get_context(session_id)

    def clear_session(self, session_id: str) -> bool:
        """
        清除指定会话的上下文

        Args:
            session_id: 会话 ID

        Returns:
            bool: 如果会话存在并被清除返回 True，否则返回 False
        """
        return self.context_manager.clear_context(session_id)

    def list_sessions(self) -> list[str]:
        """
        列出所有活跃的会话 ID

        Returns:
            list[str]: 会话 ID 列表
        """
        return self.context_manager.list_sessions()

    def terminate(self) -> None:
        """
        终止当前运行的会话

        此方法会设置终止标志位，使正在运行的 Agent 任务在下次循环迭代时终止。
        """
        self.runtime.terminate()

    def reset_runtime(self) -> None:
        """
        重置运行时状态

        重置终止标志位，使 Agent 可以正常运行新的任务。
        """
        self.runtime.reset()

    def _register_tools(self, tools: list[Tool]) -> None:
        """注册工具"""
        for tool in tools:
            self._register_tool(tool)

        # 注册子 Agent
        from ..tools.agent_adapter_tool import AgentDescriptor

        for child in self.children:
            descriptor = AgentDescriptor(
                name=child.name, description=child.description
            )
            adapter = AgentAdapterTool(
                agent_descriptor=descriptor,
                run_child_agent=child.run,
            )
            self.tool_registry.register(adapter)

    def _register_tool(self, tool: Tool) -> None:
        """注册单个工具"""
        # 设置 registry（如果工具支持）
        if hasattr(tool, "set_registry"):
            tool.set_registry(self.tool_registry)
        self.tool_registry.register(tool)

    def _register_skills(self, skills: list[Skill]) -> None:
        """注册技能"""
        for skill in skills:
            self.skill_registry.register(skill)

    def _register_skill_source(self, sources: list[str]) -> None:
        """
        注册技能源

        读取 sources 路径下的 SKILL.md 文件，解析元信息并注册到 skill_registry。

        Args:
            sources: 技能源路径列表
                - 可以是 SKILL.md 文件的地址
                - 可以是 SKILL.md 父目录的地址
                - 可以是包含多个技能子目录的父目录地址
        """
        for source in sources:
            source_path = Path(source).expanduser().resolve()
            self._register_single_skill_source(source_path)

    def _register_single_skill_source(self, source_path: Path) -> None:
        """
        注册单个技能源

        Args:
            source_path: 技能源路径
        """
        if not source_path.exists():
            logger.debug(f"Skill source does not exist: {source_path}")
            return

        # 如果是文件，直接是 SKILL.md
        if source_path.is_file():
            if source_path.name.upper() != "SKILL.MD":
                logger.debug(f"Not a SKILL.md file: {source_path}")
                return
            skill = self._parse_skill_file_sync(source_path, source_path.parent)
            if skill and not self.skill_registry.get(skill["name"]):
                self.skill_registry.register(skill)
                logger.debug(f"Registered skill: {skill['name']} from {source_path}")
            return

        # 如果是目录
        if source_path.is_dir():
            # 检查是否有直接的 SKILL.md
            skill_md = source_path / "SKILL.md"
            if skill_md.exists():
                skill = self._parse_skill_file_sync(skill_md, source_path)
                if skill and not self.skill_registry.get(skill["name"]):
                    self.skill_registry.register(skill)
                    logger.debug(f"Registered skill: {skill['name']} from {skill_md}")
                return

            # 遍历子目录查找 SKILL.md
            for entry in source_path.iterdir():
                if not entry.is_dir():
                    continue
                skill_md = entry / "SKILL.md"
                if skill_md.exists():
                    skill = self._parse_skill_file_sync(skill_md, entry, entry.name)
                    if skill and not self.skill_registry.get(skill["name"]):
                        self.skill_registry.register(skill)
                        logger.debug(f"Registered skill: {skill['name']} from {skill_md}")

    def _parse_skill_file_sync(
        self,
        skill_md_path: Path,
        skill_dir: Path,
        fallback_name: str | None = None,
    ) -> Skill | None:
        """
        同步解析技能文件

        Args:
            skill_md_path: SKILL.md 文件路径
            skill_dir: 技能目录
            fallback_name: 备用名称

        Returns:
            Skill | None: 解析后的技能，失败返回 None
        """
        try:
            content = skill_md_path.read_text()
            # 解析 YAML frontmatter
            # 格式: ---\nkey: value\n---\ncontent
            import re

            import yaml

            frontmatter_match = re.match(r"^---\s*\n(.*?)\n---\s*\n(.*)$", content, re.DOTALL)
            if frontmatter_match:
                yaml_content = frontmatter_match.group(1)
                metadata = yaml.safe_load(yaml_content)
                if isinstance(metadata, dict):
                    name = metadata.get("name", fallback_name or skill_dir.name)
                    description = metadata.get("description", "")
                    version = metadata.get("version", "")
                    author = metadata.get("author", "")
                    skill_content = frontmatter_match.group(2)

                    skill: Skill = {
                        "name": name,
                        "description": description,
                        "path": str(skill_md_path),
                    }
                    if version:
                        skill["version"] = version
                    if author:
                        skill["author"] = author
                    if skill_content.strip():
                        skill["content"] = skill_content.strip()

                    return skill

            # 如果没有 frontmatter，尝试解析整个文件为 YAML
            metadata = yaml.safe_load(content)
            if isinstance(metadata, dict):
                name = metadata.get("name", fallback_name or skill_dir.name)
                description = metadata.get("description", "")
                version = metadata.get("version", "")
                author = metadata.get("author", "")

                skill: Skill = {
                    "name": name,
                    "description": description,
                    "path": str(skill_md_path),
                }
                if version:
                    skill["version"] = version
                if author:
                    skill["author"] = author

                return skill

            # 使用目录名作为 fallback
            return {
                "name": fallback_name or skill_dir.name,
                "description": "",
                "path": str(skill_md_path),
            }

        except Exception as e:
            logger.warning(f"Failed to read SKILL.md. path={skill_md_path}, error={e}")
            return None

    def _register_builtin_tools(self) -> None:
        """注册内置工具"""

        # Codespace 工具
        if bool(self.workspace_root):
            self._register_tool(FindFilesTool())
            self._register_tool(ListDirectoryTool())
            self._register_tool(ReadFileTool())
            self._register_tool(WriteFileTool())
            self._register_tool(EditFileTool())
            self._register_tool(SearchTextTool())
            self._register_tool(ShellTool())

        # 知识库工具
        kb_dataset_ids = (self.knowledge_base or {}).get("datasetIds", [])
        if kb_dataset_ids:
            try:
                ragflow = RagFlowClient()
                self._register_tool(KnowledgeBaseRetrieveTool(self.knowledge_base or {}, ragflow))
            except Exception as e:
                logger.warning(f"RagFlow is not configured; skipping knowledge base tool. agent={self.name}, error={e}")

        # MCP 懒加载工具
        if self.mcp_lazy_load:
            for cfg in self.mcp_servers:
                if cfg.get("enabled", True):
                    self._register_tool(
                        LazyMcpAdapterTool(
                            agent_name=self.name,
                            mcp_name=cfg["name"],
                            mcp_server_config=cfg,
                        )
                    )

    async def _ensure_initialized(self) -> None:
        """确保已初始化"""
        if self._initialized:
            return
        if self._initializing:
            await self._initializing
            return

        self._initializing = asyncio.create_task(self._initialize())
        await self._initializing
        self._initialized = True

    async def _initialize(self) -> None:
        """初始化 Agent"""
        await self._load_skill_sources()

        # 如果启用 MCP 非懒加载
        if not self.mcp_lazy_load and self.mcp_servers:
            enabled_servers = [cfg for cfg in self.mcp_servers if cfg.get("enabled", True)]
            if not enabled_servers:
                return

            # TODO: 加载 MCP 工具
            # 这里需要实现 MCP 客户端的连接和工具加载

    async def _load_skill_sources(self) -> None:
        """加载技能源"""
        sources = set(self.skill_sources)
        if self.config.workspace_root:
            sources.add(os.path.join(self.config.workspace_root, ".pstock", "skills"))

        for source in sources:
            await self._load_skill_source(source)

    async def _load_skill_source(self, source: str) -> None:
        """加载单个技能源"""
        source_path = Path(source).resolve()

        if not source_path.exists():
            return

        if source_path.is_file():
            if source_path.name.upper() != "SKILL.MD":
                return
            skill = await self._parse_skill_file(source_path, source_path.parent)
            if skill and not self.skill_registry.get(skill["name"]):
                self.skill_registry.register(skill)
            return

        if source_path.is_dir():
            # 检查直接 SKILL.md
            skill_md = source_path / "SKILL.md"
            if skill_md.exists():
                skill = await self._parse_skill_file(skill_md, source_path)
                if skill and not self.skill_registry.get(skill["name"]):
                    self.skill_registry.register(skill)
                return

            # 遍历子目录
            for entry in source_path.iterdir():
                if not entry.is_dir():
                    continue
                skill_md = entry / "SKILL.md"
                if skill_md.exists():
                    skill = await self._parse_skill_file(skill_md, entry, entry.name)
                    if skill and not self.skill_registry.get(skill["name"]):
                        self.skill_registry.register(skill)

    async def _parse_skill_file(
        self,
        skill_md_path: Path,
        skill_dir: Path,
        fallback_name: str | None = None,
    ) -> Skill | None:
        """解析技能文件"""
        try:
            content = await asyncio.to_thread(skill_md_path.read_text)
            import yaml

            # 解析 frontmatter
            match = yaml.safe_load(content)
            if isinstance(match, dict):
                name = match.get("name", fallback_name or skill_dir.name)
                description = match.get("description", "")
            else:
                name = fallback_name or skill_dir.name
                description = ""

            return {
                "name": name,
                "description": description,
                "path": str(skill_md_path),
            }
        except Exception as e:
            logger.warning(f"Failed to read SKILL.md. path={skill_md_path}, error={e}")
            return None


class AgentBuilder:
    """
    Agent Builder

    使用 Builder 模式构建 Agent
    """

    def __init__(self):
        self._llm: LLM | None = None
        self._name: str | None = None
        self._description: str | None = None
        self._max_steps: int = 5
        self._instructions: str | None = None
        self._workspace_root: str | None = None
        self._tools: list[Tool] = []
        self._skills: list[Skill] = []
        self._skill_sources: list[str] = []
        self._children: list[Agent] = []
        self._mcp_servers: list[McpServerConfig] = []
        self._mcp_lazy_load: bool = False
        self._knowledge_base: dict[str, Any] | None = None
        self._max_history_rounds: int = 10
        self._memory_enabled: bool = False
        self._memory_store: Any | None = None
        self._memory_slots: list[Any] = []
        self._compression_enabled: bool = False
        self._max_context_length: int = 50
        self._compression_trigger_ratio: float = 0.8
        self._compression_ratio: float = 0.3

    def with_llm(self, llm: LLM) -> "AgentBuilder":
        """设置 LLM"""
        self._llm = llm
        return self

    def with_name(self, name: str) -> "AgentBuilder":
        """设置名称"""
        self._name = name
        return self

    def with_description(self, description: str) -> "AgentBuilder":
        """设置描述"""
        self._description = description
        return self

    def with_max_steps(self, max_steps: int) -> "AgentBuilder":
        """设置最大步数"""
        self._max_steps = max_steps
        return self

    def with_instructions(self, instructions: str | None) -> "AgentBuilder":
        """设置指令"""
        self._instructions = instructions
        return self

    def with_workspace_root(self, workspace_root: str | None) -> "AgentBuilder":
        """设置工作区根目录"""
        self._workspace_root = workspace_root
        return self

    def with_tools(self, tools: list[Tool]) -> "AgentBuilder":
        """设置工具列表"""
        self._tools = list(tools)
        return self

    def with_tool(self, tool: Tool) -> "AgentBuilder":
        """添加工具"""
        self._tools.append(tool)
        return self

    def with_skills(self, skills: list[Skill]) -> "AgentBuilder":
        """设置技能列表"""
        self._skills = list(skills)
        return self

    def with_skill(self, skill: Skill) -> "AgentBuilder":
        """添加技能"""
        self._skills.append(skill)
        return self

    def with_skill_sources(self, sources: list[str]) -> "AgentBuilder":
        """设置技能源"""
        self._skill_sources = list(sources)
        return self

    def with_children(self, children: list[Agent]) -> "AgentBuilder":
        """设置子 Agent"""
        self._children = list(children)
        return self

    def with_child(self, child: Agent) -> "AgentBuilder":
        """添加子 Agent"""
        self._children.append(child)
        return self

    def with_mcp_servers(self, servers: list[McpServerConfig]) -> "AgentBuilder":
        """设置 MCP 服务器"""
        self._mcp_servers = list(servers)
        return self

    def with_mcp_lazy_load(self, enabled: bool) -> "AgentBuilder":
        """设置 MCP 懒加载"""
        self._mcp_lazy_load = enabled
        return self

    def with_knowledge_base(self, knowledge_base: dict[str, Any]) -> "AgentBuilder":
        """设置知识库"""
        self._knowledge_base = dict(knowledge_base)
        return self

    def with_max_history_rounds(self, max_rounds: int) -> "AgentBuilder":
        """设置最大历史轮次"""
        self._max_history_rounds = max_rounds
        return self

    def with_knowledge_base(self, knowledge_base: dict[str, Any]) -> "AgentBuilder":
        """设置知识库"""
        self._knowledge_base = dict(knowledge_base)
        return self

    def with_memory_enabled(self, enabled: bool) -> "AgentBuilder":
        """启用记忆功能"""
        self._memory_enabled = enabled
        return self

    def with_memory_store(self, store: Any) -> "AgentBuilder":
        """设置记忆存储"""
        self._memory_store = store
        return self

    def with_memory_slots(self, slots: list[Any]) -> "AgentBuilder":
        """设置记忆槽配置"""
        self._memory_slots = list(slots)
        return self

    def with_compression_enabled(self, enabled: bool) -> "AgentBuilder":
        """启用上下文压缩功能"""
        self._compression_enabled = enabled
        return self

    def with_max_context_length(self, length: int) -> "AgentBuilder":
        """设置上下文最大长度"""
        self._max_context_length = length
        return self

    def with_compression_trigger_ratio(self, ratio: float) -> "AgentBuilder":
        """设置压缩触发比例"""
        self._compression_trigger_ratio = ratio
        return self

    def with_compression_ratio(self, ratio: float) -> "AgentBuilder":
        """设置压缩后保留的比例"""
        self._compression_ratio = ratio
        return self

    def build(self) -> Agent:
        """构建 Agent"""
        if not self._llm:
            raise ValueError("AgentBuilder requires an LLM instance.")
        if not self._name or not self._description:
            raise ValueError("AgentBuilder requires both name and description.")

        return Agent(
            options=AgentOptions(
                llm=self._llm,
                name=self._name,
                description=self._description,
                max_steps=self._max_steps,
                instructions=self._instructions,
                workspace_root=self._workspace_root,
                tools=self._tools,
                children=self._children,
                skills=self._skills,
                skill_sources=self._skill_sources,
                mcp_servers=self._mcp_servers,
                mcp_lazy_load=self._mcp_lazy_load,
                knowledge_base=self._knowledge_base,
                max_history_rounds=self._max_history_rounds,
                memory_enabled=self._memory_enabled,
                memory_slots=self._memory_slots,
                compression_enabled=self._compression_enabled,
                max_context_length=self._max_context_length,
                compression_trigger_ratio=self._compression_trigger_ratio,
                compression_ratio=self._compression_ratio,
            ),
        )
