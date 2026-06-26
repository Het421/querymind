from pydantic import BaseModel
from datetime import datetime
from uuid import UUID
from typing import Optional


# --- Request schemas ---

class SchemaCreate(BaseModel):
    """What we expect when saving a new schema."""
    name: str
    platform: str          # "postgresql", "mysql", "sqlite", "sqlserver"
    schema_content: str    # the actual DDL text
    source: str = "manual" # "manual" or "mcp"
    connection_string: Optional[str] = None


class SchemaUpdate(BaseModel):
    """What we expect when updating an existing schema."""
    name: Optional[str] = None
    schema_content: Optional[str] = None
    platform: Optional[str] = None


# --- Response schemas ---

class SchemaResponse(BaseModel):
    """What we return about a saved schema."""
    id: UUID
    name: str
    platform: str
    schema_content: str
    source: str
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}