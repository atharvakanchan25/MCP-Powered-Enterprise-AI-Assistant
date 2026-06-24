from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.responses import Response
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import AdminUser
from app.db.session import get_db
from app.models.conversation import Conversation, Message
from app.models.domain import AuditLog, Document, ToolCall
from app.models.user import User
from app.schemas.agent import AuditLogSchema, DashboardStats, ReportExportRequest
from app.services.monitoring import MonitoringService
from app.services.reports.generator import generate_docx, generate_pdf

router = APIRouter(prefix="/admin", tags=["Admin"])


@router.get("/dashboard", response_model=DashboardStats)
async def dashboard(
    _: AdminUser,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    async def count(model) -> int:
        result = await db.execute(select(func.count()).select_from(model))
        return result.scalar() or 0

    return DashboardStats(
        total_users=await count(User),
        total_conversations=await count(Conversation),
        total_tool_calls=await count(ToolCall),
        total_documents=await count(Document),
        total_messages=await count(Message),
    )


@router.get("/audit-logs", response_model=list[AuditLogSchema])
async def audit_logs(
    _: AdminUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    limit: int = 50,
    offset: int = 0,
):
    from app.repositories.base import BaseRepository
    repo = BaseRepository(AuditLog, db)
    return await repo.list(limit=limit, offset=offset)


@router.post("/reports/export")
async def export_report(_: AdminUser, body: ReportExportRequest):
    """Export a report as PDF or DOCX."""
    if body.format == "pdf":
        content = generate_pdf(body.title, body.query, body.answer, body.citations, body.reasoning)
        return Response(
            content=content,
            media_type="application/pdf",
            headers={"Content-Disposition": 'attachment; filename="report.pdf"'},
        )
    else:
        content = generate_docx(body.title, body.query, body.answer, body.citations, body.reasoning)
        return Response(
            content=content,
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            headers={"Content-Disposition": 'attachment; filename="report.docx"'},
        )


@router.get("/monitoring/tokens")
async def token_stats(
    _: AdminUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    limit: int = 100,
):
    """Aggregate token usage across tracked requests."""
    svc = MonitoringService(db)
    return await svc.get_token_stats(limit=limit)


@router.get("/monitoring/errors")
async def error_logs(
    _: AdminUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    limit: int = 50,
):
    """Return recent error-bearing requests."""
    svc = MonitoringService(db)
    return await svc.get_error_stats(limit=limit)
