"""
Path Utilities - 路径工具

处理工作区路径解析和安全检查
"""

import os
from typing import Any

from ..agent.core.interfaces import AgentContext


def gather_allowed_roots(default_root: str, context: AgentContext | None) -> list[str]:
    """
    收集允许的根目录列表

    Args:
        default_root: 默认根目录
        context: Agent 上下文

    Returns:
        list[str]: 允许的根目录列表
    """
    roots = [os.path.abspath(default_root)]
    extras_raw = (context.metadata if context else {}).get("skillRoots") if context and context.metadata else None
    extras = list(extras_raw) if isinstance(extras_raw, list) else []

    for maybe_path in extras:
        if isinstance(maybe_path, str):
            resolved = os.path.abspath(maybe_path)
            if resolved not in roots:
                roots.append(resolved)

    return roots


def resolve_within_allowed_roots(roots: list[str], user_path: str) -> str | None:
    """
    解析路径，确保在允许的根目录内

    Args:
        roots: 允许的根目录列表
        user_path: 用户提供的路径

    Returns:
        str | None: 解析后的绝对路径，如果不在允许的根目录内则返回 None
    """
    cleaned = (user_path or "").strip()
    if not cleaned:
        return None

    # 生成候选路径
    if os.path.isabs(cleaned):
        candidates = [os.path.abspath(cleaned)]
    else:
        candidates = [os.path.abspath(os.path.join(root, cleaned)) for root in roots]

    # 检查候选路径是否在允许的根目录内
    for candidate in candidates:
        for root in roots:
            rel = os.path.relpath(candidate, root)
            if rel == "." or (not rel.startswith("..") and not os.path.isabs(rel)):
                return candidate

    return None
