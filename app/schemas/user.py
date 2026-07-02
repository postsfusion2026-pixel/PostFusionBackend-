# app/schemas/user.py

from pydantic import BaseModel, EmailStr, field_validator, model_validator
from datetime import datetime
from typing import Optional
import re


# ─────────────────────────────────────────────────────────────────────────────
# UserBase — Fields shared across CREATE and UPDATE
# Both registration and update deal with username and email
# so they live here once instead of being repeated
# ─────────────────────────────────────────────────────────────────────────────
class UserBase(BaseModel):
    username: str
    email: EmailStr   # EmailStr validates format: user@domain.com


# ─────────────────────────────────────────────────────────────────────────────
# UserCreate — What the client sends to REGISTER
# Inherits username + email from UserBase, adds password
# ─────────────────────────────────────────────────────────────────────────────
class UserCreate(UserBase):
    password: str

    # ─────────────────────────────────────────────────────────────────────────
    # @field_validator — runs AFTER Pydantic checks the type
    # "username" = the field this validator applies to
    # mode="after" = run after type conversion (you get a clean str, not raw input)
    # ─────────────────────────────────────────────────────────────────────────
    @field_validator("username", mode="after")
    @classmethod
    def validate_username(cls, value: str) -> str:
        # Strip leading/trailing whitespace first
        value = value.strip()

        # Username cannot be empty after stripping
        if not value:
            raise ValueError("Username cannot be empty or just spaces")

        # Length check: 3 to 30 characters
        if len(value) < 3:
            raise ValueError("Username must be at least 3 characters")
        if len(value) > 30:
            raise ValueError("Username cannot exceed 30 characters")

        # Only allow: letters, numbers, underscores, hyphens
        # No spaces, no special chars — clean for URLs and display
        if not re.match(r'^[a-zA-Z0-9_-]+$', value):
            raise ValueError(
                "Username can only contain letters, numbers, underscores, hyphens"
            )

        # Return the cleaned value — Pydantic stores THIS, not the original
        return value.lower()   # force lowercase — "Ali" and "ali" are same user

    @field_validator("password", mode="after")
    @classmethod
    def validate_password(cls, value: str) -> str:
        # Minimum 8 characters — absolute minimum for any real app
        if len(value) < 8:
            raise ValueError("Password must be at least 8 characters")

        # bcrypt hard limit is 72 bytes — enforce this at schema level
        # so it never even reaches the hashing function
        if len(value.encode('utf-8')) > 72:
            raise ValueError("Password cannot exceed 72 characters")

        # At least one digit — weak but better than nothing
        # In Lecture 07 (security hardening) we'll add stronger rules
        if not any(char.isdigit() for char in value):
            raise ValueError("Password must contain at least one number")

        return value   # return as-is, hashing happens in service layer

    @field_validator("email", mode="after")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        # Force lowercase so "Ali@Example.COM" and "ali@example.com" are same
        # EmailStr already validates format, we just normalize here
        return value.lower().strip()


# ─────────────────────────────────────────────────────────────────────────────
# UserUpdate — What the client sends to UPDATE a user
#
# KEY DIFFERENCE from UserCreate:
# ALL fields are Optional — you can update just the username,
# just the email, just the password, or any combination
#
# Does NOT inherit from UserBase because we don't want to
# require username + email on every update
# ─────────────────────────────────────────────────────────────────────────────
class UserUpdate(BaseModel):
    username: Optional[str] = None    # None means "don't change this field"
    email: Optional[EmailStr] = None
    password: Optional[str] = None

    # ─────────────────────────────────────────────────────────────────────────
    # @model_validator — runs on the ENTIRE model, not a single field
    # Use this when validation depends on multiple fields together
    # mode="after" = runs after all individual field validators
    # ─────────────────────────────────────────────────────────────────────────
    @model_validator(mode="after")
    def at_least_one_field(self) -> "UserUpdate":
        # Prevent empty PATCH requests — must update at least one thing
        if not any([self.username, self.email, self.password]):
            raise ValueError("At least one field must be provided for update")
        return self

    @field_validator("username", mode="after")
    @classmethod
    def validate_username(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None   # None = not updating, skip validation
        value = value.strip()
        if len(value) < 3:
            raise ValueError("Username must be at least 3 characters")
        if len(value) > 30:
            raise ValueError("Username cannot exceed 30 characters")
        if not re.match(r'^[a-zA-Z0-9_-]+$', value):
            raise ValueError(
                "Username can only contain letters, numbers, underscores, hyphens"
            )
        return value.lower()

    @field_validator("password", mode="after")
    @classmethod
    def validate_password(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        if len(value) < 8:
            raise ValueError("Password must be at least 8 characters")
        if len(value.encode('utf-8')) > 72:
            raise ValueError("Password cannot exceed 72 characters")
        if not any(char.isdigit() for char in value):
            raise ValueError("Password must contain at least one number")
        return value

    @field_validator("email", mode="after")
    @classmethod
    def normalize_email(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        return value.lower().strip()


# ─────────────────────────────────────────────────────────────────────────────
# UserResponse — What the server sends BACK after any user operation
#
# Notice what is NOT here:
# - password (plain text — never expose)
# - hashed_password (bcrypt hash — never expose)
#
# What IS here:
# - Everything the frontend legitimately needs
# ─────────────────────────────────────────────────────────────────────────────
class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None  # nullable — added in migration 2

    class Config:
        from_attributes = True
        # Allows: UserResponse.model_validate(orm_user_object)
        # Without this, Pydantic only accepts plain dicts, not ORM objects


# ─────────────────────────────────────────────────────────────────────────────
# UserListResponse — Lighter version for list endpoints
# When returning 100 users, you don't need every field
# Fewer fields = smaller payload = faster API
# ─────────────────────────────────────────────────────────────────────────────
class UserListResponse(BaseModel):
    id: int
    username: str
    email: str
    is_active: bool

    class Config:
        from_attributes = True