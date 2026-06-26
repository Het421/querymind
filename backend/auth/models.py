import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Boolean, DateTime
from sqlalchemy.dialects.postgresql import UUID
from backend.database import Base


class User(Base):
    # This tells SQLAlchemy the actual table name in PostgreSQL
    __tablename__ = "users"

    # UUID primary key — unique, non-guessable identifier
    # default generates a new UUID automatically for every new user
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True
    )

    # Email — must be unique across all users
    # index=True makes lookups by email fast
    email = Column(
        String,
        unique=True,
        nullable=False,
        index=True
    )

    # We never store raw passwords — only the hashed version
    hashed_password = Column(
        String,
        nullable=False
    )

    # Optional display name
    full_name = Column(
        String,
        nullable=True
    )

    # Active flag — False means user is disabled, not deleted
    is_active = Column(
        Boolean,
        default=True,
        nullable=False
    )

    # Timestamp — automatically set to now when user is created
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    def __repr__(self):
        return f"<User email={self.email}>"