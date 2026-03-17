# AI Flex Server

A web-based marketplace for discovering and interacting with AI Flex agents.

## Features

- **Agent Marketplace**: Web UI displaying all registered agents with key information
- **Interactive Chat**: Real-time chat interface with agents
- **Streaming Support**: Server-Sent Events (SSE) for streaming agent responses
- **Config Panel**: View agent configuration, tools, skills, and subagents
- **Session Management**: Persistent chat sessions with conversation history

## Installation

The server is included in the AI Flex SDK. Install dependencies:

```bash
uv sync
```

## Quick Start

### 1. Create and Register Agents

```python
from sdk.agent.core.agent import AgentBuilder
from sdk.agent.llm.openai_llm import OpenAILLM, OpenAIModelOptions
from server import registry, start_server

# Create LLM
llm = OpenAILLM(
    api_key="your-api-key",
    options=OpenAIModelOptions(model="gpt-4o-mini")
)

# Create agent
agent = (
    AgentBuilder()
    .with_name("financial-analyst")
    .with_description("AI financial analyst")
    .with_llm(llm)
    .build()
)

# Register to marketplace
agent_id = registry.register(agent)
```

### 2. Start the Server

```python
start_server(host="0.0.0.0", port=8000)
```

Or run the demo script:

```bash
python examples/server_demo.py
```

Or run as a module:

```bash
python -m server
```

### 3. Access the Web UI

Visit http://localhost:8000 in your browser.

## Frontend Development

The frontend is a React + Vite + Tailwind CSS application.

### Install Dependencies

```bash
cd src/server/frontend
npm install
```

### Development Mode

```bash
npm run dev
```

This starts the Vite dev server on port 5173 with API proxy to port 8000.

### Build for Production

```bash
npm run build
```

This builds the frontend to `dist/` which is served by the FastAPI backend.

## API Endpoints

### Agent Management

- `GET /api/agents` - List all registered agents
- `GET /api/agents/{agent_id}` - Get agent details
- `GET /api/agents/{agent_id}/config` - Get agent configuration

### Chat

- `POST /api/agents/{agent_id}/chat` - Non-streaming chat
- `POST /api/agents/{agent_id}/chat/stream` - Streaming chat (SSE)
- `GET /api/agents/{agent_id}/sessions` - List chat sessions
- `GET /api/agents/{agent_id}/sessions/{session_id}` - Get session details

### Health

- `GET /health` - Health check endpoint

## Architecture

```
src/server/
├── __init__.py           # Package exports
├── __main__.py           # Entry point for `python -m server`
├── models.py             # Pydantic models
├── registry.py           # Agent registry
├── server.py             # FastAPI application
├── routes/
│   ├── agents.py         # Agent endpoints
│   └── chat.py           # Chat endpoints
└── frontend/             # React + Vite frontend
    ├── src/
    │   ├── pages/
    │   │   ├── Marketplace.tsx
    │   │   └── Chat.tsx
    │   ├── components/
    │   │   ├── AgentCard.tsx
    │   │   ├── ChatMessage.tsx
    │   │   ├── ChatInput.tsx
    │   │   └── ConfigPanel.tsx
    │   └── api/
    │       └── client.ts
    └── dist/             # Built files (not in git)
```

## Session Management

Chat sessions are stored in-memory by default. Each session maintains:
- Session ID (UUID)
- Creation timestamp
- Message history with role, content, steps, and timestamp

For production use, consider implementing persistent storage (Redis, database).
