import os
import sys
import sqlite3
import requests

BASE_URL = "http://127.0.0.1:8000/api"
DB_PATH = "C:/Users/Snuhith/projects/TrustVault/backend/trustvault.db"

def login(username, password):
    res = requests.post(f"{BASE_URL}/auth/login", json={"username_or_email": username, "password": password})
    assert res.status_code == 200
    return res.json()["access_token"]

def run_audit_tamper_tests():
    admin_token = login("admin@trustvault.io", "AdminPass2026!")
    headers = {"Authorization": f"Bearer {admin_token}"}

    # 1. Baseline verification
    v_res = requests.get(f"{BASE_URL}/audit/verify", headers=headers)
    assert v_res.status_code == 200
    assert v_res.json()["status"] == "valid", f"Baseline invalid: {v_res.text}"
    print("[Tamper Test 1] Baseline chain verified VALID (status=valid)")

    # 2. Failed operations test: submit 2 failed logins
    for i in range(2):
        requests.post(f"{BASE_URL}/auth/login", json={"username_or_email": "intruder", "password": "wrongpassword"})
    
    # Verify chain remains intact and auto-chained after failed operations
    v_res2 = requests.get(f"{BASE_URL}/audit/verify", headers=headers)
    assert v_res2.status_code == 200
    assert v_res2.json()["status"] == "valid"
    print(f"[Tamper Test 2] Chain verified VALID after failed security operations (records={v_res2.json()['total_records']})")

    # 3. Deliberate DB Tamper Test: modify metadata_json directly in SQLite
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT id, metadata_json, current_hash FROM audit_logs ORDER BY id DESC LIMIT 1")
    row = cur.fetchone()
    last_id, orig_meta, orig_hash = row
    print(f"[Tamper Test 3] Tampering with record ID {last_id} metadata_json in SQLite DB...")
    
    cur.execute("UPDATE audit_logs SET metadata_json = '{\"tampered\": true}' WHERE id = ?", (last_id,))
    conn.commit()

    try:
        # Verify endpoint MUST report tampered
        tamper_res = requests.get(f"{BASE_URL}/audit/verify", headers=headers)
        assert tamper_res.status_code == 200
        tamper_json = tamper_res.json()
        print(f"[Tamper Test 3] Verification result during tamper: {tamper_json}")
        assert tamper_json["status"] == "tampered", f"Expected status 'tampered', got {tamper_json}"
        assert tamper_json["broken_log_id"] == last_id, f"Expected broken_log_id {last_id}, got {tamper_json.get('broken_log_id')}"
        print("[Tamper Test 3] PASS: Tampering was IMMEDIATELY DETECTED by verification endpoint!")
    finally:
        # 4. Restore DB record to original state
        cur.execute("UPDATE audit_logs SET metadata_json = ? WHERE id = ?", (orig_meta, last_id))
        conn.commit()
        conn.close()
        print(f"[Tamper Test 4] Reverted record ID {last_id} back to original metadata")

    # Verify chain is restored
    restore_res = requests.get(f"{BASE_URL}/audit/verify", headers=headers)
    assert restore_res.status_code == 200
    assert restore_res.json()["status"] == "valid"
    print("[Tamper Test 4] PASS: Chain restored and mathematically verified VALID after reverting tamper")

    print("ALL_AUDIT_TAMPER_TESTS_SUCCESSFUL")

if __name__ == "__main__":
    run_audit_tamper_tests()
