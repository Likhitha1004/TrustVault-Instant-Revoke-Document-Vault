import os
import sys
import time
import json
import urllib.request
import urllib.error
from concurrent.futures import ThreadPoolExecutor, as_completed

BASE_URL = "http://127.0.0.1:8000/api"

def api_call(path, method="GET", token=None, body=None):
    url = f"{BASE_URL}{path}"
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    data = json.dumps(body).encode("utf-8") if body else None
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return resp.status, json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        err_body = e.read().decode()
        try:
            return e.code, json.loads(err_body)
        except:
            return e.code, {"raw": err_body}
    except Exception as e:
        return 500, {"error": str(e)}

def main():
    print("=== STARTING CONCURRENCY & DATA INTEGRITY SUITE ===")

    # 1. Login Admin and Owner
    _, admin_login = api_call("/auth/login", method="POST", body={
        "username_or_email": "admin@trustvault.io",
        "password": "AdminPass2026!"
    })
    admin_token = admin_login["access_token"]

    _, owner_login = api_call("/auth/login", method="POST", body={
        "username_or_email": "owner@trustvault.io",
        "password": "OwnerPass2026!"
    })
    owner_token = owner_login["access_token"]

    # 2. Upload test document
    import email.generator
    import io
    boundary = "----WebKitFormBoundaryConcurrencyTest"
    body = io.BytesIO()
    def write(s): body.write(s.encode('utf-8'))
    
    write(f"--{boundary}\r\nContent-Disposition: form-data; name=\"file\"; filename=\"concurrent_doc.pdf\"\r\nContent-Type: application/pdf\r\n\r\n")
    body.write(b"%PDF-1.4 Concurrency Audit PDF Content")
    write(f"\r\n--{boundary}\r\nContent-Disposition: form-data; name=\"title\"\r\n\r\nConcurrent Master Document\r\n")
    write(f"--{boundary}\r\nContent-Disposition: form-data; name=\"category\"\r\n\r\nLegal\r\n")
    write(f"--{boundary}--\r\n")
    
    req = urllib.request.Request(
        f"{BASE_URL}/documents/upload",
        data=body.getvalue(),
        headers={
            "Content-Type": f"multipart/form-data; boundary={boundary}",
            "Authorization": f"Bearer {owner_token}"
        },
        method="POST"
    )
    with urllib.request.urlopen(req) as resp:
        upload_data = json.loads(resp.read().decode())
    doc_id = upload_data["id"]
    print(f"1. Created test document for concurrency: {doc_id}")

    # 3. Concurrent Document Updates
    print("2. Spawning 10 concurrent metadata update threads...")
    def update_doc(i):
        return api_call(f"/documents/{doc_id}", method="PATCH", token=owner_token, body={
            "title": f"Concurrent Title Update {i}",
            "category": f"Legal_{i}"
        })

    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(update_doc, i) for i in range(10)]
        results = [f.result() for f in as_completed(futures)]

    success_updates = [r for r in results if r[0] == 200]
    print(f"   Concurrent document updates completed: {len(success_updates)}/10 succeeded.")
    assert len(success_updates) > 0, "No concurrent updates succeeded"

    # 4. Concurrent Grants and Revocations
    print("3. Spawning 10 concurrent permission grants and revocations...")
    def grant_revoke(i):
        # Grant to viewer
        g_status, g_res = api_call(f"/documents/{doc_id}/permissions", method="POST", token=owner_token, body={
            "grantee_email": "viewer@trustvault.io",
            "can_edit": bool(i % 2 == 0)
        })
        time.sleep(0.05)
        # Revoke
        r_status, r_res = api_call(f"/documents/{doc_id}/permissions/viewer@trustvault.io", method="DELETE", token=owner_token)
        return (g_status, r_status)

    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(grant_revoke, i) for i in range(10)]
        perm_results = [f.result() for f in as_completed(futures)]

    print(f"   Concurrent grant/revoke pairs executed: {len(perm_results)}")

    # 5. Concurrent Audit Log Writes
    print("4. Spawning 15 concurrent audit writes and reads...")
    def audit_op(i):
        if i % 3 == 0:
            return api_call("/audit/verify", token=admin_token)
        elif i % 3 == 1:
            return api_call("/audit/metrics", token=admin_token)
        else:
            return api_call("/auth/login", method="POST", body={
                "username_or_email": "admin@trustvault.io",
                "password": "WrongPasswordAttempt"
            })

    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(audit_op, i) for i in range(15)]
        audit_results = [f.result() for f in as_completed(futures)]

    print(f"   Concurrent audit operations executed: {len(audit_results)}")

    # 6. Verify Audit Hash Chain Intactness
    print("5. Verifying cryptographic hash chain integrity after high concurrency...")
    status, verify_res = api_call("/audit/verify", token=admin_token)
    assert status == 200, f"/audit/verify returned {status}: {verify_res}"
    assert verify_res.get("status") == "valid", f"Hash chain broken after concurrency: {verify_res}"
    print(f"   Cryptographic audit hash chain status: {verify_res.get('status').upper()} (Total blocks: {verify_res.get('total_records')}) [PASS]")

    # 7. Verify document state consistency
    status, doc_res = api_call(f"/documents/{doc_id}", token=owner_token)
    assert status == 200, f"Failed to retrieve document: {doc_res}"
    assert "Concurrent Title Update" in doc_res["title"]
    print(f"   Document final state: '{doc_res['title']}' (Consistent and intact) [PASS]")

    # Clean up test document
    api_call(f"/documents/{doc_id}", method="DELETE", token=owner_token)
    print("ALL CONCURRENCY AND AUDIT INTEGRITY CHECKS PASSED!")

if __name__ == "__main__":
    main()
