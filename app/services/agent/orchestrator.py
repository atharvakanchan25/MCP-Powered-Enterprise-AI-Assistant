from __future__ import annotations

import uuid
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.state import AgentState
from app.agents.workflow import get_workflow
from app.core.logging import get_logger
from app.models.conversation import Message, MessageRole
from app.models.domain import Memory, ToolCall
from app.repositories.base import BaseRepository
from app.services.agent.memory import MemoryService, MemoryType
from app.services.monitoring import MonitoringService

logger = get_logger(__name__)


@dataclass
class AgentResponse:
    answer: str
    plan: str
    reasoning: list[str]
    tool_results: list[dict]
    citations: list[dict]
    state: AgentState


async def run_agent(
    query: str,
    user_id: uuid.UUID,
    conversation_id: uuid.UUID,
    db: AsyncSession,
) -> AgentResponse:
    memory_svc = MemoryService(db)

    # Load existing memories for context
    memories = await memory_svc.recall(user_id, limit=15)
    user_profile = await memory_svc.get_user_profile(user_id)

    initial_state: AgentState = {
        "query": query,
        "user_id": str(user_id),
        "conversation_id": str(conversation_id),
        "memories": [{"key": m.key, "value": m.value} for m in memories],
        "user_profile": user_profile,
        "tool_results": [],
        "rag_context": [],
        "reasoning": [],
        "errors": [],
        "iteration": 0,
    }

    workflow = get_workflow()
    final_state: AgentState = await workflow.ainvoke(initial_state)

    # Persist tool call traces
    tool_repo = BaseRepository(ToolCall, db)
    msg_repo = BaseRepository(Message, db)

    # Create a stub assistant message to attach tool calls to
    assistant_msg = await msg_repo.create(
        role=MessageRole.ASSISTANT,
        content=final_state.get("final_answer", ""),
        conversation_id=conversation_id,
    )

    for tr in final_state.get("tool_results", []):
        await tool_repo.create(
            tool_name=tr["tool"],
            input_args=tr.get("args"),
            output=tr.get("output"),
            error=tr.get("error"),
            duration_ms=tr.get("duration_ms", 0),
            message_id=assistant_msg.id,
        )

    # Store query as agent memory
    await memory_svc.store(
        user_id=user_id,
        key=f"last_query_{str(conversation_id)[:8]}",
        value=query,
        memory_type=MemoryType.CONVERSATION,
        conversation_id=conversation_id,
    )

    # Track token usage if available in state
    token_usage = final_state.get("token_usage")
    if token_usage:
        monitoring = MonitoringService(db)
        await monitoring.record_request(
            path="/api/v1/agent/query",
            method="POST",
            status_code=200,
            duration_ms=0,
            user_id=user_id,
            prompt_tokens=token_usage.get("prompt_tokens"),
            completion_tokens=token_usage.get("completion_tokens"),
            total_tokens=token_usage.get("total_tokens"),
        )

    logger.info("agent.complete", user_id=str(user_id), tools_used=len(final_state.get("tool_results", [])))

    return AgentResponse(
        answer=final_state.get("final_answer", ""),
        plan=final_state.get("plan", ""),
        reasoning=final_state.get("reasoning", []),
        tool_results=final_state.get("tool_results", []),
        citations=final_state.get("citations", []),
        state=final_state,
    )
