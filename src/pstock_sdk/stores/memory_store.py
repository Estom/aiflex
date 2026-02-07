"""Missing store file - memory store"""
from typing import Any


class MemorySlotConfig(dict):
    """记忆槽配置"""
    def __init__(
        self,
        name: str,
        description: str | None = None,
        type: str = "short_term",  # 'short_term' | 'long_term'
        **kwargs: Any,
    ):
        super().__init__(
            name=name,
            description=description,
            type=type,
            **kwargs,
        )


class MemoryRecord(dict):
    """记忆记录"""
    def __init__(
        self,
        agent: str,
        name: str,
        content: str,
        type: str = "short_term",
        description: str | None = None,
        sessionId: str | None = None,
        updatedAt: str | None = None,
        createdAt: str | None = None,
        **kwargs: Any,
    ):
        from datetime import datetime
        now = datetime.utcnow().isoformat() + "Z"
        super().__init__(
            agent=agent,
            name=name,
            content=content,
            type=type,
            description=description,
            sessionId=sessionId if type == "short_term" else None,
            updatedAt=updatedAt or now,
            createdAt=createdAt or now,
            **kwargs,
        )


class InMemoryMemoryStore:
    """记忆内存存储"""

    def __init__(self):
        self._records: dict[str, MemoryRecord] = {}

    def recall(
        self,
        agent: str,
        slots: list[dict | MemorySlotConfig],
        sessionId: str | None = None,
    ) -> list[MemoryRecord]:
        if not slots:
            return []

        results = []
        for slot in slots:
            slot_name = slot.get("name") if isinstance(slot, dict) else slot.name
            slot_type = slot.get("type", "short_term") if isinstance(slot, dict) else slot.type
            session = sessionId if slot_type == "short_term" else "long"
            key = f"{agent}::{slot_name}::{session}"
            record = self._records.get(key)
            if record and record.get("content"):
                results.append(record)

        return results

    def upsert(
        self,
        agent: str,
        slot: dict | MemorySlotConfig,
        content: str,
        sessionId: str | None = None,
    ) -> MemoryRecord | None:
        slot_name = slot.get("name") if isinstance(slot, dict) else slot.name
        slot_type = slot.get("type", "short_term") if isinstance(slot, dict) else slot.type
        description = slot.get("description") if isinstance(slot, dict) else slot.description

        trimmed = (content or "").strip()
        session = sessionId if slot_type == "short_term" else "long"
        key = f"{agent}::{slot_name}::{session}"

        if not trimmed:
            self._records.pop(key, None)
            return None

        from datetime import datetime
        now = datetime.utcnow().isoformat() + "Z"
        existing = self._records.get(key)

        record = MemoryRecord(
            agent=agent,
            name=slot_name,
            content=trimmed,
            type=slot_type,
            description=description,
            sessionId=sessionId if slot_type == "short_term" else None,
            createdAt=existing.get("createdAt", now) if existing else now,
            updatedAt=now,
        )

        self._records[key] = record
        return record

    def delete(
        self,
        agent: str,
        slot: dict | MemorySlotConfig,
        sessionId: str | None = None,
    ) -> None:
        slot_name = slot.get("name") if isinstance(slot, dict) else slot.name
        slot_type = slot.get("type", "short_term") if isinstance(slot, dict) else slot.type
        session = sessionId if slot_type == "short_term" else "long"
        key = f"{agent}::{slot_name}::{session}"
        self._records.pop(key, None)
