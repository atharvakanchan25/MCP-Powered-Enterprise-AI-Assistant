import uuid
from datetime import datetime
from pydantic import BaseModel, Field


class AgentQueryRequest(BaseModel):
    query: str = Field(min_length=1, max_length=4000)
    conversation_id: uuid.UUID | None = None


class ToolResultSchema(BaseModel):
    tool: str
    success: bool
    output: object
    error: str | None
    duration_ms: int = 0


class AgentQueryResponse(BaseModel):
    answer: str
    plan: str
    reasoning: list[str]
    tool_results: list[ToolResultSchema]
    citations: list[dict]
    conversation_id: uuid.UUID


class MemoryItem(BaseModel):
    id: uuid.UUID
    key: str
    value: str
    relevance_score: float | None
    created_at: datetime

    model_config = {"from_attributes": True}


class StoreMemoryRequest(BaseModel):
    key: str
    value: str
    memory_type: str = "agent"


# ── Admin schemas ──────────────────────────────────────────────────────────

class AuditLogSchema(BaseModel):
    id: uuid.UUID
    action: str
    resource_type: str | None
    resource_id: str | None
    ip_address: str | None
    meta: dict | None
    user_id: uuid.UUID | None
    created_at: datetime

    model_config = {"from_attributes": True}


class DashboardStats(BaseModel):
    total_users: int
    total_conversations: int
    total_tool_calls: int
    total_documents: int
    total_messages: int


class ReportExportRequest(BaseModel):
    query: str
    answer: str
    citations: list[dict] = []
    reasoning: list[str] = []
    format: str = Field(default="pdf", pattern="^(pdf|docx)$")
    title: str = "AI Assistant Report"
