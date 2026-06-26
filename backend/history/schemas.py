from pydantic import BaseModel
from datetime import datetime
from uuid import UUID
from typing import Optional


# --- Request schemas ---

class ChatMessageCreate(BaseModel):
    """
    What we expect when saving a new chat message.
    Both user messages and assistant responses use this.
    """
    schema_id: Optional[UUID] = None  # which schema was active
    role: str                          # "user" or "assistant"
    message: str                       # the actual message text
    sql_output: Optional[str] = None  # SQL if assistant generated one


# --- Response schemas ---

class ChatMessageResponse(BaseModel):
    """What we return for a single chat message."""
    id: UUID
    schema_id: Optional[UUID]
    role: str
    message: str
    sql_output: Optional[str]
    created_at: datetime

    model_config = {"from_attributes": True}