import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from backend.database import Base


class ChatHistory(Base):
    __tablename__ = "chat_history"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True
    )

    # Which user this message belongs to
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Which schema was active when this message was sent
    # nullable=True because user might chat without a schema selected
    schema_id = Column(
        UUID(as_uuid=True),
        ForeignKey("schemas.id", ondelete="CASCADE"),
        nullable=True,
        index=True
    )

    # "user" or "assistant"
    role = Column(
        String(20),
        nullable=False
    )

    # The actual message text
    message = Column(
        Text,
        nullable=False
    )

    # The SQL output if assistant generated one
    # Stored separately so frontend can display it
    # in a code block easily
    sql_output = Column(
        Text,
        nullable=True
    )

    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    # Relationships for easy access
    user = relationship("User", backref="chat_history")
    schema = relationship("Schema", backref="chat_history")

    def __repr__(self):
        return f"<ChatHistory role={self.role} schema_id={self.schema_id}>"