from pydantic import BaseModel, Field, ConfigDict, field_validator
from typing import Literal, Optional
from datetime import datetime, timezone


Sender = Literal["user", "system"]


class MessageIn(BaseModel):
    message_id: str = Field(..., min_length=1, max_length=100)
    session_id: str = Field(..., min_length=1, max_length=100)
    content: str = Field(..., min_length=1)
    timestamp: datetime
    sender: Sender

    model_config = ConfigDict(extra="forbid")

    @field_validator("timestamp")
    @classmethod
    def ensure_timezone(cls, v: datetime) -> datetime:
        # Normalize to UTC if naive
        if v.tzinfo is None:
            return v.replace(tzinfo=timezone.utc)
        return v


class MessageMetadata(BaseModel):
    word_count: int
    character_count: int
    processed_at: datetime


class MessageOut(BaseModel):
    message_id: str
    session_id: str
    content: str
    timestamp: datetime
    sender: Sender
    metadata: MessageMetadata


class ErrorDetail(BaseModel):
    code: str
    message: str
    details: Optional[str] = None


class SuccessResponse(BaseModel):
    status: Literal["success"]
    data: MessageOut


class ErrorResponse(BaseModel):
    status: Literal["error"]
    error: ErrorDetail
