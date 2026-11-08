import hashlib
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session
from datetime import datetime, timedelta, timezone

from app.audit import record_audit_event
from app.auth import (
    create_access_token,
    get_current_user,
    get_password_hash,
    hash_token,
    verify_password,
)
from app.database import get_db
from app.models import AuditAction, AuditLog, RevokedToken, User, UserRole
from app.schemas import LoginRequest, TokenResponse, UserCreate, UserResponse

router = APIRouter(prefix="/auth", tags=["Authentication"])


def _enforce_audit_backed_rate_limit(
    db: Session, request: Request, action: AuditAction, limit: int, window_minutes: int,
    metadata_fragment: str | None = None,
) -> None:
    """Cross-instance rate limiting backed by the existing shared audit table (no schema change)."""
    client_ip = request.client.host if request.client else None
    if not client_ip:
        return
    cutoff = datetime.now(timezone.utc) - timedelta(minutes=window_minutes)
    query = db.query(AuditLog).filter(
        AuditLog.action == action, AuditLog.ip_address == client_ip, AuditLog.timestamp >= cutoff
    )
    if metadata_fragment:
        query = query.filter(AuditLog.metadata_json.like(f"%{metadata_fragment}%"))
    if query.count() >= limit:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many requests. Try again later.",
            headers={"Retry-After": str(window_minutes * 60)},
        )


def _request_context(request: Request) -> dict:
    """Client IP and user-agent, as passed to the audit trail."""
    return {
        "ip_address": request.client.host if request.client else None,
        "user_agent": request.headers.get("user-agent"),
    }


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(user_in: UserCreate, request: Request, db: Session = Depends(get_db)):
    # Public self-registration may create viewers or owners, never administrators.
    # Admin accounts must be provisioned through the trusted bootstrap/recovery workflow.
    if user_in.role == UserRole.ADMIN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Administrator accounts cannot be self-registered.")

    duplicate = db.query(User).filter(
        (User.email == user_in.email) | (User.username == user_in.username)
    ).first()
    if duplicate:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email or username already registered",
        )

    user = User(
        email=user_in.email,
        username=user_in.username,
        hashed_password=get_password_hash(user_in.password),
        role=user_in.role,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    record_audit_event(
        db=db,
        action=AuditAction.USER_REGISTER,
        user_id=user.id,
        metadata={"email": user.email, "role": user.role.value},
        **_request_context(request),
    )

    return user


@router.post("/login", response_model=TokenResponse)
def login(login_data: LoginRequest, request: Request, db: Session = Depends(get_db)):
    identifier = login_data.username_or_email.strip()
    identifier_hash = hashlib.sha256(identifier.casefold().encode("utf-8")).hexdigest()
    _enforce_audit_backed_rate_limit(
        db, request, AuditAction.ACCESS_DENIED, limit=10, window_minutes=15,
        metadata_fragment=f'"identifier_hash": "{identifier_hash}"',
    )
    user = db.query(User).filter(
        (User.email == identifier) | (User.username == identifier)
    ).first()

    if not user or not verify_password(login_data.password, user.hashed_password):
        record_audit_event(
            db=db,
            action=AuditAction.ACCESS_DENIED,
            metadata={"reason": "Invalid credentials", "identifier_hash": identifier_hash},
            **_request_context(request),
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is inactive",
        )

    access_token = create_access_token(data={"sub": user.id, "role": user.role.value})

    record_audit_event(
        db=db,
        action=AuditAction.USER_LOGIN,
        user_id=user.id,
        metadata={"role": user.role.value},
        **_request_context(request),
    )

    return {"access_token": access_token, "token_type": "bearer", "user": user}


@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    return current_user


@router.post("/logout")
def logout(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # Extract the raw bearer token from the Authorization header
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        token_digest = hash_token(auth_header.split(" ", 1)[1].strip())

        # Record the revocation once; repeat logouts are idempotent
        already_revoked = (
            db.query(RevokedToken).filter(RevokedToken.token_hash == token_digest).first()
        )
        if not already_revoked:
            db.add(RevokedToken(token_hash=token_digest))
            db.commit()

    record_audit_event(
        db=db,
        action=AuditAction.USER_LOGOUT,
        user_id=current_user.id,
        metadata={"email": current_user.email, "role": current_user.role.value},
        **_request_context(request),
    )
    return {"status": "success", "message": "Successfully logged out and session revoked."}
