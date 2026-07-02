from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import TypeVar, Generic, Type
from app.db.base import Base
from sqlalchemy import select, func

ModelType = TypeVar("ModelType", bound=Base)

class CRUDBase(Generic[ModelType]):
    def __init__(self, model: Type[ModelType]):
        self.model = model

    async def get(self, db: AsyncSession, id: int):
        result = await db.execute(select(self.model).where(self.model.id == id))
        return result.scalar_one_or_none()

    async def get_all(self, db: AsyncSession, skip: int = 0, limit: int = 100):
        result = await db.execute(select(self.model).offset(skip).limit(limit))
        return result.scalars().all()

    async def create(self, db: AsyncSession, obj_data: dict):
        obj = self.model(**obj_data)
        db.add(obj)
        await db.commit()
        await db.refresh(obj)
        return obj

    async def update(self, db: AsyncSession, id: int, obj_data: dict):
        obj = await self.get(db, id)
        if not obj:
            return None
        for key, value in obj_data.items():
            setattr(obj, key, value)
        await db.commit()
        await db.refresh(obj)
        return obj

    async def delete(self, db: AsyncSession, id: int):
        obj = await self.get(db, id)
        if not obj:
            return None
        await db.delete(obj)
        await db.commit()
        return obj
    
    async def count(self, db: AsyncSession) -> int:
    # SELECT COUNT(*) FROM <table>
        result = await db.execute(
            select(func.count()).select_from(self.model)
        )
        return result.scalar()