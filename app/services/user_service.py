from app.db.crud_base import CRUDBase
from app.models.user import User
from app.schemas.user import UserCreate
from app.core.security import hash_password
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

class UserCRUD(CRUDBase[User]):

    async def get_by_email(self, db: AsyncSession, email: str):
        result = await db.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()

    async def create_user(self, db: AsyncSession, user_data: UserCreate):
        return await self.create(db, {
            "username": user_data.username,
            "email": user_data.email,
            "hashed_password": hash_password(user_data.password)
        })

# single instance to use everywhere
user_service = UserCRUD(User)