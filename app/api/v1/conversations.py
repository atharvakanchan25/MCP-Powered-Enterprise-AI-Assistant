import uuid
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import CurrentUser
from app.db.session import get_db
from app.models.conversation import Conversation
from app.repositories.base import BaseRepository
from app.schemas.conversation import ConversationCreate, ConversationResponse

router = APIRouter(prefix="/conversations", tags=["Conversations"])


def _conv_repo(db: Annotated[AsyncSession, Depends(get_db)]):
    return BaseRepository(Conversation, db)


@router.post("/", response_model=ConversationResponse, status_code=201)
async def create_conversation(
    data: ConversationCreate,
    user: CurrentUser,
    repo: Annotated[BaseRepository, Depends(_conv_repo)],
):
    return await repo.create(title=data.title, user_id=user.id, meta=data.meta)


@router.get("/", response_model=list[ConversationResponse])
async def list_conversations(
    user: CurrentUser,
    repo: Annotated[BaseRepository, Depends(_conv_repo)],
    limit: int = 20,
    offset: int = 0,
):
    return await repo.list(limit=limit, offset=offset, user_id=user.id)


@router.get("/{conversation_id}", response_model=ConversationResponse)
async def get_conversation(
    conversation_id: uuid.UUID,
    user: CurrentUser,
    repo: Annotated[BaseRepository, Depends(_conv_repo)],
):
    from app.core.exceptions import NotFoundError, ForbiddenError
    conv = await repo.get(conversation_id)
    if not conv:
        raise NotFoundError("Conversation")
    if conv.user_id != user.id:
        raise ForbiddenError()
    return conv


@router.delete("/{conversation_id}", status_code=204)
async def delete_conversation(
    conversation_id: uuid.UUID,
    user: CurrentUser,
    repo: Annotated[BaseRepository, Depends(_conv_repo)],
):
    from app.core.exceptions import NotFoundError, ForbiddenError
    conv = await repo.get(conversation_id)
    if not conv:
        raise NotFoundError("Conversation")
    if conv.user_id != user.id:
        raise ForbiddenError()
    await repo.delete(conv)
