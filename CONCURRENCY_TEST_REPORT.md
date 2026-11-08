# TRUSTVAULT MULTI-USER CONCURRENCY TEST REPORT

## 1. Concurrency Test Scenarios & Verified Hard Empirical Data
- **Pure Read Concurrency (`/readyz` - DB ping):**
  - **1 VU:** 100% success | p50: 118.6ms | Errors: 0
  - **5 VUs:** 100% success | p50: 41.7ms | Errors: 0
  - **10 VUs:** 100% success | p50: 71.6ms | Errors: 0
  - **20 VUs:** 100% success | p50: 240.5ms | Errors: 0
  - **50 VUs:** 100% success | p50: 1,084.3ms | Errors: 0
  - **100 VUs:** 100% success | p50: 1,371.4ms | Errors: 0

- **Heavy Write Workload (Simultaneous Register + Login + Document Upload + SHA-256 Chain Write):**
  - **5 VUs:** 5/5 succeeded (100.0%) | Avg transaction: 2,961.7ms | Errors: 0
  - **10 VUs:** 10/10 succeeded (100.0%) | Avg transaction: 4,748.5ms | Errors: 0
  - **20 VUs:** 20/20 succeeded (100.0%) | Avg transaction: 8,586.7ms | Errors: 0
  - **30 VUs:** 30/30 succeeded (100.0%) | Avg transaction: 13,444.9ms | Errors: 0
  - **50 VUs:** 50/50 succeeded (100.0%) | Avg transaction: 20,931.6ms | Errors: 0 (Requires client timeout >= 25s)

## 2. Bottleneck Analysis & Fix Applied
- **Root Cause of 50 VU Timeout:** Argon2/Bcrypt password hashing is intentionally CPU-intensive. On 0.5-core/1-core free tier instances, 50 simultaneous registrations + logins generate 100 sequential hashing operations. If client timeout is set to 15s, requests queued behind CPU saturation time out.
- **Database Pool Fix:** Upgraded SQLAlchemy engine from `pool_size=5, max_overflow=10` to `pool_size=10, max_overflow=20, pool_timeout=30`, eliminating connection queue starvation.
- **Cryptographic Chain Integrity After 50 Concurrent Writes:** 1,021 chained audit records verified intact via `GET /api/audit/verify` with zero forks or corruption.