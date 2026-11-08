import os
import sys
import time
import json
import urllib.request
import urllib.error
import subprocess

BASE_URL = "http://127.0.0.1:8000/api"

def api_call(path, method="GET", token=None, body=None):
    url = f"{BASE_URL}{path}"
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    data = json.dumps(body).encode("utf-8") if body else None
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req) as resp:
            return resp.status, json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        err_body = e.read().decode()
        try:
            return e.code, json.loads(err_body)
        except:
            return e.code, {"raw": err_body}

def main():
    print("=== STARTING DEEP JWT LOGOUT INVALIDATION AUDIT ===")
    
    # 1. Capture valid JWT
    status, login_res = api_call("/auth/login", method="POST", body={
        "username_or_email": "admin@trustvault.io",
        "password": "AdminPass2026!"
    })
    assert status == 200, f"Login failed: {login_res}"
    token = login_res["access_token"]
    print("1. Captured valid JWT token successfully.")

    # 2. Verify token works before logout
    status, me_res = api_call("/auth/me", token=token)
    assert status == 200, f"/auth/me failed: {me_res}"
    print("2. Token verified active and authorized.")

    # 3. Perform logout
    status, logout_res = api_call("/auth/logout", method="POST", token=token)
    assert status == 200, f"/auth/logout failed: {logout_res}"
    print("3. Logged out via /auth/logout (server-side blacklist applied).")

    # 4. Test reuse against EVERY protected endpoint
    endpoints = [
        ("GET", "/auth/me", None),
        ("GET", "/documents", None),
        ("POST", "/documents/upload", {"title": "x"}),
        ("GET", "/documents/00000000-0000-0000-0000-000000000000", None),
        ("PATCH", "/documents/00000000-0000-0000-0000-000000000000", {"title": "x"}),
        ("POST", "/documents/00000000-0000-0000-0000-000000000000/permissions", {"grantee_email": "x"}),
        ("GET", "/documents/00000000-0000-0000-0000-000000000000/download", None),
        ("DELETE", "/documents/00000000-0000-0000-0000-000000000000/permissions/x", None),
        ("DELETE", "/documents/00000000-0000-0000-0000-000000000000", None),
        ("GET", "/audit", None),
        ("GET", "/audit/verify", None),
        ("GET", "/audit/metrics", None),
    ]

    print("4. Testing revoked token against all 12 protected endpoints:")
    for method, path, dummy_body in endpoints:
        status, res = api_call(path, method=method, token=token, body=dummy_body)
        detail = res.get("detail", "")
        assert status == 401, f"Expected 401 for {method} {path}, got {status}: {res}"
        assert "revoked" in detail.lower(), f"Expected revoked detail message for {method} {path}, got {detail}"
        print(f"   [{method} {path}] -> HTTP 401 Unauthorized ({detail}) [PASS]")

    # 5. Test from an independent Playwright browser context
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        # Create fresh isolated context
        context = browser.new_context()
        page = context.new_page()
        # Set localStorage with revoked token
        page.goto("http://127.0.0.1:5173")
        page.evaluate(f"localStorage.setItem('tv_token', '{token}')")
        # Attempt to fetch /api/auth/me from inside browser page context
        result = page.evaluate("""async () => {
            const res = await fetch('/api/auth/me', {
                headers: { 'Authorization': 'Bearer ' + localStorage.getItem('tv_token') }
            });
            return { status: res.status, body: await res.json() };
        }""")
        assert result["status"] == 401
        assert "revoked" in result["body"]["detail"].lower()
        print("5. Independent browser context reuse test: HTTP 401 [PASS]")
        browser.close()

    # 6. Verify blacklist persistence across backend restarts
    print("6. Verifying blacklist persistence across server restarts...")
    # Find backend PID and restart it
    out = subprocess.check_output('netstat -ano | findstr 127.0.0.1:8000', shell=True).decode()
    for line in out.strip().splitlines():
        if "LISTENING" in line:
            pid = line.strip().split()[-1]
            subprocess.run(f"taskkill /F /PID {pid}", shell=True, capture_output=True)
            print(f"   Killed backend process {pid}")

    time.sleep(1)
    # Start fresh backend
    bg_cmd = "start /B C:/Users/Snuhith/projects/TrustVault/backend/venv/Scripts/python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000"
    subprocess.Popen(bg_cmd, shell=True, cwd="C:/Users/Snuhith/projects/TrustVault/backend")
    
    # Wait for backend to recover
    for _ in range(30):
        time.sleep(0.5)
        try:
            status, _ = api_call("/auth/login", method="POST", body={
                "username_or_email": "admin@trustvault.io",
                "password": "AdminPass2026!"
            })
            if status == 200:
                print("   Backend restarted and online.")
                break
        except:
            pass

    # Verify old token STILL rejected post-restart
    status, res = api_call("/auth/me", token=token)
    assert status == 401, f"Expected 401 after restart, got {status}: {res}"
    assert "revoked" in res.get("detail", "").lower()
    print("   Post-restart token query: HTTP 401 Unauthorized (Blacklist persistent in DB) [PASS]")

    print("ALL JWT LOGOUT INVALIDATION & PERSISTENCE TESTS PASSED SUCCESSFULLY!")

if __name__ == "__main__":
    main()
