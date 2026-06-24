import asyncio
import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, UploadFile, File, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import CurrentUser
from app.core.exceptions import AppException, ForbiddenError, NotFoundError
from app.db.session import get_db
from app.models.domain import Document
from app.rag.parsers import SUPPORTED_EXTENSIONS
from app.rag.storage import delete_file, save_upload
from app.repositories.base import BaseRepository
from app.schemas.documents import (
    DocumentResponse,
    KnowledgeBaseQuery,
    KnowledgeBaseResponse,
    SearchRequest,
    SearchResponse,
    CitationSchema,
)
from app.services.rag.ingestion import ingest_document
from app.services.rag.query import query_knowledge_base, semantic_search

router = APIRouter(prefix="/documents", tags=["Documents & RAG"])


def _repo(db: Annotated[AsyncSession, Depends(get_db)]):
    return BaseRepository(Document, db)


@router.post("/upload", response_model=DocumentResponse, status_code=201)
async def upload_document(
    user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    file: UploadFile = File(...),
):
    """Upload a document and trigger async ingestion into the vector store."""
    from pathlib import Path

    ext = Path(file.filename or "").suffix.lower()
    if ext not in SUPPORTED_EXTENSIONS:
        raise AppException(415, f"Unsupported file type '{ext}'. Allowed: {sorted(SUPPORTED_EXTENSIONS)}", "UNSUPPORTED_TYPE")

    storage_path = await save_upload(file, str(user.id))
    repo = BaseRepository(Document, db)
    doc = await repo.create(
        filename=file.filename,
        content_type=file.content_type or "application/octet-stream",
        storage_path=str(storage_path),
        owner_id=user.id,
    )
    # Fire-and-forget ingestion — runs after response is returned
    asyncio.create_task(ingest_document(doc.id, db))
    return doc


@router.get("/", response_model=list[DocumentResponse])
async def list_documents(
    user: CurrentUser,
    repo: Annotated[BaseRepository, Depends(_repo)],
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    return await repo.list(limit=limit, offset=offset, owner_id=user.id)


@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: uuid.UUID,
    user: CurrentUser,
    repo: Annotated[BaseRepository, Depends(_repo)],
):
    doc = await repo.get(document_id)
    if not doc:
        raise NotFoundError("Document")
    if doc.owner_id != user.id:
        raise ForbiddenError()
    return doc


@router.delete("/{document_id}", status_code=204)
async def delete_document(
    document_id: uuid.UUID,
    user: CurrentUser,
    repo: Annotated[BaseRepository, Depends(_repo)],
):
    from app.rag.vector_store import delete_by_document
    doc = await repo.get(document_id)
    if not doc:
        raise NotFoundError("Document")
    if doc.owner_id != user.id:
        raise ForbiddenError()
    await delete_by_document(str(document_id))
    if doc.storage_path:
        await delete_file(doc.storage_path)
    await repo.delete(doc)


@router.post("/search", response_model=SearchResponse)
async def search_documents(user: CurrentUser, body: SearchRequest):
    """Semantic similarity search across all indexed documents."""
    filters = {**(body.filters or {}), "owner_id": str(user.id)}
    citations = await semantic_search(body.query, top_k=body.top_k, filters=filters)
    return SearchResponse(results=[CitationSchema(**c.__dict__) for c in citations])


@router.post("/query", response_model=KnowledgeBaseResponse)
async def query_knowledge(user: CurrentUser, body: KnowledgeBaseQuery):
    """RAG query — retrieve relevant chunks and synthesize an answer with citations."""
    filters = {**(body.filters or {}), "owner_id": str(user.id)}
    result = await query_knowledge_base(body.query, filters=filters, top_k=body.top_k)
    return KnowledgeBaseResponse(
        answer=result.answer,
        citations=[CitationSchema(**c.__dict__) for c in result.citations],
    )
