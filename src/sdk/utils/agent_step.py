"""
Agent Step Builder - Agent 步骤构建器

构建 Agent 执行步骤
"""

from ..agent.core.interfaces import AgentStep


def build_agent_step(
    step_type: str,
    content: str,
    display_name: str | None = None,
    raw: str | None = None,
    data: dict | None = None,
) -> AgentStep:
    """
    构建 Agent 步骤

    Args:
        step_type: 步骤类型 (thought/action/observation/final/error)
        content: 步骤内容
        display_name: 显示名称
        raw: 原始数据
        data: 附加数据

    Returns:
        AgentStep: Agent 步骤
    """
    # 默认显示名称映射
    default_display_names: dict[str, str] = {
        "session": "会话",
        "thought": "思考",
        "action": "调用工具",
        "observation": "工具结果",
        "token": "回复片段",
        "final": "最终回复",
        "error": "错误",
    }

    # 序列化 raw
    raw_str: str | None = None
    if raw is not None:
        if isinstance(raw, str):
            raw_str = raw
        else:
            try:
                import json
                raw_str = json.dumps(raw, ensure_ascii=False)
            except Exception:
                raw_str = str(raw)

    return AgentStep(
        type=step_type,
        content=content,
        display_name=display_name or default_display_names.get(step_type, step_type),
        raw=raw_str,
        data=data or {},
    )
