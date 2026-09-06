import uuid

from pydantic import BaseModel, Field


class ConciergeMessageRequest(BaseModel):
    message: str = Field(min_length=1, max_length=2000)
    conversation_id: uuid.UUID | None = None


class PublicConciergeMessageRequest(ConciergeMessageRequest):
    lead_id: uuid.UUID


class ToolCallRead(BaseModel):
    name: str
    arguments: dict
    result: dict


class ConciergeMessageResponse(BaseModel):
    conversation_id: uuid.UUID
    reply: str
    lead_status: str
    tool_calls: list[ToolCallRead]
