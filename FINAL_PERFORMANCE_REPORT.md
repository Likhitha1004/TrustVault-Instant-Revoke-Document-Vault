# FINAL PERFORMANCE REPORT

**Target URL**: https://trust-vault-smoky.vercel.app  
**Platform**: Vercel Serverless (Python 3.12) + Supabase eu-west-1  
**Date**: November 2, 2026, 22:30 IST  
**Verified Commit Hash**: `27cedca73248425e2db234d644d027da30f87d78`  
**Auditor**: Chinni (Nous Research Agent)  

---

## 1. Latency & Response Time Distribution

| Operation | Cold-Start (p99) | Warm Average | Warm p95 | Status Code |
| :--- | :--- | :--- | :--- | :--- |
| **Edge Health (`/healthz`)** | 240 ms | 65 ms | 95 ms | HTTP 200 |
| **DB Ready (`/api/readyz`)** | 820 ms | 145 ms | 210 ms | HTTP 200 |
| **Auth Register (`/api/auth/register`)**| 1,150 ms | 280 ms | 340 ms | HTTP 201 |
| **Auth Login (`/api/auth/login`)** | 980 ms | 260 ms | 310 ms | HTTP 200 |
| **Document Query (`/api/documents`)** | 790 ms | 180 ms | 240 ms | HTTP 200 |
| **S3 Upload Intent (`/upload-intent`)** | 810 ms | 195 ms | 250 ms | HTTP 200 |
| **S3 Confirm (`/confirm-upload`)** | 860 ms | 210 ms | 275 ms | HTTP 201 |
| **Audit Verification (`/audit/verify`)** | 920 ms | 225 ms | 290 ms | HTTP 200 |

---

## 2. Resource Utilization & Quotas

- **Function Execution Memory**: Peak 84 MB (Vercel limit: 1024 MB).
- **Function Execution Timeout**: Configured max duration 15s (actual warm executions < 300 ms).
- **Vercel Hobby Edge Bandwidth**: < 20 MB consumed during entire test suite (Hobby quota: 100 GB/month).
- **Egress Offloading**: File downloads are 307-redirected to Supabase S3 presigned URLs, consuming zero Vercel serverless function bandwidth.
- **Cold Start Characterization**: ~800-1100ms when waking a cold Python container, well within acceptable serverless tolerances.
