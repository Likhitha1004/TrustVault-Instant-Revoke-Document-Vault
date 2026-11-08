# TRUSTVAULT FREE-TIER LIMITATIONS & QUOTA SAFETY REPORT

**Date:** 2026-11-02  
**Target Monthly Budget:** Strictly ₹0/month ($0.00 USD)  
**Cost Incurred:** ₹0 (Zero payment methods configured)  

---

## 1. Zero-Cost Provider Quota Matrix

| Provider | Service Component | Free Quota Allowance | TrustVault Enforced Limit | Safety Margin | Zero-Overage Fail-Safe |
|---|---|---|---|---|---|
| **Vercel** | Frontend Hosting & Edge | 100 GB Bandwidth / month | ~0.5 GB / month | **>99%** | Vercel pauses serving or serves edge 429 when cap reached; zero auto-billing. |
| **Oracle Cloud (OCI)** | Compute VM (Ampere A1) | 3,000 OCPU hours / 18,000 GB hours / mo | 2 OCPUs, 12 GB RAM | **100% Free** | Stays within Always Free allowance; zero auto-billing without manual PAYG upgrade. |
| **Render (Rollback)** | Backend Web Service | 750 free instance hours / month | 720 hours / month (1 service) | **100% Free** | Render suspends idle web services after 15 min; cold starts take ~30-50s. |
| **Supabase**| PostgreSQL Database | 500 MB database storage | ~15 MB allocated for schemas/indexes | **>96%** | Supabase marks database read-only on quota exhaustion; never charges credit card. |
| **Supabase**| Supabase File Storage | 1 GB file storage | 10 MB per-file upload cap | **100+ Docs** | File uploads restricted to max 10MB via backend validator. |

---

## 2. Oracle Cloud Infrastructure (OCI) Always Free Policies

### Ampere A1 Architecture Limits
- **CPU & RAM**: Up to 4 OCPUs and 24 GB RAM (or 2 OCPUs and 12 GB RAM target for safe concurrency).
- **Storage**: Up to 200 GB total Block Volume across Always Free instances (Boot Volume configured at 50 GB).
- **Outbound Data Transfer**: 10 TB free per month.
- **Cost**: Strictly ₹0.00 / month.

### Oracle Idle Instance Reclamation Policy
- **Policy**: OCI monitors Always Free compute instances. An instance is considered idle if over a 7-day period:
  - CPU utilization is less than 20% for 95% of the time,
  - Network utilization is less than 20%, and
  - Memory utilization is less than 20%.
- **Action**: Oracle may reclaim (stop) idle compute instances after prior email notification.
- **Mitigation**: Production TrustVault traffic, routine health checks (`/healthz`, `/readyz`), and background workers ensure active resource utilization without artificial looping scripts.

---

## 3. Cold-Start and Availability Policies

### Render Free Instance Sleep
- **Behavior:** The free web service goes to sleep after 15 minutes of inactivity.
- **Wakeup Latency:** The initial request after sleep triggers an instance spin-up requiring approximately 30 to 50 seconds.
- **Frontend Mitigation:** The React frontend displays an active loading skeleton and live system status indicator (`#system-status-indicator`) so users understand cold starts without panicking or refreshing repeatedly.

### Supabase Inactivity Pause
- **Behavior:** Free-tier Supabase projects pause after 7 consecutive days of complete database inactivity.
- **Restoration:** Project can be restored via the Supabase web dashboard in under 2 minutes with zero data loss.
- **Prevention:** Regular health checks or occasional activity keep the database connection pool warm.

---

## 3. Safe Failure & Error 402 Mitigation

- **No Auto-Upgrades:** All provider accounts are kept on pure Free/Hobby tiers without credit card attachments.
- **Fail-Closed on Quota:** If storage or database capacity is reached, the backend safely returns `HTTP 413 Payload Too Large` or `HTTP 503 Service Unavailable` with user-friendly explanations, rather than attempting paid overage provisioning.
