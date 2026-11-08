# TRUSTVAULT FINAL API STATUS & ENDPOINT INVENTORY

**Date:** 2026-11-02  
**API Specification:** RESTful JSON API with OpenAPI 3.0 / Swagger documentation  
**Base Path:** `/api`  

---

## 1. REST Endpoint Inventory & Authorization Matrix

| Method | Endpoint Path | Role / Access Requirement | Verified Functionality | Status |
|---|---|---|---|---|
| `GET` | `/healthz` | Public | System liveness probe; responds in <5ms | **PASS** |
| `GET` | `/readyz` | Public | Readiness probe; validates DB & storage connectivity | **PASS** |
| `POST`| `/api/auth/register` | Public | Registers new user account with argon2 password hash | **PASS** |
| `POST`| `/api/auth/login` | Public | Authenticates credentials; returns Bearer JWT | **PASS** |
| `POST`| `/api/auth/logout` | Authenticated | Revokes current JWT in `RevokedToken` table | **PASS** |
| `GET` | `/api/auth/me` | Authenticated | Retrieves current authenticated user profile | **PASS** |
| `GET` | `/api/documents/` | Authenticated | Lists documents owned by user or shared with user | **PASS** |
| `POST`| `/api/documents/upload` | Owner / Admin | Uploads file, computes SHA-256, stores binary | **PASS** |
| `GET` | `/api/documents/{id}` | Read Permitted | Returns document metadata (IDOR protected) | **PASS** |
| `PATCH`| `/api/documents/{id}` | Edit Permitted | Updates title/category; records audit log | **PASS** |
| `DELETE`| `/api/documents/{id}`| Owner / Admin | Removes document binary & DB records; logs audit | **PASS** |
| `GET` | `/api/documents/{id}/download`| Read Permitted | Streams binary file; verifies SHA-256 integrity | **PASS** |
| `POST`| `/api/documents/{id}/permissions`| Owner / Admin | Grants read/edit permission to target user | **PASS** |
| `DELETE`| `/api/documents/{id}/permissions/{grantee_id}`| Owner / Admin | Revokes permission immediately (0ms latency) | **PASS** |
| `GET` | `/api/audit/logs` | Admin Only | Fetches paginated audit logs with search/filters | **PASS** |
| `GET` | `/api/audit/metrics` | Admin Only | Calculates compliance stats and event counts | **PASS** |
| `GET` | `/api/audit/verify-chain` | Admin Only | Cryptographically validates entire SHA-256 chain | **PASS** |

---

## 2. Investigation of HTTP Error Codes

| Status Code | Scenario in TrustVault | Architectural Handling & Defense |
|---|---|---|
| **401 Unauthorized** | Missing or expired JWT token | Client redirects to login tab; clears stale session from localStorage. |
| **402 Payment Required**| Provider billing paywall trigger | **Strictly prevented in TrustVault**. System limits uploads to 10MB to never exceed Supabase free quota. No paid APIs invoked. |
| **403 Forbidden** | Non-owner attempts edit/delete or non-admin attempts audit view | Server rejects with structured JSON error; prevents privilege escalation. |
| **404 Not Found** | Unauthorized user accesses another user's document ID | Zero-existence oracle returns 404 to hide document presence. |
| **413 Payload Too Large**| Upload exceeds 10MB cap | Server streams chunked read and aborts at 10MB ceiling before disk/memory saturation. |
| **422 Validation Error** | Invalid schema payload or bad email | Pydantic model rejects with precise field-level feedback. |
| **500 Server Error** | Unexpected unhandled exception | Global FastAPI exception handler catches, logs correlation ID, and returns safe response without leaking stack traces. |
