from dataclasses import dataclass
import hashlib

from openai import AsyncOpenAI

from app.core.config import get_settings
from app.rag.embedder import embed_query
from app.rag.vector_store import SearchResult, search
from app.services.cache.redis_cache import cache


@dataclass
class Citation:
    document_id: str
    filename: str
    page: int | str | None
    score: float
    excerpt: str


@dataclass
class QueryResult:
    answer: str
    citations: list[Citation]


def _build_citations(hits: list[SearchResult]) -> list[Citation]:
    return [
        Citation(
            document_id=h.metadata.get("document_id", ""),
            filename=h.metadata.get("filename", ""),
            page=h.metadata.get("page") or h.metadata.get("slide") or h.metadata.get("sheet"),
            score=round(h.score, 4),
            excerpt=h.text[:300],
        )
        for h in hits
    ]


async def semantic_search(
    query: str,
    top_k: int | None = None,
    filters: dict | None = None,
) -> list[Citation]:
    cache_key = f"sem:{hashlib.md5(query.encode()).hexdigest()}:{top_k}"
    cached = await cache.get(cache_key)
    if cached:
        return [Citation(**c) for c in cached]
    vector = await embed_query(query)
    hits = await search(vector, top_k=top_k, filters=filters)
    result = _build_citations(hits)
    await cache.set(cache_key, [c.__dict__ for c in result])
    return result


async def query_knowledge_base(
    query: str,
    filters: dict | None = None,
    top_k: int | None = None,
) -> QueryResult:
    cache_key = f"kb:{hashlib.md5(query.encode()).hexdigest()}"
    cached = await cache.get(cache_key)
    if cached:
        return QueryResult(
            answer=cached["answer"],
            citations=[Citation(**c) for c in cached["citations"]],
        )

    settings = get_settings()
    vector = await embed_query(query)
    hits = await search(vector, top_k=top_k or settings.rag_top_k, filters=filters)
    citations = _build_citations(hits)

    if not hits:
        return QueryResult(answer="No relevant documents found.", citations=[])

    context = "\n\n---\n\n".join(
        f"[Source: {h.metadata.get('filename', 'unknown')}, "
        f"page/slide/sheet: {h.metadata.get('page') or h.metadata.get('slide') or h.metadata.get('sheet', 'N/A')}]\n{h.text}"
        for h in hits
    )

    client = AsyncOpenAI(api_key=settings.openai_api_key)
    response = await client.chat.completions.create(
        model=settings.openai_chat_model,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a helpful enterprise assistant. Answer using ONLY the provided context. "
                    "Always cite the source document and page number. "
                    "If the answer is not in context, say so clearly."
                ),
            },
            {"role": "user", "content": f"Context:\n{context}\n\nQuestion: {query}"},
        ],
        temperature=0.2,
    )

    result = QueryResult(
        answer=response.choices[0].message.content or "",
        citations=citations,
    )
    await cache.set(cache_key, {"answer": result.answer, "citations": [c.__dict__ for c in citations]})
    return result
