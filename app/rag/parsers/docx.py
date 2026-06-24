from pathlib import Path
from docx import Document
from app.rag.parsers.base import ParsedChunk

_WORDS_PER_PAGE = 500


class DocxParser:
    def parse(self, path: Path) -> list[ParsedChunk]:
        doc = Document(str(path))
        paragraphs = [p.text.strip() for p in doc.paragraphs if p.text.strip()]
        chunks, page, buf, word_count = [], 1, [], 0
        for para in paragraphs:
            buf.append(para)
            word_count += len(para.split())
            if word_count >= _WORDS_PER_PAGE:
                chunks.append(ParsedChunk("\n".join(buf), {"page": page}))
                page += 1
                buf, word_count = [], 0
        if buf:
            chunks.append(ParsedChunk("\n".join(buf), {"page": page}))
        return chunks
