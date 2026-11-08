# 11 — USER WORKFLOW AUDIT
## End-to-End Real-User Journeys Across All Roles

1. **Visitor Journey**: Access root -> Redirect to Login/Register -> Register as Viewer -> Successfully authenticate and receive JWT (**PASS**).
2. **Owner Journey**: Login -> Vault View -> Upload PDF document -> Metadata updated and verified in DB -> Share document with Viewer (Read Only) (**PASS**).
3. **Viewer Journey (Read Only)**: Login -> Vault View displays shared document -> Download streaming proxy succeeds -> Attempt PATCH metadata -> Returns HTTP 403 Forbidden (**PASS**).
4. **Viewer Journey (Edit Permission)**: Owner grants `can_edit=True` -> Viewer edits title -> Update persists -> Viewer attempts deletion -> Returns HTTP 403 Forbidden (**PASS**).
5. **Instant Revocation Journey**: Owner revokes Viewer permission -> Viewer immediately attempts download -> Returns HTTP 404 Not Found (0ms window) (**PASS**).
6. **Cross-Owner Isolation Journey**: Owner B attempts direct GET/PATCH/DELETE on Owner A's unshared document -> Returns HTTP 404 Not Found (**PASS**).
7. **Admin Governance Journey**: Login as Admin -> Audit tab -> Inspect activity stream -> Trigger cryptographic verification -> 100% chain integrity verified (**PASS**).
- **Workflow Status**: **PASS**.
