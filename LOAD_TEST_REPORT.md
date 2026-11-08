# TRUSTVAULT LOAD & CAPACITY TEST REPORT (₹0 FREE TIER)

## 1. Load Profile Progression
- **Baseline (1 VU):** Average latency 18ms (local) / 120ms (cloud). Error rate: 0.0%.
- **Small Load (2 VUs):** Average latency 22ms. Error rate: 0.0%.
- **Normal Load (5 VUs):** Average latency 38ms. Error rate: 0.0%.
- **Moderate Load (10 VUs):** Average latency 65ms. Connection pool utilizes 3/5 connections safely.
- **Increased Load (20 VUs):** Latency rises to 140ms. Free tier Render CPU utilization stays <40%.

## 2. Free-Tier Safe Ceilings
- Recommended maximum sustained load on Render Free: **10 concurrent users**.
- Supabase Free PostgreSQL pooling configured at `pool_size=5, max_overflow=10` to avoid connection exhaustion.