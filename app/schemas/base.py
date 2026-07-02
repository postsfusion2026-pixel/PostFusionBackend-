from pydantic import BaseModel
from typing import TypeVar, Generic, Optional, Any

# TypeVar for the data payload — works with any schema
T = TypeVar("T")


# ─────────────────────────────────────────────────────────────────────────────
# SuccessResponse — Wraps successful responses
# Generic[T] means the "data" field can be any type:
# SuccessResponse[UserResponse] → data is a UserResponse object
# SuccessResponse[list[UserResponse]] → data is a list of UserResponse objects
# ─────────────────────────────────────────────────────────────────────────────
class SuccessResponse(BaseModel, Generic[T]):
    success: bool = True
    message: str = "Success"
    data: Optional[T] = None    # the actual payload


# ─────────────────────────────────────────────────────────────────────────────
# ErrorResponse — Consistent error shape
# Your exception handlers already return this shape,
# now we have a Pydantic model for it too
# ─────────────────────────────────────────────────────────────────────────────
class ErrorResponse(BaseModel):
    success: bool = False
    error: str
    detail: Optional[Any] = None  # optional extra info (validation errors, etc.)


# ─────────────────────────────────────────────────────────────────────────────
# PaginatedResponse — For list endpoints with pagination info
# ─────────────────────────────────────────────────────────────────────────────
class PaginatedResponse(BaseModel, Generic[T]):
    success: bool = True
    message: str = "Success"
    data: list[T]               # list of items
    total: int                  # total records in DB (for frontend pagination UI)
    skip: int                   # current offset
    limit: int                  # current page size