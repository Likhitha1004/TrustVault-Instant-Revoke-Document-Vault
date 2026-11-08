# TrustVault — Oracle Cloud Always Free Migration Plan & Execution Matrix

## 1. Executive Summary & Architecture Lock
- **Application**: TrustVault (Secure document sharing with tamper-evident cryptographic audit logs).
- **Target Backend Platform**: Oracle Cloud Infrastructure (OCI) Always Free VM.
- **Compute Target**: Ampere A1 Compute (`VM.Standard.A1.Flex`) with 2 OCPUs, 12 GB RAM, Ubuntu 22.04/24.04 ARM64.
- **Monthly Compute Allocation**: Within 1,500 OCPU-hours and 9,000 GB-hours/month allowance.
- **Cost**: Strictly ₹0.00 / month.
- **Frontend**: Existing Vercel Project (`https://trust-vault-smoky.vercel.app`) preserved.
- **Database**: Supabase PostgreSQL (`aws-0-eu-west-1.pooler.supabase.com:5432`) preserved.
- **Object Storage**: Supabase Storage private S3 bucket (`trustvault-docs`) preserved.
- **Reverse Proxy**: Caddy / Nginx with automated Let's Encrypt TLS.
- **Application Server**: FastAPI / Uvicorn managed via systemd.

---

## 2. Dependency & ARM64 Compatibility Audit Status
| Component / Package | Target Architecture | PyPI Status | Compatibility Result |
| :--- | :--- | :--- | :--- |
| `fastapi>=0.110.0` | Linux ARM64 | Pure Python wheel | PASS |
| `uvicorn[standard]` | Linux ARM64 | `uvloop` & `httptools` aarch64 wheels | PASS |
| `sqlalchemy>=2.0.28` | Linux ARM64 | Pure Python / C wheels | PASS |
| `pydantic-core` | Linux ARM64 | 38+ aarch64 native wheels | PASS |
| `psycopg2-binary>=2.9.9` | Linux ARM64 | 18+ aarch64 native wheels | PASS |
| `cryptography>=42.0.0` | Linux ARM64 | 23+ aarch64 native wheels | PASS |
| `bcrypt>=4.0.0` | Linux ARM64 | 25+ aarch64 native wheels | PASS |
| `boto3>=1.34.0` | Linux ARM64 | Pure Python wheel | PASS |

---

## 3. Account Discovery & Tenancy Verification
- **Host OCI CLI**: Not installed / absent.
- **`~/.oci/config`**: Absent.
- **Local Credentials Store**: 0 Oracle Cloud sessions or credentials.
- **Active Chrome Tab**: Loaded directly to `https://signup.cloud.oracle.com/` (Oracle Cloud Free Tier Signup).
- **Payment Verification Requirement**: Card verification hold (~$1 / ₹85-100 INR, immediately reversed). User approval gate active.

---

## 4. Phased Execution Roadmap
### Phase A — Tenancy & Compute Provisioning
1. Complete Oracle Cloud account signup & verify email / payment authorization.
2. Select Home Region (e.g. `ap-mumbai-1` or `ap-hyderabad-1`).
3. Provision Always Free `VM.Standard.A1.Flex` (2 OCPUs, 12 GB RAM, 50 GB Boot Volume, Ubuntu ARM64).
4. Configure VCN Security List: Ingress rules for TCP Port 22 (SSH), TCP Port 80 (HTTP), TCP Port 443 (HTTPS).
5. Bind Ephemeral / Free Reserved Public IPv4.

### Phase B — Host Hardening & Application Setup
1. Create non-root dedicated service user `trustvault`.
2. Disable SSH root and password login; enforce Ed25519 public key authentication.
3. Install Python 3.11+, Git, and Caddy.
4. Clone TrustVault repository (`git checkout f493c4d`).
5. Set up virtual environment and install dependencies (`pip install -r requirements.txt`).
6. Place production `.env` (Supabase DB URL, S3 Bucket credentials, JWT Secrets).

### Phase C — Systemd Service & Caddy Reverse Proxy
1. Create `/etc/systemd/system/trustvault.service`:
   - ExecStart: `/home/trustvault/TrustVault/backend/venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000 --workers 4`
   - Restart: `always`
2. Configure Caddy with automatic TLS / HTTPS reverse-proxy to `127.0.0.1:8000`.
3. Enable and start both services.

### Phase D — Production Smoke Tests & Health Checks
1. Probe `/healthz` (Process liveness).
2. Probe `/readyz` (Supabase PostgreSQL connectivity).
3. Validate S3 Storage read/write/delete against `trustvault-docs`.
4. Validate SHA-256 audit-chain integrity.
5. Execute multi-user concurrency testing (2, 5, 10, 20 users).

### Phase E — Vercel Cutover & Rollback Retention
1. Update Vercel environment variable `VITE_API_URL` to the new Oracle Cloud HTTPS endpoint.
2. Trigger production deployment on Vercel (`https://trust-vault-smoky.vercel.app`).
3. Verify browser network requests point to Oracle Cloud backend.
4. Keep Render service (`srv-dbk701u7bikc739bias0`) intact as rollback standby.
