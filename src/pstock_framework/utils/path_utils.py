"""
PStock Framework - 路径工具

提供路径处理相关的工具函数。
"""

from pathlib import Path


def resolve_agent_dir(agents_root: Path, agent_name: str) -> Path:
    """
    解析 Agent 目录路径

    Args:
        agents_root: Agent 根目录
        agent_name: Agent 名称（可能包含路径分隔符）

    Returns:
        Agent 目录的绝对路径
    """
    # 支持嵌套路径（如 "trading/financial_analyst"）
    agent_path = (agents_root / agent_name).resolve()
    return agent_path


def find_agent_config(agent_dir: Path) -> Path | None:
    """
    查找 Agent 配置文件

    Args:
        agent_dir: Agent 目录

    Returns:
        agent.json 文件路径，如果不存在则返回 None
    """
    config_file = agent_dir / "agent.json"
    if config_file.exists() and config_file.is_file():
        return config_file
    return None


def find_prompt_file(agent_dir: Path) -> Path | None:
    """
    查找 Prompt 文件

    Args:
        agent_dir: Agent 目录

    Returns:
        prompt.md 文件路径，如果不存在则返回 None
    """
    prompt_file = agent_dir / "prompt.md"
    if prompt_file.exists() and prompt_file.is_file():
        return prompt_file
    return None


def find_skill_files(agent_dir: Path) -> list[Path]:
    """
    查找所有 SKILL.md 文件

    Args:
        agent_dir: Agent 目录

    Returns:
        SKILL.md 文件路径列表
    """
    skills_dir = agent_dir / "skills"
    if not skills_dir.exists() or not skills_dir.is_dir():
        return []

    skill_files = []
    for skill_dir in skills_dir.iterdir():
        if not skill_dir.is_dir():
            continue
        skill_md = skill_dir / "SKILL.md"
        if skill_md.exists() and skill_md.is_file():
            skill_files.append(skill_md)

    return skill_files


def find_tool_files(agent_dir: Path) -> list[Path]:
    """
    查找所有工具文件

    Args:
        agent_dir: Agent 目录

    Returns:
        Python 工具文件路径列表
    """
    tools_dir = agent_dir / "tools"
    if not tools_dir.exists() or not tools_dir.is_dir():
        return []

    tool_files = []
    for tool_file in tools_dir.glob("*.py"):
        if tool_file.name.startswith("_"):
            continue
        if tool_file.is_file():
            tool_files.append(tool_file)

    return tool_files


def find_subagent_dirs(agent_dir: Path) -> list[Path]:
    """
    查找所有子 Agent 目录

    Args:
        agent_dir: Agent 目录

    Returns:
        子 Agent 目录路径列表
    """
    subagents_dir = agent_dir / "subagents"
    if not subagents_dir.exists() or not subagents_dir.is_dir():
        return []

    subagent_dirs = []
    for entry in subagents_dir.iterdir():
        if not entry.is_dir():
            continue
        # 检查是否包含 agent.json
        if (entry / "agent.json").exists():
            subagent_dirs.append(entry)

    return subagent_dirs
