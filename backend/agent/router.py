from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from uuid import UUID
from backend.database import get_db
from backend.auth.jwt import get_current_user
from backend.auth.models import User
from backend.schema.models import Schema
from backend.history.models import ChatHistory
from backend.agent.graph import agent

router = APIRouter(prefix="/chat", tags=["Chat"])


class ChatRequest(BaseModel):
    """What we expect when user sends a message."""
    message: str
    schema_id: Optional[UUID] = None  # if None, uses active schema


class ChatResponse(BaseModel):
    """What we return after processing a message."""
    message: str
    sql_output: Optional[str] = None
    explanation: Optional[str] = None
    intent: Optional[str] = None


@router.post("/", response_model=ChatResponse)
def chat(
    request: ChatRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Main chat endpoint.
    Receives user message, runs it through the agent,
    saves both messages to history, returns the response.
    """

    # Get schema — either specified or active one
    if request.schema_id:
        schema = db.query(Schema).filter(
            Schema.id == request.schema_id,
            Schema.user_id == current_user.id
        ).first()
    else:
        schema = db.query(Schema).filter(
            Schema.user_id == current_user.id,
            Schema.is_active == True
        ).first()

    if not schema:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No schema selected. Please select or activate a schema first."
        )

    # Get recent chat history for context
    recent_messages = db.query(ChatHistory).filter(
        ChatHistory.user_id == current_user.id,
        ChatHistory.schema_id == schema.id
    ).order_by(
        ChatHistory.created_at.desc()
    ).limit(10).all()

    # Format history for the agent
    # Reverse so oldest message is first
    history = [
        {"role": msg.role, "message": msg.message}
        for msg in reversed(recent_messages)
    ]

    # Save user message to history
    user_message = ChatHistory(
        user_id=current_user.id,
        schema_id=schema.id,
        role="user",
        message=request.message
    )
    db.add(user_message)
    db.commit()

    # Run the agent
    try:
        result = agent.invoke({
            "user_question": request.message,
            "platform": schema.platform,
            "schema_content": schema.schema_content,
            "chat_history": history,
            "intent": None,
            "relevant_schema": None,
            "generated_sql": None,
            "is_valid": None,
            "validation_error": None,
            "retry_count": 0,
            "explanation": None,
            "final_sql": None,
            "final_explanation": None,
            "final_response": None
        })
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Agent error: {str(e)}"
        )

    # Extract results from agent state
    final_sql = result.get("final_sql")
    final_explanation = result.get("final_explanation")
    final_response = result.get("final_response")
    intent = result.get("intent")

    # Build the assistant message text
    if final_response:
        # General answer — no SQL
        assistant_message_text = final_response
    elif final_sql:
        # SQL was generated
        assistant_message_text = final_explanation or "Here is your SQL query."
    else:
        assistant_message_text = "I could not generate a response. Please try again."

    # Save assistant response to history
    assistant_message = ChatHistory(
        user_id=current_user.id,
        schema_id=schema.id,
        role="assistant",
        message=assistant_message_text,
        sql_output=final_sql
    )
    db.add(assistant_message)
    db.commit()

    return ChatResponse(
        message=assistant_message_text,
        sql_output=final_sql,
        explanation=final_explanation,
        intent=intent
    )
    