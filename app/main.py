from fastapi import FastAPI
from app.core.config import settings
from app.db.session import engine
from app.db.base import Base
from app.api.v1.router import router

app = FastAPI(title=settings.APP_NAME)

@app.on_event("startup")
async def startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

app.include_router(router)  # 👈 register all routes

@app.get("/health")
def health_check():
    return {"status": "ok"}