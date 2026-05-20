from fastapi import APIRouter
from app.api.v1 import users, auth  # 👈 add auth

router = APIRouter(prefix="/api/v1")
router.include_router(users.router)
router.include_router(auth.router)  # 👈 add this