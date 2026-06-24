import asyncio
import uuid
from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.core.logging import get_logger
from app.db.session import AsyncSessionLocal
from app.models.domain import Document, DocumentStatus
from app.rag.chunker import chunk_parsed
from app.rag.embedder import embed_texts
from app.rag.parsers import parse_document
from app.rag.vector_store import ensure_collection, upsert_chunks
from app.repositories.base import BaseRepository

logger = get_logger(__name__)


async def ingest_document(document_id: uuid.UUID, db: AsyncSession | None = None) -> None:
    """Ingest a document. If called as a background task, opens its own session."""
    if db is not None:
        await _ingest(document_id, db)
    else:
        async with AsyncSessionLocal() as session:
            try:
                await _ingest(document_id, session)
                await session.commit()
            except Exception:
                await session.rollback()
                raise


async def _ingest(document_id: uuid.UUID, db: AsyncSession) -> None:
    repo = BaseRepository(Document, db)
    doc = await repo.get(document_id)
    if not doc:
        raise NotFoundError("Document")

    doc.status = DocumentStatus.PROCESSING
    await db.flush()

    try:
        await ensure_collection()
        path = Path(doc.storage_path)
        parsed = parse_document(path)
        doc_meta = {
            "document_id": str(doc.id),
            "filename": doc.filename,
            "owner_id": str(doc.owner_id),
        }
        chunks = chunk_parsed(parsed, doc_meta)

        if not chunks:
            doc.status = DocumentStatus.FAILED
            await db.flush()
            return

        texts = [c.text for c in chunks]
        vectors = await embed_texts(texts)

        await upsert_chunks([(text, vec, chunk.metadata) for text, vec, chunk in zip(texts, vectors, chunks)])

        doc.chunk_count = len(chunks)
        doc.status = DocumentStatus.READY
        logger.info("document.ingested", doc_id=str(doc.id), chunks=len(chunks))

    except Exception as exc:
        doc.status = DocumentStatus.FAILED
        logger.error("document.ingest_failed", doc_id=str(doc.id), error=str(exc))
        raise

    await db.flush()
