# OpenClaw Skills 管理完整指南

## 📚 文档来源

1. npm 包文档：`~/.nvm/versions/node/v22.18.0/lib/node_modules/openclaw/README.md`
2. 官方文档：https://docs.openclaw.ai
3. 本地配置：`~/.openclaw/openclaw.json`

---

## 🎯 核心概念总结

### Skills 是共享的（不是每个 agent 独立）

根据官方文档和实际配置：

```bash
# Skills 的加载顺序（从最低到最高优先级）

1. managed/workspace skills  # 主 workspace 的 skills/
2. skills.load.extraDirs         # 额外的 skills 目录（最低优先级）
3. bundled skills               # 内置 skills（最高优先级）
```

**关键结论**：
- ✅ **Skills 不是每个 agent 独立的**
- ✅ **Skills 是共享的，存储在主 workspace 的 skills/ 目录**
- ✅ **每个 agent 都可以访问相同的 skills**

---

## 📁 目录结构

```
~/.openclaw/
├── workspace/                     # main agent 的 workspace（默认）
│   ├── skills/                    # ⭐ 所有 agents 共享的 skills
│   │   ├── novel-generator/
│   │   ├── github/
│   │   └── ...
│   ├── AGENTS.md
│   ├── SOUL.md
│   └── ...
│
├── workspace-butler/            # butler agent 的 workspace
│   ├── agent/
│   ├── memory/
│   └── ...
│   └── skills/                  # ❌ 不存在（skills 是共享的）
│
├── workspace-coder/             # coder agent 的 workspace
│   ├── agent/
│   ├── memory/
│   └── ...
│   └── skills/                  # ❌ 不存在（skills 是共享的）
│
├── workspace-trader/            # trader agent 的 workspace
│   ├── agent/
│   ├── memory/
│   └── ...
│   └── skills/                  # ❌ 不存在（skills 是共享的）
│
└── workspace-scout/             # scout agent 的 workspace
    ├── agent/
    ├── memory/
    └── ...
    └── skills/                  # ❌ 不存在（skills 是共享的）
```

---

## 🔧 配置文件解析

### 1. Skills 配置（`skills` 部分）

```json5
{
  "skills": {
    "allowBundled": ["gemini", "peekaboo"],  // 允许的内置 skills
    "load": {
      "extraDirs": [                   // 额外的 skills 目录
        "~/Projects/agent-scripts/skills",
        "~/Projects/oss/some-skill-pack/skills"
      ],
      "watch": true,                  // 监控 skills 变化
      "watchDebounceMs": 250,        // 防抖时间
    },
    "install": {
      "preferBrew": true,           // 使用 brew 安装器
      "nodeManager": "npm"          // npm | pnpm | yarn | bun
    },
    "entries": {
      "image-lab": {                // 技能特定配置
        "enabled": true,
        "apiKey": { source: "env", provider: "default", id: "GEMINI_API_KEY" }
      },
      "peekaboo": { enabled: true },
      "sag": { enabled: false }
    }
  }
}
```

**关键点**：
- `skills.load.extraDirs` 可以指定额外的 skills 目录（最低优先级）
- 没有"每个 agent 的 skills 目录"这个概念

---

### 2. Agents 配置（`agents.list` 部分）

```json5
{
  "agents": {
    "defaults": {
      "workspace": "/home/estom/.openclaw/workspace",  // ⭐ 默认 workspace
      "model": { "primary": "zai/glm-4.7" }
    },
    "list": [
      {
        "id": "main",
        "name": "main agent",
        "subagents": {
          "allowAgents": ["butler", "coder", "trader", "scout"]
        }
      },
      {
        "id": "butler",
        "name": "butler",
        "workspace": "/home/estom/.openclaw/workspace-butler",  // ⭐ 独立 workspace
        "agentDir": "/home/estom/.openclaw/agents/butler/agent",
        "subagents": { "allowAgents": [] }
      },
      {
        "id": "coder",
        "name": "coder",
        "workspace": "/home/estom/.openclaw/workspace-coder",  // ⭐ 独立 workspace
        "agentDir": "/home/estom/.openclaw/agents/coder/agent",
        "subagents": { "allowAgents": [] }
      },
      {
        "id": "trader",
        "name": "trader",
        "workspace": "/home/estom/.openclaw/workspace-trader",  // ⭐ 独立 workspace
        "agentDir": "/home/estom/.openclaw/agents/trader/agent",
        "subagents": { "allowAgents": [] }
      },
      {
        "id": "scout",
        "name": "scout",
        "workspace": "/home/estom/.openclaw/workspace-scout",  // ⭐ 独立 workspace
        "agentDir": "/home/estom/.openclaw/agents/scout/agent",
        "subagents": { "allowAgents": [] }
      }
    ]
  }
}
```

**关键点**：
- 每个 agent 都有独立的 workspace
- 每个 agent 都可以访问主 workspace 的 skills

---

## 🚀 正确的 Skills 安装方式

### 方式 1：安装到主 workspace（推荐）

```bash
# 1. 进入主 workspace
cd ~/.openclaw/workspace

# 2. 使用 ClawHub 安装 skills
clawhub install novel-generator
clawhub install github
clawhub install weather

# 3. 所有 agents 都可以访问这些 skills
```

**说明**：
- ✅ **一次安装，所有 agents 共享**
- ✅ **推荐方式**：skills 在主 workspace 的 skills/ 目录
- ✅ **所有 agents**（main、butler、coder、trader、scout）都可以使用

---

### 方式 2：使用 extraDirs 指定额外目录

```bash
# 编辑 ~/.openclaw/openclaw.json
vim ~/.openclaw/openclaw.json

# 添加 extraDirs
{
  "skills": {
    "load": {
      "extraDirs": [
        "~/Projects/agent-scripts/skills",
        "~/Projects/oss/some-skill-pack/skills"
      ]
    }
  }
}
```

**说明**：
- ✅ 可以指定多个额外的 skills 目录
- ✅ extraDirs 有最低优先级
- ✅ 适用于所有 agents

---

### 方式 3：为特定 agent 配置 skills

虽然 skills 是共享的，但可以通过配置让特定 agent 使用特定 skills：

```json5
{
  "agents": {
    "list": [
      {
        "id": "trader",
        "name": "trader",
        "workspace": "/home/estom/.openclaw/workspace-trader",
        // ⭐ 这里可以配置 trader 专用的文件
        // 但 skills 仍然从主 workspace 的 skills/ 加载
      }
    ]
  },
  "skills": {
    "load": {
      "extraDirs": [
        "/home/estom/.openclaw/workspace-trader/skills"  // ⭐ trader 专用的 skills
      ]
    }
  }
}
```

---

## 📊 Skills 优先级

| 优先级 | 来源 | 说明 |
|---------|------|------|
| **1（最高）** | bundled skills | 内置 skills（gemini、peekaboo 等） |
| **2** | managed/workspace skills | 主 workspace 的 skills/ 目录 |
| **3（最低）** | extraDirs | 额外的 skills 目录 |

**加载顺序**：
```
bundled skills → workspace/skills/ → extraDirs/
```

---

## 🎯 推荐实践

### 最佳实践：所有 agents 共享 skills

```bash
# 1. 在主 workspace 安装所有 skills
cd ~/.openclaw/workspace/skills/
clawhub install novel-generator
clawhub install github
clawhub install weather
clawhub install multi-search-engine

# 2. 所有 agents 都可以使用这些 skills
# main、butler、coder、trader、scout 都可以访问
```

**优点**：
- ✅ 避免重复安装
- ✅ 统一管理和更新
- ✅ 节省磁盘空间
- ✅ 方便维护

---

### 备选实践：为特定 agent 添加专用 skills

如果某个 agent 需要专用的 skills：

```bash
# 1. 创建 agent 专用的 skills 目录
mkdir -p ~/.openclaw/workspace-trader/skills

# 2. 将 skills 复制到该目录
cp -r /path/to/skill ~/.openclaw/workspace-trader/skills/

# 3. 在 openclaw.json 中配置 extraDirs
```

```json5
{
  "skills": {
    "load": {
      "extraDirs": [
        "~/.openclaw/workspace-trader/skills"  // trader 专用
      ]
    }
  }
}
```

---

## 🛠️ 常见问题

### Q1: 我为 butler agent 安装了 skill，但 coder agent 也能用吗？

**A**: 是的！Skills 是共享的，所有 agents 都可以访问。

---

### Q2: 如何让某个 agent 不能使用某个 skill？

**A**: 使用 `skills.allowBundled` 和 `skills.entries`：

```json5
{
  "skills": {
    "allowBundled": ["gemini"],  // 只允许这个内置 skill
    "entries": {
      "novel-generator": { enabled: false }  // 禁用 novel-generator
    }
  }
}
```

---

### Q3: 如何为所有 agents 安装 skills？

**A**: 使用 `extraDirs` 或直接安装到主 workspace：

```bash
# 方法 1：直接安装
cd ~/.openclaw/workspace/skills/
clawhub install novel-generator

# 方法 2：使用 extraDirs
# 在 openclaw.json 中配置
{
  "skills": {
    "load": {
      "extraDirs": ["~/Projects/my-skills"]
    }
  }
}
```

---

## 📝 总结

| 概念 | 说明 |
|------|------|
| **Skills 位置** | `~/.openclaw/workspace/skills/`（默认） |
| **Skills 共享** | ✅ 所有 agents 共享相同的 skills |
| **Skills 优先级** | bundled > workspace/skills > extraDirs |
| **Agents Workspace** | 每个 agent 都有独立的 workspace |
| **推荐做法** | 在主 workspace 安装 skills，所有 agents 共享 |

---

## 🔗 参考资料

- [OpenClaw 官方文档](https://docs.openclaw.ai)
- [Skills 配置文档](https://docs.openclaw.ai/tools/skills-config)
- [Session 管理文档](https://docs.openclaw.ai/concepts/session)
- [ClawHub](https://clawhub.com)

---

**核心结论：Skills 应该放在 main agent 的 workspace（`~/.openclaw/workspace/skills/`），所有 agents 都可以共享使用！** 🎯
