from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.schemas.user import UserCreate, UserResponse
from app.services.user_service import user_service
from app.core.dependencies import get_current_user

router = APIRouter(prefix="/users", tags=["Users"])

@router.get("/", response_model=list[UserResponse])
async def get_users(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
):
    return await user_service.get_all(db, skip=skip, limit=limit)

@router.get("/{user_id}", response_model=UserResponse)
async def get_user(user_id: int, db: AsyncSession = Depends(get_db)):
    user = await user_service.get(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    user_data: dict,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)  # 🔐 protected
):
    user = await user_service.update(db, user_id, user_data)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@router.delete("/{user_id}", status_code=204)
async def delete_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)  # 🔐 protected
):
    user = await user_service.delete(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")