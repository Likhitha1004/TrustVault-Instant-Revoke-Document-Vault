# TrustVault Security Attack & Penetration Test Report

## 1. IDOR & Access Control Attacks
- **Attack Vector**: Viewer altering URL or request body to target another user's document ID (`/documents/{victim_doc_id}`).
- **Server Defense**: Live DB access check (`check_document_access`) runs on every operation. Returns HTTP 404/403.
- **Result**: PASS (0 unauthorized accesses).

## 2. Privilege Escalation Attacks
- **Attack Vector**: Viewer sending requests to `/api/audit/metrics` and `/api/audit/verify`.
- **Server Defense**: `require_role(UserRole.ADMIN)` dependency raises HTTP 403 Forbidden.
- **Result**: PASS.

## 3. Instant Permission Revocation Attack
- **Attack Vector**: Viewer attempting to download after owner clicks revoke.
- **Server Defense**: Authorization checked live at the moment bytes are requested from disk; revoked DB status blocks download immediately.
- **Result**: PASS.

## 4. File Path Traversal & Unsafe Upload Attacks
- **Attack Vector**: Filenames containing `../` or NULL bytes (`../../etc/passwd`).
- **Server Defense**: `os.path.basename` strips relative directories; strict MIME magic-byte verification blocks disguise files.
- **Result**: PASS.
