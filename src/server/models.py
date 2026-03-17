"""
PStock Server - Pydantic models for API

This module defines the data models used in the PStock Server API.
"""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class ToolInfo(BaseModel):
    """Tool information"""

    name: str
    description: str
    display_name: str | None = None
    parameters: dict[str, Any] | None = None


class SkillInfo(BaseModel):
    """Skill information"""

    name: str
    description: str
    path: str | None = None


class SubagentInfo(BaseModel):
    """Subagent information"""

    name: str
    description: str


class AgentConfig(BaseModel):
    """Agent configuration"""

    max_steps: int
    workspace_root: str | None = None
    instructions: str | None = None
    mcp_servers: list[dict[str, Any]] = Field(default_factory=list)
    experience_enabled: bool = False
    knowledge_base: dict[str, Any] | None = None


class AgentInfo(BaseModel):
    """Agent metadata"""

    id: str
    name: str
    description: str
    tools: list[ToolInfo] = Field(default_factory=list)
    skills: list[SkillInfo] = Field(default_factory=list)
    subagents: list[SubagentInfo] = Field(default_factory=list)
    config: AgentConfig

    created_at: datetime = Field(default_factory=datetime.utcnow)


class ChatMessage(BaseModel):
    """Chat message"""

    role: str  # 'user' | 'assistant'
    content: str


class ChatRequest(BaseModel):
    """Chat request"""

    message: str
    session_id: str | None = None
    stream: bool = False


class StepData(BaseModel):
    """Agent step data"""

    type: str
    content: str
    display_name: str | None = None
    raw: str | None = None
    data: dict[str, Any] = Field(default_factory=dict)


class ChatResponse(BaseModel):
    """Chat response"""

    response: str
    session_id: str
    steps: list[StepData] = Field(default_factory=list)


class ChatStreamEvent(BaseModel):
    """Chat stream event"""

    type: str  # 'thought' | 'action' | 'observation' | 'final' | 'error'
    content: str
    step: StepData | None = None


class SessionInfo(BaseModel):
    """Chat session information"""

    session_id: str
    created_at: datetime
    message_count: int
