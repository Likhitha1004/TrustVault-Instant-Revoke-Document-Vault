# FINAL FUNCTIONAL TEST REPORT

**Target**: https://trust-vault-smoky.vercel.app  
**Date**: November 2, 2026, 22:30 IST  
**Verified Commit Hash**: `27cedca73248425e2db234d644d027da30f87d78`  
**Scope**: Full end-to-end interactive frontend & backend functional verification  
**Total Tests**: 17 Executed | 17 PASS | 0 FAIL | 0 BLOCKED | 0 NOT TESTED  

---

## 1. Summary of Functional Operations

| Test Case | Description | Tested Endpoint / Component | Result | Evidence |
| :--- | :--- | :--- | :--- | :--- |
| **TC-01: Health Probe** | Basic liveness check | `GET /healthz` | **PASS** | HTTP 200, `{"status":"healthy"}` |
| **TC-02: DB Readiness** | Live PostgreSQL query probe | `GET /api/readyz` | **PASS** | HTTP 200, `{"database":"connected"}` |
| **TC-03: User Registration** | Account creation (Owner, Viewer, Admin) | `POST /api/auth/register` | **PASS** | HTTP 201, user profile returned |
| **TC-04: User Authentication** | Password validation & JWT issuance | `POST /api/auth/login` | **PASS** | HTTP 200, Bearer token returned |
| **TC-05: User Profile Fetch** | Current user identity resolution | `GET /api/auth/me` | **PASS** | HTTP 200, matches authenticated JWT |
| **TC-06: JWT Logout & Revocation**| Invalidate token in `RevokedToken` table | `POST /api/auth/logout` | **PASS** | HTTP 200, subsequent request returns HTTP 401 |
| **TC-07: Document Upload (<=4MB)**| Direct multipart file upload | `POST /api/documents/upload` | **PASS** | HTTP 201, Document record created |
| **TC-08: Large Upload (<=10MB)**| Direct S3 presigned upload flow | `POST /upload-intent` + `confirm-upload` | **PASS** | HTTP 200/201, 10MB file stored in S3 |
| **TC-09: Document Search** | Full-text query across titles | `GET /api/documents?search=Patent` | **PASS** | HTTP 200, filtered results returned |
| **TC-10: Category Filter** | Category-based document grouping | `GET /api/documents?category=Audit` | **PASS** | HTTP 200, matching items returned |
| **TC-11: Multi-Field Sorting** | Sort by date asc/desc, size, title | `GET /api/documents?sort_by=newest` | **PASS** | HTTP 200, deterministic ordering |
| **TC-12: Permission Grant** | Owner sharing document to Viewer | `POST /documents/{id}/permissions` | **PASS** | HTTP 200, permission recorded |
| **TC-13: Instant Revocation** | Owner revoking Viewer access | `DELETE /documents/{id}/permissions/{u}` | **PASS** | HTTP 200, `{"status":"success"}` |
| **TC-14: Metadata Update** | Patching document title / category | `PATCH /api/documents/{id}` | **PASS** | HTTP 200, metadata updated |
| **TC-15: Soft Deletion** | Marking document deleted | `DELETE /api/documents/{id}` | **PASS** | HTTP 200, `is_deleted = True` |
| **TC-16: Admin Metrics** | Consolidated system telemetry | `GET /api/audit/metrics` | **PASS** | HTTP 200, stats returned |
| **TC-17: Audit Verification** | Cryptographic hash chain validation | `GET /api/audit/verify` | **PASS** | HTTP 200, mathematical proof valid |

---

## 2. Interactive UI Element Inventory

- **Registration / Login Form**: Responsive input fields, password toggle, role selector, error alerts. (**PASS**)
- **Dashboard Header**: Live user profile badge, role indicator, logout button. (**PASS**)
- **Document Vault Table**: Title, Category, File Size, SHA-256 fingerprint, Owner, Action menu. (**PASS**)
- **Upload Modal**: File drag-and-drop zone, file size calculator, SHA-256 pre-calculation progress. (**PASS**)
- **Sharing & Permission Dialog**: Email search, read/edit checkboxes, active share list, revoke buttons. (**PASS**)
- **Audit Log Inspector**: Paginated ledger, block index, timestamp, action type, hash links. (**PASS**)
