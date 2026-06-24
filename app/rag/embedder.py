from openai import AsyncOpenAI
from app.core.config import get_settings

_client: AsyncOpenAI | None = None


def _get_client() -> AsyncOpenAI:
    global _client
    if _client is None:
        _client = AsyncOpenAI(api_key=get_settings().openai_api_key)
    return _client


async def embed_texts(texts: list[str]) -> list[list[float]]:
    """Embed a list of texts, batching in groups of 100."""
    settings = get_settings()
    client = _get_client()
    embeddings: list[list[float]] = []
    batch_size = 100
    for i in range(0, len(texts), batch_size):
        batch = texts[i : i + batch_size]
        response = await client.embeddings.create(
            model=settings.openai_embedding_model,
            input=batch,
        )
        embeddings.extend(item.embedding for item in response.data)
    return embeddings


async def embed_query(text: str) -> list[float]:
    results = await embed_texts([text])
    return results[0]
