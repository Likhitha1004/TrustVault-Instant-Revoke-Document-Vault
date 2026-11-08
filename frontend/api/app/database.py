import os

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.pool import NullPool

from app.config import settings

_CONNECT_TIMEOUT_SECONDS = 5


def _normalize_database_url(url: str) -> str:
    """Rewrite provider-style Postgres URLs (e.g. Render's postgres://) for psycopg2."""
    if url.startswith("postgres://"):
        return url.replace("postgres://", "postgresql+psycopg2://", 1)
    if url.startswith("postgresql://") and not url.startswith("postgresql+"):
        return url.replace("postgresql://", "postgresql+psycopg2://", 1)
    return url


def _running_serverless() -> bool:
    return bool(
        os.getenv("VERCEL")
        or os.getenv("SERVERLESS")
        or os.getenv("AWS_LAMBDA_FUNCTION_NAME")
    )


def _build_engine(url: str):
    if url.startswith("sqlite"):
        return create_engine(url, connect_args={"check_same_thread": False})

    # PostgreSQL pooling tuned for Supabase Free tier and serverless hosts.
    connect_args = {"connect_timeout": _CONNECT_TIMEOUT_SECONDS}
    if "sslmode" not in url:
        connect_args["sslmode"] = "require"

    if _running_serverless():
        return create_engine(url, poolclass=NullPool, connect_args=connect_args)

    return create_engine(
        url,
        pool_pre_ping=True,
        pool_size=10,
        max_overflow=20,
        pool_timeout=30,
        pool_recycle=300,
        connect_args=connect_args,
    )


db_url = _normalize_database_url(settings.DATABASE_URL)
engine = _build_engine(db_url)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """FastAPI dependency yielding a request-scoped database session."""
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
