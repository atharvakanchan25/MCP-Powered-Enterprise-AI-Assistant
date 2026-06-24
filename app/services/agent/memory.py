from __future__ import annotations

import uuid
from enum import Enum

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.domain import Memory
from app.repositories.base import BaseRepository


class MemoryType(str, Enum):
    AGENT = "agent"
    CONVERSATION = "conversation"
    USER_PROFILE = "user_profile"


class MemoryService:
    def __init__(self, db: AsyncSession) -> None:
        self._repo = BaseRepository(Memory, db)

    async def store(
        self,
        user_id: uuid.UUID,
        key: str,
        value: str,
        memory_type: MemoryType = MemoryType.AGENT,
        conversation_id: uuid.UUID | None = None,
        relevance_score: float | None = None,
    ) -> Memory:
        # Overwrite existing key for same user + memory_type
        existing = await self._repo.get_by(user_id=user_id, key=f"{memory_type}:{key}")
        if existing:
            existing.value = value
            existing.relevance_score = relevance_score
            await self._repo.db.flush()
            return existing
        return await self._repo.create(
            user_id=user_id,
            key=f"{memory_type}:{key}",
            value=value,
            conversation_id=conversation_id,
            relevance_score=relevance_score,
        )

    async def recall(
        self,
        user_id: uuid.UUID,
        memory_type: MemoryType | None = None,
        limit: int = 20,
    ) -> list[Memory]:
        filters: dict = {"user_id": user_id}
        memories = await self._repo.list(limit=limit, **filters)
        if memory_type:
            prefix = f"{memory_type}:"
            memories = [m for m in memories if m.key.startswith(prefix)]
        return memories

    async def recall_conversation(
        self, user_id: uuid.UUID, conversation_id: uuid.UUID, limit: int = 10
    ) -> list[Memory]:
        all_mem = await self._repo.list(limit=limit, user_id=user_id, conversation_id=conversation_id)
        return all_mem

    async def get_user_profile(self, user_id: uuid.UUID) -> dict[str, str]:
        memories = await self.recall(user_id, MemoryType.USER_PROFILE)
        prefix = f"{MemoryType.USER_PROFILE}:"
        return {m.key.removeprefix(prefix): m.value for m in memories}
