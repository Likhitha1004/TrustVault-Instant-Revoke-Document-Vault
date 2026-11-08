from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, EmailStr, ConfigDict, Field, field_validator
from app.models import UserRole, AuditAction

# User schemas
class UserCreate(BaseModel):
    email: EmailStr
    username: str
    password: str = Field(min_length=12, max_length=128)
    role: UserRole = UserRole.VIEWER

    @field_validator("password")
    @classmethod
    def validate_password_bytes(cls, value: str) -> str:
        # bcrypt silently truncates after 72 bytes; reject rather than truncate.
        if len(value.encode("utf-8")) > 72:
            raise ValueError("Password must not exceed 72 UTF-8 bytes.")
        return value

class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    email: str
    username: str
    role: UserRole
    is_active: bool
    created_at: datetime

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse

class LoginRequest(BaseModel):
    username_or_email: str = Field(min_length=1, max_length=255)
    password: str = Field(min_length=1, max_length=128)

# Permission schemas
class PermissionGrantRequest(BaseModel):
    grantee_email: str
    can_read: bool = True
    can_edit: bool = False

class PermissionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    document_id: str
    grantee_id: str
    grantee_username: str
    grantee_email: str
    can_read: bool
    can_edit: bool
    is_active: bool
    created_at: datetime

# Document schemas
class BulkDeleteRequest(BaseModel):
    document_ids: List[str] = Field(min_length=1, max_length=100)

class DocumentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    title: str
    original_filename: str
    category: str
    mime_type: str
    file_size: int
    file_hash_sha256: str
    owner_id: str
    owner_username: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    permissions: List[PermissionResponse] = []

class DocumentUpdateRequest(BaseModel):
    title: Optional[str] = None
    category: Optional[str] = None

class UploadIntentRequest(BaseModel):
    title: str
    category: str = "General"
    filename: str
    file_size: int
    file_hash_sha256: str
    mime_type: str = "application/octet-stream"

class UploadIntentResponse(BaseModel):
    upload_url: str
    storage_path: str
    file_uuid: str
    max_size: int
    upload_token: str

class ConfirmUploadRequest(BaseModel):
    upload_token: str
    title: str
    category: str = "General"
    original_filename: str
    storage_path: str
    file_size: int
    file_hash_sha256: str
    mime_type: str

# Audit schemas
class AuditLogResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    uuid_str: str
    timestamp: datetime
    user_id: Optional[str] = None
    document_id: Optional[str] = None
    action: AuditAction
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    metadata_json: str
    previous_hash: str
    current_hash: str
