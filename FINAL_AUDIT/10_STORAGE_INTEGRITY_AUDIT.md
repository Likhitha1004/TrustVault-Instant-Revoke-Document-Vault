# 10 — STORAGE INTEGRITY AUDIT
## Cloud Object Storage (Supabase S3) vs Database Consistency

- **Storage Manager Architecture**:
  - Supports dual backend: Local ephemeral/disk for test environments, S3-compatible cloud storage for production.
  - Production Guard: Explicitly raises `RuntimeError` if running in production without configuring cloud S3 or setting `ALLOW_EPHEMERAL_STORAGE=true`.
- **Upload Integrity**: Calculates SHA-256 hash in a single streaming pass during upload; verifies against stored hash.
- **Storage Cleanup Lifecycle**:
  - When a document is deleted, `storage_manager.delete(doc.storage_path)` expunges the underlying cloud S3 object.
  - Prevents orphaned storage costs and complies with strict zero-footprint data erasure mandates.
- **Storage Status**: **PASS**.
