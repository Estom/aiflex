

# ⭐ 声明式 Agent 框架 — 详细设计

新增一个与pstock_sdk并列的包pstock_framework,实现这个设计。


---

## 🧱 一、Agent 声明与目录规范

---

### 1. Agent 项目根目录结构

```
agents/                    # 根扫描路径
├── agent_name/
│   ├── agent.json         # Agent 元信息 (声明式配置)
│   ├── prompt.md          # 主 Prompt 文本
│   ├── skills/            # Claude Skills 模块
│   │   ├── my_skill/
│   │   │   ├── SKILL.md
│   │   │   └── ...        # 可选脚本/模板
│   ├── tools/             # 工具代码模块 (LangChain 工具)
│   │   ├── data_processing.py
│   │   └── ...
│   ├── subagents/         # 子 Agent 目录（递归）
│   ├── memory/            # 可选: Memory 配置
│   ├── policies/          # 可选: 决策策略
│   └── tests/             # 可选: 测试用例
```

---

### 2. agent.json (核心元信息)

使用 JSON 多一个好处是更易于程序化解析，比 YAML 的缩进更不易误读。

```jsonc
{
  "name": "financial_analyst",
  "version": "0.1.0",
  "description": "金融分析专家 Agent",

  "model": {
    "provider": "anthropic",
    "id": "claude-3.5-sonnet",
    "temperature": 0.2,
    "max_tokens": 4096
  },

  "prompt": { "file": "prompt.md" },

  "skills": {
    "enabled": true,
    "path": "skills"
  },

  "tools": {
    "enabled": true,
    "path": "tools"
  },

  "subagents": {
    "enabled": true,
    "path": "subagents"
  },

  "runtime": {
    "timeout": "60s",
    "max_iterations": 5
  }
}
```

✅ 目的：统一 Agent 词义、校验字段强约束、便于版本管理

---

## 🧠 二、Prompt 加载规范

设计原则：

* 主 Prompt 用于定义 Agent 的核心角色、目标和输出格式；
* 支持可替换标记、template 语法；
* 框架加载时优先读取 agent.json 中定义的 prompt.md 路径，并注入 runtime 环境。

---

## 🛠️ 三、Claude Skills 规范与解析

这是新版框架重要更新部分。

---

### 1. Skills 的设计意义

Claude Skills 是一种 **可复用、可被模型自动识别触发的模块化能力描述**。它不仅是 markdown 文档，也可包含脚本、示例和资源。它的存在可以帮助 Agent 在遇到某些任务时，自主选择并加载对应的执行逻辑。([Claude 开发平台][2])

---

### 2. Skills 核心结构与文件规范

每个 Skill 必须以一个目录组织，入口是 **SKILL.md** 文件，同时支持可选辅助文件（脚本、参考文档等）。([Claude API Docs][1])

📌 示例：

```
my_skill/
├── SKILL.md
├── reference.md      # 可选
├── examples.md       # 可选
├── scripts/          # 可选
│   └── analyzer.py
├── templates/        # 可选
│   └── prompt.txt
```

---

### 3. SKILL.md 格式规范

**前置 YAML 元数据 + Markdown 正文**

#### 必需字段：

```markdown
---
name: my-skill-name
description: 简要说明该 Skill 的用途和触发条件
# 可选: allowed-tools: ["Read","Grep"]
---

# Skill 主标题

## Instructions
明确、操作性强的步骤性指导 Claude 如何完成任务

## Examples
举例说明输入输出或使用方式
```

---

### 4. 字段定义细则

| 字段             | 描述              | 约束                                  |
| -------------- | --------------- | ----------------------------------- |
| name           | Skill 唯一标识名     | 小写字母/数字/连字符，不含 XML 标签，不含保留词，≤ 64 字符 |
| description    | Skill 功能 + 何时触发 | 必需，不能超 1024 字符                      |
| allowed-tools* | 可选，限制可访问工具      | 若指定则仅这些工具可用于 Skill 运行               |

* 特性主要用于 Claude Code 场景下的安全控制。([Claude API Docs][3])

---

### 5. Claude Skills 触发与使用流程

1. Agent Runtime 加载所有 Skill 元数据（name & description）；
2. 当 Agent 执行对话或任务时 LLM 会根据请求文本自动匹配可能相关 Skill；
3. 若匹配，则载入 Skill 的 `Instructions` 和相关资源；
4. 在二级上下文中执行 Skill 指令或触发内含脚本。([Claude 开发平台][2])

> 注意：Skill 并不是像函数调用那样 *必然执行*，而是依据模型判断“是否相关”再被加载。

---

### 6. Skill 的辅助文件

辅助文件不会被立即加载，而是 Skill 被触发后由 Claude 逐步按需读取，这样可以优化上下文窗口与令牌成本。([Claude 开发平台][2])

---

## 🔌 四、工具 (Tools) 子系统

---

### 1. 目录规范

```
tools/
├── data_processing.py
├── market_data.py
```

---

### 2. 自动发现规则

框架扫描 tools 目录下 `.py` 文件，自动 import 并识别 `@tool` 装饰过的函数（或遵循固定 class 规范）注册为可调用工具。

---

### 3. 工具定义样例

```python
from langchain.tools import tool

@tool
def get_stock_price(symbol: str) -> float:
    """获取实时股价"""
    ...
```

⚙️ 调用层面框架负责把 Tool 注册到 Agents SDK 环境中（如 LangChain AgentTool 格式）

---

## 🤖 五、SubAgents (递归 Agent)

---

### 1. SubAgents 声明

在主 agent.json 中：

```json
"subagents": {
  "enabled": true,
  "path": "subagents"
}
```

子 Agent 目录结构同主 Agent，一样包含 `agent.json` + prompt.json + skills/tools/subagents。

---

### 2. SubAgent 调用模式

支持三种运行模式：

| 模式   | 说明                       |
| ---- | ------------------------ |
| 顺序执行 | 依次运行子 Agent，父 Agent 汇总结果 |
| 并行执行 | 多子 Agent 同时执行            |
| 条件触发 | 根据任务推荐只调用相关 SubAgent     |

---

## 🚀 六、框架加载器 & 运行时

---

### 1. Loader 工作流程

```python
for agent_root in AGENTS_ROOT:
    check agent_root/agent.json
    parse json → config
    load prompt.md
    walk skills/ → parse SKILL.md
    walk tools/ → import & register
    walk subagents/ →递归加载 Loader
    registry.register(agent_def)
```

---

### 2. Registry 管理

统一管理 Agent、Skill 和 Tool 的元数据，提供运行时索引与查找。

---

## 🎯 七、扩展能力

---

### 1. Memory 配置

在 agent.json 中声明：

```json
"memory": {
  "type":"vector",
  "backend":"chroma"
}
```

框架统一注入到 Agent runtime

---

### 2. Planner / Policy

在 agent.json 中补充策略配置：

```json
"policies":{
  "type":"react"
}
```

---

## 🧪 八、校验规则与错误处理

| 场景              | 行为              |
| --------------- | --------------- |
| agent.json 缺失   | 加载失败            |
| prompt.md 无效    | 报错              |
| Skill YAML 格式错误 | SKILL 禁用 + 日志提示 |
| Tool 导入报错       | 单个工具禁用，不阻断全局    |
| 子 Agent 循环引用    | 报错              |
| Skill name 冲突   | 特别提示            |

---
