import time
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.logger import logger

def register_middleware(app: FastAPI):

    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.ALLOWED_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Request Logger
    @app.middleware("http")
    async def log_requests(request: Request, call_next):
        start = time.time()
        response = await call_next(request)
        duration = round((time.time() - start) * 1000, 2)

        logger.info(
            f"{request.method} {request.url.path} "
            f"| status={response.status_code} "
            f"| {duration}ms"
        )
        return response