# TrustVault REST API Documentation

Base URL: `/api` (Proxied in development to `http://127.0.0.1:8000/api`)

Authentication: Bearer JWT Token (`Authorization: Bearer <access_token>`)

---

## 1. Authentication Endpoints

### `POST /auth/register`
Creates a new user account.
* **Access**: Public
* **Request Body**:
  ```json
  {
    "username": "alice",
    "email": "alice@trustvault.io",
    "password": "SecurePassword2026!",
    "role": "owner"
  }
  ```
* **Response (200 OK)**:
  ```json
  {
    "id": "uuid-v4-string",
    "username": "alice",
    "email": "alice@trustvault.io",
    "role": "owner"
  }
  ```
* **Errors**: `400 Bad Request` (Email or username already exists, weak password).

---

### `POST /auth/login`
Authenticates a user and returns a signed JWT access token.
* **Access**: Public
* **Request Body**:
  ```json
  {
    "username_or_email": "owner@trustvault.io",
    "password": "OwnerPass2026!"
  }
  ```
* **Response (200 OK)**:
  ```json
  {
    "access_token": "eyJhbGciOiJIUzI1Ni...",
    "token_type": "bearer",
    "role": "owner",
    "user_id": "uuid-v4-string",
    "username": "alice_owner"
  }
  ```
* **Errors**: `401 Unauthorized` (`{"detail": "Invalid email or password"}`).

---

### `GET /auth/me`
Fetches the currently authenticated profile.
* **Access**: Authenticated (Admin, Owner, Viewer)
* **Headers**: `Authorization: Bearer <token>`
* **Response (200 OK)**:
  ```json
  {
    "id": "uuid-v4-string",
    "username": "alice_owner",
    "email": "owner@trustvault.io",
    "role": "owner"
  }
  ```
* **Errors**: `401 Unauthorized` (Missing or expired token).

---

### `POST /auth/logout`
Terminates the session and records a `USER_LOGOUT` audit log event.
* **Access**: Authenticated (Admin, Owner, Viewer)
* **Headers**: `Authorization: Bearer <token>`
* **Response (200 OK)**:
  ```json
  {
    "message": "Logged out successfully"
  }
  ```

---

## 2. Document Management Endpoints

### `POST /documents/upload`
Uploads a document with magic-byte validation and SHA-256 hash calculation.
* **Access**: Authenticated (Admin, Owner)
* **Content-Type**: `multipart/form-data`
* **Form Fields**:
  * `title`: string (1-255 characters)
  * `category`: string (`Legal`, `Financial`, `HR`, `Technical`, `Operations`)
  * `file`: Binary file upload (max 10MB, allowed types: PDF, DOCX, PNG, JPG)
* **Response (200 OK)**:
  ```json
  {
    "id": "uuid-v4-string",
    "title": "Vendor MSA Agreement",
    "category": "Legal",
    "file_name": "vendor_msa.pdf",
    "file_size": 204850,
    "file_hash_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "owner_id": "uuid-v4-string",
    "created_at": "2026-11-01T12:00:00Z"
  }
  ```
* **Errors**:
  * `400 Bad Request`: Disallowed file type, empty file, path traversal characters.
  * `413 Request Entity Too Large`: File exceeds 10MB ceiling.

---

### `GET /documents`
Lists documents accessible to the current user (owned documents or documents with active grant).
* **Access**: Authenticated (Admin, Owner, Viewer)
* **Query Parameters**:
  * `search`: string (case-insensitive title search)
  * `category`: string (filter by category)
  * `owner`: string (filter by owner username)
  * `date_from`: ISO timestamp (`2026-01-01T00:00:00Z`)
  * `date_to`: ISO timestamp (`2026-12-31T23:59:59Z`)
* **Response (200 OK)**:
  ```json
  [
    {
      "id": "uuid-v4-string",
      "title": "Vendor MSA Agreement",
      "category": "Legal",
      "file_name": "vendor_msa.pdf",
      "file_size": 204850,
      "file_hash_sha256": "e3b0c44...",
      "owner_id": "uuid-v4-string",
      "owner_username": "alice_owner",
      "created_at": "2026-11-01T12:00:00Z",
      "can_edit": true
    }
  ]
  ```

---

### `GET /documents/{document_id}`
Retrieves document metadata.
* **Access**: Authenticated (Owner, Grantee with Read/Edit, or Admin)
* **Response (200 OK)**: Document metadata object.
* **Errors**: `404 Not Found` (Does not exist or unauthorized - prevents existence oracle).

---

### `GET /documents/{document_id}/download`
Securely streams document binary directly through FastAPI proxy with zero pre-signed URL leakage.
* **Access**: Authenticated (Owner, Grantee with Read/Edit, or Admin)
* **Response (200 OK)**: Binary stream (`application/pdf`, etc.)
* **Audit Side Effect**: Records `DOC_DOWNLOAD` in chained audit log.
* **Errors**: `404 Not Found` (Denies unauthorized users or revoked grants).

---

### `PATCH /documents/{document_id}`
Updates document title or category.
* **Access**: Authenticated (Document Owner or Grantee with `can_edit = true`)
* **Request Body**:
  ```json
  {
    "title": "Updated Title",
    "category": "Financial"
  }
  ```
* **Response (200 OK)**: Updated document metadata object.
* **Audit Side Effect**: Records `DOC_UPDATE` in chained audit log.
* **Errors**: `403 Forbidden` (Viewer with Read-only access), `404 Not Found`.

---

### `DELETE /documents/{document_id}`
Deletes a document and its stored binary file.
* **Access**: Authenticated (Document Owner or Admin strictly; Viewers with Edit are denied)
* **Response (200 OK)**:
  ```json
  {
    "message": "Document deleted successfully"
  }
  ```
* **Audit Side Effect**: Records `DOC_DELETE` in chained audit log.
* **Errors**: `403 Forbidden` (Non-owner), `404 Not Found`.

---

## 3. Permissions Endpoints

### `POST /documents/{document_id}/permissions`
Grants or updates Read/Edit permissions to a designated user by email.
* **Access**: Document Owner or Admin
* **Request Body**:
  ```json
  {
    "grantee_email": "viewer@trustvault.io",
    "can_read": true,
    "can_edit": true
  }
  ```
* **Response (200 OK)**:
  ```json
  {
    "message": "Permission granted successfully",
    "permission": {
      "id": "uuid-v4-string",
      "document_id": "uuid-v4-string",
      "grantee_id": "uuid-v4-string",
      "can_read": true,
      "can_edit": true
    }
  }
  ```
* **Audit Side Effect**: Records `PERMISSION_GRANT`.

---

### `DELETE /documents/{document_id}/permissions/{grantee_id}`
Instantly revokes access for a grantee. Immediate enforcement on subsequent downloads.
* **Access**: Document Owner or Admin
* **Response (200 OK)**:
  ```json
  {
    "message": "Permission revoked successfully"
  }
  ```
* **Audit Side Effect**: Records `PERMISSION_REVOKE`.

---

## 4. Audit & Compliance Endpoints

### `GET /audit`
Lists chronological audit events.
* **Access**: Admin (views all events) or Document Owner (views events for owned documents).
* **Response (200 OK)**: Array of audit logs including hashes.

---

### `GET /audit/verify`
Mathematically recomputes the SHA-256 hash chain from genesis block to current tail.
* **Access**: Authenticated (Admin, Owner, Viewer)
* **Response (200 OK)**:
  ```json
  {
    "is_valid": true,
    "total_logs": 48,
    "genesis_hash": "0000000000000000000000000000000000000000000000000000000000000000",
    "latest_hash": "37f8d689b21f9..."
  }
  ```

---

### `GET /audit/metrics`
Provides system-wide summary metrics for administrative overview.
* **Access**: Admin only
* **Response (200 OK)**:
  ```json
  {
    "total_documents": 12,
    "total_users": 4,
    "total_grants": 3,
    "total_audit_events": 48,
    "chain_valid": true
  }
  ```
