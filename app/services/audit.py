from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.domain import AuditLog
from app.repositories.base import BaseRepository


class AuditService:
    def __init__(self, db: AsyncSession) -> None:
        self._repo = BaseRepository(AuditLog, db)

    async def log(
        self,
        action: str,
        user_id: uuid.UUID | None = None,
        resource_type: str | None = None,
        resource_id: str | None = None,
        ip_address: str | None = None,
        meta: dict[str, Any] | None = None,
    ) -> AuditLog:
        return await self._repo.create(
            action=action,
            user_id=user_id,
            resource_type=resource_type,
            resource_id=resource_id,
            ip_address=ip_address,
            meta=meta,
        )
