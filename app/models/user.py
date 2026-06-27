# app/models/user.py

from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.sql import func
from app.db.base import Base

class User(Base):
    __tablename__ = "users"

    id             = Column(Integer, primary_key=True, index=True)
    username       = Column(String, unique=True, nullable=False)
    email          = Column(String, unique=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_active      = Column(Boolean, default=True)

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),  # set by PostgreSQL on INSERT
        nullable=False
    )

    # ─────────────────────────────────────────────────────────────────────────
    # NEW COLUMN — updated_at
    # onupdate=func.now(): automatically updates timestamp on every UPDATE
    # nullable=True: existing rows don't have this value yet — they'll be NULL
    # In the next migration, we can backfill if needed
    # ─────────────────────────────────────────────────────────────────────────
    updated_at = Column(
        DateTime(timezone=True),
        onupdate=func.now(),       # fires on UPDATE (not INSERT)
        nullable=True
    )