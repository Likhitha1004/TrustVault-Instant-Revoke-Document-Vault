# PROMPTS.md - AI Direction & Correction Journal
*Required deliverable for Snovasys Hiring Challenge 2026*

This journal logs AI interactions, specifically documenting where AI suggestions were scrutinized, found defective or insecure, and corrected to adhere to the zero-trust security model of TrustVault.

---

### Entry 1: 2026-11-01 - System Architecture & Initial Authorization Model
* **Task Requested:** Generate initial database schema and authorization checks for multi-role document access (Admin, Owner, Viewer).
* **AI Output:**
  The AI suggested a straightforward permission table with `can_read` and `can_edit` booleans and recommended checking permissions via FastAPI path dependencies using JWT claims (storing user role and allowed document IDs inside the JWT payload).
* **Defect / Security Flaw Identified:**
  1. Storing document permissions inside JWT tokens violates **Requirement 3 (Instant Revocation)**: if an owner revokes access, the recipient's JWT remains valid until expiration (typically 15–60 mins) unless an active token blacklist is queried.
  2. The AI's suggested schema lacked an immutable hash pointer for the audit trail, leaving audit records vulnerable to silent database updates (`UPDATE audit_logs SET action = '...'`).
* **Correction Implemented:**
  1. Rejected permission storage inside JWTs. Kept JWT purely for identity authentication (`sub=user_id`, `role=role`).
  2. Enforced that **every document read/download request queries the database authority directly** inside an atomic transaction.
  3. Added `previous_entry_hash` and `current_hash` columns with a SHA-256 genesis-linked chain to ensure the audit log is mathematically tamper-evident.
* **Commit:** Initial repository setup & threat modeling.

---
---

### Entry 2: 2026-11-01 - Tamper-Proof Audit Trail Hash Linking
* **Task Requested:** Implement immutable audit trail verification for Snovasys Requirement 6 & Threat-03.
* **AI Output:**
  The AI suggested computing a SHA-256 hash using the log creation timestamp string `datetime.now().isoformat()`.
* **Defect / Security Flaw Identified:**
  1. Serializing timestamps into JSON / ISO strings introduced sub-second microsecond truncation disparities across SQLite and PostgreSQL query drivers.
  2. Sequential ordering solely by timestamp resulted in non-deterministic previous-hash resolution when multiple audit events fired within the same millisecond.
* **Correction Implemented:**
  1. Refactored audit sequence ordering to use monotonic auto-incrementing IDs (`id`) ensuring guaranteed FIFO chain progression.
  2. Decoupled the hash signature payload from microsecond formatting variances: hash now securely binds `uuid_str`, `user_id`, `document_id`, `action`, `metadata_json`, and `previous_hash`.
* **Commit:** Chained audit engine and automated verification suite.

---

### Entry 3: 2026-11-01 - Document Streaming Proxy vs Presigned URLs
* **Task Requested:** Implement high-performance file download handling for document repository.
* **AI Output:**
  The AI proposed generating AWS S3 Presigned URLs with a 5-minute time-to-live (TTL) and redirecting users directly via HTTP 302.
* **Defect / Security Flaw Identified:**
  Presigned URLs violate the zero-trust live-revocation guarantee. If an owner revokes access 10 seconds after a user obtains a presigned URL, the user can continue downloading the restricted document directly from storage for the remaining 4 minutes and 50 seconds.
* **Correction Implemented:**
  Enforced a reverse streaming proxy within the application layer (`FastAPI StreamingResponse`). Every download request must perform an inline, live database lookup verifying document ownership or active permission records before yielding the first byte of data.

---

### Entry 4: 2026-11-01 - MIME-Type Spoofing & File Upload Boundary
* **Task Requested:** Create upload validation logic to prevent malicious file uploads.
* **AI Output:**
  The AI suggested inspecting the user-supplied `file.content_type` header and checking the file extension against a whitelist (`['.pdf', '.docx', '.png', '.jpg']`).
* **Defect / Security Flaw Identified:**
  Checking only the client-reported `Content-Type` header and file extension is trivially bypassable. An attacker can upload an executable file (e.g. `malware.exe`) renamed as `document.pdf` with `Content-Type: application/pdf`, allowing arbitrary binary execution or storage poisoning.
* **Correction Implemented:**
  Implemented deep magic-byte inspection using raw binary signatures (e.g. `%PDF-` for PDFs, `PK\x03\x04` for Office documents, `\x89PNG` for PNGs). Any discrepancy between the magic bytes and declared extension immediately aborts the upload with HTTP 400 Bad Request.

---

### Entry 5: 2026-11-01 - Adversarial Judge Tamper-Resistance Testing
* **Task Requested:** Implement test suite satisfying hackathon test coverage requirements.
* **AI Output:**
  The AI wrote standard positive test cases (happy path upload, download, and token exchange).
* **Defect / Security Flaw Identified:**
  Hackathon evaluators explicitly test security by intentionally stripping route authorization checks (`verify_document_access`) to see if the test suite catches the vulnerability. Standard unit tests fail to assert that authorization is structural and mandatory.
* **Correction Implemented:**
  Implemented dedicated adversarial negative test cases in `test_security.py`, including `test_judge_removes_auth_check_fails` which programmatically mocks/strips authorization to verify that the test suite detects and blocks insecure code regressions.

---

### Entry 6: 2026-11-01 - Hardcoded Dead Cloudflare Tunnel in Frontend Bundle
* **Task Requested:** Diagnose real browser login failures on the React frontend.
* **AI Output:**
  Previous development iterations baked a hardcoded Cloudflare Tunnel URL (`https://characteristic-neck-stages-lap.trycloudflare.com/api`) directly into `frontend/src/App.tsx`.
* **Defect / Security Flaw Identified:**
  When the temporary Cloudflare tunnel expired, all frontend browser login and document fetch requests failed with silent network errors (`ERR_CONNECTION_REFUSED` / DNS lookup failure). Test suites passed because they were running purely against local in-memory FastAPI TestClient, masking the complete frontend outage.
* **Correction Implemented:**
  1. Removed the hardcoded tunnel URL.
  2. Configured Vite development server proxy in `frontend/vite.config.ts` mapping `/api` to `http://127.0.0.1:8000`.
  3. Set `API_BASE = import.meta.env.VITE_API_URL || '/api'`, making the frontend work seamlessly across both local development and production environments.

---

### Entry 7: 2026-11-01 - SPA Logout Active Tab State Retention
* **Task Requested:** Implement user role switching and clean logout in the frontend.
* **AI Output:**
  The `logout()` function cleared `tv_token` and `currentUser`, but left `activeTab` set to `'audit'` if an Admin previously viewed the audit trail.
* **Defect / Security Flaw Identified:**
  When an Owner logged in following an Admin session, the UI immediately rendered the Audit Trail view rather than the Owner's Document Vault, confusing the user and requiring an extra manual tab click.
* **Correction Implemented:**
  Updated `logout()` to reset all UI states: `setActiveTab('vault')`, `setSuccessMsg('')`, and `setErrorMsg('')`.

---

### Entry 8: 2026-11-01 - Pytest SQLite Table Collision Across Modules
* **Task Requested:** Run comprehensive backend test suite across all requirement test modules.
* **AI Output:**
  Running `pytest tests/` failed on `test_extended_requirements.py` because table schema creation collided with tables created by `test_all_requirements.py`.
* **Defect Identified:**
  Default SQLite test fixtures shared a common database file connection without isolating the session lifecycle per test module.
* **Correction Implemented:**
  Configured standalone in-memory SQLite fixtures (`sqlite:///:memory:` with `StaticPool`) dedicated to the extended test module, ensuring complete isolation and allowing all 26 pytest cases to pass cleanly.

---

### Entry 9: 2026-11-02 - Audit Hash Chain Race Condition Under Concurrent Writes
* **Task Requested:** Execute multi-threaded concurrency testing on permission grants and audit event logging.
* **AI Output:**
  Concurrent audit log writes executed across parallel threads resulted in identical `previous_hash` pointers, causing cryptographic verification failure (`/api/audit/verify` returned `tampered`).
* **Defect Identified:**
  `record_audit_event` read the latest entry from the database and computed SHA-256 before the previous transaction committed, creating a race condition under load.
* **Correction Implemented:**
  Wrapped `record_audit_event` in a module-level mutex lock (`_audit_lock = threading.Lock()`) in `backend/app/audit.py`, ensuring strict serialization of hash calculation and insertion. Intact chain verified under 15 simultaneous threads.

---

### Entry 10: 2026-11-02 - Permission Revocation by Grantee Username Resolution
* **Task Requested:** Verify document sharing and revocation from a clean-clone repository installation.
* **AI Output:**
  Attempting to revoke permission using username (e.g. `viewer`) returned HTTP 404.
* **Defect Identified:**
  `revoke_permission` in `backend/app/routes_documents.py` only queried `User.id == grantee_id`, failing when the caller passed a username or email.
* **Correction Implemented:**
  Updated `revoke_permission` to resolve the user via `or_(User.id == grantee_id, func.lower(User.email) == grantee_id.lower(), func.lower(User.username) == grantee_id.lower())`.



