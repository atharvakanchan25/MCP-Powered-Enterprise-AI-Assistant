import enum
import uuid

from sqlalchemy import Enum, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base
from app.models.base import TimestampMixin, UUIDMixin


class DocumentStatus(str, enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    READY = "ready"
    FAILED = "failed"


class Document(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "documents"

    filename: Mapped[str] = mapped_column(String(500), nullable=False)
    content_type: Mapped[str] = mapped_column(String(100))
    status: Mapped[DocumentStatus] = mapped_column(Enum(DocumentStatus), default=DocumentStatus.PENDING)
    chunk_count: Mapped[int] = mapped_column(Integer, default=0)
    storage_path: Mapped[str | None] = mapped_column(Text)
    meta: Mapped[dict | None] = mapped_column(JSON)
    owner_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True
    )


class Memory(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "memories"

    key: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    value: Mapped[str] = mapped_column(Text, nullable=False)
    relevance_score: Mapped[float | None] = mapped_column(Float)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    conversation_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("conversations.id", ondelete="SET NULL")
    )


class ToolCall(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "tool_calls"

    tool_name: Mapped[str] = mapped_column(String(255), nullable=False)
    input_args: Mapped[dict | None] = mapped_column(JSON)
    output: Mapped[dict | None] = mapped_column(JSON)
    error: Mapped[str | None] = mapped_column(Text)
    duration_ms: Mapped[int | None] = mapped_column(Integer)
    message_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("messages.id", ondelete="CASCADE"), index=True
    )

    message: Mapped["Message"] = relationship(back_populates="tool_calls")  # noqa: F821


class AuditLog(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "audit_logs"

    action: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    resource_type: Mapped[str | None] = mapped_column(String(100))
    resource_id: Mapped[str | None] = mapped_column(String(255))
    ip_address: Mapped[str | None] = mapped_column(String(45))
    meta: Mapped[dict | None] = mapped_column(JSON)
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), index=True
    )

    user: Mapped["User"] = relationship(back_populates="audit_logs")  # noqa: F821


class RequestLog(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "request_logs"

    path: Mapped[str] = mapped_column(String(500), nullable=False, index=True)
    method: Mapped[str] = mapped_column(String(10), nullable=False)
    status_code: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    duration_ms: Mapped[int] = mapped_column(Integer, default=0)
    prompt_tokens: Mapped[int | None] = mapped_column(Integer)
    completion_tokens: Mapped[int | None] = mapped_column(Integer)
    total_tokens: Mapped[int | None] = mapped_column(Integer)
    error_type: Mapped[str | None] = mapped_column(String(255), index=True)
    error_message: Mapped[str | None] = mapped_column(Text)
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), index=True
    )
