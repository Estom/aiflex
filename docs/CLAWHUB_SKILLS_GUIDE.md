# 如何在 AI Flex 智能体中集成 ClawHub Skills

## 📚 概述

AI Flex 框架支持从外部加载 Skills，ClawHub 是一个 Skills 仓库。本指南展示如何：

1. 使用 ClawHub 安装 Skills
2. 在特定智能体中集成这些 Skills
3. 使用 Skills 增强智能体能力

---

## 🔧 第一步：安装 Skills

### 使用 ClawHub 安装

```bash
# 安装单个技能
clawhub install novel-generator

# 安装特定版本
clawhub install novel-generator --version 1.0.0

# 强制覆盖安装
clawhub install novel-generator --force
```

### 默认安装位置

Skills 默认安装在：
```
~/.openclaw/workspace/skills/<skill-name>/
```

例如：
```
~/.openclaw/workspace/skills/novel-generator/
~/.openclaw/workspace/skills/xianxia-novel/
~/.openclaw/workspace/skills/github/
```

---

## 🎯 第二步：在智能体中集成 Skills

### 方式 1：使用 `with_skill_sources()`（推荐）

```python
from sdk.agent.core.agent import AgentBuilder
from sdk.agent.llm.openai_llm import OpenAILLM, OpenAIModelOptions
import os

from dotenv import load_dotenv

load_dotenv()

llm = OpenAILLM(
    api_key=os.getenv("OPENAI_API_KEY"),
    options=OpenAIModelOptions(
        model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        temperature=0.7,
    ),
)

agent = (
    AgentBuilder()
    .with_name("novelist-with-skill")
    .with_description("带有 novel-generator skill 的作家智能体")
    .with_llm(llm)
    .with_max_steps(10)
    .with_skill_sources([
        # 方式 1：单个 SKILL.md 文件
        "/home/estom/.openclaw/workspace/skills/novel-generator/SKILL.md",

        # 方式 2：包含 SKILL.md 的目录
        "/home/estom/.openclaw/workspace/skills/novel-generator",

        # 方式 3：包含多个技能的父目录（自动扫描子目录）
        "/home/estom/.openclaw/workspace/skills",

        # 方式 4：相对路径（相对于 workspace_root）
        "skills/",  # 需要设置 workspace_root
        "../novel-generator",
    ])
    .with_workspace_root("/home/estom/work/aiflex/examples/workspace")
    .build()
)
```

### 方式 2：使用 `with_skills()`（直接传入 Skill 对象）

```python
from sdk.agent.core.interfaces import Skill

skill = Skill(
    name="novel-generator",
    description="中文爽文小说生成技能",
    content="完整的 SKILL.md 内容字符串..."
)

agent = (
    AgentBuilder()
    .with_name("novelist")
    .with_description("作家智能体")
    .with_llm(llm)
    .with_skills([skill])  # 直接传入 Skill 对象
    .build()
)
```

---

## 📂 Skill 路径说明

### 绝对路径

```python
.with_skill_sources([
    "/home/estom/.openclaw/workspace/skills/novel-generator/SKILL.md",
])
```

### 相对路径（相对于 workspace_root）

```python
agent = (
    AgentBuilder()
    .with_workspace_root("/home/estom/work/aiflex/examples/workspace")
    .with_skill_sources([
        # 相对于 workspace_root 解析
        "skills/novel-generator",
        "../skills/novel-generator",
    ])
    .build()
)
```

### 批量加载多个 Skills

```python
agent = (
    AgentBuilder()
    .with_skill_sources([
        # 方式 1：逐个指定
        "/home/estom/.openclaw/workspace/skills/novel-generator",
        "/home/estom/.openclaw/workspace/skills/xianxia-novel",
        "/home/estom/.openclaw/workspace/skills/github",

        # 方式 2：一次性加载所有技能
        "/home/estom/.openclaw/workspace/skills",
    ])
    .build()
)
```

---

## 🎨 完整示例：增强的作家智能体

### 示例 1：集成 novel-generator skill

```python
#!/usr/bin/env python
"""
增强的作家智能体 - 集成 novel-generator skill
"""

import os
from dotenv import load_dotenv

from sdk.agent.core.agent import AgentBuilder
from sdk.agent.llm.openai_llm import OpenAILLM, OpenAIModelOptions

load_dotenv()

llm = OpenAILLM(
    api_key=os.getenv("OPENAI_API_KEY"),
    options=OpenAIModelOptions(
        model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        temperature=0.8,
    ),
)

# 安装 skill 的路径
skill_path = "/home/estom/.openclaw/workspace/skills/novel-generator/SKILL.md"

agent = (
    AgentBuilder()
    .with_name("novelist-enhanced")
    .with_description("增强版作家智能体，集成 novel-generator skill")
    .with_llm(llm)
    .with_max_steps(15)

    # 集成 Skills
    .with_skill_sources([skill_path])

    # 系统指令
    .with_instructions("""
你是一位专业小说作家，使用 novel-generator skill 来辅助创作。

创作流程：
1. 根据用户提供的方向，规划小说世界观和角色
2. 生成章节大纲，确保每章都有明确的爽点
3. 使用 skill 中的创作指南，确保质量
4. 维护角色、情节的连续性
5. 记录创作失败场景，持续优化

重点：
- 爽点密集，每章 2-3 个小爽点
- 结尾设置悬念钩子
- 角色性格鲜明
- 情节流畅自然
""")

    .with_workspace_root("/home/estom/work/aiflex/examples/workspace")
    .build()
)

# 运行智能体
import asyncio

asyncio.run(agent.run_async(
    "写一个修仙重生小说，主角前世是天界仙尊，"
    "重生到凡间小山村，重新踏上修仙之路。"
))
```

### 示例 2：集成多个 Skills

```python
#!/usr/bin/env python
"""
多技能智能体 - 集成多个 Skills
"""

llm = OpenAILLM(
    api_key=os.getenv("OPENAI_API_KEY"),
    options=OpenAIModelOptions(model="gpt-4o-mini"),
)

agent = (
    AgentBuilder()
    .with_name("multi-skill-agent")
    .with_description("集成多个技能的智能体")
    .with_llm(llm)
    .with_max_steps(20)

    # 集成多个 Skills
    .with_skill_sources([
        "/home/estom/.openclaw/workspace/skills/novel-generator",
        "/home/estom/.openclaw/workspace/skills/github",
        "/home/estom/.openclaw/workspace/skills/multi-search-engine",
    ])

    .with_instructions("""
你是一个多功能智能助手，具备以下能力：

1. 小说创作（novel-generator skill）
   - 创作中文爽文小说
   - 支持多种题材
   - 自动生成世界观和角色

2. GitHub 管理（github skill）
   - 查询仓库和 PR
   - 创建和管理 Issues
   - 自动化工作流

3. 信息搜索（multi-search-engine skill）
   - 17 个搜索引擎
   - 支持高级搜索语法
   - 无需 API key

根据用户需求，选择合适的 skill 完成任务。
""")

    .with_workspace_root("/home/estom/work/aiflex/examples/workspace")
    .build()
)
```

---

## 🔍 验证 Skills 是否加载成功

### 查看已加载的 Skills

```python
# 构建智能体
agent = builder.build()

# 查看技能注册表
skills = agent.skill_registry.list_all()

print("已加载的 Skills：")
for skill in skills:
    print(f"  - {skill['name']}: {skill['description']}")
```

### 输出示例

```
已加载的 Skills：
  - novel-generator: 中文爽文小说生成技能
  - github: GitHub 仓库管理和 PR 操作
  - multi-search-engine: 多搜索引擎集成
```

---

## 🛠️ 技能加载流程

```
1. ClawHub 安装
   ↓
2. Skill 文件下载到 ~/.openclaw/workspace/skills/
   ↓
3. AgentBuilder.with_skill_sources([path])
   ↓
4. SkillLoader 解析 SKILL.md
   ↓
5. 注册到 SkillRegistry
   ↓
6. 智能体运行时自动使用
```

---

## ⚙️ Skill 路径类型

| 路径类型 | 示例 | 说明 |
|---------|------|------|
| **SKILL.md 文件** | `/path/to/SKILL.md` | 直接指定文件 |
| **包含 SKILL.md 的目录** | `/path/to/novel-generator/` | 自动查找 SKILL.md |
| **包含多个技能的父目录** | `/path/to/skills/` | 自动扫描子目录 |
| **相对路径** | `skills/novel-generator/` | 相对于 workspace_root |

---

## 🎯 最佳实践

### 1. 组织 Skills 目录

```
aiflex/
├── examples/
│   ├── skills/           # 项目专用 skills
│   │   ├── my-novel-skill/SKILL.md
│   │   └── custom-tool/SKILL.md
│   └── workspace/
└── src/
```

### 2. 使用相对路径

```python
agent = (
    AgentBuilder()
    .with_workspace_root("/home/estom/work/aiflex/examples")
    .with_skill_sources([
        "skills/my-novel-skill",    # 相对路径
        "skills/custom-tool",
        "../../.openclaw/workspace/skills/novel-generator",  # 相对跳转
    ])
    .build()
)
```

### 3. 批量加载

```python
# 推荐：一次加载所有技能
agent = (
    AgentBuilder()
    .with_skill_sources([
        "~/.openclaw/workspace/skills",  # ClawHub 安装的技能
        "/home/estom/work/aiflex/examples/skills",  # 项目专用技能
    ])
    .build()
)
```

---

## 🐛 常见问题

### Q1: Skill 未找到

**问题**: 提示 `Skill source does not exist`

**解决**:
1. 检查路径是否正确
2. 使用绝对路径而不是相对路径
3. 确认 SKILL.md 文件存在

```python
# 调试：打印解析后的路径
from pathlib import Path

skill_path = Path(skill_source).expanduser()
print(f"Skill path: {skill_path}")
print(f"Exists: {skill_path.exists()}")
```

### Q2: Skill 解析失败

**问题**: SKILL.md 格式错误

**解决**:
1. 确认 YAML frontmatter 格式正确
2. 检查是否包含 `name` 和 `description` 字段

```yaml
---
name: my-skill
description: 我的技能描述
---
```

### Q3: Skill 未生效

**问题**: 智能体没有使用 skill

**解决**:
1. 检查 skill 是否已注册
2. 在系统指令中明确要求使用 skill
3. 确认 skill 的描述足够详细

---

## 📚 相关资源

- [AI Flex SDK 文档](../../src/sdk/README.md)
- [AgentBuilder 文档](../../src/sdk/agent/core/agent.py)
- [Skill 文档](../../src/framework/loader/skill_loader.py)
- [ClawHub 技能仓库](https://clawhub.com)

---

**开始集成 Skills，增强你的智能体吧！** 🚀
