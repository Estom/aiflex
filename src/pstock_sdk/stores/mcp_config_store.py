"""
MCP Config Store - MCP 配置存储

MCP 服务器配置的内存存储
"""

from typing import Any


class McpServerConfig(dict):
    """MCP 服务器配置"""
    def __init__(
        self,
        name: str,
        baseUrl: str,
        apiKey: str | None = None,
        description: str | None = None,
        headers: dict[str, str] | None = None,
        enabled: bool = True,
        **kwargs: Any,
    ):
        super().__init__(
            name=name,
            baseUrl=baseUrl,
            apiKey=apiKey,
            description=description,
            headers=headers or {},
            enabled=enabled,
            **kwargs,
        )

    @property
    def name(self) -> str:
        return self["name"]

    @property
    def baseUrl(self) -> str:
        return self["baseUrl"]

    @property
    def apiKey(self) -> str | None:
        return self.get("apiKey")

    @property
    def description(self) -> str | None:
        return self.get("description")

    @property
    def headers(self) -> dict[str, str]:
        return self.get("headers", {})

    @property
    def enabled(self) -> bool:
        return self.get("enabled", True)


class InMemoryMcpConfigStore:
    """
    MCP 配置内存存储
    """

    def __init__(self, initial: list[dict[str, Any]] | None = None):
        self._configs: dict[str, McpServerConfig] = {}
        if initial:
            for cfg in initial:
                self.save(cfg, allow_overwrite=True)

    def list(self) -> list[McpServerConfig]:
        """列出所有配置"""
        return sorted(self._configs.values(), key=lambda x: x["name"])

    def get(self, name: str) -> McpServerConfig | None:
        """获取配置"""
        return self._configs.get(name)

    def save(self, config: dict[str, Any], options: dict[str, Any] | None = None) -> McpServerConfig:
        """保存配置"""
        self._validate(config)

        exists = config["name"] in self._configs
        if exists and not (options or {}).get("allow_overwrite", False):
            raise ValueError(f"MCP {config['name']} already exists.")

        mcp_config = McpServerConfig(
            name=config["name"],
            baseUrl=config["baseUrl"],
            apiKey=config.get("apiKey"),
            description=config.get("description"),
            headers=config.get("headers"),
            enabled=config.get("enabled", True),
        )

        self._configs[config["name"]] = mcp_config
        return mcp_config

    def delete(self, name: str) -> None:
        """删除配置"""
        self._configs.pop(name, None)

    @staticmethod
    def _validate(config: dict[str, Any]) -> None:
        """验证配置"""
        if not config.get("name") or not isinstance(config["name"], str):
            raise ValueError("MCP name is required and must be a string.")

        import re
        if not re.match(r"^[A-Za-z0-9_-]+$", config["name"]):
            raise ValueError("MCP name must be alphanumeric, dash or underscore.")

        if not config.get("baseUrl") or not isinstance(config["baseUrl"], str):
            raise ValueError("baseUrl is required and must be a string.")

        if not config["baseUrl"].startswith(("http://", "https://")):
            raise ValueError("baseUrl must start with http:// or https://")
