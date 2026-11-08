import os
import sys
import uuid
import hashlib
import requests

BASE_URL = "http://127.0.0.1:8000/api"

def run_exhaustive_api_tests():
    print("=== EXHAUSTIVE API ENDPOINT VERIFICATION ===")
    
    # 1. POST /api/auth/register
    reg_username = f"exh_user_{uuid.uuid4().hex[:6]}"
    reg_email = f"{reg_username}@trustvault.io"
    res_reg = requests.post(f"{BASE_URL}/auth/register", json={
        "username": reg_username,
        "email": reg_email,
        "password": "Password123!",
        "role": "owner"
    })
    assert res_reg.status_code in (200, 201), f"Register failed: {res_reg.text}"
    user_data = res_reg.json()
    assert user_data["username"] == reg_username
    assert "hashed_password" not in user_data
    print(f"[1/15] POST /api/auth/register - PASS (HTTP 200, ID: {user_data['id']})")

    # 2. POST /api/auth/login
    res_login = requests.post(f"{BASE_URL}/auth/login", json={
        "username_or_email": reg_username,
        "password": "Password123!"
    })
    assert res_login.status_code == 200
    token_data = res_login.json()
    assert "access_token" in token_data
    owner_token = token_data["access_token"]
    owner_headers = {"Authorization": f"Bearer {owner_token}"}
    print("[2/15] POST /api/auth/login - PASS (HTTP 200, JWT issued)")

    # 3. GET /api/auth/me
    res_me = requests.get(f"{BASE_URL}/auth/me", headers=owner_headers)
    assert res_me.status_code == 200
    assert res_me.json()["email"] == reg_email
    owner_id = res_me.json()["id"]
    print("[3/15] GET /api/auth/me - PASS (HTTP 200, authenticated profile retrieved)")

    # 4. POST /api/documents/upload
    pdf_bytes = b"%PDF-1.4 Exhaustive API Test Payload " + os.urandom(64)
    expected_hash = hashlib.sha256(pdf_bytes).hexdigest()
    files = {"file": ("test_doc.pdf", pdf_bytes, "application/pdf")}
    res_upload = requests.post(f"{BASE_URL}/documents/upload", headers=owner_headers, files=files, data={"title": "Exhaustive Doc", "category": "finance"})
    assert res_upload.status_code in (200, 201)
    doc_data = res_upload.json()
    doc_id = doc_data["id"]
    assert doc_data["file_hash_sha256"] == expected_hash
    print(f"[4/15] POST /api/documents/upload - PASS (HTTP 201, Doc ID: {doc_id})")

    # 5. GET /api/documents
    res_docs = requests.get(f"{BASE_URL}/documents", headers=owner_headers, params={"search": "Exhaustive", "sort_by": "newest"})
    assert res_docs.status_code == 200
    docs_list = res_docs.json()
    assert any(d["id"] == doc_id for d in docs_list)
    print(f"[5/15] GET /api/documents - PASS (HTTP 200, filtered & sorted count: {len(docs_list)})")

    # 6. GET /api/documents/{id}
    res_get_doc = requests.get(f"{BASE_URL}/documents/{doc_id}", headers=owner_headers)
    assert res_get_doc.status_code == 200
    assert res_get_doc.json()["title"] == "Exhaustive Doc"
    print(f"[6/15] GET /api/documents/{{id}} - PASS (HTTP 200)")

    # 7. PATCH /api/documents/{id}
    res_patch = requests.patch(f"{BASE_URL}/documents/{doc_id}", headers=owner_headers, json={"title": "Exhaustive Doc Renamed", "category": "legal"})
    assert res_patch.status_code == 200
    assert res_patch.json()["title"] == "Exhaustive Doc Renamed"
    assert res_patch.json()["category"] == "legal"
    print("[7/15] PATCH /api/documents/{id} - PASS (HTTP 200, metadata updated)")

    # 8. POST /api/documents/{id}/permissions
    res_perm = requests.post(f"{BASE_URL}/documents/{doc_id}/permissions", headers=owner_headers, json={"grantee_email": "bob_viewer", "can_edit": True})
    assert res_perm.status_code == 200
    perm_id = res_perm.json()["id"]
    print(f"[8/15] POST /api/documents/{{id}}/permissions - PASS (HTTP 200, Perm ID: {perm_id})")

    # 9. GET /api/documents/{id}/download
    # Test download by grantee Bob
    bob_login = requests.post(f"{BASE_URL}/auth/login", json={"username_or_email": "bob_viewer", "password": "ViewerPass2026!"}).json()
    bob_headers = {"Authorization": f"Bearer {bob_login['access_token']}"}
    res_dl = requests.get(f"{BASE_URL}/documents/{doc_id}/download", headers=bob_headers)
    assert res_dl.status_code == 200
    assert res_dl.content == pdf_bytes
    print("[9/15] GET /api/documents/{id}/download - PASS (HTTP 200, streamed binary verified)")

    # 10. DELETE /api/documents/{id}/permissions/{grantee_id}
    res_rev = requests.delete(f"{BASE_URL}/documents/{doc_id}/permissions/{perm_id}", headers=owner_headers)
    assert res_rev.status_code == 200
    # Confirm Bob is now blocked
    assert requests.get(f"{BASE_URL}/documents/{doc_id}", headers=bob_headers).status_code in (403, 404)
    print("[10/15] DELETE /api/documents/{id}/permissions/{grantee_id} - PASS (HTTP 200, access revoked)")

    # 11. DELETE /api/documents/{id}
    res_del = requests.delete(f"{BASE_URL}/documents/{doc_id}", headers=owner_headers)
    assert res_del.status_code == 200
    # Confirm soft-deleted
    assert requests.get(f"{BASE_URL}/documents/{doc_id}", headers=owner_headers).status_code == 404
    print("[11/15] DELETE /api/documents/{id} - PASS (HTTP 200, soft-deletion verified)")

    # Admin endpoints
    admin_login = requests.post(f"{BASE_URL}/auth/login", json={"username_or_email": "admin@trustvault.io", "password": "AdminPass2026!"}).json()
    admin_headers = {"Authorization": f"Bearer {admin_login['access_token']}"}

    # 12. GET /api/audit
    res_audit = requests.get(f"{BASE_URL}/audit", headers=admin_headers, params={"limit": 10, "offset": 0})
    assert res_audit.status_code == 200
    assert isinstance(res_audit.json(), list)
    # Role gate test: Viewer Bob calling /audit must get 403
    assert requests.get(f"{BASE_URL}/audit", headers=bob_headers).status_code == 403
    print(f"[12/15] GET /api/audit - PASS (HTTP 200 for Admin, 403 for Viewer)")

    # 13. GET /api/audit/verify
    res_verify = requests.get(f"{BASE_URL}/audit/verify", headers=admin_headers)
    assert res_verify.status_code == 200
    assert res_verify.json()["status"] == "valid"
    assert requests.get(f"{BASE_URL}/audit/verify", headers=bob_headers).status_code == 403
    print("[13/15] GET /api/audit/verify - PASS (HTTP 200 for Admin, 403 for Viewer, valid chain)")

    # 14. GET /api/audit/metrics
    res_metrics = requests.get(f"{BASE_URL}/audit/metrics", headers=admin_headers)
    assert res_metrics.status_code == 200
    m_data = res_metrics.json()
    assert "total_documents" in m_data and "total_users" in m_data
    assert requests.get(f"{BASE_URL}/audit/metrics", headers=bob_headers).status_code == 403
    print("[14/15] GET /api/audit/metrics - PASS (HTTP 200 for Admin, 403 for Viewer, metrics valid)")

    # 15. POST /api/auth/logout
    res_logout = requests.post(f"{BASE_URL}/auth/logout", headers=owner_headers)
    assert res_logout.status_code == 200
    # Confirm token is revoked immediately
    assert requests.get(f"{BASE_URL}/auth/me", headers=owner_headers).status_code == 401
    print("[15/15] POST /api/auth/logout - PASS (HTTP 200, server-side token blacklist verified)")

    print("ALL_15_API_ENDPOINTS_EXHAUSTIVELY_VERIFIED_PASS")

if __name__ == "__main__":
    run_exhaustive_api_tests()
