from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from typing import List
from backend.database import get_db
from backend.auth.jwt import get_current_user
from backend.auth.models import User
from backend.schema.models import Schema
from backend.schema.schemas import SchemaCreate, SchemaUpdate, SchemaResponse
from uuid import UUID

router = APIRouter(prefix="/schemas", tags=["Schemas"])


@router.post("/", response_model=SchemaResponse, status_code=201)
def create_schema(
    schema_data: SchemaCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Save a new schema for the logged in user.
    The schema is saved but not set as active by default.
    """
    # Check if user already has a schema with this name
    existing = db.query(Schema).filter(
        Schema.user_id == current_user.id,
        Schema.name == schema_data.name
    ).first()

    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"You already have a schema named '{schema_data.name}'."
        )

    new_schema = Schema(
        user_id=current_user.id,
        name=schema_data.name,
        platform=schema_data.platform,
        schema_content=schema_data.schema_content,
        source=schema_data.source,
        connection_string=schema_data.connection_string
    )

    db.add(new_schema)
    db.commit()
    db.refresh(new_schema)

    return new_schema


@router.post("/upload", response_model=SchemaResponse, status_code=201)
async def upload_schema_file(
    name: str,
    platform: str,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Upload a .sql file and save it as a schema.
    The file content is read and stored as the schema_content.
    """
    # Validate file type
    if not file.filename.endswith(".sql"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only .sql files are accepted."
        )

    # Read file content
    content = await file.read()
    schema_content = content.decode("utf-8")

    # Check for duplicate name
    existing = db.query(Schema).filter(
        Schema.user_id == current_user.id,
        Schema.name == name
    ).first()

    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"You already have a schema named '{name}'."
        )

    new_schema = Schema(
        user_id=current_user.id,
        name=name,
        platform=platform,
        schema_content=schema_content,
        source="manual"
    )

    db.add(new_schema)
    db.commit()
    db.refresh(new_schema)

    return new_schema


@router.get("/", response_model=List[SchemaResponse])
def get_all_schemas(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get all schemas belonging to the logged in user.
    Used to populate the schema library sidebar in the UI.
    """
    schemas = db.query(Schema).filter(
        Schema.user_id == current_user.id
    ).order_by(Schema.created_at.desc()).all()

    return schemas


@router.get("/active", response_model=SchemaResponse)
def get_active_schema(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get the currently active schema for the logged in user.
    The agent uses this to know which schema to work with.
    """
    active_schema = db.query(Schema).filter(
        Schema.user_id == current_user.id,
        Schema.is_active == True
    ).first()

    if not active_schema:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No active schema selected. Please select a schema first."
        )

    return active_schema


@router.get("/{schema_id}", response_model=SchemaResponse)
def get_schema(
    schema_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get a specific schema by its ID.
    Only returns it if it belongs to the logged in user.
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

    return schema


@router.patch("/{schema_id}/activate", response_model=SchemaResponse)
def activate_schema(
    schema_id: UUID,  
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Set a schema as the active one for the current user.
    First deactivates all other schemas, then activates this one.
    Only one schema can be active at a time.
    """
    # First deactivate all schemas for this user
    db.query(Schema).filter(
        Schema.user_id == current_user.id
    ).update({"is_active": False})

    # Now activate the requested schema
    schema = db.query(Schema).filter(
        Schema.id == schema_id,
        Schema.user_id == current_user.id
    ).first()

    if not schema:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Schema not found."
        )

    schema.is_active = True
    db.commit()
    db.refresh(schema)

    return schema


@router.patch("/{schema_id}", response_model=SchemaResponse)
def update_schema(
    schema_id: str,
    update_data: SchemaUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update a schema's name, content, or platform.
    Only updates fields that are actually provided.
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

    # Only update fields that were actually sent
    # exclude_unset=True means fields not included in the request are ignored
    update_fields = update_data.model_dump(exclude_unset=True)
    for field, value in update_fields.items():
        setattr(schema, field, value)

    db.commit()
    db.refresh(schema)

    return schema


@router.delete("/{schema_id}", status_code=204)
def delete_schema(
    schema_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Delete a schema permanently.
    Also deletes all chat history linked to this schema
    because of the CASCADE we set up in the database model.
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

    db.delete(schema)
    db.commit()

    # 204 means success with no content to return
    return None