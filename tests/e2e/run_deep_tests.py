import os, sys, time, json, urllib.request, urllib.error
from playwright.sync_api import sync_playwright

API_BASE = "http://127.0.0.1:8000/api"
EVIDENCE_DIR = "C:/Users/Snuhith/projects/TrustVault/playwright_evidence"

def api_call(path, method="GET", data=None, token=None):
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    body = json.dumps(data).encode() if data else None
    req = urllib.request.Request(f"{API_BASE}{path}", data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req) as res:
            try:
                return res.status, json.loads(res.read().decode())
            except:
                return res.status, {"status": "ok"}
    except urllib.error.HTTPError as e:
        err_body = e.read().decode()
        try:
            return e.code, json.loads(err_body)
        except:
            return e.code, {"detail": err_body}

print("=== 1. SECURITY & IDOR TESTING ===")
# Login as Owner Alice
s, r = api_call("/auth/login", "POST", {"username_or_email": "owner@trustvault.io", "password": "OwnerPass2026!"})
assert s == 200
alice_token = r["access_token"]
alice_id = r["user"]["id"]

# Login as Viewer Bob
s, r = api_call("/auth/login", "POST", {"username_or_email": "viewer@trustvault.io", "password": "ViewerPass2026!"})
assert s == 200
bob_token = r["access_token"]
bob_id = r["user"]["id"]

# Login as Admin
s, r = api_call("/auth/login", "POST", {"username_or_email": "admin@trustvault.io", "password": "AdminPass2026!"})
assert s == 200
admin_token = r["access_token"]

# Alice gets her docs
s, alice_docs = api_call("/documents", "GET", token=alice_token)
assert s == 200
alice_doc = alice_docs[0]
print(f"Alice owns document: {alice_doc['id']} ('{alice_doc['title']}')")

# Step 1: Revoke Bob's access first so he has zero permissions
api_call(f"/documents/{alice_doc['id']}/permissions/{bob_id}", "DELETE", token=alice_token)

# Bob attempts to GET, PATCH, DELETE Alice's document without permission -> Must return 404/403
s, r = api_call(f"/documents/{alice_doc['id']}", "GET", token=bob_token)
print(f"Bob GET Alice doc without perm: status={s}")
assert s == 404, "Security breach: Bob read document details without permission!"

s, r = api_call(f"/documents/{alice_doc['id']}", "PATCH", {"title": "Hacked Title"}, token=bob_token)
print(f"Bob PATCH Alice doc without perm: status={s}")
assert s in [403, 404], "Security breach: Bob patched document without permission!"

s, r = api_call(f"/documents/{alice_doc['id']}", "DELETE", token=bob_token)
print(f"Bob DELETE Alice doc without perm: status={s}")
assert s in [403, 404], "Security breach: Bob deleted document without permission!"

# Bob attempts to access admin metrics
s, r = api_call("/audit/metrics", "GET", token=bob_token)
print(f"Bob GET /audit/metrics result: status={s}")
assert s == 403, "Security breach: Bob accessed Admin metrics!"

# Bob attempts to access audit verification
s, r = api_call("/audit/verify", "GET", token=bob_token)
print(f"Bob GET /audit/verify result: status={s}")
assert s == 403, "Security breach: Bob accessed Admin audit verify!"

# Step 2: Grant Bob Read-Only access (can_edit=False)
s, r = api_call(f"/documents/{alice_doc['id']}/permissions", "POST", {"grantee_email": "viewer@trustvault.io", "can_edit": False}, token=alice_token)
assert s == 200
print("Alice granted Bob read-only permission")

# Bob can download
s, r = api_call(f"/documents/{alice_doc['id']}/download", "GET", token=bob_token)
print(f"Bob download with read-only perm: status={s}")
assert s == 200

# Bob attempts to PATCH metadata with read-only perm -> Must be 403 Forbidden!
s, r = api_call(f"/documents/{alice_doc['id']}", "PATCH", {"title": "Bob Illegal Edit"}, token=bob_token)
print(f"Bob PATCH with read-only perm: status={s}, detail={r.get('detail')}")
assert s == 403, f"Security breach: Read-only viewer patched metadata! Status={s}"

# Step 3: Revoke Bob's access
s, r = api_call(f"/documents/{alice_doc['id']}/permissions/{bob_id}", "DELETE", token=alice_token)
assert s == 200
print("Alice revoked Bob's permission")

# Bob immediately tries to download again -> Must be 403 Forbidden
s, r = api_call(f"/documents/{alice_doc['id']}/download", "GET", token=bob_token)
print(f"Bob download after revoke result: status={s}, detail={r.get('detail')}")
assert s in [403, 404], "Security breach: Bob downloaded file after permission revocation!"

print("=== 2. RESPONSIVE VIEWPORT PLAYWRIGHT AUDIT ===")
viewports = [
    (320, 568, "mobile_320"),
    (375, 667, "mobile_375"),
    (390, 844, "mobile_390"),
    (430, 932, "mobile_430"),
    (768, 1024, "tablet_768"),
    (1024, 768, "laptop_1024"),
    (1280, 800, "desktop_1280"),
    (1440, 900, "desktop_1440"),
    (1920, 1080, "large_1920")
]

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    for width, height, name in viewports:
        page = browser.new_page(viewport={"width": width, "height": height})
        page.goto("http://127.0.0.1:5173", wait_until="networkidle")
        scroll_width = page.evaluate("document.documentElement.scrollWidth")
        client_width = page.evaluate("document.documentElement.clientWidth")
        overflow = scroll_width > client_width
        print(f"Viewport {width}x{height} ({name}): scrollWidth={scroll_width}, clientWidth={client_width}, overflow={overflow}")
        assert not overflow, f"Horizontal overflow detected at {width}px!"
        page.screenshot(path=f"{EVIDENCE_DIR}/viewport_{name}.png")
        page.close()
    browser.close()

print("ALL_DEEP_TESTS_VERIFIED_PASS")
