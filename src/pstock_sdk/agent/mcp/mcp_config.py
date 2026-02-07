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

