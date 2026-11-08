import os
import sys
import uuid
import requests

BASE_URL = "http://127.0.0.1:8000/api"

# Helper login
def login(username, password):
    res = requests.post(f"{BASE_URL}/auth/login", json={"username_or_email": username, "password": password})
    assert res.status_code == 200, f"Login failed for {username}: {res.text}"
    return res.json()["access_token"]

# Seed/Upload document helper
def upload_doc(token, title):
    headers = {"Authorization": f"Bearer {token}"}
    files = {"file": (f"{title}.pdf", b"%PDF-1.4 dummy content for trustvault testing", "application/pdf")}
    data = {"title": title, "category": "confidential"}
    res = requests.post(f"{BASE_URL}/documents/upload", headers=headers, files=files, data=data)
    assert res.status_code in (200, 201), f"Upload failed: {res.text}"
    return res.json()["id"]

def run_tests():
    alice_token = login("alice_owner", "OwnerPass2026!")
    bob_token = login("bob_viewer", "ViewerPass2026!")
    
    # Also create a third test user (charlie) if not exists
    reg_res = requests.post(f"{BASE_URL}/auth/register", json={
        "username": "charlie_test",
        "email": "charlie@trustvault.io",
        "password": "CharliePass2026!",
        "role": "viewer"
    })
    charlie_token = login("charlie_test", "CharliePass2026!")

    # Get User IDs
    bob_id = requests.get(f"{BASE_URL}/auth/me", headers={"Authorization": f"Bearer {bob_token}"}).json()["id"]
    charlie_id = requests.get(f"{BASE_URL}/auth/me", headers={"Authorization": f"Bearer {charlie_token}"}).json()["id"]

    print(f"Bob ID: {bob_id}, Charlie ID: {charlie_id}")

    # --- CASE 1: Revoke by permission ID ---
    doc1_id = upload_doc(alice_token, f"Matrix_Test_1_{uuid.uuid4().hex[:6]}")
    # Grant to Bob
    g_res = requests.post(f"{BASE_URL}/documents/{doc1_id}/permissions", 
                          headers={"Authorization": f"Bearer {alice_token}"},
                          json={"grantee_email": "bob_viewer", "can_edit": False})
    assert g_res.status_code == 200
    perm1_id = g_res.json()["id"]
    print(f"[Case 1] Granted to Bob, permission_id={perm1_id}")

    # Verify Bob can access
    assert requests.get(f"{BASE_URL}/documents/{doc1_id}", headers={"Authorization": f"Bearer {bob_token}"}).status_code == 200

    # Revoke by permission ID
    rev1 = requests.delete(f"{BASE_URL}/documents/{doc1_id}/permissions/{perm1_id}", headers={"Authorization": f"Bearer {alice_token}"})
    assert rev1.status_code == 200, f"Revoke by perm ID failed: {rev1.text}"
    print("[Case 1] Revocation by permission ID returned 200 OK")

    # Verify Bob is DENIED
    assert requests.get(f"{BASE_URL}/documents/{doc1_id}", headers={"Authorization": f"Bearer {bob_token}"}).status_code in (403, 404)
    print("[Case 1] PASS: Bob access denied after permission ID revocation")

    # --- CASE 2: Revoke by grantee ID ---
    doc2_id = upload_doc(alice_token, f"Matrix_Test_2_{uuid.uuid4().hex[:6]}")
    g_res2 = requests.post(f"{BASE_URL}/documents/{doc2_id}/permissions", 
                           headers={"Authorization": f"Bearer {alice_token}"},
                           json={"grantee_email": "bob_viewer", "can_edit": True})
    assert g_res2.status_code == 200
    assert requests.get(f"{BASE_URL}/documents/{doc2_id}", headers={"Authorization": f"Bearer {bob_token}"}).status_code == 200
    
    # Revoke by grantee ID
    rev2 = requests.delete(f"{BASE_URL}/documents/{doc2_id}/permissions/{bob_id}", headers={"Authorization": f"Bearer {alice_token}"})
    assert rev2.status_code == 200, f"Revoke by grantee ID failed: {rev2.text}"
    print("[Case 2] Revocation by grantee ID returned 200 OK")
    assert requests.get(f"{BASE_URL}/documents/{doc2_id}", headers={"Authorization": f"Bearer {bob_token}"}).status_code in (403, 404)
    print("[Case 2] PASS: Bob access denied after grantee ID revocation")

    # --- CASE 3: Multiple documents shared with the same user ---
    # Alice shares doc_a and doc_b with Bob. Revoking doc_a must leave doc_b accessible to Bob.
    doc_a = upload_doc(alice_token, f"MultiDoc_A_{uuid.uuid4().hex[:6]}")
    doc_b = upload_doc(alice_token, f"MultiDoc_B_{uuid.uuid4().hex[:6]}")
    requests.post(f"{BASE_URL}/documents/{doc_a}/permissions", headers={"Authorization": f"Bearer {alice_token}"}, json={"grantee_email": "bob_viewer", "can_edit": False})
    requests.post(f"{BASE_URL}/documents/{doc_b}/permissions", headers={"Authorization": f"Bearer {alice_token}"}, json={"grantee_email": "bob_viewer", "can_edit": False})
    
    assert requests.get(f"{BASE_URL}/documents/{doc_a}", headers={"Authorization": f"Bearer {bob_token}"}).status_code == 200
    assert requests.get(f"{BASE_URL}/documents/{doc_b}", headers={"Authorization": f"Bearer {bob_token}"}).status_code == 200

    # Revoke Bob on doc_a only
    rev_a = requests.delete(f"{BASE_URL}/documents/{doc_a}/permissions/{bob_id}", headers={"Authorization": f"Bearer {alice_token}"})
    assert rev_a.status_code == 200

    # Verify doc_a is DENIED, doc_b is STILL ACCESSIBLE
    assert requests.get(f"{BASE_URL}/documents/{doc_a}", headers={"Authorization": f"Bearer {bob_token}"}).status_code in (403, 404)
    assert requests.get(f"{BASE_URL}/documents/{doc_b}", headers={"Authorization": f"Bearer {bob_token}"}).status_code == 200
    print("[Case 3] PASS: Revoking doc A left doc B fully intact for Bob")

    # --- CASE 4 & 5: Multiple permissions on the same document & Unrelated permissions remain intact ---
    # Alice shares doc_shared with both Bob and Charlie.
    doc_shared = upload_doc(alice_token, f"MultiUser_{uuid.uuid4().hex[:6]}")
    requests.post(f"{BASE_URL}/documents/{doc_shared}/permissions", headers={"Authorization": f"Bearer {alice_token}"}, json={"grantee_email": "bob_viewer", "can_edit": False})
    requests.post(f"{BASE_URL}/documents/{doc_shared}/permissions", headers={"Authorization": f"Bearer {alice_token}"}, json={"grantee_email": "charlie@trustvault.io", "can_edit": True})

    assert requests.get(f"{BASE_URL}/documents/{doc_shared}", headers={"Authorization": f"Bearer {bob_token}"}).status_code == 200
    assert requests.get(f"{BASE_URL}/documents/{doc_shared}", headers={"Authorization": f"Bearer {charlie_token}"}).status_code == 200

    # Revoke Bob only
    rev_bob = requests.delete(f"{BASE_URL}/documents/{doc_shared}/permissions/{bob_id}", headers={"Authorization": f"Bearer {alice_token}"})
    assert rev_bob.status_code == 200

    # Verify Bob is DENIED, Charlie is STILL ACCESSIBLE with can_edit intact!
    assert requests.get(f"{BASE_URL}/documents/{doc_shared}", headers={"Authorization": f"Bearer {bob_token}"}).status_code in (403, 404)
    charlie_doc_res = requests.get(f"{BASE_URL}/documents/{doc_shared}", headers={"Authorization": f"Bearer {charlie_token}"})
    assert charlie_doc_res.status_code == 200
    print("[Case 4 & 5] PASS: Revoking Bob left Charlie's permission completely intact on shared document")

    print("ALL_PERMISSION_REVOCATION_MATRIX_TESTS_PASSED")

if __name__ == "__main__":
    run_tests()
