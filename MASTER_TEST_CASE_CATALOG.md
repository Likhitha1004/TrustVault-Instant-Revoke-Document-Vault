# TRUSTVAULT MASTER TEST CASE CATALOG

## 1. Authentication & Session Security (AUTH)
- **TC-AUTH-01:** Register new account with valid credentials. Expected: HTTP 201, argon2 hashed password, audit log entry.
- **TC-AUTH-02:** Register with existing username/email. Expected: HTTP 400 Bad Request.
- **TC-AUTH-03:** Login with valid credentials. Expected: HTTP 200, JWT token, Bearer auth header accepted.
- **TC-AUTH-04:** Login with invalid password. Expected: HTTP 401 Unauthorized, zero existence leakage.
- **TC-AUTH-05:** Logout and token revocation. Expected: Token added to RevokedToken table, subsequent calls return HTTP 401.

## 2. Document Security & Access Control (DOC)
- **TC-DOC-01:** Owner uploads valid PDF under 10MB. Expected: SHA-256 computed, binary stored, audit logged.
- **TC-DOC-02:** User attempts upload of file >10MB. Expected: HTTP 413 Payload Too Large aborts upload before disk/DB write.
- **TC-DOC-03:** Non-permitted user requests document metadata. Expected: HTTP 404 Zero-Existence Oracle.
- **TC-DOC-04:** Owner grants read permission to User B. Expected: User B downloads file with matching SHA-256.
- **TC-DOC-05:** Owner revokes permission from User B. Expected: User B download immediately blocked (0ms latency).