import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.models.domain import DocumentStatus


class DocumentResponse(BaseModel):
    id: uuid.UUID
    filename: str
    content_type: str
    status: DocumentStatus
    chunk_count: int
    owner_id: uuid.UUID
    created_at: datetime

    model_config = {"from_attributes": True}


class SearchRequest(BaseModel):
    query: str = Field(min_length=1, max_length=1000)
    top_k: int = Field(default=5, ge=1, le=20)
    filters: dict | None = None


class CitationSchema(BaseModel):
    document_id: str
    filename: str
    page: int | str | None
    score: float
    excerpt: str


class SearchResponse(BaseModel):
    results: list[CitationSchema]


class KnowledgeBaseQuery(BaseModel):
    query: str = Field(min_length=1, max_length=2000)
    top_k: int = Field(default=5, ge=1, le=20)
    filters: dict | None = None


class KnowledgeBaseResponse(BaseModel):
    answer: str
    citations: list[CitationSchema]
