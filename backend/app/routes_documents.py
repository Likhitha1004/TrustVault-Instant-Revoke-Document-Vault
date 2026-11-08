import os
import re
import hashlib
import hmac
import io
import zipfile
from datetime import datetime, timedelta, timezone
from jose import jwt, JWTError
import uuid
import aiofiles
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form, Request, Query
from fastapi.responses import FileResponse, StreamingResponse
from sqlalchemy.orm import Session, joinedload, selectinload
from sqlalchemy import or_, and_, func

from app.config import settings
from app.database import get_db
from app.models import User, UserRole, Document, DocumentPermission, AuditAction
from app.schemas import (
    DocumentResponse, DocumentUpdateRequest, PermissionGrantRequest, PermissionResponse,
    UploadIntentRequest, UploadIntentResponse, ConfirmUploadRequest, BulkDeleteRequest
)
from app.auth import get_current_user, require_owner_or_admin
from app.audit import record_audit_event
from app.storage import storage_manager
from fastapi.responses import FileResponse, StreamingResponse, RedirectResponse

router = APIRouter(prefix="/documents", tags=["Documents & Access Control"])

# Magic-byte file signatures for strict content inspection
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB maximum upload limit

ALLOWED_MAGIC_SIGNATURES = {
    b"%PDF-": "application/pdf",
    b"PK\x03\x04": "application/vnd.openxmlformats-officedocument", # docx, xlsx, pptx, zip
    b"\xd0\xcf\x11\xe0": "application/msword",                      # legacy doc/xls
    b"\x89PNG\r\n\x1a\n": "image/png",
    b"\xff\xd8\xff": "image/jpeg",
    b"GIF87a": "image/gif",
    b"GIF89a": "image/gif",
}

def validate_magic_bytes(header: bytes, filename: str) -> str:
    """
    Inspects leading bytes of uploaded file to prevent executable masquerading.
    """
    for magic, mime in ALLOWED_MAGIC_SIGNATURES.items():
        if header.startswith(magic):
            return mime
    
    # Plain text detection (ASCII / UTF-8 text)
    try:
        header[:512].decode("utf-8")
        if filename.endswith((".txt", ".md", ".csv", ".json")):
            return "text/plain"
    except UnicodeDecodeError:
        pass

    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="File content rejected: Not an allowed document type or executable masquerade detected."
    )

def validate_file_payload(content: bytes, filename: str) -> str:
    """Validate actual bytes and container structure, not just a client MIME/header."""
    clean_name = os.path.basename(filename or "").lower()
    detected = validate_magic_bytes(content[:512], clean_name)

    if content.startswith(b"PK\x03\x04"):
        office_types = {
            ".docx": ("word/document.xml", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"),
            ".xlsx": ("xl/workbook.xml", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"),
            ".pptx": ("ppt/presentation.xml", "application/vnd.openxmlformats-officedocument.presentationml.presentation"),
        }
        expected = office_types.get(os.path.splitext(clean_name)[1])
        if expected is None:
            raise HTTPException(status_code=400, detail="ZIP uploads are accepted only as validated DOCX, XLSX, or PPTX files.")
        try:
            with zipfile.ZipFile(io.BytesIO(content)) as archive:
                entries = archive.infolist()
                names = {entry.filename for entry in entries}
                if len(entries) > 1000 or "[Content_Types].xml" not in names or expected[0] not in names:
                    raise ValueError("Invalid Office Open XML package structure")
                total_uncompressed = sum(entry.file_size for entry in entries)
                total_compressed = max(1, sum(entry.compress_size for entry in entries))
                if total_uncompressed > 100 * 1024 * 1024 or total_uncompressed / total_compressed > 100:
                    raise ValueError("Archive expansion ratio exceeds safety limits")
                if any(name.startswith(("/", "\\")) or ".." in name.split("/") for name in names):
                    raise ValueError("Unsafe archive entry path")
        except (zipfile.BadZipFile, OSError, ValueError):
            raise HTTPException(status_code=400, detail="Invalid or unsafe Office document package.")
        return expected[1]

    if content.startswith(b"\xd0\xcf\x11\xe0"):
        legacy_types = {".doc": "application/msword", ".xls": "application/vnd.ms-excel", ".ppt": "application/vnd.ms-powerpoint"}
        mime = legacy_types.get(os.path.splitext(clean_name)[1])
        if mime is None:
            raise HTTPException(status_code=400, detail="Legacy Office files must use a supported .doc, .xls, or .ppt extension.")
        return mime

    extension_mimes = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".gif": "image/gif"}
    if detected in {"image/png", "image/jpeg", "image/gif"}:
        expected_mime = extension_mimes.get(os.path.splitext(clean_name)[1])
        if expected_mime != detected:
            raise HTTPException(status_code=400, detail="File extension does not match detected image content.")
    return detected


def check_document_access(
    db: Session,
    document: Document,
    user: User,
    require_edit: bool = False
) -> bool:
    """
    LIVE SERVER-SIDE AUTHORIZATION WALL:
    1. Admin has supervisory read access (and edit if explicitly given).
    2. Owner has 100% full read & edit access.
    3. Viewers must hold an active, non-revoked permission row in database.
    Zero cached or stale JWT checks.
    """
    if document.is_deleted:
        return False

    # Owner has absolute access
    if document.owner_id == user.id:
        return True

    # Admin supervisory access
    if user.role == UserRole.ADMIN:
        return True

    # Check granular user permission row
    perm = db.query(DocumentPermission).filter(
        DocumentPermission.document_id == document.id,
        DocumentPermission.grantee_id == user.id,
        DocumentPermission.is_active == True
    ).first()

    if not perm:
        return False

    if require_edit:
        return perm.can_edit
    return perm.can_read

@router.post("/upload", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    request: Request,
    title: str = Form(...),
    category: str = Form("General"),
    file: UploadFile = File(...),
    current_user: User = Depends(require_owner_or_admin),
    db: Session = Depends(get_db)
):
    try:
        os.makedirs(settings.STORAGE_DIR, exist_ok=True)
    except OSError:
        pass

    payload = await file.read(MAX_FILE_SIZE + 1)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File content rejected: Uploaded file is empty (0 bytes)."
        )
    if len(payload) > MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail=f"File exceeds maximum allowed size of {MAX_FILE_SIZE // (1024 * 1024)}MB.")
    mime_type = validate_file_payload(payload, file.filename or "file")
    await file.seek(0)

    # Sanitize original filename (prevent path traversal like ../../)
    raw_filename = os.path.basename(file.filename or "unknown").strip()
    if not raw_filename or raw_filename.startswith("."):
        raw_filename = f"document_{uuid.uuid4().hex[:8]}.bin"

    # Generate secure storage identifier with UUID
    file_uuid = str(uuid.uuid4())
    ext = os.path.splitext(raw_filename)[1]
    
    storage_path, file_size, file_hash = await storage_manager.save_file(
        file=file,
        file_uuid=file_uuid,
        ext=ext,
        max_size=MAX_FILE_SIZE
    )

    doc = Document(
        title=title.strip() if title else raw_filename,
        original_filename=raw_filename,
        storage_path=storage_path,
        mime_type=mime_type,
        file_size=file_size,
        file_hash_sha256=file_hash,
        category=category.strip() if category else "General",
        owner_id=current_user.id
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)

    record_audit_event(
        db=db,
        action=AuditAction.DOC_UPLOAD,
        user_id=current_user.id,
        document_id=doc.id,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
        metadata={"title": doc.title, "filename": doc.original_filename, "size": file_size, "hash": doc.file_hash_sha256}
    )

    return doc

@router.post("/upload-intent", response_model=UploadIntentResponse)
def create_upload_intent(
    intent_in: UploadIntentRequest,
    current_user: User = Depends(require_owner_or_admin),
    db: Session = Depends(get_db)
):
    """Issue a short-lived, user-bound authorization for one direct S3 upload."""
    if storage_manager.backend != "s3" or not storage_manager._s3_client:
        raise HTTPException(status_code=503, detail="Direct uploads require configured S3-compatible storage.")
    if intent_in.file_size <= 0 or intent_in.file_size > MAX_FILE_SIZE:
        raise HTTPException(status_code=413 if intent_in.file_size > MAX_FILE_SIZE else 400,
                            detail=f"File size must be between 1 and {MAX_FILE_SIZE} bytes.")
    if not re.fullmatch(r"[a-fA-F0-9]{64}", intent_in.file_hash_sha256 or ""):
        raise HTTPException(status_code=400, detail="A valid SHA-256 digest is required.")

    clean_filename = os.path.basename(intent_in.filename).strip()[:255] or "document.bin"
    file_uuid = str(uuid.uuid4())
    _, ext = os.path.splitext(clean_filename)
    storage_path = f"documents/{file_uuid}{ext.lower()}"
    verified_storage_path = f"documents/verified/{file_uuid}{ext.lower()}"
    content_type = (intent_in.mime_type or "application/octet-stream")[:100]
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=5)
    claims = {
        "typ": "upload_intent", "sub": current_user.id, "path": storage_path,
        "final_path": verified_storage_path, "size": intent_in.file_size, "sha256": intent_in.file_hash_sha256.lower(),
        "filename": clean_filename, "title": (intent_in.title or clean_filename)[:255],
        "category": (intent_in.category or "General")[:100], "mime": content_type,
        "exp": expires_at,
    }
    upload_token = jwt.encode(claims, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    upload_url = storage_manager.get_presigned_upload_url(
        storage_identifier=storage_path, content_type=content_type, content_length=intent_in.file_size, expires_in=300
    )
    if not upload_url:
        raise HTTPException(status_code=500, detail="Failed to generate secure upload authorization URL.")
    return UploadIntentResponse(upload_url=upload_url, storage_path=storage_path,
                                file_uuid=file_uuid, max_size=MAX_FILE_SIZE,
                                upload_token=upload_token)


@router.post("/confirm-upload", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
def confirm_upload(
    confirm_in: ConfirmUploadRequest,
    request: Request,
    current_user: User = Depends(require_owner_or_admin),
    db: Session = Depends(get_db)
):
    """Verify a user-bound intent, then inspect and hash the actual stored bytes."""
    try:
        claims = jwt.decode(confirm_in.upload_token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    except JWTError:
        raise HTTPException(status_code=401, detail="Upload authorization is invalid or expired.")
    if claims.get("typ") != "upload_intent" or claims.get("sub") != current_user.id:
        raise HTTPException(status_code=403, detail="Upload authorization does not belong to this user.")

    # The client cannot choose another user's key or alter the signed upload metadata.
    if confirm_in.storage_path != claims.get("path"):
        raise HTTPException(status_code=400, detail="Storage path does not match upload authorization.")
    if confirm_in.file_size != claims.get("size") or confirm_in.file_hash_sha256.lower() != claims.get("sha256"):
        raise HTTPException(status_code=400, detail="Upload metadata does not match upload authorization.")
    if confirm_in.file_size <= 0 or confirm_in.file_size > MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail="File exceeds maximum allowed size.")

    # Prevent token replay / duplicate document creation.
    existing = db.query(Document).filter(Document.storage_path == claims["final_path"]).first()
    if existing:
        raise HTTPException(status_code=409, detail="This upload has already been confirmed.")

    meta = storage_manager.get_object_metadata(claims["path"])
    if not meta:
        raise HTTPException(status_code=400, detail="Uploaded file not found in storage.")
    if meta.get("size") != claims["size"]:
        # Do not leave oversized or mismatched untrusted objects in the bucket.
        storage_manager.delete(claims["path"])
        raise HTTPException(status_code=400, detail="Stored object size does not match authorized size; object removed.")

    try:
        actual_bytes = storage_manager.read_object_limited(claims["path"], MAX_FILE_SIZE)
    except Exception:
        raise HTTPException(status_code=400, detail="Unable to inspect uploaded object.")
    if len(actual_bytes) != claims["size"] or len(actual_bytes) > MAX_FILE_SIZE:
        storage_manager.delete(claims["path"])
        raise HTTPException(status_code=413, detail="Stored object exceeds the permitted size or is incomplete; object removed.")
    actual_hash = hashlib.sha256(actual_bytes).hexdigest()
    if not hmac.compare_digest(actual_hash, claims["sha256"]):
        storage_manager.delete(claims["path"])
        raise HTTPException(status_code=400, detail="Stored file SHA-256 verification failed; object removed.")

    clean_filename = claims["filename"]
    try:
        detected_mime = validate_file_payload(actual_bytes, clean_filename)
    except HTTPException:
        storage_manager.delete(claims["path"])
        raise
    # Finalize the exact verified bytes under a fresh server-only key. The still-live
    # presigned URL can only recreate the temporary key, never mutate the document.
    try:
        storage_manager.put_verified_object(claims["final_path"], actual_bytes, detected_mime)
    except Exception:
        raise HTTPException(status_code=500, detail="Could not finalize verified document in private storage.")
    storage_manager.delete(claims["path"])

    # Persist server-derived values, never the untrusted MIME/hash sent by the browser.
    doc = Document(
        title=claims["title"], original_filename=clean_filename,
        storage_path=claims["final_path"], file_size=len(actual_bytes),
        file_hash_sha256=actual_hash, mime_type=detected_mime,
        category=claims["category"], owner_id=current_user.id
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)
    record_audit_event(
        db=db, action=AuditAction.DOC_UPLOAD, user_id=current_user.id,
        document_id=doc.id, ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
        metadata={"title": doc.title, "filename": doc.original_filename,
                  "size": doc.file_size, "hash": doc.file_hash_sha256,
                  "method": "verified_presigned_s3"}
    )
    return doc


@router.post("/bulk-delete")
def bulk_delete_documents(
    payload: BulkDeleteRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Soft-delete up to 100 documents, enforcing owner/admin authorization per ID."""
    requested_ids = list(dict.fromkeys(payload.document_ids))
    docs = db.query(Document).filter(
        Document.id.in_(requested_ids), Document.is_deleted == False
    ).all()
    by_id = {doc.id: doc for doc in docs}
    deleted_ids: list[str] = []
    failed_ids: list[str] = []
    cleanup_paths: list[str] = []

    for document_id in requested_ids:
        doc = by_id.get(document_id)
        if doc is None or (doc.owner_id != current_user.id and current_user.role != UserRole.ADMIN):
            failed_ids.append(document_id)
            if doc is not None:
                record_audit_event(
                    db=db, action=AuditAction.ACCESS_DENIED, user_id=current_user.id,
                    document_id=doc.id, ip_address=request.client.host if request.client else None,
                    user_agent=request.headers.get("user-agent"),
                    metadata={"reason": "Unauthorized bulk document deletion attempt"},
                )
            continue

        doc.is_deleted = True
        db.commit()
        deleted_ids.append(document_id)
        cleanup_paths.append(doc.storage_path)
        record_audit_event(
            db=db, action=AuditAction.DOC_DELETE, user_id=current_user.id,
            document_id=doc.id, ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
            metadata={"title": doc.title, "filename": doc.original_filename, "method": "bulk"},
        )

    # Storage cleanup occurs after database state and audit event are committed.
    for storage_path in cleanup_paths:
        storage_manager.delete(storage_path)

    return {"deleted_count": len(deleted_ids), "deleted_ids": deleted_ids, "failed_ids": failed_ids}


@router.get("", response_model=List[DocumentResponse])
def list_documents(
    request: Request,
    search: Optional[str] = None,
    category: Optional[str] = None,
    owner: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    sort_by: Optional[str] = Query("newest"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Returns only documents the user is authorized to know about:
    1. Admin: all documents.
    2. Owner: documents owned by user.
    3. Viewer: documents explicitly granted to user via active permission.
    """
    query = db.query(Document).filter(Document.is_deleted == False)

    if current_user.role != UserRole.ADMIN:
        # User is either owner OR has active permission
        query = query.outerjoin(DocumentPermission, and_(
            DocumentPermission.document_id == Document.id,
            DocumentPermission.grantee_id == current_user.id,
            DocumentPermission.is_active == True,
            DocumentPermission.can_read == True
        )).filter(
            or_(
                Document.owner_id == current_user.id,
                DocumentPermission.id != None
            )
        )

    if search:
        search_filter = f"%{search}%"
        query = query.filter(
            or_(
                Document.title.ilike(search_filter),
                Document.original_filename.ilike(search_filter)
            )
        )

    if category:
        query = query.filter(Document.category.ilike(f"%{category}%"))

    if owner:
        query = query.join(User, Document.owner_id == User.id).filter(
            or_(
                User.username.ilike(f"%{owner}%"),
                User.email.ilike(f"%{owner}%")
            )
        )

    if date_from:
        try:
            d_from = datetime.fromisoformat(date_from)
            query = query.filter(Document.created_at >= d_from)
        except Exception:
            pass

    if date_to:
        try:
            d_to = datetime.fromisoformat(date_to)
            query = query.filter(Document.created_at <= d_to)
        except Exception:
            pass

    if sort_by == "oldest":
        query = query.order_by(Document.created_at.asc())
    elif sort_by == "title_asc":
        query = query.order_by(Document.title.asc())
    elif sort_by == "title_desc":
        query = query.order_by(Document.title.desc())
    elif sort_by == "size_asc":
        query = query.order_by(Document.file_size.asc())
    elif sort_by == "size_desc":
        query = query.order_by(Document.file_size.desc())
    else:
        query = query.order_by(Document.created_at.desc())

    query = query.options(
        joinedload(Document.owner),
        selectinload(Document.permissions).joinedload(DocumentPermission.grantee)
    )
    docs = query.all()
    return docs

@router.get("/{document_id}", response_model=DocumentResponse)
def get_document(
    document_id: str,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    doc = db.query(Document).filter(Document.id == document_id, Document.is_deleted == False).first()
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")

    if not check_document_access(db, doc, current_user, require_edit=False):
        record_audit_event(
            db=db,
            action=AuditAction.ACCESS_DENIED,
            user_id=current_user.id,
            document_id=document_id,
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
            metadata={"reason": "Unauthorized document read attempt"}
        )
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")

    record_audit_event(
        db=db,
        action=AuditAction.DOC_READ,
        user_id=current_user.id,
        document_id=doc.id,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
        metadata={"title": doc.title}
    )

    return doc

@router.get("/{document_id}/download")
def download_document(
    document_id: str,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    STRICT SERVER-CONTROLLED DOWNLOAD PROXY:
    Evaluates DB authorization at runtime. Instant revocation terminates downloads immediately.
    """
    doc = db.query(Document).filter(Document.id == document_id, Document.is_deleted == False).first()
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")

    if not check_document_access(db, doc, current_user, require_edit=False):
        record_audit_event(
            db=db,
            action=AuditAction.ACCESS_DENIED,
            user_id=current_user.id,
            document_id=document_id,
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
            metadata={"reason": "Unauthorized file download attempt"}
        )
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")

    if not storage_manager.exists(doc.storage_path):
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Storage asset missing")

    record_audit_event(
        db=db,
        action=AuditAction.DOC_DOWNLOAD,
        user_id=current_user.id,
        document_id=doc.id,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
        metadata={"filename": doc.original_filename, "size": doc.file_size}
    )

    if storage_manager.backend == "s3":
        presigned_url = storage_manager.get_presigned_download_url(
            doc.storage_path,
            filename=doc.original_filename,
            expires_in=300
        )
        if presigned_url:
            return RedirectResponse(
                url=presigned_url,
                status_code=status.HTTP_307_TEMPORARY_REDIRECT
            )
        return StreamingResponse(
            storage_manager.get_stream(doc.storage_path),
            media_type=doc.mime_type,
            headers={
                "Content-Disposition": f'attachment; filename="{doc.original_filename}"'
            }
        )

    return FileResponse(
        path=doc.storage_path,
        media_type=doc.mime_type,
        filename=doc.original_filename
    )

@router.post("/{document_id}/permissions", response_model=PermissionResponse)
def grant_permission(
    document_id: str,
    grant_in: PermissionGrantRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    doc = db.query(Document).filter(Document.id == document_id, Document.is_deleted == False).first()
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")

    # Only document owner or system admin can grant permissions
    if doc.owner_id != current_user.id and current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only owner can grant permissions")

    target_clean = grant_in.grantee_email.strip().lower()
    grantee = db.query(User).filter(
        or_(
            func.lower(User.email) == target_clean,
            func.lower(User.username) == target_clean
        )
    ).first()
    if not grantee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail=f"Target user '{grant_in.grantee_email}' not found. Use a registered email (e.g. viewer@trustvault.io)"
        )

    existing_perms = db.query(DocumentPermission).filter(
        DocumentPermission.document_id == doc.id,
        DocumentPermission.grantee_id == grantee.id
    ).all()

    if existing_perms:
        perm = existing_perms[0]
        perm.can_read = grant_in.can_read
        perm.can_edit = grant_in.can_edit
        perm.is_active = True
        perm.revoked_at = None
        for duplicate in existing_perms[1:]:
            db.delete(duplicate)
    else:
        perm = DocumentPermission(
            document_id=doc.id,
            grantee_id=grantee.id,
            granted_by_id=current_user.id,
            can_read=grant_in.can_read,
            can_edit=grant_in.can_edit,
            is_active=True
        )
        db.add(perm)

    db.commit()
    db.refresh(perm)

    record_audit_event(
        db=db,
        action=AuditAction.PERM_GRANT,
        user_id=current_user.id,
        document_id=doc.id,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
        metadata={
            "grantee_id": grantee.id,
            "grantee_email": grantee.email,
            "can_read": perm.can_read,
            "can_edit": perm.can_edit
        }
    )

    return {
        "id": perm.id,
        "document_id": perm.document_id,
        "grantee_id": perm.grantee_id,
        "grantee_username": grantee.username,
        "grantee_email": grantee.email,
        "can_read": perm.can_read,
        "can_edit": perm.can_edit,
        "is_active": perm.is_active,
        "created_at": perm.created_at
    }

@router.delete("/{document_id}/permissions/{grantee_id}")
def revoke_permission(
    document_id: str,
    grantee_id: str,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    INSTANT REVOCATION:
    Marks permission row as inactive immediately inside DB transaction.
    """
    from datetime import datetime, timezone

    doc = db.query(Document).filter(Document.id == document_id, Document.is_deleted == False).first()
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")

    if doc.owner_id != current_user.id and current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only owner can revoke permissions")

    # Resolve grantee identifier (may be user UUID, permission UUID, email, or username)
    user_match = db.query(User).filter(
        or_(
            User.id == grantee_id,
            func.lower(User.email) == grantee_id.lower(),
            func.lower(User.username) == grantee_id.lower()
        )
    ).first()
    target_user_id = user_match.id if user_match else grantee_id

    # Find active permissions matching either grantee_id, target_user_id or permission id
    perms = db.query(DocumentPermission).filter(
        DocumentPermission.document_id == doc.id,
        or_(
            DocumentPermission.grantee_id == target_user_id,
            DocumentPermission.grantee_id == grantee_id,
            DocumentPermission.id == grantee_id
        ),
        DocumentPermission.is_active == True
    ).all()

    if not perms:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Active permission not found")

    now = datetime.now(timezone.utc)
    for perm in perms:
        perm.is_active = False
        perm.revoked_at = now
    db.commit()

    record_audit_event(
        db=db,
        action=AuditAction.PERM_REVOKE,
        user_id=current_user.id,
        document_id=doc.id,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
        metadata={"revoked_grantee_id": grantee_id}
    )

    return {"status": "success", "message": "Access revoked immediately."}

@router.patch("/{document_id}", response_model=DocumentResponse)
def update_document(
    document_id: str,
    update_data: DocumentUpdateRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update document metadata (title, category).
    Authorized: Document Owner, Admin, or Viewer granted with can_edit=True.
    Read-only viewers get 403 Forbidden.
    Unauthorized users get 404 Not Found (Zero existence oracle).
    """
    doc = db.query(Document).filter(Document.id == document_id, Document.is_deleted == False).first()
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")

    # Check if user has edit access
    if not check_document_access(db, doc, current_user, require_edit=True):
        # If user has read access, return 403 Forbidden
        if check_document_access(db, doc, current_user, require_edit=False):
            record_audit_event(
                db=db,
                action=AuditAction.ACCESS_DENIED,
                user_id=current_user.id,
                document_id=doc.id,
                ip_address=request.client.host if request.client else None,
                user_agent=request.headers.get("user-agent"),
                metadata={"reason": "Read-only viewer attempted document edit"}
            )
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Edit permission required")
        else:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")

    changes = {}
    if update_data.title is not None and update_data.title.strip():
        changes["old_title"] = doc.title
        doc.title = update_data.title.strip()
        changes["new_title"] = doc.title

    if update_data.category is not None and update_data.category.strip():
        changes["old_category"] = doc.category
        doc.category = update_data.category.strip()
        changes["new_category"] = doc.category

    db.commit()
    db.refresh(doc)

    record_audit_event(
        db=db,
        action=AuditAction.DOC_UPDATE,
        user_id=current_user.id,
        document_id=doc.id,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
        metadata=changes
    )

    return doc

@router.delete("/{document_id}")
def delete_document(
    document_id: str,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete document.
    Authorized: Document Owner or Admin ONLY.
    Viewers (even with can_edit=True) get 403 Forbidden.
    Unauthorized users get 404 Not Found.
    Audit log remains cryptographically intact.
    """
    doc = db.query(Document).filter(Document.id == document_id, Document.is_deleted == False).first()
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")

    # Strictly check owner or admin
    if doc.owner_id != current_user.id and current_user.role != UserRole.ADMIN:
        if check_document_access(db, doc, current_user, require_edit=False):
            record_audit_event(
                db=db,
                action=AuditAction.ACCESS_DENIED,
                user_id=current_user.id,
                document_id=doc.id,
                ip_address=request.client.host if request.client else None,
                user_agent=request.headers.get("user-agent"),
                metadata={"reason": "Non-owner attempted document deletion"}
            )
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only document owner or admin can delete document")
        else:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")

    doc.is_deleted = True
    db.commit()

    # Safely clean up storage file
    storage_manager.delete(doc.storage_path)

    record_audit_event(
        db=db,
        action=AuditAction.DOC_DELETE,
        user_id=current_user.id,
        document_id=doc.id,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
        metadata={"title": doc.title, "filename": doc.original_filename}
    )

    return {"status": "success", "message": "Document deleted successfully."}
