# TrustVault Test Execution & Verification Report

Date: 2026-11-01
Platform: Windows 11 / Python 3.11 / Node v20 / Vite 8.3.5 / Playwright Chromium Headless

---

## 1. Summary of Execution

| Category | Suite / Engine | Total Tests | Passed | Failed | Skipped | Pass Rate |
|---|---|---|---|---|---|---|
| **Snovasys Requirements** | pytest (`test_all_requirements.py`) | 10 | 10 | 0 | 0 | 100% |
| **Audit Scale & Cryptography**| pytest (`test_audit_1000_cases.py`) | 7 | 7 | 0 | 0 | 100% |
| **Extended Lifecycle & Search**| pytest (`test_extended_requirements.py`) | 6 | 6 | 0 | 0 | 100% |
| **Security & IDOR Tampering** | pytest (`test_security.py`) | 3 | 3 | 0 | 0 | 100% |
| **End-to-End Browser Workflows**| Playwright Headless Chromium | 6 | 6 | 0 | 0 | 100% |
| **Total** | | **32** | **32** | **0** | **0** | **100%** |

---

## 2. Playwright End-to-End Browser Test Workflows

Directory: `C:/Users/Snuhith/projects/TrustVault/playwright_evidence/`

1. **Workflow 1: Login View & Role Selection**
   * Action: Navigate to `http://127.0.0.1:5173`.
   * Result: Rendered clean login screen with quick role chips (Admin, Owner, Viewer), zero console errors.
   * Artifact: `01_login_page.png`

2. **Workflow 2: Admin Login & Chained Audit Verification**
   * Action: Authenticate as `admin@trustvault.io`, switch to "Chained Audit Trail" tab, verify cryptographic chain status.
   * Result: Chain verified 100% valid, metrics displayed, clean logout.
   * Artifacts: `02_admin_dashboard.png`, `03_admin_audit_chain.png`

3. **Workflow 3: Owner Login & Document Upload**
   * Action: Authenticate as `owner@trustvault.io`, upload `sample_nda.pdf` with metadata.
   * Result: File uploaded with magic-byte check, SHA-256 hash computed, document appears in owner vault list.
   * Artifacts: `04_owner_vault.png`, `05_doc_uploaded.png`

4. **Workflow 4: Owner Grants Permission to Viewer**
   * Action: Click "+ Grant Access", enter `viewer@trustvault.io`, select "Can Edit", submit form.
   * Result: Permission row created with audit event, success banner shown.
   * Artifact: `06_permission_granted.png`

5. **Workflow 5: Viewer Login, Metadata Edit & Streaming Download**
   * Action: Authenticate as `viewer@trustvault.io`, view shared document, open edit modal, change title to `Playwright NDA Contract (Edited by Viewer)`, click Save.
   * Result: Metadata updated via `PATCH /documents/{id}`, new title rendered immediately, logout clean.
   * Artifacts: `07_viewer_vault.png`, `08_viewer_edited.png`

6. **Workflow 6: Owner Immediate Revocation & Deletion**
   * Action: Re-login as Owner, click "Instantly Revoke Access" (viewer denied instantly), click "Delete Document".
   * Result: Access revoked with sub-millisecond enforcement, document deleted from vault and disk storage.
   * Artifacts: `09_owner_revoked.png`, `10_owner_deleted.png`

---

## 3. Production Build Output

Command: `cd frontend && npm run build`
```
> frontend@0.0.0 build
> tsc -b && vite build

vite v8.3.5 building client environment for production...
transforming...
✓ 2045 modules transformed.
rendering chunks...
computing gzip size...
dist/index.html                   0.49 kB │ gzip:  0.32 kB
dist/assets/index-C1I-1Ckd.css   34.18 kB │ gzip:  6.54 kB
dist/assets/index-BWJ6p3NW.js   262.09 kB │ gzip: 78.78 kB

✓ built in 980ms
```

---

## 4. Pytest Execution Output

Command: `cd backend && ./venv/Scripts/python.exe -m pytest tests/`
```
============================= test session starts =============================
platform win32 -- Python 3.11.16, pytest-9.2.0, pluggy-1.7.0
rootdir: C:\Users\Snuhith\projects\TrustVault\backend
plugins: anyio-4.16.0
collected 26 items

tests\test_all_requirements.py ..........                                [ 38%]
tests\test_audit_1000_cases.py .......                                   [ 65%]
tests\test_extended_requirements.py ......                               [ 88%]
tests\test_security.py ...                                               [100%]

================== 26 passed, 1 warning in 106.49s (0:01:46) ==================
```

---

## 5. Security & Edge Case Validations

* **Failing Login Test**:
  * Request: `POST /api/auth/login` with incorrect password.
  * Response: `401 Unauthorized` (`{"detail": "Invalid email or password"}`).
* **404 Document Test**:
  * Request: `GET /api/documents/non-existent-uuid-12345` with valid token.
  * Response: `404 Not Found` (`{"detail": "Document not found"}`).
* **10MB Upload Limit**:
  * Request: Attempt upload of >10MB binary payload.
  * Response: `413 Request Entity Too Large` (`{"detail": "File size exceeds 10MB limit"}`).
* **Malicious Path Traversal**:
  * Filenames with `../../` or path traversal strings are sanitized through `re.sub(r'[^a-zA-Z0-9_.-]', '_', ...)`.
