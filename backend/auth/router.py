from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.auth.models import User
from backend.auth.hashing import hash_password, verify_password
from backend.auth.jwt import create_access_token, get_current_user
from backend.auth.schemas import UserRegister, TokenResponse, UserResponse

# APIRouter is like a mini FastAPI app
# prefix means all routes in this file start with /auth
# tags groups them together in the /docs page
router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=UserResponse, status_code=201)
def register(user_data: UserRegister, db: Session = Depends(get_db)):
    """
    Register a new user account.
    Expects: email, password, optional full_name
    Returns: the created user (without password)
    """
    # Check if email already exists
    existing_user = db.query(User).filter(
        User.email == user_data.email
    ).first()

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An account with this email already exists."
        )

    # Create new user with hashed password
    new_user = User(
        email=user_data.email,
        hashed_password=hash_password(user_data.password),
        full_name=user_data.full_name
    )

    # Save to database
    db.add(new_user)
    db.commit()

    # Refresh to get the generated id and created_at
    db.refresh(new_user)

    return new_user


@router.post("/login", response_model=TokenResponse)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """
    OAuth2PasswordRequestForm gives us username and password
    from the form. We treat username as email.
    This makes the Swagger Authorize button work directly.
    """
    user = db.query(User).filter(
        User.email == form_data.username
    ).first()

    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password."
        )

    token = create_access_token(data={"sub": user.email})

    return TokenResponse(
        access_token=token,
        token_type="bearer",
        user=UserResponse.model_validate(user)
    )


@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    """
    Returns the currently logged in user's details.
    This is a protected endpoint — requires a valid token.
    """
    return current_user


# Import here to avoid circular imports
from backend.auth.jwt import get_current_user