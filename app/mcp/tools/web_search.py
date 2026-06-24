import httpx
from app.mcp.base import MCPTool, ToolResult
from app.core.config import get_settings


class WebSearchTool(MCPTool):
    name = "web_search"
    description = "Search the web for current information, news, or facts not in the knowledge base."
    parameters = {
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "Search query string"},
            "num_results": {"type": "integer", "default": 5, "description": "Number of results to return"},
        },
        "required": ["query"],
    }

    async def execute(self, query: str, num_results: int = 5) -> ToolResult:
        settings = get_settings()
        if not settings.serpapi_key:
            return ToolResult(
                tool_name=self.name,
                success=False,
                output=None,
                error="SERPAPI_KEY not configured",
            )

        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(
                "https://serpapi.com/search",
                params={"q": query, "num": num_results, "api_key": settings.serpapi_key, "engine": "google"},
            )
            resp.raise_for_status()
            data = resp.json()

        results = [
            {"title": r.get("title"), "snippet": r.get("snippet"), "link": r.get("link")}
            for r in data.get("organic_results", [])[:num_results]
        ]
        return ToolResult(tool_name=self.name, success=True, output=results, metadata={"query": query})
