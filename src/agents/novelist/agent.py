#!/usr/bin/env python
"""
作家智能体 - 专门用于小说创作

功能：
1. 自动生成小说提示词和世界观设定
2. 分章节创作小说
3. 维护角色、地点、情节的连续性
4. 生成情节图解
5. 记录创作失败场景以优化后续创作

支持题材：
- 都市、修仙、玄幻、重生、系统流、末世、科幻、游戏
"""

import asyncio
import os
from typing import Any

from dotenv import load_dotenv

from sdk.agent.core.agent import Agent, AgentBuilder
from sdk.agent.llm.openai_llm import OpenAILLM, OpenAIModelOptions
from sdk.agent.core.interfaces import AgentContext

load_dotenv()


# =============================================================================
# 创作工具
# =============================================================================

class NovelPromptTool:
    """小说提示词生成器"""

    def generate_worldview(self, genre: str, theme: str) -> str:
        """生成世界观设定"""
        worldview_templates = {
            "修仙": f"""
## 世界观设定

**背景设定**：修仙世界，境界分为炼气、筑基、金丹、元婴、化神、炼虚、合体、大乘、渡劫

**修炼体系**：
- 修仙者通过吸收天地灵气提升境界
- 境界突破需要机缘和资源
- 高境界可碾压低境界，同境界比拼功法和法宝

**势力分布**：
- 正道：青阳宗、紫霄宫、天剑门
- 魔道：血煞宗、幽冥教、鬼王谷
- 中立：散修联盟、商会、拍卖行

**宝物系统**：法宝、丹药、符箓、阵法、灵兽
""",
            "都市": f"""
## 世界观设定

**背景设定**：现代都市，主角重生或觉醒系统

**核心机制**：
- 主角拥有特殊能力或系统
- 可以获取超前信息或技能
- 面对现实世界的各种挑战

**势力分布**：
- 商界：各大集团、上市公司
- 政界：政府部门、权力中心
- 黑道：地下组织、帮派势力

**社会阶层**：普通人、中产阶级、富豪、权贵、顶级大佬
""",
            "重生": f"""
## 世界观设定

**背景设定**：主角带着前世记忆重生

**核心优势**：
- 拥有未来知识
- 知道关键事件和机会
- 可以改变遗憾和错误

**重生时间**：选择关键时间点（高考前夕、创业初期等）

**蝴蝶效应**：改变历史会导致新的变化
""",
            "系统": f"""
## 世界观设定

**背景设定**：主角觉醒神秘系统

**系统功能**：
- 发布任务和奖励
- 提供技能和能力
- 辅助主角成长

**系统类型**：
- 投资系统：财富增长
- 科技系统：科技树解锁
- 修炼系统：快速提升
- 征战系统：战争模拟
""",
        }
        return worldview_templates.get(genre, "")

    def generate_characters(self, theme: str, count: int = 3) -> str:
        """生成角色设定"""
        return f"""
## 主要角色

### 主角
- **姓名**：待定
- **性格**：坚韧、果断、重情义
- **特点**：{theme}
- **目标**：{theme}

### 配角
1. **忠诚伙伴**
   - 性格：可靠、忠诚
   - 作用：提供支持

2. **红颜知己**
   - 性格：温柔、聪慧
   - 作用：情感线

3. **宿敌对手**
   - 性格：傲慢、野心
   - 作用：制造冲突
"""


class NovelWritingTool:
    """小说写作工具"""

    def generate_chapter_outline(self, chapter_num: int, content: str) -> str:
        """生成章节大纲"""
        return f"""
## 第 {chapter_num} 章：[标题]

### 章节目标
{content}

### 剧情要点
- 开篇（50-100字）：承接上文，设置悬念
- 发展（200-300字）：推进剧情，铺垫冲突
- 高潮（100-150字）：本节最紧张刺激的部分
- 回落（50-80字）：高潮后的事件反应
- 结尾（50-80字）：埋下伏笔，引出下一章

### 预期字数
2000-3000字
"""


class MemoryManager:
    """记忆管理器"""

    def __init__(self, workspace: str):
        self.workspace = workspace
        self.characters_file = os.path.join(workspace, "characters.md")
        self.plot_file = os.path.join(workspace, "plot.md")
        self.worldview_file = os.path.join(workspace, "worldview.md")

    def save_character(self, name: str, description: str):
        """保存角色信息"""
        with open(self.characters_file, "a", encoding="utf-8") as f:
            f.write(f"\n## {name}\n\n{description}\n")

    def save_plot(self, chapter: int, content: str):
        """保存情节信息"""
        with open(self.plot_file, "a", encoding="utf-8") as f:
            f.write(f"\n## 第 {chapter} 章\n\n{content}\n")

    def save_worldview(self, content: str):
        """保存世界观信息"""
        with open(self.worldview_file, "w", encoding="utf-8") as f:
            f.write(content)


# =============================================================================
# 作家智能体
# =============================================================================


def create_novelist_agent(genre: str = "都市") -> Agent:
    """
    创建作家智能体

    Args:
        genre: 小说类型（都市、修仙、玄幻、重生、系统流等）

    Returns:
        Agent: 配置好的作家智能体
    """
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY 环境变量未设置")

    llm = OpenAILLM(
        api_key=api_key,
        options=OpenAIModelOptions(
            model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            api_base=os.getenv("OPENAI_API_BASE", "https://api.openai.com/v1"),
            temperature=0.8,  # 创作温度较高，增加创意性
        ),
    )

    # 初始化工具
    prompt_tool = NovelPromptTool()
    writing_tool = NovelWritingTool()

    # 工作区设置
    workspace_root = os.path.expanduser(
        os.getenv("AI_FLEX_WORKSPACE", f"/home/estom/work/aiflex/examples/workspace")
    )

    instructions = f"""
你是一位专业的{genre}小说作家，擅长创作引人入胜的故事。

## 创作流程

1. **准备阶段**
   - 了解用户的创作意图（一句话方向或题材）
   - 生成世界观设定（{genre}题材）
   - 设计主要角色（主角、配角、反派）
   - 规划故事大纲（分卷结构）

2. **创作阶段**
   - 分章节创作，每章 2000-3000 字
   - 每章要有明确的情节进展
   - 设置"爽点"（打脸、突破、收获等）
   - 结尾设置悬念钩子

3. **维护阶段**
   - 记录角色信息，保持一致性
   - 记录情节发展，避免矛盾
   - 记录世界观细节，保持统一

## {genre}题材特点

{prompt_tool.generate_worldview(genre, "创作方向")}

## 创作要点

1. **主角设定**
   - 出身平凡但有特殊机缘
   - 性格坚韧、重情重义
   - 不断成长，超越自我

2. **剧情节奏**
   - 开篇吸引人，快速入题
   - 中期高潮迭起，爽点密集
   - 后期收束伏笔，圆满结局

3. **爽点设计**
   - 小爽点：每章 2-3 个（突破、打脸、收获）
   - 中爽点：每 5-10 章 1 个（击败宿敌、获得宝物）
   - 大爽点：每卷 1 个（解决主要矛盾）

4. **情感线**
   - 适当穿插感情戏
   - 与主线剧情相结合
   - 不要喧宾夺主

## 写作风格

- 语言生动流畅，富有感染力
- 对话自然，符合人物性格
- 描写细腻，画面感强
- 节奏紧凑，不拖沓

开始创作吧！用户会给你一句话方向，你将开启一段精彩的创作之旅。
"""

    agent = (
        AgentBuilder()
        .with_name("novelist")
        .with_description(f"专业{genre}小说作家")
        .with_llm(llm)
        .with_max_steps(10)
        .with_instructions(instructions)
        .with_workspace_root(workspace_root)
        .build()
    )

    return agent


def entry_point() -> None:
    """入口函数"""
    import sys

    if len(sys.argv) > 1:
        genre = sys.argv[1]
    else:
        genre = "都市"  # 默认题材

    agent = create_novelist_agent(genre)

    print(f"✅ {genre}小说作家智能体已启动！")
    print(f"📝 工作区：{agent.workspace_root}")
    print(f"🎯 开始创作吧！给我一句话方向。")

    # 运行智能体
    asyncio.run(agent.run_async("请开始创作"))


if __name__ == "__main__":
    entry_point()
