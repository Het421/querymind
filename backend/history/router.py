from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID
from backend.database import get_db
from backend.auth.jwt import get_current_user
from backend.auth.models import User
from backend.history.models import ChatHistory
from backend.schema.models import Schema
from backend.history.schemas import ChatMessageCreate, ChatMessageResponse

router = APIRouter(prefix="/history", tags=["Chat History"])


@router.post("/", response_model=ChatMessageResponse, status_code=201)
def save_message(
    message_data: ChatMessageCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Save a single chat message to history.
    Called after every user message and every assistant response.
    """
    # If schema_id provided, verify it belongs to current user
    if message_data.schema_id:
        schema = db.query(Schema).filter(
            Schema.id == message_data.schema_id,
            Schema.user_id == current_user.id
        ).first()

        if not schema:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Schema not found."
            )

    new_message = ChatHistory(
        user_id=current_user.id,
        schema_id=message_data.schema_id,
        role=message_data.role,
        message=message_data.message,
        sql_output=message_data.sql_output
    )

    db.add(new_message)
    db.commit()
    db.refresh(new_message)

    return new_message


@router.get("/schema/{schema_id}", response_model=List[ChatMessageResponse])
def get_history_by_schema(
    schema_id: UUID,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get all chat messages for a specific schema.
    This is what populates the history panel in the UI.
    Returns messages in chronological order (oldest first).
    limit controls how many messages to return — default 50.
    """
    # Verify schema belongs to current user
    schema = db.query(Schema).filter(
        Schema.id == schema_id,
        Schema.user_id == current_user.id
    ).first()

    if not schema:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Schema not found."
        )

    messages = db.query(ChatHistory).filter(
        ChatHistory.user_id == current_user.id,
        ChatHistory.schema_id == schema_id
    ).order_by(
        ChatHistory.created_at.asc()  # oldest first for chat display
    ).limit(limit).all()

    return messages


@router.get("/schema/{schema_id}/recent", response_model=List[ChatMessageResponse])
def get_recent_messages(
    schema_id: UUID,
    limit: int = 10,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get the most recent messages for a schema.
    The agent uses this to understand conversation context
    before generating a new SQL response.
    Default limit is 10 — last 10 messages gives enough context.
    """
    schema = db.query(Schema).filter(
        Schema.id == schema_id,
        Schema.user_id == current_user.id
    ).first()

    if not schema:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Schema not found."
        )

    # Get most recent messages then reverse so oldest is first
    # This gives the agent messages in correct chronological order
    messages = db.query(ChatHistory).filter(
        ChatHistory.user_id == current_user.id,
        ChatHistory.schema_id == schema_id
    ).order_by(
        ChatHistory.created_at.desc()
    ).limit(limit).all()

    # Reverse to get chronological order
    return list(reversed(messages))


@router.delete("/schema/{schema_id}", status_code=204)
def clear_schema_history(
    schema_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Clear all chat history for a specific schema.
    Useful when the user wants a fresh start on a schema.
    """
    schema = db.query(Schema).filter(
        Schema.id == schema_id,
        Schema.user_id == current_user.id
    ).first()

    if not schema:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Schema not found."
        )

    db.query(ChatHistory).filter(
        ChatHistory.user_id == current_user.id,
        ChatHistory.schema_id == schema_id
    ).delete()

    db.commit()
    return None