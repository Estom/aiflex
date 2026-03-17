"""
AI Flex Server - Agent Management Routes

This module provides API endpoints for agent listing and details.
"""

from fastapi import APIRouter, HTTPException

from ..models import AgentInfo
from ..registry import registry

router = APIRouter(prefix="/api/agents", tags=["agents"])


@router.get("", response_model=list[AgentInfo])
async def list_agents() -> list[AgentInfo]:
    """
    List all registered agents

    Returns:
        list[AgentInfo]: List of all registered agent metadata
    """
    return registry.list_all()


@router.get("/{agent_id}", response_model=AgentInfo)
async def get_agent(agent_id: str) -> AgentInfo:
    """
    Get agent details by ID

    Args:
        agent_id: The agent ID

    Returns:
        AgentInfo: Agent metadata

    Raises:
        HTTPException: 404 if agent not found
    """
    agent_info = registry.get_info(agent_id)
    if not agent_info:
        raise HTTPException(status_code=404, detail=f"Agent not found: {agent_id}")
    return agent_info


@router.get("/{agent_id}/config")
async def get_agent_config(agent_id: str) -> dict:
    """
    Get agent configuration

    Args:
        agent_id: The agent ID

    Returns:
        dict: Agent configuration

    Raises:
        HTTPException: 404 if agent not found
    """
    agent_info = registry.get_info(agent_id)
    if not agent_info:
        raise HTTPException(status_code=404, detail=f"Agent not found: {agent_id}")
    return {
        "name": agent_info.name,
        "description": agent_info.description,
        "config": agent_info.config,
        "tools": agent_info.tools,
        "skills": agent_info.skills,
        "subagents": agent_info.subagents,
    }
