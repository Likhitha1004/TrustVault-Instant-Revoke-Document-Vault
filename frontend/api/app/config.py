import os
import secrets

from pydantic import ConfigDict
from pydantic_settings import BaseSettings

_TRUTHY = ("true", "1", "yes")


def _env_flag(name: str, default: str) -> bool:
    """Read a boolean feature flag from the environment."""
    return os.getenv(name, default).lower() in _TRUTHY


def _is_serverless_runtime() -> bool:
    return bool(os.getenv("VERCEL") or os.getenv("AWS_LAMBDA_FUNCTION_NAME"))


class Settings(BaseSettings):
    model_config = ConfigDict(case_sensitive=True)

    # Application identity
    PROJECT_NAME: str = "TrustVault"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api"

    # Security / token settings
    # Never ship a known signing key. Production must supply SECRET_KEY explicitly.
    SECRET_KEY: str = os.getenv("SECRET_KEY", "")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60  # 1 hour; short-lived bearer sessions

    # Database: SQLite by default for zero-cost local runs and self-contained tests;
    # Postgres whenever DATABASE_URL is provided (e.g. Render / Supabase).
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./trustvault.db")

    # File storage ("local" or "s3")
    STORAGE_BACKEND: str = os.getenv("STORAGE_BACKEND", "local")
    STORAGE_DIR: str = os.getenv(
        "STORAGE_DIR",
        "/tmp/storage" if _is_serverless_runtime() else "./storage",
    )
    S3_BUCKET_NAME: str = os.getenv("S3_BUCKET_NAME", "")
    S3_ENDPOINT_URL: str = os.getenv("S3_ENDPOINT_URL", "")
    S3_ACCESS_KEY_ID: str = os.getenv("S3_ACCESS_KEY_ID", "")
    S3_SECRET_ACCESS_KEY: str = os.getenv("S3_SECRET_ACCESS_KEY", "")
    S3_REGION_NAME: str = os.getenv("S3_REGION_NAME", "auto")

    # Deployment lifecycle and bootstrap admin
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "production" if _is_serverless_runtime() else "development")
    INITIAL_ADMIN_PASSWORD: str = os.getenv("INITIAL_ADMIN_PASSWORD", "")
    _default_demo_seed = "false" if (os.getenv("ENVIRONMENT", "").lower() == "production" or _is_serverless_runtime()) else "true"
    ALLOW_DEMO_SEED: bool = _env_flag("ALLOW_DEMO_SEED", _default_demo_seed)
    ALLOW_EPHEMERAL_STORAGE: bool = _env_flag("ALLOW_EPHEMERAL_STORAGE", "false")


settings = Settings()
if not settings.SECRET_KEY:
    if settings.ENVIRONMENT.lower() == "production":
        raise RuntimeError("SECRET_KEY must be configured with a cryptographically random value in production.")
    # Development-only key; tokens are invalidated whenever the process restarts.
    settings.SECRET_KEY = secrets.token_urlsafe(48)
elif len(settings.SECRET_KEY) < 32:
    raise RuntimeError("SECRET_KEY must contain at least 32 characters.")
if settings.ENVIRONMENT.lower() == "production":
    if not os.getenv("CORS_ORIGINS", "").strip():
        raise RuntimeError("CORS_ORIGINS must explicitly list trusted frontend origins in production.")
    if settings.ALLOW_DEMO_SEED:
        raise RuntimeError("ALLOW_DEMO_SEED must be false in production.")

