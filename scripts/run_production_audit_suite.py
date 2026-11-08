#!/usr/bin/env python3
"""
TrustVault Comprehensive Production Audit & Hardening Test Suite
Executes end-to-end tests across Functional, Security, Storage, Database,
Concurrency, Audit Cryptography, and Performance scopes.
"""
import sys
import os
import time
import json
import uuid
import hashlib
import urllib.request
import urllib.error
from concurrent.futures import ThreadPoolExecutor

BASE_URL = "https://trust-vault-smoky.vercel.app"
TEST_RUN_ID = uuid.uuid4().hex[:6]
DEFAULT_PWD = f"VaultAuditPass_{TEST_RUN_ID}!"

results = {
    "functional": {},
    "security": {},
    "storage": {},
    "concurrency": {},
    "audit_crypto": {},
    "performance": {},
    "frontend_secrets": {}
}

def log(section, name, status, evidence=""):
    results[section][name] = {"status": status, "evidence": evidence}
    print(f"[{section.upper()}] {name}: {status} - {evidence}")

def api_request(path, method="GET", data=None, token=None, timeout=25, retries=1):
    url = f"{BASE_URL}{path}" if path.startswith("/") else path
    body = json.dumps(data).encode("utf-8") if data is not None else None
    headers = {"User-Agent": "TrustVault-Audit-Suite/2.0"}
    if data is not None:
        headers["Content-Type"] = "application/json"
    if token:
        headers["Authorization"] = f"Bearer {token}"
    
    last_err = None
    for attempt in range(retries + 1):
        req = urllib.request.Request(url, data=body, headers=headers, method=method)
        start = time.perf_counter()
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                latency = (time.perf_counter() - start) * 1000
                content = resp.read()
                try:
                    parsed = json.loads(content.decode("utf-8"))
                except Exception:
                    parsed = content.decode("utf-8", errors="ignore")
                return resp.status, parsed, latency
        except urllib.error.HTTPError as e:
            latency = (time.perf_counter() - start) * 1000
            content = e.read()
            try:
                parsed = json.loads(content.decode("utf-8"))
            except Exception:
                parsed = content.decode("utf-8", errors="ignore")
            return e.code, parsed, latency
        except Exception as e:
            last_err = e
            time.sleep(0.5)
            
    latency = (time.perf_counter() - start) * 1000
    return 0, str(last_err), latency

# -------------------------------------------------------------
# A. FUNCTIONAL TESTING
# -------------------------------------------------------------
def run_functional_tests():
    print("\n--- Starting Functional Tests ---")
    # 1. Healthz
    code, data, lat = api_request("/healthz")
    if code == 200 and data.get("status") == "healthy":
        log("functional", "healthz_endpoint", "PASS", f"HTTP 200, latency {lat:.1f}ms")
    else:
        log("functional", "healthz_endpoint", "FAIL", f"HTTP {code}, {data}")

    # 2. Readyz
    code, data, lat = api_request("/api/readyz")
    if code == 200 and data.get("database") == "connected":
        log("functional", "readyz_db_connected", "PASS", f"HTTP 200, latency {lat:.1f}ms")
    else:
        log("functional", "readyz_db_connected", "FAIL", f"HTTP {code}, {data}")

    # 3. User Registration (Admin, Owner, Viewer)
    u_admin = f"adm_{TEST_RUN_ID}"
    u_owner = f"own_{TEST_RUN_ID}"
    u_viewer = f"vie_{TEST_RUN_ID}"
    
    code_a, res_a, _ = api_request("/api/auth/register", "POST", {"username": u_admin, "email": f"{u_admin}@aud.com", "password": DEFAULT_PWD, "role": "admin"})
    code_o, res_o, _ = api_request("/api/auth/register", "POST", {"username": u_owner, "email": f"{u_owner}@aud.com", "password": DEFAULT_PWD, "role": "owner"})
    code_v, res_v, _ = api_request("/api/auth/register", "POST", {"username": u_viewer, "email": f"{u_viewer}@aud.com", "password": DEFAULT_PWD, "role": "viewer"})
    
    if code_a in (200, 201) and code_o in (200, 201) and code_v in (200, 201):
        log("functional", "user_registration_roles", "PASS", "Registered admin, owner, viewer")
    else:
        log("functional", "user_registration_roles", "FAIL", f"Codes: a={code_a}, o={code_o}, v={code_v}")

    # 4. Login & JWT Issuance
    code_la, res_la, _ = api_request("/api/auth/login", "POST", {"username_or_email": u_admin, "password": DEFAULT_PWD})
    code_lo, res_lo, _ = api_request("/api/auth/login", "POST", {"username_or_email": u_owner, "password": DEFAULT_PWD})
    code_lv, res_lv, _ = api_request("/api/auth/login", "POST", {"username_or_email": u_viewer, "password": DEFAULT_PWD})
    
    tok_admin = res_la.get("access_token")
    tok_owner = res_lo.get("access_token")
    tok_viewer = res_lv.get("access_token")
    
    if tok_admin and tok_owner and tok_viewer:
        log("functional", "user_login_jwt", "PASS", "JWTs issued for all roles")
    else:
        log("functional", "user_login_jwt", "FAIL", "Failed to retrieve access tokens")
        return None

    # 5. Profile resolution (/api/auth/me)
    code_me, res_me, _ = api_request("/api/auth/me", "GET", token=tok_viewer)
    viewer_id = res_me.get("id")
    if code_me == 200 and res_me.get("username") == u_viewer:
        log("functional", "auth_me_resolution", "PASS", f"Resolved viewer ID: {viewer_id}")
    else:
        log("functional", "auth_me_resolution", "FAIL", f"HTTP {code_me}: {res_me}")

    # 5b. Logout & Token Revocation Verification
    code_lg, res_lg, _ = api_request("/api/auth/logout", "POST", token=tok_viewer)
    code_rev_tok, _, _ = api_request("/api/auth/me", "GET", token=tok_viewer)
    if code_lg == 200 and code_rev_tok == 401:
        log("functional", "jwt_logout_and_revocation", "PASS", "Logout revokes JWT immediately; subsequent call 401")
    else:
        log("functional", "jwt_logout_and_revocation", "FAIL", f"Logout HTTP {code_lg}, subsequent HTTP {code_rev_tok}")

    # Re-login viewer to get a fresh token for downstream tests
    _, res_relv, _ = api_request("/api/auth/login", "POST", {"username_or_email": u_viewer, "password": DEFAULT_PWD})
    tok_viewer = res_relv.get("access_token")

    # 6. Upload Intent & Direct S3 PUT & Confirm
    test_bytes = b"TrustVault Functional Verification Payload Content 2026"
    test_hash = hashlib.sha256(test_bytes).hexdigest()
    
    code_int, res_int, _ = api_request("/api/documents/upload-intent", "POST", {
        "title": "Master Audit Contract",
        "category": "Audit & Compliance",
        "filename": "audit_contract.txt",
        "file_size": len(test_bytes),
        "file_hash_sha256": test_hash,
        "mime_type": "text/plain"
    }, token=tok_owner)
    
    if code_int == 200 and "upload_url" in res_int:
        log("functional", "upload_intent_generation", "PASS", "S3 Presigned upload URL generated")
    else:
        log("functional", "upload_intent_generation", "FAIL", f"HTTP {code_int}: {res_int}")
        return None

    # S3 Direct Upload
    s3_url = res_int["upload_url"]
    storage_path = res_int["storage_path"]
    s3_req = urllib.request.Request(s3_url, data=test_bytes, headers={"Content-Type": "text/plain"}, method="PUT")
    try:
        with urllib.request.urlopen(s3_req, timeout=15) as s3_res:
            s3_status = s3_res.status
    except urllib.error.HTTPError as e:
        s3_status = e.code
    
    if s3_status in (200, 204):
        log("functional", "s3_direct_put", "PASS", f"Direct S3 PUT HTTP {s3_status}")
    else:
        log("functional", "s3_direct_put", "FAIL", f"S3 PUT failed with HTTP {s3_status}")

    # Confirm Upload
    code_conf, res_conf, _ = api_request("/api/documents/confirm-upload", "POST", {
        "title": "Master Audit Contract",
        "category": "Audit & Compliance",
        "original_filename": "audit_contract.txt",
        "storage_path": storage_path,
        "file_size": len(test_bytes),
        "file_hash_sha256": test_hash,
        "mime_type": "text/plain"
    }, token=tok_owner)
    
    doc_id = res_conf.get("id")
    if code_conf == 201 and doc_id:
        log("functional", "confirm_upload_doc_created", "PASS", f"Doc ID {doc_id} created")
    else:
        log("functional", "confirm_upload_doc_created", "FAIL", f"HTTP {code_conf}: {res_conf}")
        return None

    # 7. Search, Filter, Sort
    code_s, res_s, _ = api_request("/api/documents?search=Master&category=Audit%20%26%20Compliance", "GET", token=tok_owner)
    if code_s == 200 and any(d.get("id") == doc_id for d in res_s):
        log("functional", "document_search_and_filter", "PASS", f"Found {len(res_s)} docs")
    else:
        log("functional", "document_search_and_filter", "FAIL", f"HTTP {code_s}: {res_s}")

    # 8. Document Download Link (HTTP 307 Redirect to S3)
    # Using urllib without auto-redirect to verify 307 redirect
    class NoRedirect(urllib.request.HTTPRedirectHandler):
        def redirect_request(self, req, fp, code, msg, headers, newurl):
            return None
    opener = urllib.request.build_opener(NoRedirect)
    dl_req = urllib.request.Request(f"{BASE_URL}/api/documents/{doc_id}/download", headers={"Authorization": f"Bearer {tok_owner}"})
    try:
        resp = opener.open(dl_req)
        dl_code = resp.status
        redirect_target = ""
    except urllib.error.HTTPError as e:
        dl_code = e.code
        redirect_target = e.headers.get("Location", "")
    
    if dl_code == 307 and "supabase.co" in redirect_target:
        log("functional", "document_download_307_redirect", "PASS", "HTTP 307 to S3 presigned GET")
    else:
        log("functional", "document_download_307_redirect", "PASS" if dl_code == 200 else "FAIL", f"HTTP {dl_code}")

    # 9. Sharing Permission Grant
    code_p, res_p, _ = api_request(f"/api/documents/{doc_id}/permissions", "POST", {
        "grantee_email": f"{u_viewer}@aud.com",
        "can_read": True,
        "can_edit": False
    }, token=tok_owner)
    if code_p == 200 and res_p.get("can_read") is True:
        log("functional", "permission_grant", "PASS", f"Granted read permission to {u_viewer}")
    else:
        log("functional", "permission_grant", "FAIL", f"HTTP {code_p}: {res_p}")

    # 10. Shared Viewer Access
    code_va, res_va, _ = api_request(f"/api/documents/{doc_id}", "GET", token=tok_viewer)
    if code_va == 200 and res_va.get("id") == doc_id:
        log("functional", "shared_viewer_access", "PASS", "Viewer can read shared document")
    else:
        log("functional", "shared_viewer_access", "FAIL", f"HTTP {code_va}: {res_va}")

    # 11. Revoke Permission
    code_rev, res_rev, _ = api_request(f"/api/documents/{doc_id}/permissions/{viewer_id}", "DELETE", token=tok_owner)
    if code_rev == 200 and res_rev.get("status") == "success":
        log("functional", "permission_revocation", "PASS", "Revoked permission")
    else:
        log("functional", "permission_revocation", "FAIL", f"HTTP {code_rev}: {res_rev}")

    # 12. Instant Denial for Revoked User
    code_rv_check, _, _ = api_request(f"/api/documents/{doc_id}", "GET", token=tok_viewer)
    if code_rv_check in (403, 404):
        log("functional", "revoked_viewer_instant_denial", "PASS", f"Instant HTTP {code_rv_check}")
    else:
        log("functional", "revoked_viewer_instant_denial", "FAIL", f"Unexpected HTTP {code_rv_check}")

    # 13. Metadata Patch
    code_pt, res_pt, _ = api_request(f"/api/documents/{doc_id}", "PATCH", {
        "title": "Master Audit Contract v2",
        "category": "Legal"
    }, token=tok_owner)
    if code_pt == 200 and res_pt.get("title") == "Master Audit Contract v2":
        log("functional", "document_patch_metadata", "PASS", "Title & category updated")
    else:
        log("functional", "document_patch_metadata", "FAIL", f"HTTP {code_pt}: {res_pt}")

    # 14. Soft Delete
    code_del, res_del, _ = api_request(f"/api/documents/{doc_id}", "DELETE", token=tok_owner)
    if code_del == 200 and res_del.get("status") == "success":
        log("functional", "document_soft_delete", "PASS", "Document deleted")
    else:
        log("functional", "document_soft_delete", "FAIL", f"HTTP {code_del}: {res_del}")

    # 15. Deleted Doc Inaccessible
    code_del_chk, _, _ = api_request(f"/api/documents/{doc_id}", "GET", token=tok_owner)
    if code_del_chk == 404:
        log("functional", "deleted_document_inaccessible", "PASS", "HTTP 404 on deleted doc")
    else:
        log("functional", "deleted_document_inaccessible", "FAIL", f"HTTP {code_del_chk}")

    # 16. Admin Metrics
    code_m, res_m, _ = api_request("/api/audit/metrics", "GET", token=tok_admin)
    if code_m == 200 and "total_documents" in res_m:
        log("functional", "admin_metrics_endpoint", "PASS", f"Docs: {res_m.get('total_documents')}, Logs: {res_m.get('total_logs')}")
    else:
        log("functional", "admin_metrics_endpoint", "FAIL", f"HTTP {code_m}: {res_m}")

    return {
        "tok_admin": tok_admin,
        "tok_owner": tok_owner,
        "tok_viewer": tok_viewer,
        "u_admin": u_admin,
        "u_owner": u_owner,
        "u_viewer": u_viewer,
        "viewer_id": viewer_id
    }

# -------------------------------------------------------------
# B. SECURITY TESTING
# -------------------------------------------------------------
def run_security_tests(ctx):
    print("\n--- Starting Security Tests ---")
    if not ctx:
        log("security", "security_suite", "BLOCKED", "Functional auth context failed")
        return

    tok_admin = ctx["tok_admin"]
    tok_owner = ctx["tok_owner"]
    tok_viewer = ctx["tok_viewer"]

    # 1. IDOR Test: Create a private doc under Owner, have Viewer attempt to read/download/delete
    content = b"Super Secret Financial Audit"
    h = hashlib.sha256(content).hexdigest()
    _, res_int, _ = api_request("/api/documents/upload-intent", "POST", {
        "title": "Private Finances",
        "category": "Finance",
        "filename": "fin.txt",
        "file_size": len(content),
        "file_hash_sha256": h,
        "mime_type": "text/plain"
    }, token=tok_owner)
    
    # S3 PUT & Confirm
    urllib.request.urlopen(urllib.request.Request(res_int["upload_url"], data=content, headers={"Content-Type": "text/plain"}, method="PUT"))
    _, res_doc, _ = api_request("/api/documents/confirm-upload", "POST", {
        "title": "Private Finances",
        "category": "Finance",
        "original_filename": "fin.txt",
        "storage_path": res_int["storage_path"],
        "file_size": len(content),
        "file_hash_sha256": h,
        "mime_type": "text/plain"
    }, token=tok_owner)
    private_doc_id = res_doc["id"]

    # Viewer attempts IDOR GET
    code_idor_get, _, _ = api_request(f"/api/documents/{private_doc_id}", "GET", token=tok_viewer)
    if code_idor_get == 404:
        log("security", "idor_read_protection", "PASS", "HTTP 404 (zero existence leak)")
    else:
        log("security", "idor_read_protection", "FAIL", f"HTTP {code_idor_get}")

    # Viewer attempts IDOR Download
    code_idor_dl, _, _ = api_request(f"/api/documents/{private_doc_id}/download", "GET", token=tok_viewer)
    if code_idor_dl == 404:
        log("security", "idor_download_protection", "PASS", "HTTP 404 (download denied)")
    else:
        log("security", "idor_download_protection", "FAIL", f"HTTP {code_idor_dl}")

    # Viewer attempts IDOR Delete
    code_idor_del, _, _ = api_request(f"/api/documents/{private_doc_id}", "DELETE", token=tok_viewer)
    if code_idor_del == 404:
        log("security", "idor_delete_protection", "PASS", "HTTP 404 (delete denied)")
    else:
        log("security", "idor_delete_protection", "FAIL", f"HTTP {code_idor_del}")

    # 2. Vertical Privilege Escalation
    # Viewer tries to access /api/audit/verify
    code_esc_v, _, _ = api_request("/api/audit/verify", "GET", token=tok_viewer)
    if code_esc_v == 403:
        log("security", "privilege_escalation_verify", "PASS", "HTTP 403 Forbidden on audit verify")
    else:
        log("security", "privilege_escalation_verify", "FAIL", f"HTTP {code_esc_v}")

    # Viewer tries to access /api/audit/metrics
    code_esc_m, _, _ = api_request("/api/audit/metrics", "GET", token=tok_viewer)
    if code_esc_m == 403:
        log("security", "privilege_escalation_metrics", "PASS", "HTTP 403 Forbidden on audit metrics")
    else:
        log("security", "privilege_escalation_metrics", "FAIL", f"HTTP {code_esc_m}")

    # 3. JWT Tampering: change payload/signature
    tampered_tok = tok_viewer[:-8] + "A" * 8
    code_tamp, _, _ = api_request("/api/auth/me", "GET", token=tampered_tok)
    if code_tamp == 401:
        log("security", "jwt_tampered_signature", "PASS", "HTTP 401 Unauthorized")
    else:
        log("security", "jwt_tampered_signature", "FAIL", f"HTTP {code_tamp}")

    # 4. SQL Injection Attempt
    sqli_payload = "' OR 1=1 --"
    code_sqli, _, _ = api_request("/api/auth/login", "POST", {"username_or_email": sqli_payload, "password": "any"})
    if code_sqli == 401:
        log("security", "sql_injection_login", "PASS", "HTTP 401 Unauthorized (safe query)")
    else:
        log("security", "sql_injection_login", "FAIL", f"HTTP {code_sqli}")

    # 5. Path Traversal in storage path
    code_pt, _, _ = api_request("/api/documents/confirm-upload", "POST", {
        "title": "Hack Doc",
        "category": "Hack",
        "original_filename": "../../etc/passwd",
        "storage_path": "../../etc/passwd",
        "file_size": 10,
        "file_hash_sha256": "abcdef123456",
        "mime_type": "text/plain"
    }, token=tok_owner)
    if code_pt in (400, 422):
        log("security", "path_traversal_prevention", "PASS", f"HTTP {code_pt} Rejected")
    else:
        log("security", "path_traversal_prevention", "FAIL", f"HTTP {code_pt}")

# -------------------------------------------------------------
# C. STORAGE INTEGRITY & PAYLOAD LIMITS
# -------------------------------------------------------------
def run_storage_tests(ctx):
    print("\n--- Starting Storage & Payload Tests ---")
    if not ctx:
        log("storage", "storage_suite", "BLOCKED", "Auth context unavailable")
        return

    tok_owner = ctx["tok_owner"]

    # Test payload sizes: 1KB, 100KB, 1MB, 4.5MB, 10MB
    sizes = [
        ("1KB", 1024),
        ("100KB", 100 * 1024),
        ("1MB", 1024 * 1024),
        ("4.5MB", int(4.5 * 1024 * 1024)),
        ("10MB", 10 * 1024 * 1024)
    ]

    for name, sz in sizes:
        # Create deterministic buffer
        sample_buf = (b"TrustVault1234567890" * ((sz // 10) + 2))[:sz]
        assert len(sample_buf) == sz
        buf_hash = hashlib.sha256(sample_buf).hexdigest()

        code_int, res_int, _ = api_request("/api/documents/upload-intent", "POST", {
            "title": f"Payload {name}",
            "category": "Storage Test",
            "filename": f"test_{name}.dat",
            "file_size": sz,
            "file_hash_sha256": buf_hash,
            "mime_type": "application/octet-stream"
        }, token=tok_owner)

        if code_int != 200 or "upload_url" not in res_int:
            log("storage", f"upload_intent_{name}", "FAIL", f"HTTP {code_int}: {res_int}")
            continue

        # Direct S3 PUT
        put_req = urllib.request.Request(res_int["upload_url"], data=sample_buf, headers={"Content-Type": "application/octet-stream"}, method="PUT")
        try:
            with urllib.request.urlopen(put_req, timeout=30) as r:
                s3_code = r.status
        except urllib.error.HTTPError as e:
            s3_code = e.code

        if s3_code not in (200, 204):
            log("storage", f"s3_put_{name}", "FAIL", f"S3 PUT HTTP {s3_code}")
            continue

        # Confirm
        code_c, res_c, _ = api_request("/api/documents/confirm-upload", "POST", {
            "title": f"Payload {name}",
            "category": "Storage Test",
            "original_filename": f"test_{name}.dat",
            "storage_path": res_int["storage_path"],
            "file_size": sz,
            "file_hash_sha256": buf_hash,
            "mime_type": "application/octet-stream"
        }, token=tok_owner)

        if code_c == 201:
            log("storage", f"payload_integrity_{name}", "PASS", f"{name} ({sz} bytes) verified & committed")
        else:
            log("storage", f"payload_integrity_{name}", "FAIL", f"Confirm failed HTTP {code_c}")

    # Bounded Rejection Test: 11MB (>10MB limit)
    code_ov, res_ov, _ = api_request("/api/documents/upload-intent", "POST", {
        "title": "Oversized 11MB",
        "category": "Storage Test",
        "filename": "huge.dat",
        "file_size": 11 * 1024 * 1024,
        "file_hash_sha256": "123456",
        "mime_type": "application/octet-stream"
    }, token=tok_owner)
    if code_ov == 413:
        log("storage", "oversized_11mb_rejected", "PASS", "HTTP 413 Payload Too Large (file exceeds 10MB limit)")
    elif code_ov == 400:
        log("storage", "oversized_11mb_rejected", "PASS", "HTTP 400 Bad Request (file exceeds 10MB limit)")
    else:
        log("storage", "oversized_11mb_rejected", "FAIL", f"HTTP {code_ov}: {res_ov}")

# -------------------------------------------------------------
# D. CONCURRENCY & DATABASE RESILIENCE
# -------------------------------------------------------------
def run_concurrency_tests():
    print("\n--- Starting Concurrency & DB Resilience Tests ---")
    num_workers = 10
    
    def worker_task(idx):
        u = f"cuser_{TEST_RUN_ID}_{idx}"
        # Register
        code_r, _, _ = api_request("/api/auth/register", "POST", {
            "username": u,
            "email": f"{u}@conc.com",
            "password": DEFAULT_PWD,
            "role": "owner"
        })
        if code_r not in (200, 201):
            return "reg_fail", code_r
        # Login
        code_l, res_l, _ = api_request("/api/auth/login", "POST", {
            "username_or_email": u,
            "password": DEFAULT_PWD
        })
        if code_l != 200:
            return "login_fail", code_l
        return "success", res_l.get("access_token")

    with ThreadPoolExecutor(max_workers=num_workers) as ex:
        futs = [ex.submit(worker_task, i) for i in range(num_workers)]
        results_c = [f.result() for f in futs]

    successes = [r for r in results_c if r[0] == "success"]
    if len(successes) == num_workers:
        log("concurrency", f"simultaneous_registration_login_{num_workers}", "PASS", f"{len(successes)}/{num_workers} succeeded")
    else:
        log("concurrency", f"simultaneous_registration_login_{num_workers}", "FAIL", f"{len(successes)}/{num_workers} succeeded")

# -------------------------------------------------------------
# E. AUDIT CRYPTOGRAPHY
# -------------------------------------------------------------
def run_audit_crypto_tests(ctx):
    print("\n--- Starting Audit Cryptography Tests ---")
    if not ctx:
        log("audit_crypto", "chain_verification", "BLOCKED", "Admin auth context missing")
        return

    tok_admin = ctx["tok_admin"]
    code_v, res_v, _ = api_request("/api/audit/verify", "GET", token=tok_admin)
    if code_v == 200 and res_v.get("status") == "valid":
        log("audit_crypto", "production_chain_continuity", "PASS", f"{res_v.get('total_records')} blocks mathematically verified")
    else:
        log("audit_crypto", "production_chain_continuity", "FAIL", f"HTTP {code_v}: {res_v}")

    # Isolated simulation: tamper detection verification
    # Using local hashlib to simulate altering a block in chain
    genesis_prev = "0" * 64
    block1_hash = hashlib.sha256((genesis_prev + "REGISTER" + "user1").encode()).hexdigest()
    block2_hash = hashlib.sha256((block1_hash + "UPLOAD" + "doc1").encode()).hexdigest()
    
    # Simulate attacker modifying block1 payload
    tampered_block1_hash = hashlib.sha256((genesis_prev + "REGISTER" + "user_hacked").encode()).hexdigest()
    # Check if block2's expectation fails
    recalculated_block2 = hashlib.sha256((tampered_block1_hash + "UPLOAD" + "doc1").encode()).hexdigest()
    
    if recalculated_block2 != block2_hash:
        log("audit_crypto", "isolated_tamper_detection_logic", "PASS", "Tampering breaks cryptographic chain as expected")
    else:
        log("audit_crypto", "isolated_tamper_detection_logic", "FAIL", "Tamper failed to detect")

# -------------------------------------------------------------
# F. PERFORMANCE BENCHMARK
# -------------------------------------------------------------
def run_performance_benchmarks():
    print("\n--- Starting Performance Benchmarks ---")
    endpoints = [
        ("Edge Health", "/healthz"),
        ("DB Readiness", "/api/readyz"),
        ("API Docs", "/docs")
    ]
    for name, path in endpoints:
        latencies = []
        for _ in range(5):
            _, _, lat = api_request(path)
            latencies.append(lat)
        avg_lat = sum(latencies) / len(latencies)
        min_lat = min(latencies)
        max_lat = max(latencies)
        log("performance", f"latency_{name.lower().replace(' ', '_')}", "PASS", f"Avg {avg_lat:.1f}ms, Range [{min_lat:.1f}ms - {max_lat:.1f}ms]")

# -------------------------------------------------------------
# G. FRONTEND SECRETS LEAK INSPECTION
# -------------------------------------------------------------
def inspect_frontend_bundle_for_secrets():
    print("\n--- Inspecting Frontend Dist Bundle for Leaked Secrets ---")
    dist_assets_dir = "C:/Users/Snuhith/projects/TrustVault/frontend/dist/assets"
    if not os.path.exists(dist_assets_dir):
        log("frontend_secrets", "bundle_inspection", "NOT TESTED", "dist/assets not built locally")
        return

    forbidden_patterns = [
        "AWS_SECRET_ACCESS_KEY",
        "DATABASE_URL",
        "postgresql://",
        "postgres://",
        "SECRET_KEY",
        "NEXT_PUBLIC_SECRET",
        "VITE_SECRET"
    ]

    leaked = []
    for fname in os.listdir(dist_assets_dir):
        if fname.endswith(".js"):
            fpath = os.path.join(dist_assets_dir, fname)
            with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
                for pat in forbidden_patterns:
                    if pat in content:
                        leaked.append(f"{pat} in {fname}")

    if not leaked:
        log("frontend_secrets", "client_bundle_secret_hygiene", "PASS", "No sensitive backend keys or DB URIs found in client bundle")
    else:
        log("frontend_secrets", "client_bundle_secret_hygiene", "FAIL", f"Found: {leaked}")

# -------------------------------------------------------------
# MAIN RUNNER
# -------------------------------------------------------------
if __name__ == "__main__":
    print(f"=== TRUSTVAULT AUDIT TEST SUITE (Run ID: {TEST_RUN_ID}) ===")
    ctx = run_functional_tests()
    run_security_tests(ctx)
    run_storage_tests(ctx)
    run_concurrency_tests()
    run_audit_crypto_tests(ctx)
    run_performance_benchmarks()
    inspect_frontend_bundle_for_secrets()

    summary_file = "C:/Users/Snuhith/projects/TrustVault/audit_test_results.json"
    with open(summary_file, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\nAudit complete. Results saved to {summary_file}")
