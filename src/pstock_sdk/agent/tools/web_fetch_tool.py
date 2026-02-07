"""
Web Fetch Tool - 网页抓取工具

从指定 URL 获取纯文本内容
"""

import re
from typing import Any, ClassVar

import httpx

from pstock_sdk.agent.core.interfaces import AgentContext
from pstock_sdk.agent.tools.base_tool import BaseTool

FETCH_TIMEOUT_MS = 10_000
MAX_CONTENT_LENGTH = 8000


class WebFetchTool(BaseTool):
    """
    网页抓取工具

    从指定 URL 获取纯文本内容
    """

    parameters: ClassVar[dict[str, Any]] = {
        "type": "object",
        "properties": {
            "url": {
                "type": "string",
                "description": "The URL to fetch (must start with http:// or https://).",
            },
        },
        "required": ["url"],
    }

    def __init__(self) -> None:
        self._name = "web_fetch"
        self._display_name = "Web Fetch"
        self._description = "Fetch plain text content from a given URL (http/https) with a 10s timeout."

    @property
    def name(self) -> str:
        """工具名称"""
        return self._name

    @property
    def display_name(self) -> str:
        """工具显示名称"""
        return self._display_name

    @property
    def description(self) -> str:
        """工具描述"""
        return self._description

    async def execute(self, input: Any, context: AgentContext | None = None) -> str:
        """
        执行工具

        Args:
            input: 工具输入
            context: Agent 上下文（未使用）

        Returns:
            str: 工具执行结果
        """
        _ = context  # Reserved for future use
        url = self._extract_url(input)
        if not url:
            return "Error: `url` is required and must start with http:// or https://"

        timeout = httpx.Timeout(FETCH_TIMEOUT_MS / 1000.0, connect=5.0)

        try:
            async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
                response = await client.get(url)
                if not response.is_success:
                    return f"Error: request failed with status {response.status_code} {response.reason_phrase}"

                raw = response.text
                text = self._to_plain_text(raw)[:MAX_CONTENT_LENGTH]
                return text or "Fetched content is empty."

        except httpx.TimeoutException:
            return f"Error fetching {url}: Request timed out after {FETCH_TIMEOUT_MS}ms"
        except httpx.HTTPStatusError as e:
            return f"Error fetching {url}: HTTP status error {e.response.status_code}"
        except Exception as e:
            return f"Error fetching {url}: {e!s}"

    def _extract_url(self, input: Any) -> str | None:
        """
        提取 URL

        Args:
            input: 原始输入

        Returns:
            规范化后的 URL，如果无效则返回 None
        """
        if isinstance(input, str):
            return self._normalize_url(input)
        if input and isinstance(input, dict) and "url" in input:
            val = input["url"]
            if isinstance(val, str):
                return self._normalize_url(val)
        return None

    def _normalize_url(self, url: str) -> str | None:
        """
        规范化 URL

        Args:
            url: 原始 URL

        Returns:
            规范化后的 URL，如果无效则返回 None
        """
        trimmed = url.strip()
        if trimmed.startswith(("http://", "https://")):
            return trimmed
        return None

    def _to_plain_text(self, html: str) -> str:
        """
        将 HTML 转换为纯文本

        Args:
            html: HTML 内容

        Returns:
            纯文本内容
        """
        # Remove script tags and their content
        without_scripts = re.sub(r"<script[\s\S]*?</script>", " ", html, flags=re.IGNORECASE)
        # Remove style tags and their content
        without_styles = re.sub(r"<style[\s\S]*?</style>", " ", without_scripts, flags=re.IGNORECASE)
        # Remove all HTML tags
        without_tags = re.sub(r"<[^>]+>", " ", without_styles)
        # Collapse whitespace
        plain_text = re.sub(r"\s+", " ", without_tags).strip()
        return plain_text
