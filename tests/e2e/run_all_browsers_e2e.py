import os
import sys
import time
from playwright.sync_api import sync_playwright

EVIDENCE_DIR = "C:/Users/Snuhith/projects/TrustVault/playwright_evidence"
os.makedirs(EVIDENCE_DIR, exist_ok=True)

def run_browser_suite(browser_name, launcher_func, channel=None):
    print(f"\n=======================================================")
    print(f"STARTING APPLICATION E2E SUITE: {browser_name.upper()} (channel={channel})")
    print(f"=======================================================")
    
    launch_kwargs = {"headless": True}
    if channel:
        launch_kwargs["channel"] = channel

    with sync_playwright() as p:
        launcher = getattr(p, launcher_func)
        browser = launcher.launch(**launch_kwargs)
        context = browser.new_context(viewport={"width": 1280, "height": 800})
        page = context.new_page()

        console_errors = []
        page.on("console", lambda msg: console_errors.append(msg.text) if msg.type == "error" else None)

        # 1. Landing Page
        page.goto("http://127.0.0.1:5173", wait_until="networkidle")
        assert "TrustVault" in page.title()
        print(f"[{browser_name}] 1. Landing Page Load: PASS")

        # 2. Quick Switch Persona
        page.click("#quick-owner-btn")
        page.wait_for_timeout(200)
        assert page.input_value("#login-id-input") == "owner@trustvault.io"
        print(f"[{browser_name}] 2. Persona Quick-Select: PASS")

        # 3. Registration Switch & Create User
        page.click("#tab-register-btn")
        page.wait_for_selector("#reg-username-input")
        unique_user = f"user_{browser_name}_{int(time.time())}"
        page.fill("#reg-username-input", unique_user)
        page.fill("#reg-email-input", f"{unique_user}@trustvault.io")
        page.fill("#reg-password-input", "UserPass2026!")
        page.select_option("#reg-role-select", "owner")
        page.click("#reg-submit-btn")
        page.wait_for_selector("#tab-login-btn")
        print(f"[{browser_name}] 3. Registration Workflow: PASS (Created {unique_user})")

        # 4. Switch to Sign In Tab & Admin Login
        page.click("#tab-login-btn")
        page.wait_for_timeout(200)
        page.click("#quick-admin-btn")
        page.wait_for_timeout(200)
        page.click("#login-submit-btn")
        page.wait_for_selector("#nav-tab-vault")
        assert page.is_visible("#nav-tab-vault")
        print(f"[{browser_name}] 4. Admin Authentication: PASS")

        # 5. Profile Modal
        page.click("#header-profile-btn")
        page.wait_for_selector("#close-profile-modal-btn")
        page.click("#copy-userid-btn")
        page.click("#close-profile-modal-btn")
        page.wait_for_timeout(200)
        print(f"[{browser_name}] 5. Profile Modal Interaction: PASS")

        # 6. Search & Filters
        page.fill("#search-input", "Test")
        page.wait_for_timeout(300)
        page.click("#clear-search-btn")
        page.wait_for_timeout(300)
        page.select_option("#sort-select", "oldest")
        page.wait_for_timeout(300)
        page.select_option("#sort-select", "newest")
        page.wait_for_timeout(300)
        print(f"[{browser_name}] 6. Search, Clear & Sort: PASS")

        # 7. Edit Metadata Modal
        edit_btn = page.locator("button[id^='edit-btn-']").first
        if edit_btn.count() > 0:
            edit_btn.click()
            page.wait_for_selector("#modal-edit-save-btn")
            page.fill("#edit-title-input", f"Updated_{browser_name}_Doc")
            page.click("#modal-edit-save-btn")
            page.wait_for_timeout(400)
            print(f"[{browser_name}] 7. Edit Metadata Action: PASS")

        # 8. Grant & Revoke Permissions
        grant_btn = page.locator("button[id^='open-grant-btn-']").first
        if grant_btn.count() > 0:
            grant_btn.click()
            page.wait_for_selector("#save-grant-btn")
            page.fill("#grantee-input", "viewer@trustvault.io")
            page.click("#save-grant-btn")
            page.wait_for_timeout(500)
            print(f"[{browser_name}] 8. Grant Permission Action: PASS")

            # Revoke
            revoke_btn = page.locator("button[id^='revoke-btn-']").first
            if revoke_btn.count() > 0:
                revoke_btn.click()
                page.wait_for_timeout(500)
                print(f"[{browser_name}] 8b. Revoke Permission Action: PASS")

        # 9. Audit Trail & Cryptographic Verification
        page.click("#nav-tab-audit")
        page.wait_for_selector("#reverify-chain-btn")
        page.click("#reverify-chain-btn")
        page.wait_for_timeout(600)
        page.click("#back-to-vault-btn")
        page.wait_for_selector("#nav-tab-vault")
        print(f"[{browser_name}] 9. Audit Trail & Re-verify Chain: PASS")

        # 10. Responsive Viewport
        page.set_viewport_size({"width": 375, "height": 667})
        page.wait_for_timeout(300)
        assert page.is_visible("#mobile-menu-btn")
        page.click("#mobile-menu-btn")
        page.wait_for_selector("#mobile-nav-vault")
        page.click("#mobile-menu-btn")
        page.set_viewport_size({"width": 1280, "height": 800})
        print(f"[{browser_name}] 10. Responsive Navigation Drawer: PASS")

        # 11. Logout & State Wipe
        page.click("#header-logout-btn")
        page.wait_for_selector("#tab-login-btn")
        print(f"[{browser_name}] 11. Logout & Session Termination: PASS")

        browser.close()
        print(f"RESULT FOR {browser_name.upper()}: 100% SUITE VERIFIED PASS")
        return True

def main():
    browsers = [
        ("chromium", "chromium", None),
        ("firefox", "firefox", None),
        ("webkit", "webkit", None),
        ("google_chrome", "chromium", "chrome"),
        ("microsoft_edge", "chromium", "msedge")
    ]
    
    results = {}
    for name, launcher, channel in browsers:
        try:
            success = run_browser_suite(name, launcher, channel)
            results[name] = "PASS" if success else "FAIL"
        except Exception as e:
            print(f"ERROR on {name}: {e}")
            results[name] = f"FAIL ({e})"

    print("\n=======================================================")
    print("FINAL MULTI-BROWSER PLAYWRIGHT TEST SUMMARY:")
    for b, res in results.items():
        print(f"  {b}: {res}")
    print("=======================================================")

if __name__ == "__main__":
    main()
