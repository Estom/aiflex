"""
AI Flex Framework - Agent 配置模型

定义 agent.json 的 Pydantic 模型。
"""

from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field, field_validator


class ModelConfig(BaseModel):
    """LLM 模型配置"""

    model: str = Field(description="模型名称（如 'gpt-4', 'claude-3-5-sonnet-20241022'）")
    api_key: str | None = Field(default=None, description="API 密钥（可选，默认使用全局）")
    api_base: str | None = Field(default=None, description="API 基础 URL（可选）")
    temperature: float | None = Field(default=None, description="温度参数")
    max_tokens: int | None = Field(default=None, description="最大 tokens")


class PromptConfig(BaseModel):
    """Prompt 配置"""

    system: str | None = Field(default=None, description="系统提示词")
    file: str | None = Field(default=None, description="从文件加载提示词（相对于 agent.json）")
    variables: dict[str, str] = Field(default_factory=dict, description="提示词变量")

    @field_validator("file")
    @classmethod
    def validate_file(cls, v: str | None) -> str | None:
        if v and (v.endswith(".md") or v.endswith(".txt")):
            return v
        return v


class SkillsConfig(BaseModel):
    """Skills 配置"""

    sources: list[str] = Field(default_factory=list, description="技能源路径列表")
    inline: list[dict[str, Any]] = Field(
        default_factory=list, description="内联技能定义（不推荐）"
    )


class ToolsConfig(BaseModel):
    """Tools 配置"""

    auto_discover: bool = Field(default=True, description="自动发现 tools/*.py 文件")
    paths: list[str] = Field(default_factory=list, description="额外工具路径")
    enabled: list[str] = Field(default_factory=list, description="启用的工具名称列表")
    disabled: list[str] = Field(default_factory=list, description="禁用的工具名称列表")


class SubagentConfig(BaseModel):
    """子 Agent 配置"""

    name: str = Field(description="子 Agent 名称（目录名）")
    alias: str | None = Field(default=None, description="别名（用作工具名称）")
    description: str | None = Field(default=None, description="描述（覆盖子 Agent 配置）")
    enabled: bool = Field(default=True, description="是否启用")


class RuntimeConfig(BaseModel):
    """运行时配置"""

    max_steps: int = Field(default=5, description="最大推理步数")
    workspace_root: str | None = Field(default=None, description="工作区根目录")
    mcp_lazy_load: bool = Field(default=False, description="MCP 懒加载")
    mcp_servers: list[dict[str, Any]] = Field(default_factory=list, description="MCP 服务器配置")
    experience_enabled: bool = Field(default=False, description="启用经验系统")
    knowledge_base: dict[str, Any] | None = Field(default=None, description="知识库配置")


class AgentConfig(BaseModel):
    """
    Agent 配置模型

    对应 agent.json 文件结构。
    """

    name: str = Field(description="Agent 名称")
    version: str = Field(default="1.0.0", description="版本号")
    description: str = Field(description="Agent 描述")

    model: ModelConfig | None = Field(default=None, description="LLM 模型配置")
    prompt: PromptConfig = Field(
        default_factory=PromptConfig, description="Prompt 配置"
    )
    skills: SkillsConfig = Field(default_factory=SkillsConfig, description="Skills 配置")
    tools: ToolsConfig = Field(default_factory=ToolsConfig, description="Tools 配置")
    subagents: list[SubagentConfig] = Field(
        default_factory=list, description="子 Agent 配置"
    )
    runtime: RuntimeConfig = Field(
        default_factory=RuntimeConfig, description="运行时配置"
    )

    # 内部字段（非配置） - 使用私有属性（Pydantic v2 方式）
    config_dir: Path = Field(default=Path("."), exclude=True)

    model_config = {"extra": "ignore"}

    def set_config_dir(self, config_dir: Path) -> None:
        """设置配置文件所在目录（用于解析相对路径）"""
        object.__setattr__(self, "config_dir", config_dir)

    def get_config_dir(self) -> Path:
        """获取配置文件所在目录"""
        return self.config_dir

    def resolve_path(self, relative_path: str) -> Path:
        """解析相对于配置文件的路径"""
        return (self.config_dir / relative_path).resolve()
