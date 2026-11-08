# FREE-TIER USAGE, QUOTAS & ZERO-COST GOVERNANCE (₹0/MONTH)

**Policy:** Hard ₹0.00 / Month Limit. Zero Paid Resources. Zero Auto-Upgrades.

---

## 1. Provider Quota Allocations & Safety Margins

| Provider | Metric / Resource | Free Tier Monthly Limit | TrustVault Target Usage | Safety Margin | Zero-Cost Action on Limit |
|---|---|---|---|---|---|
| **Vercel** | Bandwidth (Egress) | 100 GB / month | ~ 0.5 GB / month | **99.5% Headroom** | Pauses deployment; no overage billed |
| **Vercel** | Serverless Invocations | Free static/edge rewrites | Edge routing only | **Unlimited** | Built into hobby edge proxy |
| **Render** | Instance Hours | 750 hours / month | ~ 720 hours (1 instance) | **100% Covered** | Service sleeps if hours exceeded |
| **Render** | RAM Memory | 512 MB | ~ 95 MB idle / 160 MB peak | **68% Headroom** | Restart pod; no billing possible |
| **Supabase** | Database Disk Storage | 500 MB | ~ 15 MB (10,000+ docs) | **97% Headroom** | Read-only mode; zero automatic charge |
| **Supabase** | Egress Bandwidth | 2 GB / month | ~ 0.1 GB / month | **95% Headroom** | Rate limited; zero auto-upgrade |
| **Cloudflare R2**| Storage Volume | 10 GB / month | ~ 1.5 GB | **85% Headroom** | Uploads fail with 403; zero bill |
| **Cloudflare R2**| Class A Writes (Upload) | 1,000,000 requests / mo | ~ 5,000 / month | **99.5% Headroom** | Returns 429; no card charge |
| **Cloudflare R2**| Class B Reads (Download)| 10,000,000 requests / mo| ~ 20,000 / month | **99.8% Headroom** | Returns 429; no card charge |
| **Cloudflare R2**| Egress Bandwidth | **UNLIMITED / $0.00** | Any volume | **100% Free** | Cloudflare R2 has ZERO egress fees! |

---

## 2. Hard Cost Controls & Safeguards

### 1. Zero-Cost Architectural Safeguards
- **No Payment Methods Required**: None of the free tiers require a payment method to provision base resources.
- **Anti-Overfill File Upload Limiter**: Backend enforces a 10 MB per-document upload ceiling (`MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024`), preventing malicious storage exhaustion.
- **Strict Ephemeral Lock**: If `STORAGE_BACKEND=local` is detected in `production`, `StorageManager` throws an immediate `RuntimeError` unless `ALLOW_EPHEMERAL_STORAGE=true`. This guarantees zero reliance on expensive persistent disks.
- **Zero Egress Fee Storage**: Using Cloudflare R2 instead of AWS S3 eliminates the standard $0.09/GB AWS internet data transfer egress fee entirely.

### 2. Cold Start & Inactivity Lifecycle
- **Render Free Spin-Down**: Render automatically suspends web service containers after 15 minutes of zero inbound HTTP traffic.
- **Inbound Awakening**: The first HTTP request after sleep wakes the container within 30 to 50 seconds.
- **Frontend Readiness UX**: The Vercel frontend displays animated reconnection telemetry during cold starts rather than failing or timing out.

### 3. Monitoring & Quota Verification Procedures
1. **Supabase Disk Monitoring**:
   - Query current database size:
     ```sql
     SELECT pg_size_pretty(pg_database_size(current_database()));
     ```
2. **Cloudflare R2 Usage**:
   - Check Cloudflare Dashboard > R2 > `trustvault-prod-docs` > **Metrics** to monitor total stored bytes and Class A/B request volume.
3. **Render Compute Usage**:
   - Check Render Dashboard > Account Settings > **Resource Usage** to verify hours remain under 750 free hours.
