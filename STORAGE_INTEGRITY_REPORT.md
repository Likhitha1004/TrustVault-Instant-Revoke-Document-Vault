# TRUSTVAULT STORAGE & OBJECT INTEGRITY REPORT

## 1. S3-Compatible Storage Verification
- **Chunked Streaming:** Uploads read in 1MB chunks to compute SHA-256 on the fly without memory spikes.
- **Enforced File Ceiling:** 10MB maximum file size strictly enforced; files >10MB aborted before writing to storage.
- **Hash Verification:** On download, byte streams match recorded database SHA-256 hash byte-for-byte.
- **Storage Isolation:** Private bucket `trustvault-docs` prevents direct public bucket URL access.