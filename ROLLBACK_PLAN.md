# TrustVault — Rollback & Disaster Recovery Plan

## 1. Baseline State & Preserved Artifacts
- **Vercel Frontend**: `https://trust-vault-smoky.vercel.app`
- **Render Backend**: `srv-dbk701u7bikc739bias0` (`https://trustvault-backend-blh0.onrender.com` / `https://trustvault-backend.onrender.com`)
- **Render Service Status**: Suspended: `not_suspended`, Active.
- **Supabase Database**: Host `aws-0-eu-west-1.pooler.supabase.com`, Port 5432.
- **Supabase S3 Bucket**: `trustvault-docs` (Region `eu-west-1`).
- **Verified Codebase Git Commit**: `f493c4d988876d80bc3764757e1e606b0222627e`.

---

## 2. Rollback Triggers
Rollback to Render will immediately occur if:
1. Oracle VM provisioning stalls or Always Free capacity is completely exhausted across all target Availability Domains.
2. Oracle backend fails `/readyz` Supabase DB connectivity checks.
3. S3 document upload/download hash verification fails on the Oracle instance.
4. Concurrency testing causes unrecoverable process faults.
5. Vercel frontend experiences CORS or mixed-content regressions post-cutover.

---

## 3. Immediate Rollback Execution Protocol (< 60 Seconds)
1. **Frontend Re-point**:
   - In Vercel Project settings or via Vercel CLI, restore `VITE_API_URL` to `https://trustvault-backend.onrender.com`.
   - Deploy immediate rollback build.
2. **Database Integrity Audit**:
   - Verify zero schema drift or dropped tables in Supabase PostgreSQL.
   - Run audit-log hash verification (`SELECT count(*) FROM audit_logs`).
3. **Render Health Verification**:
   - Verify Render web service returns HTTP 200 on `/healthz`.
4. **Render Retirement Policy**:
   - Render web service SHALL NOT be deleted, suspended, or modified until Oracle Cloud backend has operated with zero regressions for 7 consecutive days and explicit user sign-off is granted.
