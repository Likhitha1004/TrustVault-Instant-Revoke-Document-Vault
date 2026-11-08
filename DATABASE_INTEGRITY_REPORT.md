# TRUSTVAULT DATABASE & TRANSACTION INTEGRITY REPORT

## 1. Schema Constraints & ACID Compliance
- **Foreign Keys:** `Document.owner_id -> User.id` (ON DELETE CASCADE), `DocumentPermission.grantee_id -> User.id`.
- **Unique Constraints:** `User.username`, `User.email`, `DocumentPermission(document_id, grantee_id)`.
- **Transaction Rollback:** Failure during multi-step document deletion rolls back metadata changes completely.
- **Data Persistence:** Reboots retain all committed rows; tables created via non-destructive `create_all`.