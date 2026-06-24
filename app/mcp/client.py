from __future__ import annotations

from typing import Any

from app.mcp.base import ToolResult
from app.mcp.registry import ToolRegistry, registry as _default_registry
from app.core.logging import get_logger

logger = get_logger(__name__)


class MCPClient:
    def __init__(self, tool_registry: ToolRegistry | None = None) -> None:
        self._registry = tool_registry or _default_registry

    def list_tools(self) -> list[dict]:
        return self._registry.to_openai_functions()

    def discover(self, query: str) -> list[str]:
        return [t.name for t in self._registry.discover(query)]

    async def execute(self, tool_name: str, **kwargs: Any) -> ToolResult:
        tool = self._registry.get(tool_name)
        if not tool:
            return ToolResult(
                tool_name=tool_name,
                success=False,
                output=None,
                error=f"Tool '{tool_name}' not found in registry",
            )
        logger.info("mcp.execute", tool=tool_name, args=list(kwargs.keys()))
        result = await tool.safe_execute(**kwargs)
        logger.info(
            "mcp.result",
            tool=tool_name,
            success=result.success,
            duration_ms=result.duration_ms,
        )
        return result
