import pytest
from app.rag.chunker import chunk_parsed
from app.rag.parsers.base import ParsedChunk


def test_chunker_basic():
    parsed = [ParsedChunk("word " * 300, {"page": 1})]
    chunks = chunk_parsed(parsed, doc_meta={"document_id": "abc", "filename": "test.txt"})
    assert len(chunks) > 1
    for c in chunks:
        assert c.metadata["document_id"] == "abc"
        assert c.metadata["filename"] == "test.txt"
        assert c.metadata["page"] == 1
        assert "chunk_index" in c.metadata


def test_chunker_empty():
    chunks = chunk_parsed([], doc_meta={"document_id": "x"})
    assert chunks == []


def test_chunker_respects_size():
    parsed = [ParsedChunk("a " * 1000, {"page": 1})]
    chunks = chunk_parsed(parsed)
    for c in chunks:
        assert len(c.text) <= 600  # chunk_size (512) + some tolerance


def test_chunker_metadata_merging():
    parsed = [
        ParsedChunk("text one", {"page": 1}),
        ParsedChunk("text two", {"page": 2}),
    ]
    chunks = chunk_parsed(parsed, doc_meta={"owner_id": "user1"})
    pages = [c.metadata["page"] for c in chunks]
    assert 1 in pages
    assert 2 in pages
    assert all(c.metadata["owner_id"] == "user1" for c in chunks)
