"""
Agent - 智能体实现

Agent 是框架的核心类，负责：
- 管理工具、技能、子 Agent、MCP 服务器
- 初始化和配置
- 运行任务
"""

import asyncio
import json
import os
from pathlib import Path
from typing import Any

from loguru import logger

from .agent_runtime import AgentRuntime, AgentRuntimeConfig
from .interfaces import AgentContext, AgentRunResult, LLM, Skill, Tool
from ..tools.tool_registry import ToolRegistry
from ..skills.skill_registry import SkillRegistry
from ..tools.base_tool import BaseTool
from ..tools.agent_adapter_tool import AgentAdapterTool
from ..tools.lazy_mcp_adapter_tool import LazyMcpAdapterTool
from ..tools.experience_query_tool import ExperienceQueryTool
from ..tools.experience_update_tool import ExperienceUpdateTool
from ..tools.find_files_tool import FindFilesTool
from ..tools.list_directory_tool import ListDirectoryTool
from ..tools.read_file_tool import ReadFileTool
from ..tools.write_file_tool import WriteFileTool
from ..tools.edit_file_tool import EditFileTool
from ..tools.search_text_tool import SearchTextTool
from ..tools.shell_tool import ShellTool
from ..tools.knowledge_base_retrieve_tool import KnowledgeBaseRetrieveTool
from ...integration.ragflow_client import RagFlowClient
from ...stores.mcp_config_store import McpServerConfig


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
        experience_enabled: bool = False,
        knowledge_base: dict[str, Any] | None = None,
    ):
        self.llm = llm
        self.name = name
        self.description = description
        self.max_steps = max_steps
        self.instructions = instructions
        self.workspace_root = workspace_root
        self.tools = tools or []
        self.children = children or []
        self.skills = skills or []
        self.skill_sources = skill_sources or []
        self.mcp_servers = mcp_servers or []
        self.mcp_lazy_load = mcp_lazy_load
        self.experience_enabled = experience_enabled
        self.knowledge_base = knowledge_base


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

        # 经验和知识库
        self.experience_enabled: bool = options.experience_enabled
        self.experience_store = options.experience_store
        self.knowledge_base: dict[str, Any] | None = options.knowledge_base

        # Codespace 标记
        self.codespace_enabled: bool = bool(options.workspace_root)

        # 技能源
        self.skill_sources: list[str] = options.skill_sources

        # 初始化标记
        self._initialized = False
        self._initializing: asyncio.Task | None = None

        # 注册内置工具和工具
        self._register_builtin_tools()
        self._register_tools(options.tools)
        self._register_skills(options.skills)

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

    def _register_builtin_tools(self) -> None:
        """注册内置工具"""
        # 经验工具
        if self.experience_enabled:
            if not self.experience_store:
                logger.warning(f"Experience tools enabled but experienceStore is missing. agent={self.name}")
            else:
                self._register_tool(ExperienceQueryTool(self.name, self.experience_store))
                self._register_tool(ExperienceUpdateTool(self.name, self.experience_store))

        # Codespace 工具
        if self.codespace_enabled:
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
            pass

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
        self._experience_enabled: bool = False
        self._experience_store: ExperienceStore | None = None
        self._knowledge_base: dict[str, Any] | None = None

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

    def with_experience_enabled(self, enabled: bool) -> "AgentBuilder":
        """启用经验"""
        self._experience_enabled = enabled
        return self

    def with_experience_store(self, store: ExperienceStore) -> "AgentBuilder":
        """设置经验存储"""
        self._experience_store = store
        return self

    def with_knowledge_base(self, knowledge_base: dict[str, Any]) -> "AgentBuilder":
        """设置知识库"""
        self._knowledge_base = dict(knowledge_base)
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
                experience_enabled=self._experience_enabled,
                experience_store=self._experience_store,
                knowledge_base=self._knowledge_base,
            ),
        )
