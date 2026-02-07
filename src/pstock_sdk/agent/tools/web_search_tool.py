"""
Web Search Tool - 网页搜索工具

通过 BoCha API 搜索网页
"""

import os
import re
from dataclasses import dataclass
from enum import StrEnum
from typing import Any, ClassVar

import httpx

from pstock_sdk.agent.core.interfaces import AgentContext
from pstock_sdk.agent.tools.base_tool import BaseTool

API_URL = "https://api.bocha.cn/v1/web-search"
DEFAULT_COUNT = 5
MAX_COUNT = 20
SEARCH_TIMEOUT_MS = 10_000


class Freshness(StrEnum):
    """搜索时间范围"""
    NO_LIMIT = "noLimit"
    DAY = "day"
    WEEK = "week"
    MONTH = "month"
    YEAR = "year"

    @classmethod
    def allowed(cls) -> list[str]:
        return [e.value for e in cls]


@dataclass
class WebSearchInput:
    """网页搜索输入"""
    query: str
    summary: bool = True
    freshness: Freshness = Freshness.NO_LIMIT
    count: int = DEFAULT_COUNT


@dataclass
class WebPageItem:
    """网页搜索结果项"""
    name: str | None = None
    url: str | None = None
    display_url: str | None = None
    snippet: str | None = None
    site_name: str | None = None
    date_last_crawled: str | None = None


@dataclass
class WebSearchData:
    """网页搜索数据"""
    summary: str | None = None
    web_pages: "WebPages | None" = None


@dataclass
class WebPages:
    """网页搜索结果"""
    total_estimated_matches: int | None = None
    value: list[WebPageItem] | None = None


@dataclass
class WebSearchResponse:
    """网页搜索响应"""
    code: int | None = None
    msg: str | None = None
    data: WebSearchData | None = None


class WebSearchTool(BaseTool):
    """
    网页搜索工具

    通过 BoCha API 搜索网页
    """

    parameters: ClassVar[dict[str, Any]] = {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": 'Search query string, e.g., "阿里巴巴2024年的ESG报告".',
            },
            "summary": {
                "type": "boolean",
                "description": "Whether BoCha should return a summary when available (default: true).",
            },
            "freshness": {
                "type": "string",
                "enum": Freshness.allowed(),
                "description": "Time filter; use noLimit for no filter (default).",
            },
            "count": {
                "type": "integer",
                "minimum": 1,
                "maximum": MAX_COUNT,
                "description": f"Number of results to return (1-{MAX_COUNT}, default: {DEFAULT_COUNT}).",
            },
        },
        "required": ["query"],
    }

    def __init__(self) -> None:
        self._name = "web_search"
        self._display_name = "Web Search (BoCha)"
        self._description = "Search the web via BoCha (requires BOCHA_API_KEY). Returns concise results with URLs and snippets."

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
        parsed = self._parse_input(input)
        if not parsed.query:
            return "Error: `query` is required and must be a non-empty string."

        api_key = os.getenv("BOCHA_API_KEY", "").strip()
        if not api_key:
            return "Error: BOCHA_API_KEY is not set. Please configure the API key before using web_search."

        timeout = httpx.Timeout(SEARCH_TIMEOUT_MS / 1000.0, connect=5.0)

        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.post(
                    API_URL,
                    headers={
                        "Authorization": f"Bearer {api_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "query": parsed.query,
                        "summary": parsed.summary,
                        "freshness": parsed.freshness,
                        "count": parsed.count,
                    },
                )

                if not response.is_success:
                    text = response.text
                    return f"Error: BoCha search failed with status {response.status_code} {response.reason_phrase}. {text or ''}".strip()

                data = response.json()
                search_response = self._parse_response(data)
                if search_response.code and search_response.code != 200:
                    return f"Error: BoCha search returned code {search_response.code}. {search_response.msg or ''}".strip()

                return self._format_response(search_response, parsed.query)

        except httpx.TimeoutException:
            return f"Error performing web search: Request timed out after {SEARCH_TIMEOUT_MS}ms"
        except Exception as e:
            return f"Error performing web search: {e!s}"

    def _parse_input(self, input: Any) -> WebSearchInput:
        """
        解析输入

        Args:
            input: 原始输入

        Returns:
            解析后的搜索输入
        """
        if isinstance(input, str):
            return WebSearchInput(
                query=input.strip(),
                summary=True,
                freshness=Freshness.NO_LIMIT,
                count=DEFAULT_COUNT,
            )

        if input and isinstance(input, dict):
            query = input.get("query", "")
            query_str = query.strip() if isinstance(query, str) else ""

            summary = input.get("summary", True)
            summary_bool = summary if isinstance(summary, bool) else True

            freshness_str = input.get("freshness", "noLimit")
            freshness = (
                Freshness(freshness_str)
                if isinstance(freshness_str, str) and freshness_str in Freshness.allowed()
                else Freshness.NO_LIMIT
            )

            count_val = input.get("count", DEFAULT_COUNT)
            count_num = (isinstance(count_val, (int, float)) and round(float(count_val))) or DEFAULT_COUNT
            count = max(1, min(int(count_num), MAX_COUNT))

            return WebSearchInput(
                query=query_str,
                summary=summary_bool,
                freshness=freshness,
                count=count,
            )

        return WebSearchInput(
            query="",
            summary=True,
            freshness=Freshness.NO_LIMIT,
            count=DEFAULT_COUNT,
        )

    def _parse_response(self, data: dict[str, Any]) -> WebSearchResponse:
        """
        解析响应

        Args:
            data: 原始响应数据

        Returns:
            解析后的搜索响应
        """
        response = WebSearchResponse()

        if "code" in data:
            response.code = data["code"]
        if "msg" in data:
            response.msg = data["msg"]

        if "data" in data and isinstance(data["data"], dict):
            data_dict = data["data"]
            search_data = WebSearchData()

            if "summary" in data_dict:
                search_data.summary = data_dict["summary"]

            if "webPages" in data_dict and isinstance(data_dict["webPages"], dict):
                pages_dict = data_dict["webPages"]
                web_pages = WebPages()

                if "totalEstimatedMatches" in pages_dict:
                    web_pages.total_estimated_matches = pages_dict["totalEstimatedMatches"]

                if "value" in pages_dict and isinstance(pages_dict["value"], list):
                    items = []
                    for item in pages_dict["value"]:
                        if isinstance(item, dict):
                            page_item = WebPageItem(
                                name=item.get("name"),
                                url=item.get("url"),
                                display_url=item.get("displayUrl"),
                                snippet=item.get("snippet"),
                                site_name=item.get("siteName"),
                                date_last_crawled=item.get("dateLastCrawled"),
                            )
                            items.append(page_item)
                    web_pages.value = items

                search_data.web_pages = web_pages

            response.data = search_data

        return response

    def _format_response(self, res: WebSearchResponse, query: str) -> str:
        """
        格式化响应

        Args:
            res: 搜索响应
            query: 搜索查询

        Returns:
            格式化后的结果字符串
        """
        summary = (res.data.summary or "").strip() if res.data else None
        items = (res.data.web_pages.value or []) if res.data and res.data.web_pages else []

        if (not items or len(items) == 0) and not summary:
            return f'No results found for "{query}".'

        lines: list[str] = [f'Results for "{query}":']

        if summary:
            lines.append(f"Summary: {summary}")

        total = res.data.web_pages.total_estimated_matches if res.data and res.data.web_pages else None
        if isinstance(total, (int, float)):
            lines.append(f"Approx. matches: {total}")

        for idx, item in enumerate(items[:MAX_COUNT]):
            title = (item.name or item.display_url or item.url or "Untitled").strip()
            url = item.url or item.display_url or ""
            snippet = self._clean_text(item.snippet)[:260] if item.snippet else ""
            site = item.site_name.strip() if item.site_name else ""
            date = item.date_last_crawled or ""

            parts = [f"{idx + 1}. {title}"]
            if url:
                parts.append(f"URL: {url}")
            if snippet:
                parts.append(f"Snippet: {snippet}")
            if site or date:
                source_parts = [p for p in [site, date] if p]
                parts.append(f"Source: {' | '.join(source_parts)}")

            lines.append(" \n ".join(parts))

        return "\n".join(lines)

    def _clean_text(self, value: str | None) -> str:
        """
        清理文本

        Args:
            value: 原始文本

        Returns:
            清理后的文本
        """
        if not value:
            return ""
        return re.sub(r"\s+", " ", value).strip()
