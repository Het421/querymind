from pydantic import BaseModel, EmailStr, field_validator
from datetime import datetime
from uuid import UUID
from typing import Optional


# --- Request schemas (data coming IN to the API) ---

class UserRegister(BaseModel):
    """What we expect when someone registers."""
    email: EmailStr        # EmailStr automatically validates email format
    password: str
    full_name: Optional[str] = None
    @field_validator("password")
    @classmethod
    def password_must_be_valid(cls, v):
        if len(v) < 6:
            raise ValueError("Password must be at least 6 characters.")
        if len(v) > 72:
            raise ValueError("Password cannot be longer than 72 characters.")
        return v

class UserLogin(BaseModel):
    """What we expect when someone logs in."""
    email: EmailStr
    password: str


# --- Response schemas (data going OUT of the API) ---

class UserResponse(BaseModel):
    """What we return about a user — never includes the password."""
    id: UUID
    email: str
    full_name: Optional[str]
    is_active: bool
    created_at: datetime

    # This tells Pydantic to read data from SQLAlchemy model attributes
    # Without this, Pydantic wouldn't know how to read SQLAlchemy objects
    model_config = {"from_attributes": True}


class TokenResponse(BaseModel):
    """What we return after a successful login."""
    access_token: str
    token_type: str = "bearer"
    user: UserResponse