# TrustVault 🛡️
> Secure Document Sharing with Cryptographically Tamper-Evident Audit Trail  
> **Engineered for Snovasys Fresher Hiring Challenge 2026 (RISE)**

[![Security: Zero-Trust](https://img.shields.io/badge/Security-Zero--Trust-emerald)](https://github.com/Likhitha1004/TrustVault-Instant-Revoke-Document-Vault)
[![Audit: SHA256 Chained](https://img.shields.io/badge/Audit-SHA256%20Chained-purple)](https://github.com/Likhitha1004/TrustVault-Instant-Revoke-Document-Vault)
[![Tests: 100% Adversarial Pass](https://img.shields.io/badge/Tests-100%25%20Adversarial%20Pass-blue)](https://github.com/Likhitha1004/TrustVault-Instant-Revoke-Document-Vault)

---

## 🌐 Live Deployments & Repository
* **GitHub Repository:** [https://github.com/Likhitha1004/TrustVault-Instant-Revoke-Document-Vault](https://github.com/Likhitha1004/TrustVault-Instant-Revoke-Document-Vault)
* **Production Live Application (Vercel):** [https://trust-vault-smoky.vercel.app](https://trust-vault-smoky.vercel.app)
* **Production API Health Endpoint:** [https://trust-vault-smoky.vercel.app/healthz](https://trust-vault-smoky.vercel.app/healthz)
* **Production Database Readiness:** [https://trust-vault-smoky.vercel.app/api/readyz](https://trust-vault-smoky.vercel.app/api/readyz)

---

## 🏗️ Architecture Overview

TrustVault operates as a unified, zero-cost production cloud application:
* **Frontend:** React 18 with TypeScript, Tailwind CSS, Lucide icons, and Vite. Deployed on Vercel Edge CDN.
* **Backend:** FastAPI (Python 3.12) deployed on Vercel Serverless Functions (`/api/index.py`) using ASGI.
* **Database:** Supabase Managed PostgreSQL via transaction pooler with SQLAlchemy `NullPool` (preventing serverless connection leaks).
* **Storage:** Supabase S3-Compatible Storage via presigned direct PUT/GET workflows with a strict 10MB ceiling.
* **Audit Engine:** Continuous SHA-256 cryptographic hash-chained audit ledger with PostgreSQL advisory lock serialization (`pg_advisory_xact_lock(77123991)`).

---

## 🔒 10 Functional Requirements & Security Architecture

1. **User Authentication & RBAC (Req 1 & 2):**
   * Three distinct roles: **Admin**, **Document Owner**, **Viewer**.
   * Passwords hashed via high-workfactor `bcrypt`. Stateless JWTs encode only user identity, never authorization states.
2. **Strict Server-Side Access Control (Req 3 - Zero BOLA / IDOR):**
   * Stored documents are strictly walled behind a FastAPI streaming proxy (`StreamingResponse`).
   * No direct disk links or presigned URLs. Access rights (`is_active` permission check) are evaluated on every single byte request directly from database state.
3. **Instant Revocation (Req 4):**
   * Revocation takes effect in 0 milliseconds. Once an owner revokes a grant, subsequent download attempts fail immediately with HTTP 403 Forbidden.
4. **Binary Content & Magic-Byte Validation (Req 5):**
   * Prevents extension spoofing (e.g. `malware.exe` renamed to `doc.pdf`).
   * Validates header magic bytes (`%PDF-`, `PK\x03\x04`, `\x89PNG`) before writing to storage.
5. **Cryptographically Tamper-Evident Audit Log (Req 6):**
   * Every action (`DOCUMENT_UPLOAD`, `PERMISSION_GRANT`, `PERMISSION_REVOKE`, `ACCESS_DENIED`, `DOCUMENT_DOWNLOAD`) forms an immutable hash-chained block.
   * Current hash formula: `SHA-256(previous_hash + id + uuid + user_id + document_id + action + metadata)`.
   * Any tampering via manual SQL updates breaks hash chaining and is detected by `/api/audit/verify`.

---

## 🧪 Adversarial Test Suite

The test suite tests the application against adversarial bypass attempts:
* `test_10_adversarial_security_suite`: Verifies multi-user isolation, upload inspection, permission propagation, download proxying, instant revocation, and audit hash-chain integrity.
* `test_judge_removes_auth_check_fails`: Verifies that if an evaluator removes or bypasses authorization checks in routes, tests immediately fail.

To run tests locally:
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: .\venv\Scripts\activate
pip install -r requirements.txt
python -m pytest tests/ -v
```

---

## 🔑 Preset Test Credentials

| Role | Username / Email | Password | Allowed Capabilities |
| :--- | :--- | :--- | :--- |
| **Admin** | `admin@trustvault.io` | `AdminPass2026!` | Global supervisory view, full chained audit log verification |
| **Owner** | `owner@trustvault.io` | `OwnerPass2026!` | Document upload, grant permissions, revoke permissions |
| **Viewer** | `viewer@trustvault.io` | `ViewerPass2026!` | Read & stream permitted documents only |
|

---

## 🚀 Clean-Clone Setup & Run Instructions

### Prerequisites
* Python 3.11+
* Node.js 18+ and npm
* Git

### 1. Clone the Repository
```bash
git clone https://github.com/Likhitha1004/TrustVault-Instant-Revoke-Document-Vault.git
cd TrustVault-Instant-Revoke-Document-Vault
```

### 2. Backend Setup
```bash
cd backend
python -m venv venv

# Linux / macOS
source venv/bin/activate
# Windows
.\venv\Scripts\activate

pip install -r requirements.txt

# Run all 32 unit and security tests
python -m pytest tests/ -v

# Run the local backend server (optional)
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

### 3. Frontend Setup
```bash
cd ../frontend
npm install

# Run TypeScript checks and production build
npm run build

# Start local Vite development server
npm run dev
```
Open your browser at `http://localhost:5173`. The development server automatically proxies `/api` requests to `http://127.0.0.1:8000`.

---

## 🧪 Comprehensive Verification Commands

```bash
# 1. Run all backend tests
cd backend && venv/Scripts/python.exe -m pytest tests -v

# 2. Run frontend production build
cd ../frontend && npm run build

# 3. Run full production smoke test suite against live URL
cd .. && python scripts/run_production_audit_suite.py
```

---

## 📹 5-Minute Demo Video Walkthrough Outline

The demo video showcases the end-to-end user journeys and security validations:
1. **0:00 - 0:45**: Architectural Introduction (Zero-Trust Model, Vercel Serverless, Supabase PostgreSQL, S3 Storage).
2. **0:45 - 1:45**: Document Owner Experience (Registration, 10MB file upload, magic-byte check, category tagging, search & filter).
3. **1:45 - 2:45**: Granular Sharing & Instant Revocation (Granting Read/Edit to Viewer, verifying Viewer access, instant revocation, verifying immediate HTTP 404).
4. **2:45 - 3:45**: Administrative Oversight & SHA-256 Audit Trail (Genesis block, cryptographic hash chaining, real-time verification).
5. **3:45 - 5:00**: Adversarial Security Suite & Code Walkthrough (Zero BOLA, DB advisory locking, pytest execution).

---

## 📄 Deliverables Index
* **Threat Model & Defense:** [`THREATS.md`](THREATS.md)
* **AI Interaction & Corrections Journal:** [`PROMPTS.md`](PROMPTS.md)
* **REST API Specification:** [`API.md`](API.md)
* **System Architecture:** [`ARCHITECTURE.md`](ARCHITECTURE.md)
* **Compliance Audit Report:** [`SNOVASYS_REQUIREMENTS_COMPLIANCE_REPORT.md`](SNOVASYS_REQUIREMENTS_COMPLIANCE_REPORT.md)

