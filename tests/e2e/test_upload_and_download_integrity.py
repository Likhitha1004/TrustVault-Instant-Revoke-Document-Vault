import os
import sys
import hashlib
import requests

BASE_URL = "http://127.0.0.1:8000/api"

def login(username, password):
    res = requests.post(f"{BASE_URL}/auth/login", json={"username_or_email": username, "password": password})
    assert res.status_code == 200
    return res.json()["access_token"]

def run_upload_tests():
    token = login("alice_owner", "OwnerPass2026!")
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Genuine PDF & byte-for-byte file download integrity check
    raw_payload = b"%PDF-1.4 TrustVault Secure Test Payload " + (b"0123456789ABCDEF" * 64)
    expected_hash = hashlib.sha256(raw_payload).hexdigest()
    
    files = {"file": ("integrity_test.pdf", raw_payload, "application/pdf")}
    data = {"title": "Integrity Test Doc", "category": "general"}
    up_res = requests.post(f"{BASE_URL}/documents/upload", headers=headers, files=files, data=data)
    assert up_res.status_code in (200, 201), f"Upload failed: {up_res.text}"
    doc_data = up_res.json()
    doc_id = doc_data["id"]
    assert doc_data["file_hash_sha256"] == expected_hash, "Reported SHA-256 hash does not match computed hash!"
    print(f"[Upload Test 1] Uploaded document ID {doc_id} with SHA-256: {expected_hash}")

    # Download bytes back and verify byte-for-byte identity
    dl_res = requests.get(f"{BASE_URL}/documents/{doc_id}/download", headers=headers)
    assert dl_res.status_code == 200
    downloaded_bytes = dl_res.content
    downloaded_hash = hashlib.sha256(downloaded_bytes).hexdigest()
    assert downloaded_hash == expected_hash, f"Downloaded hash {downloaded_hash} != expected {expected_hash}"
    assert downloaded_bytes == raw_payload, "Downloaded byte content differs from uploaded payload!"
    print("[Upload Test 1] PASS: Downloaded bytes verified 100% identical byte-for-byte!")

    # 2. Binary masquerade attack test (random bytes pretending to be text)
    masquerade_payload = b"MZ\x90\x00\x03\x00\x00\x00" + os.urandom(512)
    files_masq = {"file": ("malicious.txt", masquerade_payload, "text/plain")}
    res_masq = requests.post(f"{BASE_URL}/documents/upload", headers=headers, files=files_masq, data={"title": "Masq", "category": "general"})
    print(f"[Upload Test 2] Executable masquerade upload status: {res_masq.status_code}")
    assert res_masq.status_code == 400, f"Expected 400 Bad Request, got {res_masq.status_code}"
    print("[Upload Test 2] PASS: Executable / binary masquerade blocked by magic byte inspection")

    # 3. File size limit (>10MB) check
    large_payload = b"%PDF-1.4 " + (b"X" * (11 * 1024 * 1024))
    files_large = {"file": ("large.pdf", large_payload, "application/pdf")}
    res_large = requests.post(f"{BASE_URL}/documents/upload", headers=headers, files=files_large, data={"title": "Too Large", "category": "general"})
    print(f"[Upload Test 3] 11MB file upload status: {res_large.status_code}")
    assert res_large.status_code == 413, f"Expected 413 Payload Too Large, got {res_large.status_code}"
    print("[Upload Test 3] PASS: >10MB upload rejected with HTTP 413")

    # 4. Path traversal attack in filename
    traversal_filename = "../../../../etc/passwd"
    files_traversal = {"file": (traversal_filename, b"%PDF-1.4 safe pdf content", "application/pdf")}
    res_trav = requests.post(f"{BASE_URL}/documents/upload", headers=headers, files=files_traversal, data={"title": "Traversal Test", "category": "general"})
    assert res_trav.status_code in (200, 201)
    saved_filename = res_trav.json()["original_filename"]
    print(f"[Upload Test 4] Traversal input '{traversal_filename}' sanitized to: '{saved_filename}'")
    assert "/" not in saved_filename and ".." not in saved_filename
    print("[Upload Test 4] PASS: Path traversal sanitized cleanly by os.path.basename")

    # 5. Duplicate file upload check
    dup_files = {"file": ("duplicate.pdf", raw_payload, "application/pdf")}
    res_dup = requests.post(f"{BASE_URL}/documents/upload", headers=headers, files=dup_files, data={"title": "Duplicate Doc", "category": "general"})
    assert res_dup.status_code in (200, 201)
    dup_data = res_dup.json()
    assert dup_data["id"] != doc_id, "Duplicate upload should create a new unique document record"
    assert dup_data["file_hash_sha256"] == expected_hash
    print(f"[Upload Test 5] PASS: Duplicate payload created distinct document ID {dup_data['id']} with identical hash {expected_hash}")

    print("ALL_UPLOAD_INTEGRITY_TESTS_PASSED")

if __name__ == "__main__":
    run_upload_tests()
