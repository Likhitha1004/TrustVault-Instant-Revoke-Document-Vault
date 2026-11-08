import enum
import hashlib
import json
import uuid
from datetime import datetime, timezone
from sqlalchemy import (
    Column, String, Integer, Boolean, DateTime, ForeignKey, Text, Enum
)
from sqlalchemy.orm import relationship
from app.database import Base

def generate_uuid() -> str:
    return str(uuid.uuid4())

class UserRole(str, enum.Enum):
    ADMIN = "admin"
    OWNER = "owner"
    VIEWER = "viewer"

class User(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    email = Column(String(255), unique=True, index=True, nullable=False)
    username = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    role = Column(Enum(UserRole), default=UserRole.VIEWER, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    # Relationships
    owned_documents = relationship("Document", back_populates="owner", cascade="all, delete-orphan")
    granted_permissions = relationship("DocumentPermission", foreign_keys="DocumentPermission.grantee_id", back_populates="grantee")

class Document(Base):
    __tablename__ = "documents"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    title = Column(String(255), index=True, nullable=False)
    original_filename = Column(String(255), nullable=False)
    storage_path = Column(String(500), nullable=False, unique=True)
    mime_type = Column(String(100), nullable=False)
    file_size = Column(Integer, nullable=False)
    file_hash_sha256 = Column(String(64), nullable=False)
    category = Column(String(100), index=True, default="General", nullable=False)
    
    owner_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    is_deleted = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    owner = relationship("User", back_populates="owned_documents")
    permissions = relationship("DocumentPermission", back_populates="document", cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", back_populates="document")

    @property
    def owner_username(self) -> str | None:
        return self.owner.username if self.owner else None

class DocumentPermission(Base):
    __tablename__ = "document_permissions"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    document_id = Column(String(36), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False)
    grantee_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    granted_by_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    
    can_read = Column(Boolean, default=True, nullable=False)
    can_edit = Column(Boolean, default=False, nullable=False)
    
    is_active = Column(Boolean, default=True, nullable=False)  # For instant revocation tracking
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    revoked_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    document = relationship("Document", back_populates="permissions")
    grantee = relationship("User", foreign_keys=[grantee_id], back_populates="granted_permissions")
    granted_by = relationship("User", foreign_keys=[granted_by_id])

    @property
    def grantee_username(self) -> str:
        return self.grantee.username if self.grantee else ""

    @property
    def grantee_email(self) -> str:
        return self.grantee.email if self.grantee else ""

class AuditAction(str, enum.Enum):
    USER_REGISTER = "USER_REGISTER"
    USER_LOGIN = "USER_LOGIN"
    DOC_UPLOAD = "DOC_UPLOAD"
    DOC_READ = "DOC_READ"
    DOC_DOWNLOAD = "DOC_DOWNLOAD"
    DOC_UPDATE = "DOC_UPDATE"
    DOC_DELETE = "DOC_DELETE"
    PERM_GRANT = "PERM_GRANT"
    PERM_REVOKE = "PERM_REVOKE"
    ACCESS_DENIED = "ACCESS_DENIED"
    USER_LOGOUT = "USER_LOGOUT"

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    uuid_str = Column(String(36), default=generate_uuid, unique=True, index=True, nullable=False)
    timestamp = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True, nullable=False)
    
    user_id = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    document_id = Column(String(36), ForeignKey("documents.id", ondelete="SET NULL"), nullable=True)
    action = Column(Enum(AuditAction), nullable=False)
    
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(String(255), nullable=True)
    metadata_json = Column(Text, default="{}", nullable=False)
    
    # Cryptographic Hash Chaining for Tamper Evidence
    previous_hash = Column(String(64), nullable=False)
    current_hash = Column(String(64), nullable=False)

    # Relationships
    user = relationship("User")
    document = relationship("Document", back_populates="audit_logs")

    @staticmethod
    def compute_hash(
        uuid_str: str,
        user_id: str | None,
        document_id: str | None,
        action: str,
        metadata_str: str,
        previous_hash: str
    ) -> str:
        payload = f"{uuid_str}|{user_id or ''}|{document_id or ''}|{action}|{metadata_str}|{previous_hash}"
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

class RevokedToken(Base):
    __tablename__ = "revoked_tokens"

    id = Column(Integer, primary_key=True, autoincrement=True)
    token_hash = Column(String(64), unique=True, index=True, nullable=False)
    revoked_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
