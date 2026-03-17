# 作家智能体 - Novelist Agent

专业的小说创作 AI 智能体，支持多种题材的爽文创作。

---

## ✨ 功能特性

- 🎨 **自动生成世界观**：根据题材自动构建完整的世界观设定
- 👥 **角色设计**：智能生成主要角色（主角、配角、反派）
- 📚 **分章节创作**：每章 2000-3000 字，层层递进
- 🔥 **爽点布局**：自动设计小爽点、中爽点、大爽点
- 🧠 **记忆系统**：记录角色、情节、世界观，保持一致性
- 📝 **章节大纲**：自动生成章节写作大纲
- 🎭 **多题材支持**：都市、修仙、玄幻、重生、系统流、末世、科幻、游戏

---

## 🎯 支持的题材

| 题材 | 特点 |
|------|------|
| **都市** | 现代背景，系统/重生，商业权谋 |
| **修仙** | 修炼体系，境界提升，机缘宝物 |
| **玄幻** | 异界冒险，魔法斗气，种族战争 |
| **重生** | 带着前世记忆，改变遗憾 |
| **系统流** | 觉醒系统，任务奖励，技能加点 |
| **末世** | 末日生存，丧尸变异，人性考验 |
| **科幻** | 未来科技，星际战争，宇宙探索 |
| **游戏** | 游戏异界，升级打怪，装备收集 |

---

## 🚀 快速开始

### 1. 安装依赖

```bash
cd /home/estom/work/aiflex
pip install -e .
```

### 2. 配置环境变量

创建 `.env` 文件：

```bash
OPENAI_API_KEY=sk-your-api-key
OPENAI_MODEL=gpt-4o-mini
OPENAI_API_BASE=https://api.openai.com/v1
AI_FLEX_WORKSPACE=/home/estom/work/aiflex/examples/workspace
```

### 3. 运行智能体

```bash
# 运行默认（都市题材）
python src/agents/novelist/agent.py

# 运行指定题材
python src/agents/novelist/agent.py 修仙
python src/agents/novelist/agent.py 重生
python src/agents/novelist/agent.py 系统流
```

---

## 💡 使用示例

### 示例 1：创作修仙小说

```python
from src.agents.novelist import create_novelist_agent
import asyncio

agent = create_novelist_agent("修仙")

asyncio.run(agent.run_async(
    "写一个山村少年获得上古传承，踏上修仙之路的故事"
))
```

### 示例 2：创作重生爽文

```python
agent = create_novelist_agent("重生")

asyncio.run(agent.run_async(
    "重生在高考前夕，带着前世记忆改变命运"
))
```

### 示例 3：创作系统流小说

```python
agent = create_novelist_agent("系统流")

asyncio.run(agent.run_async(
    "觉醒投资系统，用未来财富创造商业帝国"
))
```

---

## 📂 项目结构

创作完成后，会在工作区生成以下文件：

```
workspace/
├── worldview.md      # 世界观设定
├── characters.md     # 角色档案
├── plot.md          # 情节发展记录
├── outline.md       # 故事大纲
└── chapters/        # 章节文件
    ├── chapter_01.md
    ├── chapter_02.md
    └── ...
```

---

## 🎨 创作流程

### 1. 准备阶段
- 📝 了解用户创作意图
- 🌍 生成世界观设定
- 👥 设计主要角色
- 📋 规划故事大纲

### 2. 创作阶段
- ✍️ 分章节创作
- 🔥 布局爽点
- 💕 穿插感情线
- 🎭 设置悬念钩子

### 3. 维护阶段
- 🧠 记录角色信息
- 📊 追踪情节发展
- 🌐 保持世界观统一
- ❌ 避免矛盾冲突

---

## 🔧 高级功能

### 自定义指令

```python
custom_instructions = """
你是言情小说作家，擅长描写细腻的情感。
重点：情感线为主，商业线为辅。
风格：温馨浪漫，避免虐心。
"""

agent = (
    AgentBuilder()
    .with_instructions(custom_instructions)
    .build()
)
```

### 多 Agent 协作

```python
# 研究员 Agent（收集素材）
researcher = create_research_agent()

# 创作家 Agent（创作小说）
novelist = create_novelist_agent()

# 协作创作
agent.with_tools([
    AgentAdapterTool(researcher),
    AgentAdapterTool(novelist)
])
```

---

## 📊 输出示例

### 章节示例

```
# 第一章：山村少年

清晨的阳光透过薄雾洒落在青云山脚下的小山村。

林凡缓缓睁开眼睛，头痛欲裂。昨夜的记忆如潮水般涌来——

"这...这里是...？"

他猛地坐起身，看着陌生的环境，心中一片茫然。但很快，那些不属于他的记忆便

（此处省略 2800 字）
```

---

## 🎯 提示词技巧

### 给智能体的输入

- ✅ **好**："写一个都市重生小说，主角是程序员，重生到2010年"
- ✅ **好**："修仙小说，废柴主角意外获得上古传承"
- ❌ **差**："写小说"
- ❌ **差**："随便写点什么"

### 明确要求

```
请创作一部重生都市爽文，要求：
1. 主角是程序员，重生到2010年
2. 前世因为错过了比特币机会而后悔
3. 这一世要抓住机会，建立商业帝国
4. 重点是爽点密集，不要虐心
5. 前十章完成第一桶金
```

---

## 🚧 注意事项

1. **API 配额**：创作小说会消耗较多 tokens，注意 API 配额
2. **内容质量**：AI 生成的内容可能需要人工润色
3. **原创性**：避免抄袭已有作品
4. **合规性**：遵守平台规则，避免敏感内容

---

## 📈 后续计划

- [ ] 支持更多题材
- [ ] 增加风格选项（爽文、言情、悬疑等）
- [ ] 集成 novel-generator skill
- [ ] 支持自动生成插图
- [ ] 支持导出为 EPUB 格式
- [ ] 支持多语言创作

---

## 🤝 贡献

欢迎贡献代码、提出建议或报告问题！

---

## 📄 许可证

MIT License

---

**开始你的小说创作之旅吧！** 📚✨
