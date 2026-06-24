from __future__ import annotations

from app.mcp.base import MCPTool


class ToolRegistry:
    def __init__(self) -> None:
        self._tools: dict[str, MCPTool] = {}

    def register(self, tool: MCPTool) -> None:
        self._tools[tool.name] = tool

    def get(self, name: str) -> MCPTool | None:
        return self._tools.get(name)

    def all_tools(self) -> list[MCPTool]:
        return list(self._tools.values())

    def discover(self, query: str) -> list[MCPTool]:
        """Simple keyword discovery — returns tools whose name/description contains query terms."""
        q = query.lower()
        return [t for t in self._tools.values() if q in t.name.lower() or q in t.description.lower()]

    def to_openai_functions(self) -> list[dict]:
        """Serialize all registered tools as OpenAI function-calling schemas."""
        return [
            {
                "type": "function",
                "function": {
                    "name": t.name,
                    "description": t.description,
                    "parameters": t.parameters,
                },
            }
            for t in self._tools.values()
        ]


# Singleton registry
registry = ToolRegistry()
