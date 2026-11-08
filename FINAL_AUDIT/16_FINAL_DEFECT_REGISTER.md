# 16 — FINAL DEFECT REGISTER
## Evaluator Challenge Findings & Resolution Matrix

| Defect ID | Severity | Description | Root Cause | Status | Resolution |
|:---|:---|:---|:---|:---|:---|
| **DEF-01** | Medium | N+1 queries on document list | Lazy loaded `owner.username` and permissions | **RESOLVED** | Added `joinedload(Document.owner)` and `selectinload(Document.permissions)` |
| **DEF-02** | Medium | High sequential latency deleting multiple docs | Sequential client DELETE requests | **RESOLVED** | Implemented dedicated `POST /api/documents/bulk-delete` with batch queries |
| **DEF-03** | Low | High UI perceived latency on edits | Synchronous blocking await before dialog close | **RESOLVED** | Added optimistic React state updating with automated rollback on failure |
| **DEF-04** | Architectural | Soft-deleted documents expunge S3 file immediately | Storage cleanup prevents orphan costs | **ACCEPTED RISK** | Meets strict privacy and zero-footprint requirements; undelete requires backup |
| **DEF-05** | Architectural | Pre-signed S3 download URLs valid until 300s TTL | AWS S3 signature caching at CDN edge | **ACCEPTED RISK** | Mitigated by using streaming proxy by default and capping pre-signed TTL |
