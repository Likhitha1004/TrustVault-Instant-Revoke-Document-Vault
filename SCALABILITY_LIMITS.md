# TRUSTVAULT SCALABILITY LIMITS & CAPACITY BOTTLENECKS

## 1. Free-Tier Capacity Analysis
| Bottleneck Component | Safe Operating Limit | Exceedance Behavior | Zero-Cost Mitigation |
|---|---|---|---|
| **Render Web Service (Free)** | ~10-15 Concurrent Users | Request latency increases | Idle sleep after 15 min; frontend cold-start spinner |
| **Supabase PostgreSQL (Free)** | 500 MB Database Storage | Database becomes read-only | Document binaries stored in S3, not PostgreSQL |
| **Supabase S3 Storage (Free)** | 1 GB Document Storage | HTTP 413 / Storage full | 10MB per-document upload cap |
| **Vercel Bandwidth (Hobby)** | 100 GB / month | Edge bandwidth throttling | Static asset minification & gzip compression |