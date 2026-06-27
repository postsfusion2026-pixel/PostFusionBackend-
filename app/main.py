# from fastapi import FastAPI
# from app.core.config import settings
# from app.core.middleware import register_middleware
# from app.core.exceptions import register_exception_handlers
# from app.core.logger import logger
# # from app.db.session import engine        # 👈 commented out
# # from app.db.base import Base             # 👈 commented out
# from app.api.v1.router import router

# app = FastAPI(
#     title=settings.APP_NAME,
#     debug=settings.DEBUG,
#     docs_url="/docs" if not settings.is_production else None,
#     redoc_url="/redoc" if not settings.is_production else None,
# )

# register_middleware(app)
# register_exception_handlers(app)

# @app.on_event("startup")
# async def startup():
#     # async with engine.begin() as conn:   # 👈 commented out
#     #     await conn.run_sync(Base.metadata.create_all)
#     logger.info(f"{settings.APP_NAME} started | env={settings.ENVIRONMENT}")

# @app.on_event("shutdown")
# async def shutdown():
#     logger.info("App shutting down...")
#     # await engine.dispose()               # 👈 commented out

# app.include_router(router)

# @app.get("/health")
# def health_check():
#     return {
#         "status": "ok",
#         "app": settings.APP_NAME,
#         "environment": settings.ENVIRONMENT
#     }

# app/main.py

from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.core.config import settings
from app.core.middleware import register_middleware
from app.core.exceptions import register_exception_handlers
from app.core.logger import logger
from app.db.session import engine          # ← uncomment this
from app.db.base import Base               # ← uncomment this
from app.api.v1.router import router


# ─────────────────────────────────────────────────────────────────────────────
# LIFESPAN — Replaces @app.on_event("startup") and @app.on_event("shutdown")
#
# @asynccontextmanager turns this into a context manager:
# Everything BEFORE `yield` runs on startup
# Everything AFTER `yield` runs on shutdown
#
# FastAPI receives this function and calls it automatically.
# The app stays alive while the yield is active.
# ─────────────────────────────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    # ── STARTUP ──────────────────────────────────────────────────────────────
    logger.info(f"🚀 {settings.APP_NAME} starting | env={settings.ENVIRONMENT}")

    # NOTE: We are NOT using create_all here anymore.
    # Alembic handles table creation from now on.
    # create_all is fine for early learning but breaks in production.
    # We keep this commented for reference only:
    #
    # async with engine.begin() as conn:
    #     await conn.run_sync(Base.metadata.create_all)
    #
    # Instead: run `alembic upgrade head` before starting the app.

    logger.info("✅ Database engine ready")

    yield  # ← App is now alive and serving requests

    # ── SHUTDOWN ─────────────────────────────────────────────────────────────
    # Dispose the engine: closes all connections in the pool gracefully
    # Without this: PostgreSQL might hold orphaned connections open
    await engine.dispose()
    logger.info("🛑 Database connections closed. App shut down.")


# ─────────────────────────────────────────────────────────────────────────────
# THE APP — Pass lifespan here
# FastAPI will call lifespan(app) and manage it automatically
# ─────────────────────────────────────────────────────────────────────────────
app = FastAPI(
    title=settings.APP_NAME,
    debug=settings.DEBUG,
    lifespan=lifespan,                          # ← pass the lifespan function
    docs_url="/docs" if not settings.is_production else None,
    redoc_url="/redoc" if not settings.is_production else None,
)

register_middleware(app)
register_exception_handlers(app)
app.include_router(router)


@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "app": settings.APP_NAME,
        "environment": settings.ENVIRONMENT,
    }