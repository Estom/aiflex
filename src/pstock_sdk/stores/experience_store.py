"""
Experience Store - 经验存储

Agent 经验的内存存储
"""

import uuid
from datetime import datetime
from typing import Any


class ExperienceRecord(dict):
    """经验记录"""
    def __init__(
        self,
        id: str,
        agent: str,
        keywords: list[str],
        content: str,
        createdAt: str,
        updatedAt: str,
        **kwargs: Any,
    ):
        super().__init__(
            id=id,
            agent=agent,
            keywords=keywords,
            content=content,
            createdAt=createdAt,
            updatedAt=updatedAt,
            **kwargs,
        )

    @property
    def id(self) -> str:
        return self["id"]

    @property
    def agent(self) -> str:
        return self["agent"]

    @property
    def keywords(self) -> list[str]:
        return self["keywords"]

    @property
    def content(self) -> str:
        return self["content"]

    @property
    def createdAt(self) -> str:
        return self["createdAt"]

    @property
    def updatedAt(self) -> str:
        return self["updatedAt"]


class ExperienceStore:
    """
    经验存储接口
    """

    def list(self, agent: str, keyword: str | None = None) -> list[ExperienceRecord]:
        """
        列出经验

        Args:
            agent: Agent 名称
            keyword: 可选的关键词过滤

        Returns:
            list[ExperienceRecord]: 经验记录列表
        """
        raise NotImplementedError

    def get(self, agent: str, id: str) -> ExperienceRecord | None:
        """
        获取经验

        Args:
            agent: Agent 名称
            id: 经验 ID

        Returns:
            ExperienceRecord | None: 经验记录或 None
        """
        raise NotImplementedError

    def upsert(self, agent: str, payload: dict[str, Any]) -> ExperienceRecord:
        """
        创建或更新经验

        Args:
            agent: Agent 名称
            payload: 经验数据

        Returns:
            ExperienceRecord: 经验记录
        """
        raise NotImplementedError


def _normalize_keywords(input: Any) -> list[str]:
    """规范化关键词"""
    if isinstance(input, list):
        return [str(k).strip() for k in input if isinstance(k, str) and k.strip()]
    if isinstance(input, str):
        return [k.strip() for k in input.replace(",", " ").split() if k.strip()]
    return []


def _safe_record_id(provided: str | None = None) -> str:
    """生成或使用提供的记录 ID"""
    if provided and provided.strip():
        return provided.strip()
    return str(uuid.uuid4())


class InMemoryExperienceStore(ExperienceStore):
    """
    经验内存存储实现
    """

    def __init__(self):
        self._records: dict[str, ExperienceRecord] = {}

    def list(self, agent: str, keyword: str | None = None) -> list[ExperienceRecord]:
        """列出经验"""
        target = (keyword or "").strip().lower()
        items = [r for r in self._records.values() if r["agent"] == agent and r["content"].strip()]

        if not target:
            return sorted(items, key=lambda x: x.get("updatedAt", ""), reverse=True)

        filtered = [
            r for r in items
            if any(k.lower() in target for k in r["keywords"]) or target in r["content"].lower()
        ]
        return sorted(filtered, key=lambda x: x.get("updatedAt", ""), reverse=True)

    def get(self, agent: str, id: str) -> ExperienceRecord | None:
        """获取经验"""
        record = self._records.get(f"{agent}::{id}")
        if record and record["agent"] == agent:
            return record
        return None

    def upsert(self, agent: str, payload: dict[str, Any]) -> ExperienceRecord:
        """创建或更新经验"""
        content = str(payload.get("content", "")).strip()
        if not content:
            raise ValueError("content is required")

        keywords = _normalize_keywords(payload.get("keywords"))
        if not keywords:
            raise ValueError("keywords is required")

        now = datetime.utcnow().isoformat() + "Z"
        id = _safe_record_id(payload.get("id"))
        existing = self.get(agent, id)

        record = ExperienceRecord(
            id=id,
            agent=agent,
            keywords=keywords,
            content=content,
            createdAt=existing["createdAt"] if existing else now,
            updatedAt=now,
        )

        self._records[f"{agent}::{id}"] = record
        return record
