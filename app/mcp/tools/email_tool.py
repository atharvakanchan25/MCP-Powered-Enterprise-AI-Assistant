import asyncio
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from app.mcp.base import MCPTool, ToolResult
from app.core.config import get_settings


class EmailTool(MCPTool):
    name = "send_email"
    description = "Send an email to one or more recipients."
    parameters = {
        "type": "object",
        "properties": {
            "to": {"type": "string", "description": "Recipient email address"},
            "subject": {"type": "string", "description": "Email subject line"},
            "body": {"type": "string", "description": "Email body content (plain text or HTML)"},
            "is_html": {"type": "boolean", "default": False},
        },
        "required": ["to", "subject", "body"],
    }

    def _send_sync(self, to: str, subject: str, body: str, is_html: bool) -> None:
        s = get_settings()
        msg = MIMEMultipart("alternative")
        msg["From"] = s.smtp_user
        msg["To"] = to
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "html" if is_html else "plain"))

        with smtplib.SMTP(s.smtp_host, s.smtp_port) as server:
            server.starttls()
            server.login(s.smtp_user, s.smtp_password)
            server.sendmail(s.smtp_user, to, msg.as_string())

    async def execute(self, to: str, subject: str, body: str, is_html: bool = False) -> ToolResult:
        await asyncio.get_running_loop().run_in_executor(None, self._send_sync, to, subject, body, is_html)
        return ToolResult(
            tool_name=self.name,
            success=True,
            output={"sent_to": to, "subject": subject},
        )
