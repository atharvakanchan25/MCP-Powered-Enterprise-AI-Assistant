from app.mcp.registry import registry
from app.mcp.tools.postgresql import PostgreSQLTool
from app.mcp.tools.web_search import WebSearchTool
from app.mcp.tools.email_tool import EmailTool
from app.mcp.tools.google_sheets import GoogleSheetsTool
from app.mcp.tools.slack import SlackTool


def register_all_tools() -> None:
    for tool in [PostgreSQLTool(), WebSearchTool(), EmailTool(), GoogleSheetsTool(), SlackTool()]:
        registry.register(tool)
