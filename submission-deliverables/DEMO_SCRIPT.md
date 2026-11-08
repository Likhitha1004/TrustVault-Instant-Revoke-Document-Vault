# TRUSTVAULT — 5-MINUTE HACKATHON DEMO WALKTHROUGH

## 0:00 - 0:45 | Introduction & Problem Statement
- **Speaker**: "Hello evaluators, my name is GVS Snuhith. Today I am presenting TrustVault, an enterprise-grade zero-trust document security platform. In typical systems like Google Drive, document sharing suffers from IDOR vulnerabilities, stale permissions upon revocation, and mutable audit logs. TrustVault solves this with server-enforced RBAC, instant 0ms revocation, and an append-only SHA-256 chained cryptographic audit ledger."

## 0:45 - 1:45 | Authentication & Multi-Role Architecture
- **Action**: Log in as `owner@trustvault.io`.
- **Display**: Show clean, responsive Vault dashboard. Highlight distinct categories, search filters, and file metadata.
- **Key Point**: Explain that all API calls carry signed JWTs, and roles (`Admin`, `Owner`, `Viewer`) are verified server-side on every request.

## 1:45 - 2:45 | Secure Upload & Magic Bytes Inspection
- **Action**: Upload a confidential document `Semester_Results.pdf`.
- **Behind the Scenes**: Show that the backend reads the first 2,048 bytes, verifying `%PDF-` magic bytes and rejecting executable files disguised with a `.pdf` extension.
- **Display**: Document appears in Vault instantly with optimistic UI updates (<15ms perceived latency).

## 2:45 - 3:45 | Granular Sharing & Instant Revocation (Zero Stale Window)
- **Action**: Share `Semester_Results.pdf` with `viewer@trustvault.io` with `can_read=True`.
- **Action**: Open incognito tab, log in as `viewer@trustvault.io`. Download succeeds via streaming proxy.
- **Action**: In the owner tab, immediately revoke viewer's permission.
- **Action**: In the viewer tab, attempt download again. Request fails instantly with HTTP 404 Not Found (0ms window).

## 3:45 - 4:30 | Cryptographic Audit Ledger & Tamper Detection
- **Action**: Log in as `admin@trustvault.io` and open the **Audit Logs** tab.
- **Display**: Show the chained log sequence. Each block contains `prev_hash` bound to `record_hash`.
- **Action**: Click **Verify Cryptographic Chain**. The engine scans the entire database ledger and returns: `All blocks valid (Tamper-free)`. Explain advisory locking preventing ledger forks.

## 4:30 - 5:00 | Conclusion & Architecture Defense
- **Speaker**: "TrustVault runs on FastAPI, React 19, Supabase PostgreSQL, and cloud S3 storage, backed by 29 automated tests covering 100% of adversarial boundaries with zero mocks. Thank you!"
