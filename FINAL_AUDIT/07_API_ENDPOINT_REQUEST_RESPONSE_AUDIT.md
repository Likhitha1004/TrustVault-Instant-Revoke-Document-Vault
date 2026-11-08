# 07 — API ENDPOINT REQUEST / RESPONSE AUDIT
## Complete HTTP Route Inventory & Status Code Matrix

| Route | Method | Auth Required | Expected Status | Error Codes | DB / Storage Effect | Status |
|:---|:---|:---|:---|:---|:---|:---|
| `/api/auth/register` | POST | None | 201 Created | 400 (Duplicate) | User created with hashed password | **PASS** |
| `/api/auth/login` | POST | None | 200 OK | 401 (Invalid creds) | Issues signed HS256 JWT | **PASS** |
| `/api/auth/me` | GET | Bearer Token | 200 OK | 401 (Expired/Invalid) | Reads current user profile | **PASS** |
| `/api/documents/upload` | POST | Owner / Admin | 201 Created | 400 (Bad magic bytes), 413 (>10MB) | Saves to S3/Disk, records upload in audit | **PASS** |
| `/api/documents` | GET | Authenticated | 200 OK | 401 (Unauth) | Eager loaded list with owner & permissions | **PASS** |
| `/api/documents/{id}` | GET | Reader / Owner / Admin | 200 OK | 404 (Unauth/Missing) | Reads document metadata | **PASS** |
| `/api/documents/{id}/download` | GET | Reader / Owner / Admin | 200 OK / 307 Redirect | 404 (Unauth/Revoked) | Streams binary file; logs download audit | **PASS** |
| `/api/documents/{id}` | PATCH | Owner / Viewer(Edit) | 200 OK | 404 (Unauth), 403 (No edit) | Updates title/category; logs edit audit | **PASS** |
| `/api/documents/{id}` | DELETE | Owner / Admin | 200 OK | 404 (Unauth), 403 (Viewer) | Soft deletes doc; expunges S3 storage | **PASS** |
| `/api/documents/bulk-delete` | POST | Owner / Admin | 200 OK | 401 (Unauth) | Atomic multi-doc deletion & audit logs | **PASS** |
| `/api/documents/{id}/permissions` | POST | Owner / Admin | 200 OK | 404 (Unauth), 403 (Viewer) | Creates/updates permission record | **PASS** |
| `/api/documents/{id}/permissions/{grantee_id}` | DELETE | Owner / Admin | 200 OK | 404 (Unauth), 403 (Viewer) | Deletes permission (Instant revocation) | **PASS** |
| `/api/audit` | GET | Admin Only | 200 OK | 403 (Non-admin) | Returns audit ledger entries | **PASS** |
| `/api/audit/verify` | GET | Admin Only | 200 OK | 403 (Non-admin) | Verifies complete SHA-256 hash chain | **PASS** |
| `/api/audit/metrics` | GET | Admin Only | 200 OK | 403 (Non-admin) | Computes security & document stats | **PASS** |
| `/healthz` | GET | None | 200 OK | - | Liveness probe | **PASS** |
| `/api/readyz` | GET | None | 200 OK | 503 (DB down) | Readiness probe with DB ping | **PASS** |
