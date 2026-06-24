from dataclasses import dataclass, field
from langchain_text_splitters import RecursiveCharacterTextSplitter
from app.rag.parsers.base import ParsedChunk
from app.core.config import get_settings


@dataclass
class TextChunk:
    text: str
    metadata: dict = field(default_factory=dict)


def chunk_parsed(parsed: list[ParsedChunk], doc_meta: dict | None = None) -> list[TextChunk]:
    settings = get_settings()
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=settings.chunk_size,
        chunk_overlap=settings.chunk_overlap,
        separators=["\n\n", "\n", ". ", " ", ""],
    )
    result: list[TextChunk] = []
    for item in parsed:
        splits = splitter.split_text(item.text)
        for idx, split in enumerate(splits):
            meta = {**(doc_meta or {}), **item.metadata, "chunk_index": idx}
            result.append(TextChunk(text=split, metadata=meta))
    return result
