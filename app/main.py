from fastapi import FastAPI
from app.core.config import settings
from app.core.middleware import register_middleware
from app.core.exceptions import register_exception_handlers
from app.core.logger import logger
# from app.db.session import engine        # 👈 commented out
# from app.db.base import Base             # 👈 commented out
from app.api.v1.router import router

app = FastAPI(
    title=settings.APP_NAME,
    debug=settings.DEBUG,
    docs_url="/docs" if not settings.is_production else None,
    redoc_url="/redoc" if not settings.is_production else None,
)

register_middleware(app)
register_exception_handlers(app)

@app.on_event("startup")
async def startup():
    # async with engine.begin() as conn:   # 👈 commented out
    #     await conn.run_sync(Base.metadata.create_all)
    logger.info(f"{settings.APP_NAME} started | env={settings.ENVIRONMENT}")

@app.on_event("shutdown")
async def shutdown():
    logger.info("App shutting down...")
    # await engine.dispose()               # 👈 commented out

app.include_router(router)

@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "app": settings.APP_NAME,
        "environment": settings.ENVIRONMENT
    }