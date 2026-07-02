from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.schemas.auth import LoginRequest, TokenResponse
from app.schemas.user import UserCreate, UserResponse
from app.schemas.base import SuccessResponse
from app.services.user_service import user_service
from app.core.security import verify_password, create_access_token
from app.core.dependencies import get_current_user

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post(
    "/register",
    response_model=SuccessResponse[UserResponse],  # wrapped in envelope
    status_code=201
)
async def register(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db)
):
    # Check duplicate email
    existing_email = await user_service.get_by_email(db, user_data.email)
    if existing_email:
        raise HTTPException(status_code=400, detail="Email already registered")

    # Check duplicate username
    existing_username = await user_service.get_by_username(db, user_data.username)
    if existing_username:
        raise HTTPException(status_code=400, detail="Username already taken")

    user = await user_service.create_user(db, user_data)

    return SuccessResponse(
        data=user,
        message="Account created successfully"
    )


@router.post("/login", response_model=SuccessResponse[TokenResponse])
async def login(
    credentials: LoginRequest,
    db: AsyncSession = Depends(get_db)
):
    user = await user_service.get_by_email(db, credentials.email)

    # Both checks in one if — prevents timing attacks and info leakage
    if not user or not verify_password(credentials.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )

    # Check if account is active — handle disabled accounts
    if not user.is_active:
        raise HTTPException(
            status_code=403,
            detail="Account is disabled. Contact support."
        )

    token = create_access_token({"sub": str(user.id)})

    return SuccessResponse(
        data={"access_token": token, "token_type": "bearer"},
        message="Login successful"
    )


@router.get("/me", response_model=SuccessResponse[UserResponse])
async def me(current_user=Depends(get_current_user)):
    return SuccessResponse(data=current_user, message="Profile retrieved")