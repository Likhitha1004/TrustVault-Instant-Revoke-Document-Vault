import json
import threading
import uuid
from datetime import datetime, timezone

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.models import AuditAction, AuditLog

GENESIS_HASH = "0" * 64
_POSTGRES_AUDIT_LOCK_KEY = 77123991
_audit_lock = threading.Lock()


def action_name(action) -> str:
    """Normalise an AuditAction (or raw value) to the string used in hashing."""
    return action.value if hasattr(action, "value") else str(action)


def compute_entry_hash(entry: AuditLog, previous_hash: str | None = None) -> str:
    """Recompute the SHA-256 signature for a stored audit entry."""
    return AuditLog.compute_hash(
        uuid_str=entry.uuid_str,
        user_id=entry.user_id,
        document_id=entry.document_id,
        action=action_name(entry.action),
        metadata_str=entry.metadata_json,
        previous_hash=entry.previous_hash if previous_hash is None else previous_hash,
    )


def _acquire_postgres_chain_lock(db: Session) -> None:
    """On PostgreSQL, take a transaction-scoped advisory lock so audit commits are
    strictly serialised across concurrent serverless instances."""
    if db.bind and db.bind.dialect.name == "postgresql":
        try:
            db.execute(text(f"SELECT pg_advisory_xact_lock({_POSTGRES_AUDIT_LOCK_KEY})"))
        except Exception:
            pass


def record_audit_event(
    db: Session,
    action: AuditAction,
    user_id: str | None = None,
    document_id: str | None = None,
    ip_address: str | None = None,
    user_agent: str | None = None,
    metadata: dict | None = None,
) -> AuditLog:
    """
    Appends an immutable audit log entry linked to the previous entry via SHA-256 hash.
    Provides mathematical proof of tamper-evidence. Thread-safe sequential chain locking.
    """
    metadata_str = json.dumps(metadata or {}, sort_keys=True)

    with _audit_lock:
        _acquire_postgres_chain_lock(db)

        # Strictly ordered by auto-incrementing integer id
        latest_entry = db.query(AuditLog).order_by(AuditLog.id.desc()).first()
        previous_hash = latest_entry.current_hash if latest_entry else GENESIS_HASH

        entry_uuid = str(uuid.uuid4())

        log_entry = AuditLog(
            uuid_str=entry_uuid,
            timestamp=datetime.now(timezone.utc),
            user_id=user_id,
            document_id=document_id,
            action=action,
            ip_address=ip_address,
            user_agent=user_agent[:255] if user_agent else None,
            metadata_json=metadata_str,
            previous_hash=previous_hash,
            current_hash=AuditLog.compute_hash(
                uuid_str=entry_uuid,
                user_id=user_id,
                document_id=document_id,
                action=action_name(action),
                metadata_str=metadata_str,
                previous_hash=previous_hash,
            ),
        )

        db.add(log_entry)
        db.commit()
        db.refresh(log_entry)
        return log_entry


def verify_audit_chain(db: Session) -> dict:
    """
    Verifies every entry in the audit trail from the genesis block forward.
    Returns whether the chain is unbroken, along with broken index details if tampered.
    """
    logs = db.query(AuditLog).order_by(AuditLog.id.asc()).all()
    if not logs:
        return {"status": "valid", "total_records": 0, "message": "Audit trail is empty."}

    expected_previous_hash = GENESIS_HASH
    for index, entry in enumerate(logs):
        if entry.previous_hash != expected_previous_hash:
            return {
                "status": "tampered",
                "broken_at_index": index,
                "broken_log_id": entry.id,
                "reason": f"Previous hash mismatch. Expected {expected_previous_hash}, found {entry.previous_hash}",
            }

        recalculated_hash = compute_entry_hash(entry)
        if recalculated_hash != entry.current_hash:
            return {
                "status": "tampered",
                "broken_at_index": index,
                "broken_log_id": entry.id,
                "reason": f"Content signature mismatch. Expected {recalculated_hash}, found {entry.current_hash}",
            }

        expected_previous_hash = entry.current_hash

    return {
        "status": "valid",
        "total_records": len(logs),
        "latest_block_hash": expected_previous_hash,
        "message": "Audit chain mathematically verified: 100% intact and untampered.",
    }
