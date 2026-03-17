"""
PStock Server - Chat Routes

This module provides API endpoints for agent chat functionality.
"""

import asyncio
import json
import uuid
from collections.abc import AsyncGenerator
from datetime import datetime

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from loguru import logger

from sdk.agent.core.interfaces import AgentContext, AgentRunResult, AgentStep

from ..models import ChatRequest, ChatResponse, StepData
from ..registry import registry

router = APIRouter(prefix="/api/agents", tags=["chat"])

# In-memory session storage
_sessions: dict[str, dict] = {}


def get_or_create_session(session_id: str | None) -> str:
    """Get existing session or create new one"""
    if session_id and session_id in _sessions:
        return session_id
    new_session_id = str(uuid.uuid4())
    _sessions[new_session_id] = {
        "created_at": datetime.utcnow(),
        "messages": [],
    }
    return new_session_id


def format_step_event(step: AgentStep) -> str:
    """Format a step as SSE event"""
    event_data = {
        "type": "step",
        "content": step.content,
        "step": {
            "type": step.type,
            "content": step.content,
            "display_name": step.display_name,
            "data": step.data,
        },
    }
    return f"event: step\ndata: {json.dumps(event_data)}\n\n"


def format_final_event(response: str, session_id: str) -> str:
    """Format final response as SSE event"""
    event_data = {
        "type": "final",
        "content": response,
        "session_id": session_id,
    }
    return f"event: final\ndata: {json.dumps(event_data)}\n\n"


def format_error_event(error: str) -> str:
    """Format error as SSE event"""
    event_data = {
        "type": "error",
        "content": error,
    }
    return f"event: error\ndata: {json.dumps(event_data)}\n\n"


async def stream_agent_run(
    agent_id: str,
    task: str,
    session_id: str,
) -> AsyncGenerator[str, None]:
    """
    Stream agent execution as SSE events

    Args:
        agent_id: The agent ID
        task: The user task/message
        session_id: The session ID

    Yields:
        str: SSE formatted events
    """
    agent = registry.get(agent_id)
    if not agent:
        yield format_error_event(f"Agent not found: {agent_id}")
        return

    # Create context with session
    context = AgentContext(session_id=session_id)

    # Queue for streaming steps
    queue: asyncio.Queue[AgentStep | None] = asyncio.Queue()

    async def emit(step: AgentStep) -> None:
        """Emit step to stream"""
        await queue.put(step)

    # Start the agent run in background
    async def run_agent() -> AgentRunResult | None:
        try:
            return await agent.run_stream(task, context, emit)
        except Exception as e:
            logger.error(f"Error running agent {agent_id}: {e}")
            return None

    # Start agent task
    agent_task = asyncio.create_task(run_agent())

    try:
        # Stream steps as they arrive
        while True:
            step = await asyncio.wait_for(queue.get(), timeout=0.1)
            if step is None:
                break
            yield format_step_event(step)

    except TimeoutError:
        pass

    # Wait for agent to complete
    result = await agent_task

    if result:
        # Send final response
        yield format_final_event(result.output, session_id)

        # Store in session
        if session_id in _sessions:
            _sessions[session_id]["messages"].append(
                {"role": "user", "content": task, "timestamp": datetime.utcnow().isoformat()}
            )
            _sessions[session_id]["messages"].append(
                {
                    "role": "assistant",
                    "content": result.output,
                    "steps": [StepData(**s.__dict__) for s in result.steps],
                    "timestamp": datetime.utcnow().isoformat(),
                }
            )
    else:
        yield format_error_event("Agent execution failed")


@router.post("/{agent_id}/chat", response_model=ChatResponse)
async def chat_agent(agent_id: str, request: ChatRequest) -> ChatResponse:
    """
    Non-streaming chat with an agent

    Args:
        agent_id: The agent ID
        request: Chat request with message and optional session_id

    Returns:
        ChatResponse: Agent response with steps

    Raises:
        HTTPException: 404 if agent not found
    """
    agent = registry.get(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail=f"Agent not found: {agent_id}")

    # Get or create session
    session_id = get_or_create_session(request.session_id)

    # Create context
    context = AgentContext(session_id=session_id)

    try:
        # Run agent
        result = await agent.run(request.message, context)

        # Store in session
        _sessions[session_id]["messages"].append(
            {"role": "user", "content": request.message, "timestamp": datetime.utcnow().isoformat()}
        )
        _sessions[session_id]["messages"].append(
            {
                "role": "assistant",
                "content": result.output,
                "steps": [StepData(**s.__dict__) for s in result.steps],
                "timestamp": datetime.utcnow().isoformat(),
            }
        )

        return ChatResponse(
            response=result.output,
            session_id=session_id,
            steps=[StepData(**s.__dict__) for s in result.steps],
        )

    except Exception as e:
        logger.error(f"Error running agent {agent_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{agent_id}/chat/stream")
async def chat_agent_stream_post(agent_id: str, request: ChatRequest) -> StreamingResponse:
    """
    Streaming chat with an agent using Server-Sent Events (POST method)

    Args:
        agent_id: The agent ID
        request: Chat request with message and optional session_id

    Returns:
        StreamingResponse: SSE stream of agent execution

    Raises:
        HTTPException: 404 if agent not found
    """
    agent = registry.get(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail=f"Agent not found: {agent_id}")

    # Get or create session
    session_id = get_or_create_session(request.session_id)

    return StreamingResponse(
        stream_agent_run(agent_id, request.message, session_id),
        media_type="text/event-stream",
    )


@router.get("/{agent_id}/chat/stream")
async def chat_agent_stream_get(
    agent_id: str,
    message: str,
    session_id: str | None = None,
) -> StreamingResponse:
    """
    Streaming chat with an agent using Server-Sent Events (GET method for EventSource)

    Args:
        agent_id: The agent ID
        message: The user message
        session_id: Optional session ID for conversation continuity

    Returns:
        StreamingResponse: SSE stream of agent execution

    Raises:
        HTTPException: 404 if agent not found
    """
    agent = registry.get(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail=f"Agent not found: {agent_id}")

    # Get or create session
    session_id = get_or_create_session(session_id)

    return StreamingResponse(
        stream_agent_run(agent_id, message, session_id),
        media_type="text/event-stream",
    )


@router.get("/{agent_id}/sessions")
async def list_sessions(agent_id: str) -> list[dict]:
    """
    List chat sessions

    Args:
        agent_id: The agent ID (for filtering, currently returns all)

    Returns:
        list[dict]: List of session information
    """
    return [
        {
            "session_id": session_id,
            "created_at": data["created_at"].isoformat(),
            "message_count": len(data["messages"]),
        }
        for session_id, data in _sessions.items()
    ]


@router.get("/{agent_id}/sessions/{session_id}")
async def get_session(agent_id: str, session_id: str) -> dict:
    """
    Get session details

    Args:
        agent_id: The agent ID
        session_id: The session ID

    Returns:
        dict: Session details with messages

    Raises:
        HTTPException: 404 if session not found
    """
    if session_id not in _sessions:
        raise HTTPException(status_code=404, detail=f"Session not found: {session_id}")

    session = _sessions[session_id]
    return {
        "session_id": session_id,
        "created_at": session["created_at"].isoformat(),
        "messages": session["messages"],
    }
