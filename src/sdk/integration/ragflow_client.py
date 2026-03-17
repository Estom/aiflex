"""
RagFlow Client - RagFlow 知识库客户端

与 RagFlow 知识库系统交互
"""

import os
from typing import Any

import httpx


class RagFlowConfig:
    """RagFlow 配置"""
    def __init__(self, base_url: str, api_key: str):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key


class RagFlowChunk(dict):
    """RagFlow 检索块"""
    def __init__(
        self,
        id: str,
        content: str,
        similarity: float | None = None,
        document_id: str | None = None,
        **kwargs: Any,
    ):
        super().__init__(
            id=id,
            content=content,
            similarity=similarity,
            document_id=document_id,
            **kwargs,
        )


class RetrieveChunksRequest(dict):
    """检索块请求"""
    def __init__(
        self,
        question: str,
        dataset_ids: list[str] | None = None,
        similarity_threshold: float | None = None,
        vector_similarity_weight: float | None = None,
        top_k: int | None = None,
        **kwargs: Any,
    ):
        super().__init__(
            question=question,
            dataset_ids=dataset_ids or [],
            similarity_threshold=similarity_threshold,
            vector_similarity_weight=vector_similarity_weight,
            top_k=top_k,
            **kwargs,
        )


class RetrieveChunksResult(dict):
    """检索块结果"""
    def __init__(
        self,
        chunks: list[RagFlowChunk],
        total: int | None = None,
        **kwargs: Any,
    ):
        super().__init__(
            chunks=chunks,
            total=total,
            **kwargs,
        )


def _read_env(name: str) -> str | None:
    """读取环境变量"""
    value = os.getenv(name)
    return value.strip() if value else None


def resolve_ragflow_config() -> RagFlowConfig:
    """解析 RagFlow 配置"""
    base_url = _read_env("RAGFLOW_BASE_URL") or _read_env("RAGFLOW_ADDRESS")
    api_key = _read_env("RAGFLOW_API_KEY") or _read_env("RAGFLOW_APIKEY")

    if not base_url:
        raise ValueError("RagFlow is not configured: missing RAGFLOW_BASE_URL.")
    if not base_url.startswith(("http://", "https://")):
        raise ValueError("RAGFLOW_BASE_URL must start with http:// or https://")
    if not api_key:
        raise ValueError("RagFlow is not configured: missing RAGFLOW_API_KEY.")

    return RagFlowConfig(base_url=base_url, api_key=api_key)


class RagFlowClient:
    """
    RagFlow 客户端

    与 RagFlow 知识库系统交互
    """

    def __init__(self, config: RagFlowConfig | None = None):
        """
        初始化 RagFlow 客户端

        Args:
            config: RagFlow 配置，如果为 None 则从环境变量读取
        """
        self.config = config or resolve_ragflow_config()

    async def retrieve_chunks(self, payload: RetrieveChunksRequest) -> RetrieveChunksResult:
        """
        检索知识块

        Args:
            payload: 检索请求

        Returns:
            RetrieveChunksResult: 检索结果
        """
        if not payload.get("question") or not isinstance(payload["question"], str):
            raise ValueError("question is required")

        url = f"{self.config.base_url}/api/v1/retrieval"

        headers = {
            "Authorization": f"Bearer {self.config.api_key}",
            "Content-Type": "application/json",
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()

        if data.get("code", 0) != 0:
            raise ValueError(data.get("message", "Failed to retrieve chunks"))

        chunks_data = data.get("data", {}).get("chunks", [])
        chunks = [
            RagFlowChunk(
                id=c["id"],
                content=c["content"],
                similarity=c.get("similarity"),
                document_id=c.get("document_id"),
            )
            for c in chunks_data
            if c.get("id") and c.get("content")
        ]

        return RetrieveChunksResult(
            chunks=chunks,
            total=data.get("data", {}).get("total", len(chunks)),
        )

    async def list_datasets(
        self,
        page: int = 1,
        page_size: int = 30,
        name: str | None = None,
    ) -> dict:
        """
        列出数据集

        Args:
            page: 页码
            page_size: 每页大小
            name: 数据集名称过滤

        Returns:
            dict: 数据集列表
        """
        url = f"{self.config.base_url}/api/v1/datasets"

        params: dict[str, Any] = {
            "page": page,
            "page_size": page_size,
        }
        if name:
            params["name"] = name

        headers = {
            "Authorization": f"Bearer {self.config.api_key}",
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url, headers=headers, params=params)
            response.raise_for_status()
            return response.json()
