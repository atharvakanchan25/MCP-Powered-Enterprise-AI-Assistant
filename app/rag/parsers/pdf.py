from pathlib import Path
from pypdf import PdfReader
from app.rag.parsers.base import ParsedChunk


class PDFParser:
    def parse(self, path: Path) -> list[ParsedChunk]:
        reader = PdfReader(str(path))
        chunks = []
        for i, page in enumerate(reader.pages):
            text = (page.extract_text() or "").strip()
            if text:
                chunks.append(ParsedChunk(text, {"page": i + 1, "total_pages": len(reader.pages)}))
        return chunks
