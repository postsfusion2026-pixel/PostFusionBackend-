from fastapi import APIRouter, Depends, HTTPException, Query, Path, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.schemas.user import UserResponse, UserListResponse, UserUpdate
from app.schemas.base import SuccessResponse, PaginatedResponse
from app.services.user_service import user_service
from app.core.dependencies import get_current_user
from app.models.user import User

router = APIRouter(prefix="/users", tags=["Users"])

# ─────────────────────────────────────────────────────────────────────────────
# GET ALL USERS — with pagination constraints
#
# FIX 1: Added Query() with constraints
# Query(100, ge=1, le=500):
#   default=100, minimum=1 (ge=greater than or equal), maximum=500 (le=less than or equal)
#   Someone sending ?limit=999999 now gets a 422 validation error automatically
#
# FIX 2: Returns PaginatedResponse so frontend knows total count
# FIX 3: Uses UserListResponse (lighter schema) instead of full UserResponse
# ─────────────────────────────────────────────────────────────────────────────
@router.get("/", response_model=PaginatedResponse[UserListResponse])
async def get_users(
    skip: int = Query(
        default=0,
        ge=0,                           # ge = greater than or equal
        description="Number of records to skip for pagination"
    ),
    limit: int = Query(
        default=10,
        ge=1,                           # minimum 1 — can't request 0 items
        le=500,                         # maximum 500 — prevents DB dumps
        description="Number of records to return (max 500)"
    ),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # At this point skip and limit are guaranteed valid integers
    # No negative values, no absurdly large limits — Pydantic handled it

    # Two DB queries:
    # Query 1: SELECT * FROM users OFFSET skip LIMIT limit
    users = await user_service.get_all(db, skip=skip, limit=limit)

    # Query 2: SELECT COUNT(*) FROM users
    # Frontend needs total count to build pagination UI
    # (e.g. "Page 2 of 10" — frontend calculates: total/limit = pages)
    total = await user_service.count(db)

    return PaginatedResponse(
        data=users,
        total=total,
        skip=skip,
        limit=limit,
        message=f"Retrieved {len(users)} of {total} users"
    )

# ─────────────────────────────────────────────────────────────────────────────
# GET SINGLE USER
# ─────────────────────────────────────────────────────────────────────────────
@router.get("/{user_id}", response_model=SuccessResponse[UserResponse])
async def get_user(
    user_id: int = Path(
        gt=0,                           # gt = greater than → must be > 0
        description="The ID of the user to retrieve"
        # This description shows in Swagger automatically
    ),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # At this point:
    # → user_id is guaranteed to be a positive integer (Path enforced it)
    # → current_user is guaranteed to be a valid logged-in User object
    # → db is a live AsyncSession ready for queries
    user = await user_service.get(db, user_id)

    # If no user found with that ID → return 404
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Wrap in envelope → {"success": true, "data": {...}, "message": "..."}
    return SuccessResponse(data=user, message="User retrieved successfully")


# ─────────────────────────────────────────────────────────────────────────────
# UPDATE USER
#
# FIX 1: Takes UserUpdate schema instead of raw dict
#         → only username, email, password can be updated
#         → all fields optional — send only what you want to change
#
# FIX 2: Ownership check
#         → users can only update their OWN profile
#         → prevents user 2 from updating user 1's data
#
# Using PATCH not PUT:
# PUT = replace entire resource (all fields required)
# PATCH = partial update (only send what changes) ← correct for optional updates
# ─────────────────────────────────────────────────────────────────────────────
@router.patch("/{user_id}", response_model=SuccessResponse[UserResponse])
async def update_user(
    user_id: int,
    user_data: UserUpdate,                           # ← Pydantic schema, not dict
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # ── OWNERSHIP CHECK ──────────────────────────────────────────────────────
    # Only allow users to update their own profile
    # current_user is injected by get_current_user dependency
    if current_user.id != user_id:
        raise HTTPException(
            status_code=403,    # 403 Forbidden (not 401 Unauthorized)
            detail="You can only update your own profile"
            # 401 = not authenticated
            # 403 = authenticated but not allowed — correct here
        )

    # ── DUPLICATE CHECK ──────────────────────────────────────────────────────
    # If they're changing email, make sure new email isn't taken
    if user_data.email:
        existing = await user_service.get_by_email(db, user_data.email)
        if existing and existing.id != user_id:
            raise HTTPException(status_code=400, detail="Email already in use")

    # ── DUPLICATE USERNAME CHECK ─────────────────────────────────────────────
    if user_data.username:
        existing = await user_service.get_by_username(db, user_data.username)
        if existing and existing.id != user_id:
            raise HTTPException(status_code=400, detail="Username already taken")

    # ── PERFORM UPDATE ───────────────────────────────────────────────────────
    # model_dump(exclude_none=True):
    # exclude_none=True → only include fields that were actually sent
    # If username=None (not sent), it's excluded → DB field stays unchanged
    update_data = user_data.model_dump(exclude_none=True)

    # If password is being changed, hash it before storing
    if "password" in update_data:
        from app.core.security import hash_password
        update_data["hashed_password"] = hash_password(update_data.pop("password"))
        # pop("password") removes the plain text key
        # we store it as "hashed_password" to match the DB column

    updated_user = await user_service.update(db, user_id, update_data)
    if not updated_user:
        raise HTTPException(status_code=404, detail="User not found")

    return SuccessResponse(data=updated_user, message="User updated successfully")


# ─────────────────────────────────────────────────────────────────────────────
# DELETE USER
#
# FIX: Ownership check — users can only delete their own account
# ─────────────────────────────────────────────────────────────────────────────
@router.delete("/{user_id}", status_code=200)
async def delete_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Ownership check
    if current_user.id != user_id:
        raise HTTPException(
            status_code=403,
            detail="You can only delete your own account"
        )

    deleted = await user_service.delete(db, user_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="User not found")

    # Return 200 with message instead of 204 No Content
    # 204 means "no body" — but a message is more helpful to the client
    return SuccessResponse(data=None, message="User deleted successfully")