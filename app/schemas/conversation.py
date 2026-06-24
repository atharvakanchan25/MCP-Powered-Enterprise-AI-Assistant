import uuid
from datetime import datetime

from pydantic import BaseModel

from app.models.conversation import ConversationStatus, MessageRole


class ConversationCreate(BaseModel):
    title: str = "New Conversation"
    meta: dict | None = None


class ConversationResponse(BaseModel):
    id: uuid.UUID
    title: str
    status: ConversationStatus
    user_id: uuid.UUID
    created_at: datetime

    model_config = {"from_attributes": True}


class MessageCreate(BaseModel):
    content: str
    role: MessageRole = MessageRole.USER


class MessageResponse(BaseModel):
    id: uuid.UUID
    role: MessageRole
    content: str
    token_count: int | None
    conversation_id: uuid.UUID
    created_at: datetime

    model_config = {"from_attributes": True}
