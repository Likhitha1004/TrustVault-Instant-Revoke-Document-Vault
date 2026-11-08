# TrustVault Failure Recovery & Fault-Tolerance Report

## Simulated Failure Scenarios
1. **Backend Server Unreachable**: Frontend displays clean banner with error notification rather than blank screen.
2. **Invalid / Malformed JSON**: API response parser handles non-JSON payload safely without unhandled exception.
3. **Interrupted Download**: Live file streaming does not corrupt database state or log bogus success entries.
4. **Duplicate Permission Grants**: Deduplication logic replaces prior permissions or updates existing rows safely.
