import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.services.rag.query import semantic_search, query_knowledge_base, Citation
from app.services.rag.vision import VisionTask, analyze_image, SUPPORTED_IMAGE_TYPES
from app.rag.vector_store import SearchResult


# ── Query service tests ──────────────────────────────────────────────────────

@pytest.fixture
def mock_hit():
    return SearchResult(
        chunk_id="chunk-1",
        score=0.92,
        text="The quarterly revenue increased by 15%.",
        metadata={"document_id": "doc-1", "filename": "report.pdf", "page": 3, "owner_id": "user-1"},
    )


async def test_semantic_search(mock_hit):
    with patch("app.services.rag.query.embed_query", new=AsyncMock(return_value=[0.1] * 1536)), \
         patch("app.services.rag.query.search", new=AsyncMock(return_value=[mock_hit])):
        results = await semantic_search("revenue growth", top_k=3)
        assert len(results) == 1
        assert isinstance(results[0], Citation)
        assert results[0].filename == "report.pdf"
        assert results[0].score == 0.92


async def test_query_knowledge_base_with_answer(mock_hit):
    mock_response = MagicMock()
    mock_response.choices[0].message.content = "Revenue grew by 15% this quarter."

    with patch("app.services.rag.query.embed_query", new=AsyncMock(return_value=[0.1] * 1536)), \
         patch("app.services.rag.query.search", new=AsyncMock(return_value=[mock_hit])), \
         patch("app.services.rag.query.AsyncOpenAI") as mock_openai:
        mock_openai.return_value.chat.completions.create = AsyncMock(return_value=mock_response)
        result = await query_knowledge_base("What is the revenue growth?")
        assert "15%" in result.answer
        assert len(result.citations) == 1


async def test_query_knowledge_base_no_results():
    with patch("app.services.rag.query.embed_query", new=AsyncMock(return_value=[0.1] * 1536)), \
         patch("app.services.rag.query.search", new=AsyncMock(return_value=[])):
        result = await query_knowledge_base("unknown topic")
        assert result.answer == "No relevant documents found."
        assert result.citations == []


# ── Vision service tests ─────────────────────────────────────────────────────

async def test_analyze_image_unsupported_type(tmp_path):
    from app.core.exceptions import AppException
    f = tmp_path / "file.tiff"
    f.write_bytes(b"\x00" * 10)
    # .tiff is not in SUPPORTED_IMAGE_TYPES
    with pytest.raises(AppException) as exc_info:
        await analyze_image(f, task=VisionTask.GENERAL)
    assert exc_info.value.status_code == 415


async def test_analyze_image_calls_gpt4o(tmp_path):
    from PIL import Image
    img_path = tmp_path / "test.png"
    Image.new("RGB", (100, 100), color=(255, 0, 0)).save(str(img_path))

    mock_response = MagicMock()
    mock_response.choices[0].message.content = "A red square image."

    with patch("app.services.rag.vision.AsyncOpenAI") as mock_openai:
        mock_openai.return_value.chat.completions.create = AsyncMock(return_value=mock_response)
        result = await analyze_image(img_path, task=VisionTask.UNDERSTAND)
        assert result == "A red square image."
        mock_openai.return_value.chat.completions.create.assert_called_once()


async def test_analyze_image_ocr_task(tmp_path):
    from PIL import Image, ImageDraw
    img_path = tmp_path / "ocr.png"
    img = Image.new("RGB", (200, 50), color=(255, 255, 255))
    ImageDraw.Draw(img).text((10, 10), "Invoice #1234", fill=(0, 0, 0))
    img.save(str(img_path))

    mock_response = MagicMock()
    mock_response.choices[0].message.content = "Invoice #1234"

    with patch("app.services.rag.vision.AsyncOpenAI") as mock_openai:
        mock_openai.return_value.chat.completions.create = AsyncMock(return_value=mock_response)
        result = await analyze_image(img_path, task=VisionTask.OCR)
        assert "Invoice" in result
        # Verify the OCR system prompt was used
        call_args = mock_openai.return_value.chat.completions.create.call_args
        messages = call_args.kwargs["messages"]
        assert "Extract ALL text" in messages[0]["content"][0]["text"]
