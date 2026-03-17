"""
AI Flex Server - Agent Registry

This module provides a central registry for managing agents in the marketplace.
"""

import threading
import uuid
from datetime import datetime

from loguru import logger

from sdk.agent.core.agent import Agent

from .models import AgentConfig, AgentInfo, SkillInfo, SubagentInfo, ToolInfo


class AgentRegistry:
    """
    Central registry for managing agents

    Thread-safe singleton registry for storing and retrieving agents.
    """

    _instance: "AgentRegistry | None" = None
    _lock = threading.Lock()

    def __new__(cls) -> "AgentRegistry":
        """Singleton pattern"""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        """Initialize the registry"""
        if self._initialized:
            return

        self._agents: dict[str, tuple[Agent, AgentInfo]] = {}
        self._lock = threading.RLock()
        self._initialized = True
        logger.info("AgentRegistry initialized")

    def register(self, agent: Agent) -> str:
        """
        Register an agent to the marketplace

        Args:
            agent: The Agent instance to register

        Returns:
            str: The unique agent ID
        """
        agent_id = str(uuid.uuid4())
        agent_info = self._create_agent_info(agent, agent_id)

        with self._lock:
            self._agents[agent_id] = (agent, agent_info)

        logger.info(f"Registered agent: {agent.name} (id={agent_id})")
        return agent_id

    def get(self, agent_id: str) -> Agent | None:
        """
        Get an agent by ID

        Args:
            agent_id: The agent ID

        Returns:
            Agent | None: The Agent instance or None if not found
        """
        with self._lock:
            result = self._agents.get(agent_id)
            return result[0] if result else None

    def get_info(self, agent_id: str) -> AgentInfo | None:
        """
        Get agent info by ID

        Args:
            agent_id: The agent ID

        Returns:
            AgentInfo | None: The AgentInfo or None if not found
        """
        with self._lock:
            result = self._agents.get(agent_id)
            return result[1] if result else None

    def list_all(self) -> list[AgentInfo]:
        """
        List all registered agents

        Returns:
            list[AgentInfo]: List of agent metadata
        """
        with self._lock:
            return [info for _, info in self._agents.values()]

    def unregister(self, agent_id: str) -> bool:
        """
        Unregister an agent

        Args:
            agent_id: The agent ID to unregister

        Returns:
            bool: True if unregistered, False if not found
        """
        with self._lock:
            if agent_id in self._agents:
                agent, _ = self._agents.pop(agent_id)
                logger.info(f"Unregistered agent: {agent.name} (id={agent_id})")
                return True
            return False

    def clear(self) -> None:
        """Clear all registered agents"""
        with self._lock:
            count = len(self._agents)
            self._agents.clear()
            logger.info(f"Cleared {count} agents from registry")

    def _create_agent_info(self, agent: Agent, agent_id: str) -> AgentInfo:
        """
        Create AgentInfo from an Agent instance

        Args:
            agent: The Agent instance
            agent_id: The unique agent ID

        Returns:
            AgentInfo: Agent metadata
        """
        # Extract tools
        tools = [
            ToolInfo(
                name=tool.name,
                description=tool.description,
                display_name=getattr(tool, "display_name", None),
                parameters=tool.parameters,
            )
            for tool in agent.tool_registry.list()
        ]

        # Extract skills
        skills = [
            SkillInfo(
                name=skill["name"],
                description=skill["description"],
                path=skill.get("path"),
            )
            for skill in agent.skill_registry.list()
        ]

        # Extract subagents
        subagents = [
            SubagentInfo(
                name=child.name,
                description=child.description,
            )
            for child in agent.children
        ]

        # Create config
        config = AgentConfig(
            max_steps=agent.config.max_steps,
            workspace_root=agent.config.workspace_root,
            instructions=agent.config.instructions,
            mcp_servers=agent.mcp_servers,
            knowledge_base=agent.knowledge_base,
        )

        return AgentInfo(
            id=agent_id,
            name=agent.name,
            description=agent.description,
            tools=tools,
            skills=skills,
            subagents=subagents,
            config=config,
            created_at=datetime.utcnow(),
        )


# Global registry instance
registry = AgentRegistry()
