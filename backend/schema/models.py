import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Boolean, DateTime, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from backend.database import Base


class Schema(Base):
    __tablename__ = "schemas"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True
    )

    # Foreign key — links this schema to the user who owns it
    # ondelete="CASCADE" means if the user is deleted,
    # all their schemas are automatically deleted too
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # User-given name for this schema
    name = Column(
        String(100),
        nullable=False
    )

    # Which SQL platform this schema belongs to
    # e.g. "postgresql", "mysql", "sqlite", "sqlserver"
    platform = Column(
        String(50),
        nullable=False
    )

    # The actual schema DDL content
    # Text type because DDL can be very long
    schema_content = Column(
        Text,
        nullable=False
    )

    # How was this schema added — "manual" or "mcp"
    source = Column(
        String(20),
        nullable=False,
        default="manual"
    )

    # Only filled when source is "mcp"
    # We store this so the user can reconnect later
    connection_string = Column(
        String(500),
        nullable=True
    )

    # Is this the currently active schema for the user
    is_active = Column(
        Boolean,
        default=False,
        nullable=False
    )

    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    # Relationship — lets us access schema.owner to get the User object
    # and user.schemas to get all schemas belonging to a user
    owner = relationship("User", backref="schemas")

    def __repr__(self):
        return f"<Schema name={self.name} platform={self.platform}>"