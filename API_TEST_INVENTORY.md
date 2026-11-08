# TrustVault Complete API Test Inventory

| Endpoint | Method | Required Role | Request Body / Params | Expected Status | Verified Status |
|----------|--------|---------------|-----------------------|-----------------|-----------------|
| `/api/auth/login` | POST | Public | `username_or_email`, `password` | 200 / 401 | 200 PASS |
| `/api/auth/register` | POST | Public | `username`, `email`, `password`, `role` | 200 / 400 | 200 PASS |
| `/api/auth/logout` | POST | Authenticated | None | 200 | 200 PASS |
| `/api/auth/me` | GET | Authenticated | None | 200 / 401 | 200 PASS |
| `/api/documents` | GET | Authenticated | `search`, `category`, `owner`, `date_from`, `date_to`, `sort_by` | 200 | 200 PASS |
| `/api/documents/upload` | POST | Owner / Admin | `multipart/form-data` (file, title, category) | 200 / 400 / 413 | 200 PASS |
| `/api/documents/{id}` | GET | Permitted / Owner / Admin | None | 200 / 404 | 200 PASS |
| `/api/documents/{id}` | PATCH | Owner / Admin / CanEdit | `title`, `category` | 200 / 403 / 404 | 200 PASS |
| `/api/documents/{id}` | DELETE | Owner / Admin | None | 200 / 403 / 404 | 200 PASS |
| `/api/documents/{id}/download` | GET | Permitted / Owner / Admin | None | 200 / 403 / 404 | 200 PASS |
| `/api/documents/{id}/permissions` | POST | Owner / Admin | `grantee_email`, `can_edit` | 200 / 403 / 404 | 200 PASS |
| `/api/documents/{id}/permissions/{grantee_id}` | DELETE | Owner / Admin | None | 200 / 403 / 404 | 200 PASS |
| `/api/audit` | GET | Admin | `limit`, `offset`, `action` | 200 / 403 | 200 PASS |
| `/api/audit/verify` | GET | Admin | None | 200 / 403 | 200 PASS |
| `/api/audit/metrics` | GET | Admin | None | 200 / 403 | 200 PASS |
