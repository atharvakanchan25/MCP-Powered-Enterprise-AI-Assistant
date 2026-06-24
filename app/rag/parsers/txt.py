from pathlib import Path
from app.rag.parsers.base import ParsedChunk


class TxtParser:
    def parse(self, path: Path) -> list[ParsedChunk]:
        text = path.read_text(encoding="utf-8", errors="replace").strip()
        return [ParsedChunk(text, {"page": 1})] if text else []
