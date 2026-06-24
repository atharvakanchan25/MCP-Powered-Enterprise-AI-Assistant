from typing import Protocol
from pathlib import Path


class ParsedChunk:
    __slots__ = ("text", "metadata")

    def __init__(self, text: str, metadata: dict):
        self.text = text
        self.metadata = metadata


class DocumentParser(Protocol):
    def parse(self, path: Path) -> list[ParsedChunk]: ...
