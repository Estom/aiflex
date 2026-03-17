# PStock Server - Agent Marketplace Documentation

## 概述

`server` 是 PStock 框架的 Web 服务器模块，提供 Agent 市场、交互式聊天和多种运行模式。

## 功能特性

- **Web 市场模式**：提供 Web 界面展示所有注册的 Agent
- **交互式模式**：命令行交互式对话，支持历史上下文
- **单次提示模式**：一次性执行 Agent 任务
- **流式响应**：支持 SSE 流式输出 Agent 执行过程
- **会话管理**：维护对话历史和会话状态

## 架构

```
server/
├── __init__.py           # 包导出
├── __main__.py           # 模块入口
├── models.py             # Pydantic 数据模型
├── registry.py           # Agent 注册表
├── server.py             # AgentServer 类
├── routes/               # API 路由
│   ├── agents.py         # Agent 列表和详情
│   └── chat.py           # 聊天接口
└── frontend/             # React + Vite 前端
    ├── src/
    │   ├── pages/        # 页面组件
    │   ├── components/   # UI 组件
    │   └── api/          # API 客户端
    └── dist/             # 构建产物
```

## 快速开始

### 1. 创建并注册 Agent

```python
import os
from dotenv import load_dotenv
from sdk.agent.core.agent import AgentBuilder
from sdk.agent.llm.openai_llm import OpenAILLM, OpenAIModelOptions
from server import registry, AgentServer

load_dotenv()

# 创建 LLM
llm = OpenAILLM(
    api_key=os.getenv("OPENAI_API_KEY"),
    options=OpenAIModelOptions(
        model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        api_base=os.getenv("OPENAI_API_BASE", "https://api.openai.com/v1")
    )
)

# 创建 Agent
agent = (
    AgentBuilder()
    .with_name("financial-analyst")
    .with_description("AI 财务分析助手")
    .with_llm(llm)
    .build()
)

# 注册到市场
registry.register(agent)
```

### 2. 创建 AgentServer

```python
server = AgentServer(registry)
```

### 3. 运行不同模式

#### Web 模式（市场界面）

```python
# 方式一：命令行参数
server.run(["--web"])

# 方式二：命令行
python -m server --web

# 方式三：指定端口
server.run(["--web", "--port", "8080"])
```

访问 http://localhost:8000 查看 Agent 市场。

#### 交互式模式（CLI 对话）

```python
# 方式一：命令行参数
server.run(["--interactive"])

# 方式二：命令行
python -m server --interactive

# 方式三：指定 Agent
server.run(["--interactive", "--agent", "financial-analyst"])
```

交互式对话示例：
```
Starting interactive session with: financial-analyst
Type 'quit' or 'exit' to end the session.
------------------------------------------------------------

You: 分析一下苹果公司
financial-analyst: [分析结果...]

[Executed 3 step(s)]

You: 微软呢？
financial-analyst: [结合上下文分析微软...]

[Executed 2 step(s)]
```

#### 单次提示模式

```python
# 方式一：命令行参数
server.run(["--prompt", "AAPL 股价是多少？"])

# 方式二：命令行
python -m server --prompt "AAPL 股价是多少？"

# 方式三：指定 Agent
server.run(["--prompt", "分析 AAPL", "--agent", "financial-analyst"])
```

#### 列出所有 Agent

```python
# 方式一：命令行参数
server.run(["--list"])

# 方式二：命令行
python -m server --list
```

输出示例：
```
Registered Agents (2):
------------------------------------------------------------

Name: financial-analyst
ID: 550e8400-e29b-41d4-a716-446655440000
Description: AI 财务分析助手
Tools: 0
Skills: 0
Subagents: 0

Name: code-assistant
ID: 6ba7b810-9dad-11d1-80b4-00c04fd430c8
Description: AI 代码助手
Tools: 0
Skills: 0
Subagents: 0
```

## AgentServer 类

### 构造函数

```python
server = AgentServer(registry: AgentRegistry)
```

### run() 方法

```python
server.run(args: list[str] | None = None)
```

解析命令行参数并运行相应模式。

### 命令行参数

| 参数 | 短参数 | 说明 |
|------|--------|------|
| `--web` | `-w` | 启动 Web 服务器 |
| `--interactive` | `-i` | 启动交互式模式 |
| `--prompt PROMPT` | `-p PROMPT` | 单次提示模式 |
| `--agent NAME` | | 指定 Agent 名称 |
| `--host HOST` | | Web 服务器地址（默认：0.0.0.0） |
| `--port PORT` | | Web 服务器端口（默认：8000） |
| `--list` | | 列出所有 Agent |

## API 端点

### Agent 管理

- `GET /api/agents` - 列出所有 Agent
- `GET /api/agents/{agent_id}` - 获取 Agent 详情
- `GET /api/agents/{agent_id}/config` - 获取 Agent 配置

### 聊天

- `POST /api/agents/{agent_id}/chat` - 非流式聊天
- `POST /api/agents/{agent_id}/chat/stream` - 流式聊天（SSE）
- `GET /api/agents/{agent_id}/sessions` - 列出会话
- `GET /api/agents/{agent_id}/sessions/{session_id}` - 获取会话详情

### 健康检查

- `GET /health` - 服务健康状态

## 前端开发

### 安装依赖

```bash
cd src/server/frontend
npm install
```

### 开发模式

```bash
npm run dev
```

Vite 开发服务器会在 http://localhost:5173 启动，自动代理 API 请求到后端。

### 构建生产版本

```bash
npm run build
```

构建产物输出到 `dist/` 目录，由 FastAPI 静态文件服务提供。

## 环境变量

```bash
# OpenAI 配置
OPENAI_API_KEY=sk-...              # API 密钥
OPENAI_API_BASE=https://api.openai.com/v1  # API 地址（可选）
OPENAI_MODEL=gpt-4o-mini           # 模型名称（可选）
```

## 示例脚本

完整示例参考 `examples/server_demo.py`：

```bash
# Web 模式
python examples/server_demo.py --web

# 交互式模式
python examples/server_demo.py --interactive

# 单次提示
python examples/server_demo.py --prompt "你好"

# 列出 Agent
python examples/server_demo.py --list
```

## VS Code 调试配置

`.vscode/launch.json` 已配置好四种调试模式：

1. **PStock Server: Web Mode** - Web 服务器调试
2. **PStock Server: Interactive Mode** - 交互式模式调试
3. **PStock Server: Prompt Mode** - 单次提示模式调试
4. **PStock Server: List Agents** - 列出 Agent 调试

按 `F5` 或使用调试面板选择配置启动。

## 会话管理

### 交互式模式会话

交互式模式自动维护对话历史：

```python
context = AgentContext(history_messages=[])

# 每轮对话后自动添加到历史
context.history_messages.append(ChatMessage(role="user", content=user_input))
context.history_messages.append(ChatMessage(role="assistant", content=result.output))
```

### Web 模式会话

Web 模式使用会话 ID 维护对话状态：

```python
# 首次请求
POST /api/agents/{agent_id}/chat
{
  "message": "你好"
}
# 返回 session_id

# 后续请求携带 session_id
POST /api/agents/{agent_id}/chat
{
  "message": "怎么样？",
  "session_id": "xxx"
}
```

## 流式响应

使用 Server-Sent Events (SSE) 实现流式输出：

```typescript
// 前端示例
chatApi.streamChat(
  agentId,
  { message: "你好", stream: true },
  (event) => {
    if (event.type === 'step') {
      console.log('执行步骤:', event.step);
    } else if (event.type === 'final') {
      console.log('最终响应:', event.content);
    }
  }
);
```

## 扩展

### 添加自定义 API 端点

在 `routes/` 目录下创建新模块：

```python
# routes/custom.py
from fastapi import APIRouter
from ..registry import registry

router = APIRouter(prefix="/api/custom", tags=["custom"])

@router.get("/stats")
async def get_stats():
    agents = registry.list_all()
    return {"count": len(agents)}
```

在 `server.py` 中注册：

```python
from .routes import custom

app.include_router(custom.router)
```

### 添加自定义前端页面

1. 在 `frontend/src/pages/` 创建新组件
2. 在 `App.tsx` 中添加路由
3. 运行 `npm run build` 重新构建前端

## 故障排查

### 前端不显示

```bash
# 检查 dist 目录是否存在
ls src/server/frontend/dist

# 如果不存在，重新构建
cd src/server/frontend
npm run build
```

### Agent 未注册

```bash
# 列出所有已注册的 Agent
python -m server --list
```

### API 请求失败

检查后端日志，确认：
1. Agent 已正确注册
2. LLM 配置正确（API Key、Model 等）
3. 网络连接正常

## 最佳实践

1. **使用环境变量配置**：避免硬编码 API Key 和 Model
2. **错误处理**：在生产环境添加完善的错误处理
3. **日志记录**：使用 `loguru` 记录关键操作
4. **会话持久化**：考虑将会话数据保存到 Redis 或数据库
5. **流式响应**：长时间任务使用流式响应提升用户体验

## 许可证

MIT
