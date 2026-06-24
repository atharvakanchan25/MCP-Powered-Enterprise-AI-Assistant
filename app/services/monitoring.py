from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.domain import RequestLog
from app.repositories.base import BaseRepository


class MonitoringService:
    def __init__(self, db: AsyncSession) -> None:
        self._repo = BaseRepository(RequestLog, db)

    async def record_request(
        self,
        path: str,
        method: str,
        status_code: int,
        duration_ms: int,
        user_id: uuid.UUID | None = None,
        prompt_tokens: int | None = None,
        completion_tokens: int | None = None,
        total_tokens: int | None = None,
    ) -> RequestLog:
        return await self._repo.create(
            path=path,
            method=method,
            status_code=status_code,
            duration_ms=duration_ms,
            user_id=user_id,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
        )

    async def record_error(
        self,
        path: str,
        method: str,
        status_code: int,
        duration_ms: int,
        error_type: str,
        error_message: str,
        user_id: uuid.UUID | None = None,
    ) -> RequestLog:
        return await self._repo.create(
            path=path,
            method=method,
            status_code=status_code,
            duration_ms=duration_ms,
            error_type=error_type,
            error_message=error_message,
            user_id=user_id,
        )

    async def get_token_stats(self, limit: int = 100) -> dict[str, Any]:
        logs = await self._repo.list(limit=limit)
        token_logs = [l for l in logs if l.total_tokens is not None]
        total = sum(l.total_tokens for l in token_logs)  # type: ignore[misc]
        prompt = sum(l.prompt_tokens or 0 for l in token_logs)
        completion = sum(l.completion_tokens or 0 for l in token_logs)
        return {
            "total_tokens": total,
            "prompt_tokens": prompt,
            "completion_tokens": completion,
            "requests_tracked": len(token_logs),
        }

    async def get_error_stats(self, limit: int = 100) -> list[dict]:
        logs = await self._repo.list(limit=limit)
        return [
            {
                "path": l.path,
                "error_type": l.error_type,
                "error_message": l.error_message,
                "status_code": l.status_code,
                "created_at": l.created_at,
            }
            for l in logs
            if l.error_type is not None
        ]
