from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from backend.database import get_db
from backend.auth.jwt import get_current_user
from backend.auth.models import User
from backend.schema.models import Schema
from backend.schema.schemas import SchemaResponse
from backend.mcp.connector import extract_schema

router = APIRouter(prefix="/mcp", tags=["MCP Database Connector"])


class MCPConnectRequest(BaseModel):
    """
    What we expect when a user wants to connect
    their database directly.
    """
    name: str              # name to save this schema as
    platform: str          # postgresql, mysql, sqlite
    host: Optional[str] = "localhost"
    port: Optional[int] = 5432
    database: str          # database name on their server
    username: str
    password: str


@router.post("/connect", response_model=SchemaResponse, status_code=201)
def connect_and_extract(
    conn_data: MCPConnectRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Connects to the user's database, extracts the full schema,
    and saves it as a named schema in our app.
    The user never has to paste DDL manually.
    """
    # Check for duplicate schema name
    existing = db.query(Schema).filter(
        Schema.user_id == current_user.id,
        Schema.name == conn_data.name
    ).first()

    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"You already have a schema named '{conn_data.name}'."
        )

    # Build the connection string from individual fields
    # We build it here so the user fills a simple form
    # instead of knowing the exact connection string format
    if conn_data.platform == "postgresql":
        connection_string = (
            f"postgresql://{conn_data.username}:{conn_data.password}"
            f"@{conn_data.host}:{conn_data.port}/{conn_data.database}"
        )
    elif conn_data.platform == "mysql":
        connection_string = (
            f"mysql+pymysql://{conn_data.username}:{conn_data.password}"
            f"@{conn_data.host}:{conn_data.port}/{conn_data.database}"
        )
    elif conn_data.platform == "sqlite":
        # SQLite uses a file path not host/port
        connection_string = f"sqlite:///{conn_data.database}"
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Platform '{conn_data.platform}' is not supported."
        )

    # Try to connect and extract schema
    # If connection fails, we catch the error and return
    # a clear message instead of a cryptic server error
    try:
        schema_content = extract_schema(
            conn_data.platform,
            connection_string
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Could not connect to database: {str(e)}"
        )

    # Save the extracted schema
    new_schema = Schema(
        user_id=current_user.id,
        name=conn_data.name,
        platform=conn_data.platform,
        schema_content=schema_content,
        source="mcp",
        # Store connection string so user can reconnect later
        # In production you would encrypt this
        connection_string=connection_string
    )

    db.add(new_schema)
    db.commit()
    db.refresh(new_schema)

    return new_schema


@router.post("/refresh/{schema_id}", response_model=SchemaResponse)
def refresh_schema(
    schema_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Re-connects to the database and refreshes the schema content.
    Useful when the user has made changes to their database
    and wants the assistant to see the updated structure.
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

    if schema.source != "mcp":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This schema was added manually and cannot be refreshed via connection."
        )

    if not schema.connection_string:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No connection string saved for this schema."
        )

    try:
        updated_content = extract_schema(
            schema.platform,
            schema.connection_string
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Could not reconnect to database: {str(e)}"
        )

    schema.schema_content = updated_content
    db.commit()
    db.refresh(schema)

    return schema
