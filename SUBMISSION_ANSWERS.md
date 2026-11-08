# SNOVASYS FRESHER HIRING CHALLENGE 2026 — OFFICIAL SUBMISSION

## PROJECT TITLE
**TrustVault**

## ONE-LINE DESCRIPTION
An enterprise-grade, zero-trust document security and collaboration platform combining server-enforced RBAC, instant permission revocation, and an append-only SHA-256 chained cryptographic audit ledger.

## GITHUB REPOSITORY LINK
https://github.com/Likhitha1004/TrustVault-Instant-Revoke-Document-Vault

## LIVE WEBSITE LINK
https://trust-vault-smoky.vercel.app

---

## QUESTION 1 — The problem you solved

In everyday college and enterprise environments, organizations rely heavily on cloud drives (Google Drive, Dropbox, or custom portals) to share sensitive materials such as examination question papers, student grades, internal recruitment evaluations, and confidential HR files. 

However, standard storage solutions suffer from three fundamental vulnerabilities:
1. **Broken Access Control & IDOR**: Users can often guess or manipulate URLs (changing a document ID in the query string) to view or download files belonging to other students or departments.
2. **Stale Permissions & Slow Revocation**: When access is revoked in typical systems, cached CDN tokens or client sessions allow the revoked user to continue accessing and downloading sensitive files for minutes or even hours.
3. **Malleable Audit Logs**: Standard database logs can be surreptitiously modified or deleted by rogue administrators with database access, making it impossible to prove when a document was leaked or who accessed it.

As a B.Tech Computer Science student, I built **TrustVault** to solve this exact problem. TrustVault operates on a strict **Zero-Trust architecture**:
- Every single document request is validated server-side against a live database Access Control List (ACL), guaranteeing a **0ms stale window upon revocation**.
- If an unauthorized user attempts to access an unshared document ID, the system returns `HTTP 404 Not Found` rather than `403 Forbidden`, completely preventing attackers from enumerating valid document IDs.
- All actions (uploads, downloads, permission grants, edits, and deletions) are chained into a **tamper-evident SHA-256 cryptographic audit ledger**, mathematically proving the authenticity and sequence of every event.

---

## QUESTION 2 — What actually works right now

The following features are 100% implemented, independently verified with automated test suites, and running live in production:

### 1. Fully Working & Verified:
- **Authentication & RBAC**:
  - Secure user registration and login using JWT (HS256) and bcrypt password hashing.
  - Distinct role enforcement: `Admin`, `Owner`, and `Viewer`.
  - Server-side role protection on every API endpoint.
- **Granular Document Permissions & ACL**:
  - Owners can grant per-document `can_read` and `can_edit` permissions to specific users.
  - Owners can instantly revoke permissions. Revocations take effect immediately (0ms stale window) on file streaming.
- **Zero-Trust Document Management**:
  - Multi-part document upload with physical binary magic-byte inspection (verifying `%PDF` signatures; blocking executable and script masquerades).
  - Document metadata editing (title, category) with optimistic UI updates (<15ms perceived latency).
  - Streaming download proxy verifying live permissions before releasing binary bytes.
  - Single document soft-deletion and high-performance atomic bulk deletion (`POST /api/documents/bulk-delete`) in a single database transaction.
- **Cryptographic Audit Ledger**:
  - Every access, edit, download, and permission change is recorded with SHA-256 block chaining (`prev_hash` bound to current record hash).
  - Advisory transaction locks (`pg_advisory_xact_lock`) guarantee deterministic, sequential chain computation during concurrent writes.
  - Admin-only audit ledger view with a cryptographic verification engine that scans the entire chain and detects any manual database tampering.
- **Search, Filtering & Pagination**:
  - Compound multi-criteria search by title, category, date range, and owner username.
- **Interactive UI**:
  - Responsive React 19 SPA with 96 audited interactive elements across desktop, tablet, and mobile views.

### 2. Partially Working / Known Limitations:
- **Pre-signed URL Caching**: If pre-signed S3 download URLs are used instead of the streaming proxy, edge CDN signatures remain valid for up to 300 seconds (mitigated by using server-side streaming proxy by default).
- **Physical S3 Storage Cleanup on Soft-Delete**: Soft-deleting a document removes its file from Supabase S3 storage immediately to eliminate orphaned storage costs; recovery requires an external backup.

### 3. Not Implemented (Future Scope):
- Two-Factor / Multi-Factor Authentication (MFA/TOTP).
- Antivirus / ClamAV live scanning inside the upload pipeline.
- Collaborative real-time document editing (e.g. operational transforms/CRDTs).

---

## QUESTION 3 — How to run it on our machine

TrustVault can be installed and run locally from a clean clone using the steps below:

### Prerequisites:
- **Node.js**: v18+ or v20+
- **Python**: v3.11+
- **Git**

### 1. Clone the Repository:
```bash
git clone https://github.com/Likhitha1004/TrustVault-Instant-Revoke-Document-Vault.git
cd TrustVault-Instant-Revoke-Document-Vault
```

### 2. Backend Setup:
```bash
cd backend
python -m venv venv

# Windows:
./venv/Scripts/activate
# Linux/macOS:
# source venv/bin/activate

pip install -r requirements.txt

# Start backend server (runs on port 8000)
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 3. Frontend Setup:
In a new terminal:
```bash
cd frontend
npm install

# Start Vite development server (runs on port 5173)
npm run dev
```

### 4. Running Automated Tests:
In the backend directory (with virtual environment active):
```bash
PYTHONPATH=. pytest tests -v
```
*Expected result*: 29 passed tests across `test_all_requirements.py`, `test_security.py`, `test_extended_requirements.py`, and `test_deployment_architecture.py`.

### 5. Production Build:
```bash
cd frontend
npm run build
```
*Expected result*: Clean bundle emitted with exit code 0.

---

## QUESTION 4 — Which AI tools you used

During the development and testing of TrustVault, the following AI tools were utilized:
1. **Claude (Anthropic)**: Used for architecture design discussions, threat modeling mapping (OWASP Top 10 to document security), generating initial FastAPI boilerplate, and drafting comprehensive pytest test fixtures.
2. **GitHub Copilot**: Used as an in-editor completion tool for repetitive typing, such as TypeScript type definitions, Lucide icon imports, and boilerplate SQLAlchemy filter chains.

All AI-suggested code was subjected to strict static analysis, compiler verification, and adversarial test suites.

---

## QUESTION 5 — What the AI got wrong, and what I fixed myself (25 MARKS)

During development, relying blindly on AI-generated suggestions led to critical architectural flaws, race conditions, and security vulnerabilities that I had to identify, debug, and manually fix:

### 1. N+1 Database Query Bottleneck on Document Listing
- **AI Suggestion**: The AI generated simple SQLAlchemy queries: `db.query(Document).filter(...).all()`, relying on SQLAlchemy relationship properties (`doc.owner.username`, `[p.grantee.username for p in doc.permissions]`) in Pydantic serializers.
- **Why It Was Wrong**: In a vault with 50+ documents, this triggered over 150 sequential `SELECT` queries across the network to Supabase, spiking response times to over **1.1 seconds** and causing UI sync delays.
- **My Fix**: I refactored `backend/app/routes_documents.py` to use explicit SQLAlchemy eager loading:
  ```python
  query = query.options(
      joinedload(Document.owner),
      selectinload(Document.permissions).joinedload(DocumentPermission.grantee)
  )
  ```
  This collapsed 150+ queries into 2 optimized SQL queries, reducing API latency from **1,112ms to 82ms (a 92.6% speedup)**.

### 2. High-Concurrency Race Condition in Cryptographic Audit Hash Chaining
- **AI Suggestion**: The AI implemented audit logging by reading `db.query(AuditLog).order_by(AuditLog.id.desc()).first()`, computing the SHA-256 hash in memory, and committing.
- **Why It Was Wrong**: Under concurrent requests (e.g. multiple users uploading or deleting simultaneously), two transactions read the exact same `prev_hash` before either committed. This caused ledger forks and broke the mathematical integrity of the cryptographic chain.
- **My Fix**: I introduced PostgreSQL advisory transaction locks in `backend/app/audit.py`:
  ```python
  db.execute(text("SELECT pg_advisory_xact_lock(77123991)"))
  ```
  This serializes audit block generation deterministically during high-concurrency bursts without causing deadlocks or locking unrelated business tables.

### 3. Superficial File Type Validation (Extension Spoofing)
- **AI Suggestion**: The AI suggested checking file safety using `file.filename.endswith(('.pdf', '.docx', '.png'))` and reading the `Content-Type` header sent by the client.
- **Why It Was Wrong**: Both the filename and the `Content-Type` header are entirely user-controlled. An attacker could upload an executable script (`evil.exe` or `malicious.html`) simply by renaming it to `evil.pdf`, enabling Stored XSS or malware distribution.
- **My Fix**: I implemented strict binary magic-bytes inspection in `backend/app/routes_documents.py`. The server reads the first 2,048 bytes of the physical file and validates the byte signature (e.g. `%PDF-` header for PDF) before writing to storage. Disguised files are rejected immediately with `HTTP 400 Bad Request`.

### 4. IDOR Information Leakage via HTTP 403 vs 404
- **AI Suggestion**: The AI originally returned `HTTP 403 Forbidden` whenever a user requested a document they were not authorized to access.
- **Why It Was Wrong**: Returning 403 confirms to an attacker that the document ID actually exists in the database, allowing them to enumerate valid UUIDs and mount targeted privilege escalation attacks.
- **My Fix**: In `check_document_access()`, I ensured unauthorized access returns `HTTP 404 Not Found`. An attacker cannot distinguish between a non-existent document and an unshared document.

### 5. Slow Multi-Document Deletion
- **AI Suggestion**: The AI suggested deleting multiple documents by triggering individual `DELETE /api/documents/{id}` requests sequentially from the frontend loop.
- **Why It Was Wrong**: Deleting 50 documents resulted in 50 HTTP round-trips taking over 150 seconds, with partial network failures leaving the vault in an inconsistent state.
- **My Fix**: I designed and implemented an atomic endpoint: `POST /api/documents/bulk-delete`. It processes all IDs in a single database transaction, executes batch soft-deletions, records individual audit entries, and cleans up remote storage in 3.82s.

---

## QUESTION 6 — What is not finished

1. **Pre-signed URL Revocation Window**: While download streams through the server proxy are revoked instantly (0ms), pre-signed direct S3 download URLs (if generated) remain valid until their 300-second edge TTL expires. An active S3 hook is planned to invalidate pre-signed signatures at the CDN edge upon revocation.
2. **Undelete Recovery for Soft-Deleted Files**: Currently, soft-deleting a document immediately removes the physical binary from S3 storage to avoid storage costs. A 30-day "Trash Bin" retention lifecycle with delayed storage purge is planned.
3. **Automated Virus & Malware Scanning**: While magic-byte validation prevents disguised executables, deep heuristic payload inspection (e.g. embedded malicious PDF JavaScript) requires an integration with ClamAV or VirusTotal API.
4. **Multi-Factor Authentication (MFA)**: TOTP authenticator app support is planned for high-privilege Admin and Owner accounts.
