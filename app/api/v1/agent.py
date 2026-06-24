import uuid
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import CurrentUser
from app.db.session import get_db
from app.models.conversation import Conversation
from app.repositories.base import BaseRepository
from app.schemas.agent import AgentQueryRequest, AgentQueryResponse, MemoryItem, StoreMemoryRequest, ToolResultSchema
from app.services.agent.memory import MemoryService, MemoryType
from app.services.agent.orchestrator import run_agent
from app.services.audit import AuditService

router = APIRouter(prefix="/agent", tags=["Agentic AI"])


@router.post("/query", response_model=AgentQueryResponse)
async def agent_query(
    body: AgentQueryRequest,
    user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """
    Run the full multi-agent LangGraph workflow:
    Planner → Research → Tool → RAG → Memory → Report
    """
    conv_repo = BaseRepository(Conversation, db)

    # Resolve or create conversation
    if body.conversation_id:
        conv = await conv_repo.get(body.conversation_id)
    else:
        conv = await conv_repo.create(title=body.query[:80], user_id=user.id)

    # Audit the query
    audit = AuditService(db)
    await audit.log("agent.query", user_id=user.id, resource_type="conversation",
                    resource_id=str(conv.id), meta={"query": body.query[:200]})

    response = await run_agent(
        query=body.query,
        user_id=user.id,
        conversation_id=conv.id,
        db=db,
    )

    await audit.log("agent.response", user_id=user.id, resource_type="conversation",
                    resource_id=str(conv.id), meta={"tools_used": len(response.tool_results)})

    return AgentQueryResponse(
        answer=response.answer,
        plan=response.plan,
        reasoning=response.reasoning,
        tool_results=[ToolResultSchema(**{k: v for k, v in tr.items() if k in ToolResultSchema.model_fields})
                      for tr in response.tool_results],
        citations=response.citations,
        conversation_id=conv.id,
    )


@router.get("/memory", response_model=list[MemoryItem])
async def get_memories(user: CurrentUser, db: Annotated[AsyncSession, Depends(get_db)]):
    svc = MemoryService(db)
    return await svc.recall(user.id)


@router.post("/memory", response_model=MemoryItem, status_code=201)
async def store_memory(
    body: StoreMemoryRequest,
    user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    svc = MemoryService(db)
    try:
        mem_type = MemoryType(body.memory_type)
    except ValueError:
        mem_type = MemoryType.AGENT
    return await svc.store(user_id=user.id, key=body.key, value=body.value, memory_type=mem_type)


@router.get("/tools", tags=["MCP"])
async def list_tools(_: CurrentUser):
    """List all registered MCP tools."""
    from app.mcp.client import MCPClient
    return {"tools": MCPClient().list_tools()}
