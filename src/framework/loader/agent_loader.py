"""
AI Flex Framework - Agent 加载器

主加载器，协调所有组件加载 Agent。
"""

import asyncio
from pathlib import Path
from typing import TYPE_CHECKING, Any

from loguru import logger

from ..config.agent_config import AgentConfig
from ..exceptions import AgentConfigError, PromptNotFoundError
from ..utils.path_utils import (
    find_agent_config,
    find_prompt_file,
    resolve_agent_dir,
)
from ..utils.validators import validate_json_file
from .skill_loader import SkillLoader
from .subagent_loader import SubagentLoader
from .tool_loader import ToolLoader

if TYPE_CHECKING:
    from sdk.agent.core.agent import Agent
    from sdk.agent.core.interfaces import LLM, Skill, Tool


class AgentLoader:
    """
    Agent 加载器

    从 agent.json 和相关文件加载 Agent。
    """

    def __init__(
        self,
        default_llm: "LLM",
        default_model: str | None = None,
        default_api_key: str | None = None,
    ):
        """
        初始化 Agent 加载器

        Args:
            default_llm: 默认 LLM 实例
            default_model: 默认模型名称
            default_api_key: 默认 API 密钥
        """
        self.default_llm = default_llm
        self.default_model = default_model
        self.default_api_key = default_api_key

        # 初始化子加载器
        self.skill_loader = SkillLoader()
        self.subagent_loader = SubagentLoader(self)

    async def load_agent_from_directory(
        self,
        agent_dir: Path,
        parent_llm: "LLM | None" = None,
    ) -> "Agent":
        """
        从目录加载 Agent

        Args:
            agent_dir: Agent 目录
            parent_llm: 父 Agent 的 LLM（用于继承）

        Returns:
            Agent 实例

        Raises:
            AgentConfigError: 配置无效或缺失
            PromptNotFoundError: Prompt 文件缺失
        """
        # 1. 查找配置文件
        config_file = find_agent_config(agent_dir)
        if not config_file:
            raise AgentConfigError(
                f"agent.json not found in {agent_dir}",
                details={"directory": str(agent_dir)},
            )

        # 2. 加载配置
        config_data = validate_json_file(config_file)
        config = AgentConfig(**config_data)
        config.set_config_dir(agent_dir)

        # 3. 加载 Prompt
        prompt_text = await self._load_prompt(config)

        # 4. 准备 LLM
        llm = await self._prepare_llm(config, parent_llm)

        # 5. 加载 Tools
        tools = await self._load_tools(config)

        # 6. 加载 Skills
        skills = await self._load_skills(config)

        # 7. 加载 Subagents
        subagents = await self._load_subagents(config, config.name)

        # 8. 构建并返回 Agent (确保列表不为 None)
        return self._build_agent(
            config,
            llm,
            prompt_text,
            tools or [],
            skills or [],
            subagents or [],
        )

    async def _load_prompt(self, config: AgentConfig) -> str:
        """
        加载 Prompt

        Args:
            config: Agent 配置

        Returns:
            Prompt 文本

        Raises:
            PromptNotFoundError: Prompt 文件缺失
        """
        prompt_parts = []

        # 1. 系统提示词
        if config.prompt.system:
            prompt_parts.append(config.prompt.system)

        # 2. 从文件加载
        if config.prompt.file:
            prompt_file = config.resolve_path(config.prompt.file)
            if not prompt_file.exists():
                raise PromptNotFoundError(
                    f"Prompt file not found: {prompt_file}",
                    details={"path": str(prompt_file)},
                )

            file_content = await asyncio.to_thread(prompt_file.read_text, encoding="utf-8")
            prompt_parts.append(file_content)

        # 3. 默认从 prompt.md 加载
        if not prompt_parts:
            prompt_file = find_prompt_file(config.get_config_dir())
            if prompt_file:
                file_content = await asyncio.to_thread(prompt_file.read_text, encoding="utf-8")
                prompt_parts.append(file_content)
            else:
                # 使用默认描述
                prompt_parts.append(f"You are {config.name}. {config.description}")

        # 4. 替换变量
        prompt_text = "\n\n".join(prompt_parts)
        if config.prompt.variables:
            for key, value in config.prompt.variables.items():
                prompt_text = prompt_text.replace(f"{{{key}}}", value)

        return prompt_text

    async def _prepare_llm(self, config: AgentConfig, parent_llm: "LLM | None") -> "LLM":
        """
        准备 LLM

        Args:
            config: Agent 配置
            parent_llm: 父 Agent 的 LLM

        Returns:
            LLM 实例
        """
        # 如果配置了模型，创建新的 LLM
        if config.model:
            from sdk import OpenAILLM

            model = config.model.model or self.default_model or "gpt-4"
            api_key = config.model.api_key or self.default_api_key

            llm_options: dict[str, Any] = {"model": model}

            if config.model.api_base:
                llm_options["api_base"] = config.model.api_base
            if config.model.temperature is not None:
                llm_options["temperature"] = config.model.temperature
            if config.model.max_tokens is not None:
                llm_options["max_tokens"] = config.model.max_tokens

            return OpenAILLM(api_key=api_key or "", options=llm_options)

        # 继承父 Agent 的 LLM
        if parent_llm:
            return parent_llm

        # 使用默认 LLM
        return self.default_llm

    async def _load_tools(self, config: AgentConfig) -> list["Tool"]:
        """
        加载工具

        Args:
            config: Agent 配置

        Returns:
            工具列表
        """
        tool_loader = ToolLoader(config.get_config_dir())

        tools = await tool_loader.load_tools(
            auto_discover=config.tools.auto_discover,
            enabled=config.tools.enabled if config.tools.enabled else None,
            disabled=config.tools.disabled if config.tools.disabled else None,
        )

        logger.info(f"Loaded {len(tools)} tools for agent {config.name}")
        return tools

    async def _load_skills(self, config: AgentConfig) -> list[dict[str, Any]]:
        """
        加载技能

        Args:
            config: Agent 配置

        Returns:
            技能列表
        """
        all_skills = []

        # 1. 从源加载
        if config.skills.sources:
            skills = await self.skill_loader.load_skills_from_sources(
                config.skills.sources, config.get_config_dir()
            )
            all_skills.extend(skills)

        # 2. 自动发现 skills/ 目录
        from ..utils.path_utils import find_skill_files

        skill_files = find_skill_files(config.get_config_dir())
        for skill_file in skill_files:
            skill = await self.skill_loader.load_skill_file(skill_file, skill_file.parent.name)
            if skill:
                all_skills.append(skill)

        # 3. 内联技能
        for inline_skill in config.skills.inline:
            if "name" in inline_skill and "description" in inline_skill:
                all_skills.append(inline_skill)

        logger.info(f"Loaded {len(all_skills)} skills for agent {config.name}")
        return all_skills

    async def _load_subagents(self, config: AgentConfig, parent_name: str) -> list["Agent"]:
        """
        加载子 Agent

        Args:
            config: Agent 配置
            parent_name: 父 Agent 名称

        Returns:
            子 Agent 列表
        """
        subagents = await self.subagent_loader.load_subagents(config, parent_name)

        logger.info(f"Loaded {len(subagents)} subagents for agent {config.name}")
        return subagents

    def _build_agent(
        self,
        config: AgentConfig,
        llm: "LLM",
        instructions: str,
        tools: list["Tool"],
        skills: list["Skill"],
        subagents: list["Agent"],
    ) -> "Agent":
        """
        构建 Agent

        Args:
            config: Agent 配置
            llm: LLM 实例
            instructions: 指令文本
            tools: 工具列表
            skills: 技能列表
            subagents: 子 Agent 列表

        Returns:
            Agent 实例
        """
        from sdk import AgentBuilder

        builder = (
            AgentBuilder()
            .with_llm(llm)
            .with_name(config.name)
            .with_description(config.description)
            .with_instructions(instructions)
            .with_max_steps(config.runtime.max_steps)
            .with_workspace_root(config.runtime.workspace_root)
            .with_tools(tools)
            .with_skills(skills)
            .with_children(subagents)
            .with_mcp_servers(config.runtime.mcp_servers)
            .with_mcp_lazy_load(config.runtime.mcp_lazy_load)
            .with_experience_enabled(config.runtime.experience_enabled)
        )

        # Only set knowledge_base if it's not None
        if config.runtime.knowledge_base is not None:
            builder = builder.with_knowledge_base(config.runtime.knowledge_base)

        agent = builder.build()

        # 如果有 Skill，注册 SkillAdapterTool
        if skills:
            from sdk.agent.tools.skill_adapter_tool import SkillAdapterTool

            skill_adapter = SkillAdapterTool(agent.skill_registry)
            agent._register_tool(skill_adapter)
            logger.info(f"Registered SkillAdapterTool for agent {config.name}")

        return agent
