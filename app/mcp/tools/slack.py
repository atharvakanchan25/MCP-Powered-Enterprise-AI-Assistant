import httpx
from app.mcp.base import MCPTool, ToolResult
from app.core.config import get_settings

_SLACK_BASE = "https://slack.com/api"


class SlackTool(MCPTool):
    name = "slack"
    description = "Send messages to Slack channels or read recent channel messages."
    parameters = {
        "type": "object",
        "properties": {
            "action": {"type": "string", "enum": ["send", "read"], "description": "Action to perform"},
            "channel": {"type": "string", "description": "Channel ID or name (e.g. #general)"},
            "text": {"type": "string", "description": "Message text (required for send)"},
            "limit": {"type": "integer", "default": 10, "description": "Number of messages to read"},
        },
        "required": ["action", "channel"],
    }

    async def execute(self, action: str, channel: str, text: str = "", limit: int = 10) -> ToolResult:
        settings = get_settings()
        if not settings.slack_bot_token:
            return ToolResult(tool_name=self.name, success=False, output=None, error="SLACK_BOT_TOKEN not configured")

        headers = {"Authorization": f"Bearer {settings.slack_bot_token}"}
        async with httpx.AsyncClient(timeout=15) as client:
            if action == "send":
                resp = await client.post(f"{_SLACK_BASE}/chat.postMessage",
                                          headers=headers, json={"channel": channel, "text": text})
                data = resp.json()
                if not data.get("ok"):
                    raise RuntimeError(data.get("error", "Slack API error"))
                return ToolResult(tool_name=self.name, success=True, output={"ts": data["ts"], "channel": channel})
            else:
                resp = await client.get(f"{_SLACK_BASE}/conversations.history",
                                         headers=headers, params={"channel": channel, "limit": limit})
                data = resp.json()
                if not data.get("ok"):
                    raise RuntimeError(data.get("error", "Slack API error"))
                messages = [{"user": m.get("user"), "text": m.get("text"), "ts": m.get("ts")}
                            for m in data.get("messages", [])]
                return ToolResult(tool_name=self.name, success=True, output=messages)
