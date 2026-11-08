# TrustVault Architecture & Threat Defense Model

TrustVault is a zero-trust enterprise document sharing repository featuring live database-enforced authorization and an immutable, SHA-256 chained cryptographic audit ledger.

---

## 1. System Overview & Technology Stack

* **Frontend**: React 19 + TypeScript + Vite + Tailwind CSS + Lucide Icons.
* **Backend API**: Python 3.11 + FastAPI + Pydantic v2 + SQLAlchemy 2.0.
* **Database**: SQLite (local development / testing) / PostgreSQL (production Render deployment).
* **Storage Engine**: Content-addressable UUID binary isolation on disk (`storage/{file_uuid}.bin`).
* **Cryptographic Engine**: SHA-256 message digests for both document payloads and audit block linking.

```
+-----------------------------------------------------------------------+
|                         TrustVault React SPA                          |
|         (Enterprise Dark Theme, Role Switcher, Modals, Filters)       |
+-----------------------------------------------------------------------+
                                   |
                         HTTP / REST API (JWT)
                                   v
+-----------------------------------------------------------------------+
|                         FastAPI Core Engine                           |
|  +--------------------+  +-------------------+  +-------------------+ |
|  |   Authentication   |  |     Documents     |  |   Chained Audit   | |
|  |  (Argon2 / JWT)    |  | (Proxy Streaming) |  | (SHA-256 Linked)  | |
|  +--------------------+  +-------------------+  +-------------------+ |
+-----------------------------------------------------------------------+
            |                                  |
            v                                  v
+-----------------------+          +-----------------------+
|  Relational Database  |          |   Isolated Storage    |
| (Users, Permissions)  |          | (UUID Binary Storage) |
+-----------------------+          +-----------------------+
```

---

## 2. Zero-Trust Access Control Matrix

Authorization is re-evaluated server-side on **every single request**. Frontend roles or client-side cached permissions are never trusted.

| Role | Upload Docs | View Owned Docs | View Shared Docs | Edit Metadata (Owned) | Edit Metadata (Shared) | Download Binary | Delete Document | Manage Grants | View Full Audit | View Metrics |
|---|---|---|---|---|---|---|---|---|---|---|
| **Admin** | Yes | Yes | Yes (Global) | Yes | Yes | Yes | Yes | Yes | Yes | Yes |
| **Owner** | Yes | Yes | No (Only if shared) | Yes | No | Yes | Yes | Yes | Yes (Owned) | No |
| **Viewer (Read-only)** | No | N/A | Yes | No | No | Yes | No | No | No | No |
| **Viewer (with Edit)** | No | N/A | Yes | No | Yes (`can_edit`) | Yes | No | No | No | No |
| **Unauthenticated** | No | No | No | No | No | No | No | No | No | No |

---

## 3. Cryptographic Audit Chain Specification

Every mutation or sensitive access event triggers an append-only transaction in the `audit_logs` table.

### Hash Link Formula
```
current_hash = SHA-256(
    id +
    timestamp_utc +
    user_id +
    document_id +
    action +
    metadata_json +
    previous_hash
)
```

1. **Genesis Block**: The initial system event references `previous_hash = "0000000000000000000000000000000000000000000000000000000000000000"`.
2. **Sequential Integrity**: Row `N` strictly binds the digest of Row `N-1`.
3. **Verification**: Any tampering or direct SQL modification of historical records (`UPDATE audit_logs SET ...`) breaks the downstream signature chain, immediately flagged by `GET /api/audit/verify`.

---

## 4. Reverse Streaming Proxy vs Pre-Signed URLs

* Traditional object stores issue pre-signed URLs with expirations (e.g., 5-60 minutes).
* If an Owner revokes a Viewer's permission, pre-signed URLs remain valid until expiration, violating zero-trust guarantees.
* **TrustVault Solution**: All document binary streams pass through `FastAPI.responses.StreamingResponse`. The route handler checks current database grant status before emitting bytes. Revocation takes effect in sub-millisecond real time.
