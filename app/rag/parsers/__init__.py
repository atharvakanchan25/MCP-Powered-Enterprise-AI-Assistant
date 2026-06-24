from pathlib import Path
from app.rag.parsers.base import DocumentParser, ParsedChunk
from app.rag.parsers.pdf import PDFParser
from app.rag.parsers.docx import DocxParser
from app.rag.parsers.pptx import PptxParser
from app.rag.parsers.xlsx import XlsxParser
from app.rag.parsers.txt import TxtParser

_REGISTRY: dict[str, DocumentParser] = {
    ".pdf": PDFParser(),
    ".docx": DocxParser(),
    ".pptx": PptxParser(),
    ".xlsx": XlsxParser(),
    ".txt": TxtParser(),
    ".md": TxtParser(),
    ".csv": TxtParser(),
}

SUPPORTED_EXTENSIONS = set(_REGISTRY.keys())


def get_parser(path: Path) -> DocumentParser:
    ext = path.suffix.lower()
    parser = _REGISTRY.get(ext)
    if not parser:
        raise ValueError(f"Unsupported file type: {ext}")
    return parser


def parse_document(path: Path) -> list[ParsedChunk]:
    return get_parser(path).parse(path)
