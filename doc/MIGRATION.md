# TypeScript → Python 迁移指南

本文档说明如何将 TypeScript PStock SDK 代码迁移到 Python 版本。

## 核心映射关系

### 类型系统

| TypeScript | Python |
|------------|--------|
| `interface` | `TypedDict` / `dataclass` / `Protocol` |
| `type` | `TypeAlias` |
| `enum` | `str` / `Enum` |
| `any` | `Any` |
| `unknown` | `Any` |
| `void` | `None` |
| `Promise<T>` | `Coroutine[Any, Any, T]` / `await T` |
| `T \| null` | `T \| None` |
| `Array<T>` | `list[T]` |
| `Record<K, V>` | `dict[K, V]` |

### 异步处理

```typescript
// TypeScript
async function run(): Promise<string> {
  const result = await llm.chat(messages);
  return result.message.content || "";
}
```

```python
# Python
async def run() -> str:
    result = await llm.chat(messages)
    return result["message"].get("content") or ""
```

### 类定义

```typescript
// TypeScript
class Agent {
  private readonly llm: LLM;
  private initialized = false;

  constructor(options: AgentOptions) {
    this.llm = options.llm;
  }

  async run(task: string): Promise<AgentRunResult> {
    await this.ensureInitialized();
    // ...
  }
}
```

```python
# Python
class Agent:
    def __init__(self, options: AgentOptions):
        self._llm = options.llm
        self._initialized = False

    async def run(self, task: str) -> AgentRunResult:
        await self._ensure_initialized()
        # ...
```

### 接口和协议

```typescript
// TypeScript - interface
export interface Tool {
  name: string;
  description: string;
  execute(input: unknown): Promise<string>;
}
```

```python
# Python - Protocol
from typing import Protocol, Any

class Tool(Protocol):
    @property
    def name(self) -> str: ...

    @property
    def description(self) -> str: ...

    async def execute(self, input: Any) -> str: ...
```

### 字典操作

```typescript
// TypeScript
const config = { name: "test", value: 42 };
const name = config.name;
const keys = Object.keys(config);
```

```python
# Python
config = {"name": "test", "value": 42}
name = config["name"]
keys = config.keys()
```

### 可选链和空值合并

```typescript
// TypeScript
const value = obj?.property ?? "default";
```

```python
# Python
value = obj.get("property") if obj else None
value = value or "default"
```

## 库映射

### HTTP 请求

```typescript
// TypeScript - fetch
const response = await fetch(url, {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify(payload),
});
const data = await response.json();
```

```python
# Python - httpx
import httpx

async with httpx.AsyncClient() as client:
    response = await client.post(
        url,
        json=payload,
        headers={"Content-Type": "application/json"},
    )
    data = response.json()
```

### 文件操作

```typescript
// TypeScript - fs
import fs from 'node:fs/promises';
const content = await fs.readFile(path, 'utf-8');
await fs.writeFile(path, content, 'utf-8');
```

```python
# Python - pathlib
from pathlib import Path
import asyncio

content = await asyncio.to_thread(Path(path).read_text, encoding="utf-8")
await asyncio.to_thread(Path(path).write_text, content, encoding="utf-8")
```

### JSON 和 YAML

```typescript
// TypeScript
import YAML from 'yaml';
const config = YAML.parse(content);
const output = JSON.stringify(data, null, 2);
```

```python
# Python
import yaml
import json

config = yaml.safe_load(content)
output = json.dumps(data, indent=2)
```

### 日志

```typescript
// TypeScript - winston
import { logger } from './utils/logger';
logger.info('Message', { meta: 'data' });
```

```python
# Python - loguru
from loguru import logger
logger.info("Message", extra={"meta": "data"})
```

### Glob 和文件匹配

```typescript
// TypeScript - glob/minimatch
import { glob } from 'glob';
import { minimatch } from 'minimatch';
const files = await.glob('**/*.ts', { cwd: dir });
```

```python
# Python - glob/fnmatch
from glob import glob
import fnmatch

files = glob('**/*.ts', root_dir=dir, recursive=True)
```

## 命名约定

### 变量和函数

- TypeScript: `camelCase`
- Python: `snake_case`

```typescript
// TypeScript
const workspaceRoot = process.cwd();
function getWorkspaceRoot(): string { ... }
```

```python
# Python
workspace_root = os.getcwd()
def get_workspace_root() -> str: ...
```

### 类

- TypeScript: `PascalCase`
- Python: `PascalCase` (相同)

```typescript
// TypeScript
class AgentRuntime { ... }
```

```python
# Python
class AgentRuntime: ...
```

### 常量

- TypeScript: `UPPER_SNAKE_CASE`
- Python: `UPPER_SNAKE_CASE` (相同)

### 私有成员

```typescript
// TypeScript
private readonly llm: LLM;
private _initialized = false;
```

```python
# Python
self._llm: LLM
self._initialized = False
```

## 错误处理

```typescript
// TypeScript
try {
  await tool.execute(args);
} catch (error) {
  const message = error instanceof Error ? error.message : String(error);
  console.error(`Error: ${message}`);
}
```

```python
# Python
try:
    await tool.execute(args)
except Exception as e:
    message = str(e)
    print(f"Error: {message}")
```

## 环境变量

```typescript
// TypeScript
const apiKey = process.env.OPENAI_API_KEY;
```

```python
# Python
import os

api_key = os.getenv("OPENAI_API_KEY")
# 或使用 python-dotenv
from dotenv import load_dotenv
load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")
```

## 包和导入

```typescript
// TypeScript
import { Agent, AgentBuilder } from './agent/core/Agent';
import type { Tool } from './agent/core/interfaces';
```

```python
# Python
from .agent.core.agent import Agent, AgentBuilder
from .agent.core.interfaces import Tool
