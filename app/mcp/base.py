from __future__ import annotations

import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class ToolResult:
    tool_name: str
    success: bool
    output: Any
    error: str | None = None
    duration_ms: int = 0
    metadata: dict = field(default_factory=dict)


class MCPTool(ABC):
    name: str
    description: str
    parameters: dict  # JSON Schema of expected args

    @abstractmethod
    async def execute(self, **kwargs: Any) -> ToolResult: ...

    async def safe_execute(self, **kwargs: Any) -> ToolResult:
        start = time.monotonic()
        try:
            result = await self.execute(**kwargs)
        except Exception as exc:
            result = ToolResult(
                tool_name=self.name,
                success=False,
                output=None,
                error=str(exc),
            )
        result.duration_ms = int((time.monotonic() - start) * 1000)
        return result
