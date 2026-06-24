import json
import asyncio
from typing import Any

import httpx
from app.mcp.base import MCPTool, ToolResult
from app.core.config import get_settings


def _get_access_token(credentials_path: str) -> str:
    """Get OAuth2 token from service account JSON using google-auth (optional dep)."""
    try:
        from google.oauth2 import service_account
        from google.auth.transport.requests import Request as GRequest

        creds = service_account.Credentials.from_service_account_file(
            credentials_path,
            scopes=["https://www.googleapis.com/auth/spreadsheets"],
        )
        creds.refresh(GRequest())
        return creds.token
    except ImportError:
        raise RuntimeError("Install google-auth: pip install google-auth")


class GoogleSheetsTool(MCPTool):
    name = "google_sheets"
    description = "Read data from or append rows to a Google Sheets spreadsheet."
    parameters = {
        "type": "object",
        "properties": {
            "spreadsheet_id": {"type": "string", "description": "Google Sheets spreadsheet ID"},
            "range": {"type": "string", "description": "A1 notation range, e.g. 'Sheet1!A1:D10'"},
            "action": {"type": "string", "enum": ["read", "append"], "default": "read"},
            "values": {
                "type": "array",
                "items": {"type": "array"},
                "description": "Rows to append (only for action=append)",
            },
        },
        "required": ["spreadsheet_id", "range"],
    }

    async def execute(
        self,
        spreadsheet_id: str,
        range: str,
        action: str = "read",
        values: list[list[Any]] | None = None,
    ) -> ToolResult:
        settings = get_settings()
        if not settings.google_credentials_json:
            return ToolResult(tool_name=self.name, success=False, output=None, error="Google credentials not configured")

        token = await asyncio.get_running_loop().run_in_executor(
            None, _get_access_token, settings.google_credentials_json
        )
        headers = {"Authorization": f"Bearer {token}"}
        base = f"https://sheets.googleapis.com/v4/spreadsheets/{spreadsheet_id}/values/{range}"

        async with httpx.AsyncClient(timeout=15) as client:
            if action == "read":
                resp = await client.get(base, headers=headers)
                resp.raise_for_status()
                return ToolResult(tool_name=self.name, success=True, output=resp.json().get("values", []))
            else:
                body = {"values": values or [], "majorDimension": "ROWS"}
                resp = await client.post(f"{base}:append", headers=headers, json=body,
                                         params={"valueInputOption": "USER_ENTERED"})
                resp.raise_for_status()
                return ToolResult(tool_name=self.name, success=True, output=resp.json())
