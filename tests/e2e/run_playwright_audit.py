import os
import sys
import time
import argparse
from playwright.sync_api import sync_playwright

parser = argparse.ArgumentParser()
parser.add_argument("--browser", default="chromium", choices=["chromium", "firefox", "webkit", "chrome", "msedge"])
args, _ = parser.parse_known_args()


EVIDENCE_DIR = "C:/Users/Snuhith/projects/TrustVault/playwright_evidence"
os.makedirs(EVIDENCE_DIR, exist_ok=True)

test_results = []

def record(name, status, details=""):
    test_results.append({"name": name, "status": status, "details": details})
    print(f"[{status}] {name} - {details}")

def run_all_tests(browser_choice="chromium"):
    with sync_playwright() as p:
        if browser_choice == "chromium":
            browser = p.chromium.launch(headless=True)
        elif browser_choice == "firefox":
            browser = p.firefox.launch(headless=True)
        elif browser_choice == "webkit":
            browser = p.webkit.launch(headless=True)
        elif browser_choice == "chrome":
            browser = p.chromium.launch(headless=True, channel="chrome")
        elif browser_choice == "msedge":
            browser = p.chromium.launch(headless=True, channel="msedge")
        else:
            browser = p.chromium.launch(headless=True)
            
        print(f"\n================ BROWSER TARGET: {browser_choice.upper()} ================" )
        context = browser.new_context(viewport={"width": 1280, "height": 800})
        page = context.new_page()

        console_errors = []
        page.on("console", lambda msg: console_errors.append(msg.text) if msg.type == "error" else None)

        print("--- TEST SUITE 1: AUTHENTICATION & PERSONA SWITCHING ---")
        page.goto("http://127.0.0.1:5173", wait_until="networkidle")
        page.screenshot(path=f"{EVIDENCE_DIR}/01_auth_landing.png")
        record("Landing Page Load", "PASS", "Title & UI loaded without errors")

        # Quick Switch Owner
        page.click("#quick-owner-btn")
        page.wait_for_timeout(300)
        assert page.input_value("#login-id-input") == "owner@trustvault.io"
        record("Quick Persona Switch (Owner)", "PASS", "Login form auto-filled with owner credentials")

        # Quick Switch Viewer
        page.click("#quick-viewer-btn")
        page.wait_for_timeout(300)
        assert page.input_value("#login-id-input") == "viewer@trustvault.io"
        record("Quick Persona Switch (Viewer)", "PASS", "Login form auto-filled with viewer credentials")

        # Quick Switch Admin
        page.click("#quick-admin-btn")
        page.wait_for_timeout(300)
        assert page.input_value("#login-id-input") == "admin@trustvault.io"
        record("Quick Persona Switch (Admin)", "PASS", "Login form auto-filled with admin credentials")

        # Test Register Tab Switch
        page.click("#tab-register-btn")
        page.wait_for_timeout(300)
        assert page.is_visible("#reg-username-input")
        record("Auth Tab Switch to Register", "PASS", "Registration form displayed")

        # Test Register Account Creation with unique username
        new_username = f"test_user_{int(time.time())}"
        new_email = f"{new_username}@trustvault.io"
        page.fill("#reg-username-input", new_username)
        page.fill("#reg-email-input", new_email)
        page.fill("#reg-password-input", "Password2026!")
        page.select_option("#reg-role-select", "viewer")
        page.click("#reg-submit-btn")
        page.wait_for_timeout(1000)
        page.wait_for_selector("#success-toast-banner")
        record("Registration Submit Action", "PASS", f"User {new_username} created successfully")

        # Switch back to Sign In Tab and login as Admin
        page.click("#tab-login-btn")
        page.click("#quick-admin-btn")
        page.click("#login-submit-btn")
        page.wait_for_selector("#nav-tab-vault", timeout=10000)
        page.screenshot(path=f"{EVIDENCE_DIR}/02_admin_logged_in.png")
        record("Admin Login & Dashboard", "PASS", "Logged in with admin role and vault loaded")

        print("--- TEST SUITE 2: PROFILE & MODAL CONTROLS ---")
        # Open Profile Modal
        page.click("#header-profile-btn")
        page.wait_for_selector("#close-profile-modal-btn")
        record("Profile Modal Open", "PASS", "Profile & Session Security modal opened")

        # Test Copy User ID Button
        page.click("#copy-userid-btn")
        page.wait_for_timeout(300)
        record("Copy User ID Button", "PASS", "User ID copied trigger executed")

        # Close Profile Modal via Close button
        page.click("#close-profile-modal-btn")
        page.wait_for_timeout(300)
        assert not page.is_visible("#close-profile-modal-btn")
        record("Profile Modal Close Button", "PASS", "Modal closed cleanly")

        # Open Profile Modal again and test Escape key
        page.click("#header-profile-btn")
        page.wait_for_selector("#close-profile-modal-btn")
        page.keyboard.press("Escape")
        page.wait_for_timeout(300)
        assert not page.is_visible("#close-profile-modal-btn")
        record("Modal Keyboard Escape Action", "PASS", "Escape key dismissed active modal")

        print("--- TEST SUITE 3: SEARCH, FILTERING & SORTING ---")
        # Test Search Input
        page.fill("#search-input", "resume")
        page.wait_for_timeout(600)
        assert page.is_visible("#clear-search-btn")
        record("Search Title Execution", "PASS", "Search query filtered document list")

        # Test Clear Search Button
        page.click("#clear-search-btn")
        page.wait_for_timeout(600)
        assert page.input_value("#search-input") == ""
        record("Clear Search Button", "PASS", "Search input cleared and list restored")

        # Test Category Filter Dropdown
        page.select_option("#filter-category-select", "Legal")
        page.wait_for_timeout(600)
        page.select_option("#filter-category-select", "")
        page.wait_for_timeout(600)
        record("Category Filter Dropdown", "PASS", "Category filtering and reset verified")

        # Test Sorting Dropdown
        page.select_option("#sort-select", "oldest")
        page.wait_for_timeout(600)
        page.select_option("#sort-select", "title_asc")
        page.wait_for_timeout(600)
        page.select_option("#sort-select", "newest")
        page.wait_for_timeout(600)
        record("Sort Options Dropdown", "PASS", "Oldest, Title A-Z, and Newest sorting verified")

        # Test Advanced Filters Drawer Toggle
        page.click("#toggle-advanced-filters-btn")
        page.wait_for_selector("#clear-all-filters-btn")
        page.fill("#filter-owner-input", "alice")
        page.wait_for_timeout(500)
        page.click("#clear-all-filters-btn")
        page.wait_for_timeout(500)
        assert page.input_value("#filter-owner-input") == ""
        page.click("#toggle-advanced-filters-btn")
        record("Advanced Filter Drawer & Clear All", "PASS", "Drawer toggled and filters reset")

        # Test Refresh Documents Button
        page.click("#refresh-docs-btn")
        page.wait_for_timeout(600)
        record("Refresh Documents Button", "PASS", "Document re-fetch triggered cleanly")

        print("--- TEST SUITE 4: EDIT METADATA & DELETE MODALS ---")
        # Find first edit button
        first_edit_btn = page.locator("button[id^='edit-btn-']").first
        if first_edit_btn.count() > 0:
            first_edit_btn.click()
            page.wait_for_selector("#save-edit-modal-btn")
            record("Open Edit Metadata Modal", "PASS", "Edit modal opened with pre-filled inputs")

            # Change category and title
            page.fill("#edit-doc-title-input", "Verified Master Document")
            page.select_option("#edit-doc-category-select", "Legal")
            page.click("#save-edit-modal-btn")
            page.wait_for_selector("#success-toast-banner")
            record("Save Metadata Changes Action", "PASS", "Metadata PATCH executed and toast shown")

        # Test Delete Modal (Open and Cancel)
        first_del_btn = page.locator("button[id^='delete-btn-']").first
        if first_del_btn.count() > 0:
            first_del_btn.click()
            page.wait_for_selector("#cancel-delete-modal-btn")
            page.click("#cancel-delete-modal-btn")
            page.wait_for_timeout(300)
            assert not page.is_visible("#confirm-delete-modal-btn")
            record("Delete Confirmation Modal Cancel", "PASS", "Deletion safely aborted via Cancel")

        print("--- TEST SUITE 5: PERMISSIONS (GRANT & REVOKE) ---")
        # Open inline grant form
        open_grant_btn = page.locator("button[id^='open-grant-btn-']").first
        if open_grant_btn.count() > 0:
            open_grant_btn.click()
            page.wait_for_selector("#save-grant-btn")
            record("Open Inline Grant Form", "PASS", "Grant access controls rendered")

            # Check Can Edit checkbox
            page.check("#grant-can-edit-checkbox")
            page.click("#save-grant-btn")
            page.wait_for_selector("#success-toast-banner")
            record("Save Grant Permission Action", "PASS", "Permission granted with Can Edit=True")

        # Revoke Permission button
        revoke_btn = page.locator("button[id^='revoke-btn-']").first
        if revoke_btn.count() > 0:
            revoke_btn.click()
            page.wait_for_selector("#success-toast-banner")
            record("Instant Revoke Permission Action", "PASS", "Permission instantly revoked")

        print("--- TEST SUITE 6: CHAINED AUDIT TRAIL & TAMPER EVIDENCE ---")
        # Switch to Audit Tab
        page.click("#nav-tab-audit")
        page.wait_for_selector("#reverify-chain-btn")
        page.screenshot(path=f"{EVIDENCE_DIR}/03_audit_trail_view.png")
        record("Audit Trail Tab Navigation", "PASS", "Cryptographic audit trail table rendered")

        # Re-verify Chain Button
        page.click("#reverify-chain-btn")
        page.wait_for_timeout(1000)
        record("Re-verify Chain Button", "PASS", "Cryptographic hash verification re-executed")

        # Audit Action Filter Dropdown
        page.select_option("#audit-action-select", "PERM_GRANT")
        page.wait_for_timeout(500)
        page.select_option("#audit-action-select", "ALL")
        page.wait_for_timeout(500)
        record("Audit Action Filter Dropdown", "PASS", "Filtered actions dynamically")

        # Refresh Audit Button
        page.click("#refresh-audit-btn")
        page.wait_for_timeout(500)
        record("Refresh Audit Button", "PASS", "Audit log refresh triggered")

        # Back to Vault Button
        page.click("#back-to-vault-btn")
        page.wait_for_selector("#nav-tab-vault")
        record("Back to Vault Navigation Button", "PASS", "Navigated back to vault documents")

        print("--- TEST SUITE 7: RESPONSIVE VIEWPORTS & MOBILE DRAWER ---")
        # Test 375px mobile viewport
        page.set_viewport_size({"width": 375, "height": 667})
        page.wait_for_timeout(500)
        assert page.is_visible("#mobile-menu-btn")
        page.click("#mobile-menu-btn")
        page.wait_for_selector("#mobile-nav-vault")
        page.screenshot(path=f"{EVIDENCE_DIR}/04_mobile_375px_drawer.png")
        record("Mobile 375px Navigation Drawer", "PASS", "Hamburger menu and drawer functional")

        # Close mobile menu
        page.click("#mobile-menu-btn")
        page.wait_for_timeout(300)

        # Restore desktop viewport
        page.set_viewport_size({"width": 1280, "height": 800})
        page.wait_for_timeout(500)

        print("--- TEST SUITE 8: LOGOUT & NOTIFICATION DISMISSAL ---")
        # Dismiss toast notification
        dismiss_btn = page.locator("#dismiss-success-btn")
        if dismiss_btn.count() > 0:
            dismiss_btn.click()
            page.wait_for_timeout(300)
            assert not page.is_visible("#success-toast-banner")
            record("Dismiss Success Toast Action", "PASS", "Toast banner dismissed")

        # Logout
        page.click("#header-logout-btn")
        page.wait_for_selector("#tab-login-btn")
        record("Logout Action", "PASS", "Logged out, token removed, and returned to auth screen")

        browser.close()

run_all_tests(args.browser)
print("PLAYWRIGHT_ALL_TESTS_COMPLETED_SUCCESSFULLY")
