import os

from fastapi import Depends, FastAPI, Response, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.config import settings
from app.database import Base, engine, get_db
from app.routes_audit import router as audit_router
from app.routes_auth import router as auth_router
from app.routes_documents import router as docs_router

SECURITY_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "X-XSS-Protection": "1; mode=block",
    "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
    "Referrer-Policy": "strict-origin-when-cross-origin",
}


def _is_serverless() -> bool:
    return bool(
        os.getenv("VERCEL")
        or os.getenv("SERVERLESS")
        or os.getenv("AWS_LAMBDA_FUNCTION_NAME")
    )


def _create_schema() -> None:
    try:
        Base.metadata.create_all(bind=engine)
    except Exception as exc:
        print(f"Database schema initialization warning: {exc}")


def _should_create_schema() -> bool:
    """Local dev creates tables automatically; serverless skips it (cold-start DDL
    contention) unless INIT_DB is explicitly enabled."""
    if not _is_serverless():
        return True
    return os.getenv("INIT_DB", "false").lower() in ("true", "1")


if _should_create_schema():
    _create_schema()

try:
    os.makedirs(settings.STORAGE_DIR, exist_ok=True)
except Exception:
    pass

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="TrustVault - Secure document sharing platform with cryptographic tamper-evident audit trail",
)

# Explicit allowlist. Configure CORS_ORIGINS as comma-separated HTTPS origins in production.
_default_origins = "http://localhost:5173,http://127.0.0.1:5173"
_cors_origins = [origin.strip().rstrip("/") for origin in os.getenv("CORS_ORIGINS", _default_origins).split(",") if origin.strip()]
if settings.ENVIRONMENT.lower() == "production":
    from urllib.parse import urlparse
    if "*" in _cors_origins:
        raise RuntimeError("Wildcard CORS origins are forbidden in production.")
    for _origin in _cors_origins:
        _parsed = urlparse(_origin)
        if _parsed.scheme != "https" or not _parsed.netloc or _parsed.path or _parsed.query or _parsed.fragment:
            raise RuntimeError("Production CORS_ORIGINS must contain only exact HTTPS origins.")
app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=False,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "Accept"],
)


@app.middleware("http")
async def add_security_headers(request, call_next):
    response = await call_next(request)
    for header, value in SECURITY_HEADERS.items():
        response.headers[header] = value
    return response


for _router in (auth_router, docs_router, audit_router):
    app.include_router(_router, prefix=settings.API_V1_STR)


@app.get("/")
def health_check_root():
    return {
        "status": "online",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "security_policy": "Zero-Trust live DB evaluation with SHA-256 chained audit",
    }


@app.get("/healthz")
@app.get("/api/healthz")
def health_check_healthz():
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
    }


@app.get("/readyz")
@app.get("/api/readyz")
def readiness_check(response: Response, db: Session = Depends(get_db)):
    try:
        db.execute(text("SELECT 1"))
    except Exception as exc:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return {
            "status": "not_ready",
            "service": settings.PROJECT_NAME,
            "database": "disconnected",
            "error": str(exc),
        }
    return {
        "status": "ready",
        "service": settings.PROJECT_NAME,
        "database": "connected",
    }
