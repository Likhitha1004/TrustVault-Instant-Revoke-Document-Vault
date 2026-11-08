# TrustVault Data Integrity & Storage Audit Report

## 1. Database Consistency
- SQLite database schema enforced with Foreign Keys (`User.id`, `Document.owner_id`, `DocumentPermission.grantee_id`).
- Soft-deletion via `Document.is_deleted = True` ensures orphaned permission records do not cause dangling references.

## 2. Cryptographic Hash Integrity
- Files stored on disk are verified against their SHA-256 digests (`file_hash_sha256`).
- Audit log chain computes `current_hash = SHA256(...)` linking previous block hash to current entry. Verified valid across all 146+ events.

## 3. Storage Layer Consistency
- Stored binaries reside in isolated storage directories with deterministic hash filenames, preventing collision.
