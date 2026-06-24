from __future__ import annotations

import uuid
from typing import Any, TypedDict


class AgentState(TypedDict, total=False):
    # Input
    user_id: str
    conversation_id: str
    query: str

    # Planning
    plan: str
    selected_tools: list[str]
    reasoning: list[str]

    # Execution
    tool_results: list[dict]
    rag_context: list[dict]

    # Memory
    memories: list[dict]
    user_profile: dict[str, str]

    # Output
    final_answer: str
    citations: list[dict]
    report: str | None
    token_usage: dict[str, int] | None

    # Metadata
    iteration: int
    errors: list[str]
