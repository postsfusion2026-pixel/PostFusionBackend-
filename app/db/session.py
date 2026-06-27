# from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
# from app.core.config import settings

# engine = create_async_engine(settings.DATABASE_URL, echo=settings.DEBUG)

# AsyncSessionLocal = async_sessionmaker(
#     engine, expire_on_commit=False, class_=AsyncSession
# )

# async def get_db() -> AsyncSession:
#     async with AsyncSessionLocal() as session:
#         yield session


# app/db/session.py

from sqlalchemy.ext.asyncio import (
    create_async_engine,
    AsyncSession,
    async_sessionmaker
)
from app.core.config import settings

# ─────────────────────────────────────────────────────────────────────────────
# THE ENGINE — One object, lives for the entire app lifetime
#
# The engine manages a CONNECTION POOL — a set of pre-opened connections
# to PostgreSQL that get reused across requests.
#
# Without a pool: every request opens + closes a DB connection = slow
# With a pool: connections are kept open and handed out as needed = fast
# ─────────────────────────────────────────────────────────────────────────────
engine = create_async_engine(
    settings.DATABASE_URL,

    # echo=True prints all generated SQL to console
    # Great for debugging in dev, TURN OFF in production (too noisy + slow)
    echo=settings.DEBUG,

    # pool_pre_ping=True:
    # Before giving a connection to a request, send a lightweight "ping" to DB
    # If the connection is dead (DB restarted, network hiccup), PostgreSQL
    # responds with an error → SQLAlchemy discards it and opens a fresh one
    # Without this: you get "server closed the connection unexpectedly" in prod
    pool_pre_ping=True,

    # pool_size: how many connections to keep open permanently
    # Default is 5. For a small API, 5-10 is plenty.
    # Each connection uses ~5MB of memory in PostgreSQL
    pool_size=10,

    # max_overflow: how many EXTRA connections can be opened during traffic spikes
    # These get closed when the spike subsides
    # Total max connections = pool_size + max_overflow = 10 + 20 = 30
    max_overflow=20,

    # pool_timeout: how long (seconds) to wait for an available connection
    # If all 30 connections are busy and a new request comes in,
    # it waits this long before giving up with a timeout error
    pool_timeout=30,

    # pool_recycle: close and reopen connections older than this many seconds
    # Prevents issues with database server connection timeouts
    # Most PostgreSQL servers drop idle connections after ~1 hour
    # 1800 = 30 minutes — safely recycles before the server drops them
    pool_recycle=1800,
)

# ─────────────────────────────────────────────────────────────────────────────
# SESSION FACTORY — Creates individual session objects per request
#
# Think of the engine as the "pool of cars"
# and the session factory as the "car rental desk"
# Each request gets one car (session), uses it, returns it
# ─────────────────────────────────────────────────────────────────────────────
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,

    # expire_on_commit=False:
    # After session.commit(), SQLAlchemy by default "expires" all objects —
    # meaning accessing obj.id would fire ANOTHER SELECT query to refresh it.
    # With False: the object keeps its data in memory after commit.
    # This is almost always what you want in async FastAPI.
    expire_on_commit=False,
)


# ─────────────────────────────────────────────────────────────────────────────
# get_db() — The dependency injected into every route that needs DB access
#
# This is an ASYNC GENERATOR — the `yield` is what makes it special:
#
# Step 1: "async with AsyncSessionLocal() as session:" opens a session
# Step 2: "yield session" — FastAPI receives this session, runs the route
# Step 3: After the route finishes (success or error), execution
#         returns here and the `async with` block closes the session
#
# The session is AUTOMATICALLY committed or rolled back and closed.
# You never leak a connection, even if the route raises an exception.
# ─────────────────────────────────────────────────────────────────────────────
async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session           # ← route handler gets the session here
            await session.commit()  # ← commit if route completed successfully
        except Exception:
            await session.rollback()  # ← rollback if anything raised an error
            raise                     # ← re-raise the exception (don't swallow it)
        # session.close() is called automatically by the `async with` block