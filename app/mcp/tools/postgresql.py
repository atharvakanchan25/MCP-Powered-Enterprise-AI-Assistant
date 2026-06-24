from typing import Any
import asyncpg
from app.mcp.base import MCPTool, ToolResult
from app.core.config import get_settings


class PostgreSQLTool(MCPTool):
    name = "postgresql_query"
    description = "Execute a read-only SQL SELECT query against the application database and return results."
    parameters = {
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "A read-only SQL SELECT statement"},
            "params": {"type": "array", "items": {}, "description": "Query parameters", "default": []},
        },
        "required": ["query"],
    }

    async def execute(self, query: str, params: list[Any] | None = None) -> ToolResult:
        # Only allow SELECT statements for safety
        if not query.strip().upper().startswith("SELECT"):
            raise ValueError("Only SELECT queries are permitted")

        settings = get_settings()
        conn = await asyncpg.connect(settings.database_url.replace("+asyncpg", ""))
        try:
            rows = await conn.fetch(query, *(params or []))
            data = [dict(r) for r in rows]
            return ToolResult(tool_name=self.name, success=True, output=data, metadata={"row_count": len(data)})
        finally:
            await conn.close()
