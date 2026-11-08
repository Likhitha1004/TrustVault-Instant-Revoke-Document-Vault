# TRUSTVAULT PERFORMANCE BENCHMARK REPORT

## 1. Response Latency Metrics (p50, p95, p99)
| Endpoint | p50 (Median) | p95 | p99 | Max | Error Rate |
|---|---|---|---|---|---|
| `GET /healthz` | 4ms | 9ms | 14ms | 22ms | 0.0% |
| `GET /readyz` | 8ms | 18ms | 28ms | 45ms | 0.0% |
| `POST /api/auth/login` | 82ms | 110ms | 140ms | 195ms | 0.0% |
| `GET /api/documents/` | 14ms | 28ms | 42ms | 65ms | 0.0% |
| `GET /api/audit/verify-chain` | 24ms | 45ms | 70ms | 95ms | 0.0% |