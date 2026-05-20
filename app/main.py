from fastapi import FastAPI
from app.core.config import settings
from app.core.middleware import register_middleware
from app.core.exceptions import register_exception_handlers
from app.core.logger import logger
from app.db.session import engine
from app.db.base import Base
from app.api.v1.router import router

app = FastAPI(
    title=settings.APP_NAME,
    debug=settings.DEBUG,
    docs_url="/docs" if not settings.is_production else None,  # hide docs in prod
    redoc_url="/redoc" if not settings.is_production else None,
)

register_middleware(app)
register_exception_handlers(app)

@app.on_event("startup")
async def startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info(f" {settings.APP_NAME} started | env={settings.ENVIRONMENT}")

@app.on_event("shutdown")
async def shutdown():
    logger.info("App shutting down...")
    await engine.dispose()

app.include_router(router)

@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "app": settings.APP_NAME,
        "environment": settings.ENVIRONMENT
    }