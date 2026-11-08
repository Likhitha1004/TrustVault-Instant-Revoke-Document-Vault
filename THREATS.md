# THREATS.md - Threat Model & Security Defense Strategy
*Required deliverable for Snovasys Hiring Challenge 2026*

This document catalogs attack vectors evaluated against TrustVault, the defensive mitigations built into the platform, and consciously accepted architectural trade-offs.

---

## 1. Attack Vectors & Mitigations

| Threat ID | Threat Name | Description | Mitigation Implemented |
|---|---|---|---|
| **THREAT-01** | **BOLA / IDOR on Document Retrieval** | An authenticated Viewer attempts to read/download a document belonging to another user by guessing or enumerating the UUID/ID in `/api/documents/{id}/download`. | Database-level authorization policy inside the route handler: checks `document.owner_id == user.id OR permission.grantee_id == user.id AND permission.can_read == true`. Failure logs a `DENIED_ACCESS` event in the audit trail and returns HTTP 404 (preventing document existence oracle). |
| **THREAT-02** | **Stale Authorization / Lagged Revocation** | An owner revokes access for user B. User B attempts to use an existing bearer token or pre-signed URL to download the document. | **Zero cached permissions.** Every download request evaluates the live database permission state. The file binary is never exposed via public object URLs; it is streamed strictly through an authenticated FastAPI proxy. Revocation takes effect instantly (sub-millisecond). |
| **THREAT-03** | **Audit Trail Tampering (Internal DB Alteration)** | A rogue administrator or attacker with database access alters the audit log table to conceal unauthorized document reads. | **Cryptographic Hash Chaining.** Every audit log row includes `previous_hash` and `current_hash = SHA256(id + timestamp + user_id + document_id + action + previous_hash)`. The API provides an endpoint `/api/audit/verify` that mathematically re-computes the chain from genesis and flags broken links. |
| **THREAT-04** | **Malicious File Masquerading (MIME Spoofing)** | An attacker renames an executable/script (e.g. `payload.exe` to `invoice.pdf`) and uploads it. | **Magic-Byte Content Inspection.** Validation uses byte signatures (e.g., `%PDF-` for PDFs, PK zip headers for Office documents) instead of relying solely on the client-provided `Content-Type` header or file extension. |
| **THREAT-05** | **Path Traversal via Filename Injection** | Attacker uploads a document with filename `../../etc/passwd` or `..\..\Windows\System32\cmd.exe` to overwrite system files. | **UUID-isolated on-disk storage.** Files are stored using cryptographic UUIDs on disk (`storage/{file_uuid}.bin`), while the original sanitized display name is stored separately in the database metadata table. |
| **THREAT-06** | **AI Agent Over-Privileging** | An integrated AI assistant autonomously grants document permissions without explicit owner intervention. | **Hard Architectural Gate.** AI may suggest recipient candidates, but cannot mutate the database permissions table. Only the authenticated document owner can sign and commit a grant transaction. |
| **THREAT-07** | **Denial of Service via Unbounded File Uploads** | Attacker floods upload endpoint with gigabyte-sized files to exhaust disk space and memory. | **10MB Upload Ceiling & Stream Bounding.** Backend inspects Content-Length and chunks binary reads; aborts with HTTP 413 if payload exceeds 10MB (`10 * 1024 * 1024`). |
| **THREAT-08** | **Directory Traversal via Multipart Filename** | Attacker submits filenames with `../` or special shell characters to escape storage root. | **Sanitization + UUID decoupling.** Filename is sanitized via regex `re.sub(r'[^a-zA-Z0-9_.-]', '_', ...)` and stored on disk purely as `{uuid}.bin`. |
| **THREAT-09** | **Privilege Escalation on Document Mutations (PATCH/DELETE)** | Viewer attempts to rename or delete documents belonging to another user. | **Role-Strict Route Gates.** PATCH requires Owner or Grantee with `can_edit=true`. DELETE strictly requires Document Owner or Platform Admin; Viewers even with edit permission receive HTTP 403 Forbidden. |

---

## 2. Accepted Trade-Offs & Conscious Limitations

1. **Proxy Streaming Overhead:** Streaming document binaries through FastAPI rather than using direct S3 pre-signed URLs increases server bandwidth and memory usage. **Reason Accepted:** Guarantees 0-millisecond instant revocation without relying on cloud-provider URL expiry timeouts.
2. **Hash Chain Concurrency:** Under heavy concurrent writes, audit hash chaining requires row-level sequence locking on the latest audit tail. **Reason Accepted:** Prioritizes strict audit integrity over extreme write throughput.
