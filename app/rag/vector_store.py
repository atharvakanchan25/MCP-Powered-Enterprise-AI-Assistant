import uuid
from dataclasses import dataclass

from qdrant_client import AsyncQdrantClient
from qdrant_client.models import (
    Distance,
    FieldCondition,
    Filter,
    MatchValue,
    PointStruct,
    VectorParams,
)

from app.core.config import get_settings

_client: AsyncQdrantClient | None = None


def get_qdrant() -> AsyncQdrantClient:
    global _client
    if _client is None:
        s = get_settings()
        _client = AsyncQdrantClient(host=s.qdrant_host, port=s.qdrant_port)
    return _client


async def ensure_collection() -> None:
    s = get_settings()
    client = get_qdrant()
    existing = await client.get_collections()
    names = [c.name for c in existing.collections]
    if s.qdrant_collection not in names:
        await client.create_collection(
            collection_name=s.qdrant_collection,
            vectors_config=VectorParams(size=s.embedding_dimension, distance=Distance.COSINE),
        )


@dataclass
class SearchResult:
    chunk_id: str
    score: float
    text: str
    metadata: dict


async def upsert_chunks(
    chunks: list[tuple[str, list[float], dict]]  # (text, vector, metadata)
) -> None:
    s = get_settings()
    client = get_qdrant()
    points = [
        PointStruct(
            id=str(uuid.uuid4()),
            vector=vector,
            payload={"text": text, **metadata},
        )
        for text, vector, metadata in chunks
    ]
    await client.upsert(collection_name=s.qdrant_collection, points=points)


async def search(
    query_vector: list[float],
    top_k: int | None = None,
    filters: dict | None = None,
) -> list[SearchResult]:
    s = get_settings()
    client = get_qdrant()
    qdrant_filter = None
    if filters:
        conditions = [FieldCondition(key=k, match=MatchValue(value=v)) for k, v in filters.items()]
        qdrant_filter = Filter(must=conditions)

    hits = await client.search(
        collection_name=s.qdrant_collection,
        query_vector=query_vector,
        limit=top_k or s.rag_top_k,
        query_filter=qdrant_filter,
        with_payload=True,
    )
    return [
        SearchResult(
            chunk_id=str(hit.id),
            score=hit.score,
            text=hit.payload.get("text", ""),
            metadata={k: v for k, v in hit.payload.items() if k != "text"},
        )
        for hit in hits
    ]


async def delete_by_document(document_id: str) -> None:
    s = get_settings()
    client = get_qdrant()
    await client.delete(
        collection_name=s.qdrant_collection,
        points_selector=Filter(
            must=[FieldCondition(key="document_id", match=MatchValue(value=document_id))]
        ),
    )
