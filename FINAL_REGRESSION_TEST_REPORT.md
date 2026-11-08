# TrustVault Final Regression Test Report

**Evaluation Date:** November 02, 2026  
**Commit Hash:** `fed0fb5e1fcc72520efe0346084195ddc867d07b`  
**Target Environment:** `https://trust-vault-smoky.vercel.app`  

---

## 1. Test Summary

| Scope | Executed | Passed | Failed | Blocked / Untested | Conclusion |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Backend Unit & Security** | 32 | 32 | 0 | 0 | **PASS** |
| **Frontend TypeScript Build** | 1 | 1 | 0 | 0 | **PASS** |
| **Production API Endpoints** | 18 | 18 | 0 | 0 | **PASS** |
| **Security & IDOR Isolation** | 8 | 8 | 0 | 0 | **PASS** |
| **Static Bundle Secret Hygiene**| 1 | 1 | 0 | 0 | **PASS** |

*Conclusion:* No defects were found within the executed verification scope.

---

## 2. Detailed Verification Results

### A. Backend Pytest Suite (`backend/tests/`)
Command: `backend/venv/Scripts/python.exe -m pytest tests -v` (32 tests):
- `test_01_user_registration_and_rbac_roles`: **PASSED**
- `test_02_password_hashing_and_jwt_issuance`: **PASSED**
- `test_03_document_upload_and_magic_byte_validation`: **PASSED**
- `test_04_bola_idor_prevention_on_metadata_and_download`: **PASSED**
- `test_05_permission_grant_and_streaming_proxy`: **PASSED**
- `test_06_instant_revocation_zero_stale_window`: **PASSED**
- `test_07_chained_audit_trail_valid_verification`: **PASSED**
- `test_08_tampered_database_audit_trail_detection`: **PASSED**
- `test_09_viewer_cannot_upload_or_grant_permissions`: **PASSED**
- `test_10_adversarial_judge_removes_auth_check_fails`: **PASSED**
- `test_1000_sequential_chained_audit_events`: **PASSED**
- `test_1000_audit_chain_tamper_detection_at_multiple_offsets` (5 tests): **PASSED**
- `test_liveness_and_readiness_checks`: **PASSED**
- `test_storage_manager_lifecycle`: **PASSED**
- `test_seed_idempotency_and_production_security`: **PASSED**
- `test_production_storage_safety_guard`: **PASSED**
- `test_admin_recovery_tool`: **PASSED**
- `test_database_persistence_across_simulated_restart`: **PASSED**
- `test_document_edit_permissions`: **PASSED**
- `test_document_delete_permissions`: **PASSED**
- `test_file_upload_validation_and_size_limits`: **PASSED**
- `test_search_by_owner_and_date`: **PASSED**
- `test_admin_metrics_and_tamper_evidence`: **PASSED**
- `test_mutation_defense_fails_when_auth_bypassed`: **PASSED**
- `test_10_adversarial_security_suite`: **PASSED**
- `test_judge_removes_auth_check_fails`: **PASSED**
- `test_tampered_database_audit_log_detected`: **PASSED**

### B. Frontend TypeScript & Production Build
Command: `npm run build` inside `frontend/`:
- `tsc -b`: **PASSED** (0 errors)
- `vite build`: **PASSED** (2,053 modules transformed in 46.61s)
- Production assets generated in `frontend/dist/`.

### C. Live Production API Tests (`https://trust-vault-smoky.vercel.app`)
- Healthz check (`/healthz`): **PASSED** (HTTP 200, 526.9ms avg)
- Supabase DB connection (`/api/readyz`): **PASSED** (HTTP 200)
- Role registration & JWT login (`/api/auth/login`): **PASSED**
- JWT session revocation on logout (`/api/auth/logout`): **PASSED** (Subsequent requests return HTTP 401)
- Presigned S3 upload intent (`/api/documents/upload-intent`): **PASSED**
- Direct S3 PUT: **PASSED** (HTTP 200)
- Confirm upload: **PASSED** (Document committed to vault)
- Instant permission revocation: **PASSED** (HTTP 404 instant access denial)
- IDOR isolation: **PASSED** (HTTP 404 on unshared document access)

---

## 3. Preserved Architecture & Invariants

- **Hosting Provider:** Maintained on Vercel Serverless (FastAPI) + Supabase PostgreSQL.
- **Cost Ceiling:** Strictly zero-cost limits maintained (₹0 / $0 spend).
- **Upload Protocol:** Preserved direct-to-S3 presigned upload with 10MB limit.
- **Audit Integrity:** Cryptographic SHA-256 chain verified end-to-end.
