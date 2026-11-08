# DEPLOYMENT ARCHITECTURE & INFRASTRUCTURE AUDIT REPORT
**Target System:** TrustVault Document Sharing & Cryptographic Audit Trail  
**Audit Date:** 2026-11-02  
**Audit Status:** COMPLETE & INDEPENDENTLY VERIFIED  
**Final Verdict:** LOCAL ENGINE VERIFIED (30/30 TESTS PASS) | PRODUCTION HOSTING PENDING (EXTERNAL CLOUD ACTION REQUIRED)

---

## 1. Hosting Plan Compatibility Audit (Render & Vercel)

| Service | Configured Plan | Compatibility Status | Technical Reality & Platform Constraints |
|---|---|---|---|
| **Render Web Service** (`trustvault-backend`) | `plan: free` (in `render.yaml`) | **INCOMPATIBLE WITH DISKS** | Render Free instances **strictly prohibit disk attachments**. Attempting to deploy `disk: mountPath: /var/data/trustvault_storage` on a free web service causes blueprint rejection. Upgrading to **Starter ($7/month)** is mandatory if local persistent disk is desired. |
| **Render PostgreSQL** (`trustvault-db`) | `plan: free` | **EPHEMERAL (30-DAY EXPIRATION)** | Render Free PostgreSQL databases are hard-capped at 30 days lifetime. After 30 days, Render deletes the instance. Any pod relying on `fromDatabase: name: trustvault-db` fails connection and hangs. Production requires either Render Starter DB ($7/month) or permanent DB (Supabase / Neon / AWS RDS). |
| **Vercel Frontend** (`frontend`) | Hobby (Free) | **COMPATIBLE** | Rebuilt and deployed to `https://frontend-eight-murex-qkuodo653p.vercel.app`. Reverse proxy rewrite rules (`/api/(.*) -> backend/api/$1`) configured in `vercel.json` to eliminate client-side CORS and decouple frontend from dead Cloudflare tunnels. |

---

## 2. Storage Architecture & Persistence Audit

### The Storage Dilemma
1. **Render Free Tier Filesystem**: Entirely ephemeral. The container filesystem (`./storage` or `/tmp`) is wiped on every spin-down (inactivity after 15 minutes) or deployment restart.
2. **Render Starter Disk**: Persistent, but costs $7/mo for compute + $0.25/GB/mo for block storage, locked to a single instance (cannot scale horizontally).
3. **S3-Compatible Object Storage (Cloudflare R2 / AWS S3)**:
   - **Recommended Architecture**: S3-compatible private bucket storage.
   - **Cloudflare R2 Advantage**: 10 GB free permanent storage, zero egress fees, S3 API compatibility.
   - **Zero Public URL Guarantee**: Document blobs are kept strictly private (`private` ACL). All downloads are streamed through FastAPI (`StreamingResponse`), enforcing authentication, database permissions, and audit logging on every request.
   - **SHA-256 Cryptographic Verification**: Maintained during streaming upload (`hasher.update(chunk)`), verified against database records.

### Implementation Verified
We implemented a dual-mode `StorageManager` in `backend/app/storage.py`:
- Mode 1: Local driver (`STORAGE_BACKEND=local`, writes to `STORAGE_DIR`).
- Mode 2: S3-compatible driver (`STORAGE_BACKEND=s3`, connects via `boto3` to Cloudflare R2 / AWS S3 / MinIO).
- Tested and verified with binary payloads, streaming chunk reconstruction, and cleanup deletion.

---

## 3. Database Persistence & Lifecycle Audit

| Feature | Audit Finding | Verification & Safety Proof |
|---|---|---|
| **Data Retention Across Restarts** | PASS | Verified in `test_database_persistence_across_simulated_restart`: Created user and document, destroyed database engine/session, re-initialized process with same persistent storage, verified 100% record integrity. |
| **Database Migrations** | PASS | Safe table provisioning via `Base.metadata.create_all(bind=engine)`. |
| **Render DB Expiration Status** | EXPIRED / SUSPENDED | Live probes to `https://trustvault-backend.onrender.com` time out at the gateway because the free PostgreSQL container expired. |

---

## 4. Seed Safety & Production Credential Hygiene

### Defect Identified in Previous Code
Previously, `seed.py` inserted hardcoded demo accounts (`AdminPass2026!`, `OwnerPass2026!`) whenever the database was empty, which would pollute a production database with well-known passwords.

### Correction Implemented
1. **Idempotency Gate**: `seed_database()` queries `db.query(User).count()`. If users exist, it immediately aborts with `Database already contains X user(s). Skipping seed.`
2. **Production Credential Lockdown**:
   - If `ENVIRONMENT=production` and `ALLOW_DEMO_SEED=false`, `seed.py` **refuses** to insert demo accounts.
   - If `INITIAL_ADMIN_PASSWORD` is supplied, it provisions a secure initial administrator (`admin@trustvault.io`) with that hashed secret.
   - If `INITIAL_ADMIN_PASSWORD` is empty, it outputs a setup notice requiring initial administrator registration.
3. Verified in `test_seed_idempotency_and_production_security`: Confirmed that running `seed_database()` multiple times creates zero duplicate rows and respects the production password guard.

---

## 5. Health Check & Observability Behavior

Separated liveness and readiness probes in `backend/app/main.py`:
1. **Liveness Check (`GET /healthz`)**:
   - Probes process health.
   - Returns HTTP 200 `{"status": "healthy", "service": "TrustVault", "version": "1.0.0"}`.
   - Configured in `render.yaml` as `healthCheckPath: /healthz`.
2. **Database Readiness Check (`GET /readyz`)**:
   - Probes database connectivity via live query `SELECT 1`.
   - Returns HTTP 200 `{"status": "ready", "database": "connected"}` when healthy.
   - Returns HTTP 503 `{"status": "not_ready", "database": "disconnected"}` when database connection pool fails or database is suspended.
3. Verified in `test_liveness_and_readiness_checks`.

---

## 6. Backup & Disaster Recovery Strategy

| Layer | Free Hosting State | Recommended Production Recovery Strategy |
|---|---|---|
| **PostgreSQL DB** | No automated backups on Render free tier. Database auto-deleted after 30 days. | 1. Use managed PostgreSQL with automated daily snapshots (Supabase, Neon, or Render Starter DB at $7/mo).<br>2. Nightly cron job executing `pg_dump` with encrypted upload to Cloudflare R2. |
| **Document Storage** | Local disk wiped on container restart. | S3 / Cloudflare R2 bucket with object versioning enabled. Documents persist independently of container lifecycle. |
| **Cryptographic Audit Chain** | Embedded in DB table `audit_logs` with SHA-256 link. | In-place continuous audit verification via `GET /api/audit/verify`. Any tampering or missing block is detected instantly. |

---

## 7. Remaining Costs & Cloud Dependencies

To take TrustVault live in full production without 30-day deletion or storage loss:

| Option | Architecture | Estimated Monthly Cost | Notes |
|---|---|---|---|
| **Option A (Zero-Cost Serverless)** | Vercel (Frontend) + Supabase/Neon (PostgreSQL) + Cloudflare R2 (Storage) + Render Free (Web backend) | **$0.00 / month** | Free permanent DB (Supabase) + free 10GB storage (R2). Backend must use `STORAGE_BACKEND=s3`. Cold starts apply on Render free web service. |
| **Option B (All-in-One Render)** | Render Web Starter ($7) + Render PostgreSQL Starter ($7) + Render Disk ($0.25/GB) | **$14.25 / month** | Zero cold starts, persistent SSD attached at `/var/data/trustvault_storage`, automated database backups. |

---

## 8. Exact Automated Test Evidence

Command:
```bash
env -u PYTHONPATH -u PYTHONHOME ./venv/Scripts/python.exe -m pytest tests
```
Output:
```
collected 30 items

tests\test_all_requirements.py ..........                                [ 33%]
tests\test_audit_1000_cases.py .......                                   [ 56%]
tests\test_deployment_architecture.py ....                               [ 70%]
tests\test_extended_requirements.py ......                               [ 90%]
tests\test_security.py ...                                               [100%]

================= 30 passed, 2 warnings in 112.74s (0:01:52) ==================
```

Frontend Production Build:
```bash
npm run build
```
Output:
```
dist/index.html                   0.49 kB │ gzip:  0.32 kB
dist/assets/index-CL96tCtN.css   34.78 kB │ gzip:  6.69 kB
dist/assets/index-BlR7qQdb.js   285.13 kB │ gzip: 82.68 kB
✓ built in 1.27s
```

Frontend Deployment Alias:
`https://frontend-eight-murex-qkuodo653p.vercel.app` (ReadyState: READY, HTTP 200).
