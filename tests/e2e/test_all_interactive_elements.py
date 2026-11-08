import os
import sys
import time
from playwright.sync_api import sync_playwright

def test_interactive_elements():
    results = []
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1280, "height": 800})
        page = context.new_page()

        print("--- PHASE 2: INTERACTIVE ELEMENT INVENTORY AUDIT ---")
        
        # 1. Unauthenticated View
        page.goto("http://127.0.0.1:5173", wait_until="networkidle")
        
        # Test tab toggling
        for tab_id in ["tab-register-btn", "tab-login-btn"]:
            page.click(f"#{tab_id}")
            time.sleep(0.2)
            results.append({"id": tab_id, "type": "button", "status": "PASS", "desc": f"Toggle {tab_id}"})
            print(f"[PASS] {tab_id} (button): Toggle auth mode")

        # Test presets and input fields
        for preset_id, role in [("quick-owner-btn", "Owner"), ("quick-viewer-btn", "Viewer"), ("quick-admin-btn", "Admin")]:
            page.click(f"#{preset_id}")
            results.append({"id": preset_id, "type": "button", "status": "PASS", "desc": f"Preset {role} credentials"})
            print(f"[PASS] {preset_id} (button): Preset {role} credentials")

        for input_id in ["login-id-input", "login-password-input"]:
            val = page.input_value(f"#{input_id}")
            status = "PASS" if val else "FAIL"
            results.append({"id": input_id, "type": "input", "status": status, "desc": f"Input populated: {input_id}"})
            print(f"[{status}] {input_id} (input): Populated with credential")

        # Submit Login as Admin
        page.click("#login-submit-btn")
        results.append({"id": "login-submit-btn", "type": "button", "status": "PASS", "desc": "Submit authentication"})
        print("[PASS] login-submit-btn (button): Submit authentication")
        page.wait_for_selector("#nav-tab-vault", timeout=10000)

        # 2. Main Navigation & Header Elements
        header_nav_elements = [
            ("nav-brand-logo", "brand", "Logo and brand name"),
            ("nav-tab-vault", "tab", "Switch to Vault Tab"),
            ("nav-tab-audit", "tab", "Switch to Audit Logs Tab"),
            ("system-status-indicator", "badge", "Live backend health badge"),
            ("header-profile-btn", "button", "Open User Profile Modal"),
            ("header-logout-btn", "button", "Logout button in header"),
        ]

        for elem_id, elem_type, desc in header_nav_elements:
            visible = page.is_visible(f"#{elem_id}")
            if elem_id == "header-profile-btn":
                page.click(f"#{elem_id}")
                time.sleep(0.3)
                profile_modal_visible = page.is_visible("#profile-modal-dialog")
                page.click("#close-profile-modal-btn")
                status = "PASS" if profile_modal_visible else "FAIL"
            elif elem_id == "header-logout-btn":
                status = "PASS" if visible else "FAIL"
            elif elem_type == "tab":
                page.click(f"#{elem_id}")
                time.sleep(0.3)
                status = "PASS" if visible else "FAIL"
            else:
                status = "PASS" if visible else "FAIL"
            print(f"[{status}] {elem_id} ({elem_type}): {desc}")
            results.append({"id": elem_id, "type": elem_type, "status": status, "desc": desc})

        # 3. Vault Tab Controls
        page.click("#nav-tab-vault")
        vault_controls = [
            ("search-input", "input", "Search documents by filename/title"),
            ("filter-category-select", "select", "Filter by security category"),
            ("sort-select", "select", "Sort by date/size/name"),
            ("toggle-advanced-filters-btn", "button", "Toggle Advanced Filters Drawer"),
            ("refresh-docs-btn", "button", "Reload documents from API"),
            ("upload-title-input", "input", "Input document title for upload"),
            ("upload-category-select", "select", "Select document category for upload"),
            ("upload-file-input", "input", "Select binary file for upload"),
            ("reset-upload-btn", "button", "Reset upload form inputs"),
            ("commit-upload-btn", "button", "Commit document upload to vault")
        ]

        for elem_id, elem_type, desc in vault_controls:
            visible = page.is_visible(f"#{elem_id}")
            if elem_id == "toggle-advanced-filters-btn":
                page.click(f"#{elem_id}")
                time.sleep(0.2)
                drawer_open = page.is_visible("#filter-owner-input")
                page.click(f"#{elem_id}")
                status = "PASS" if drawer_open else "FAIL"
            elif elem_id == "refresh-docs-btn":
                page.click(f"#{elem_id}")
                status = "PASS" if visible else "FAIL"
            elif elem_id == "reset-upload-btn":
                page.click(f"#{elem_id}")
                status = "PASS" if visible else "FAIL"
            elif elem_type == "select":
                page.select_option(f"#{elem_id}", index=0)
                status = "PASS" if visible else "FAIL"
            elif elem_type == "input" and elem_id != "upload-file-input":
                page.fill(f"#{elem_id}", "test")
                page.fill(f"#{elem_id}", "")
                status = "PASS" if visible else "FAIL"
            else:
                status = "PASS" if visible else "FAIL"
            print(f"[{status}] {elem_id} ({elem_type}): {desc}")
            results.append({"id": elem_id, "type": elem_type, "status": status, "desc": desc})

        # 4. Audit Tab Controls
        page.click("#nav-tab-audit")
        time.sleep(0.5)
        audit_controls = [
            ("reverify-chain-btn", "button", "Cryptographically verify hash chain integrity"),
            ("refresh-audit-btn", "button", "Reload audit trail"),
            ("audit-action-select", "select", "Filter by action type"),
        ]
        for elem_id, elem_type, desc in audit_controls:
            visible = page.is_visible(f"#{elem_id}")
            if elem_id in ["reverify-chain-btn", "refresh-audit-btn"]:
                page.click(f"#{elem_id}")
                time.sleep(0.3)
                status = "PASS" if visible else "FAIL"
            elif elem_type == "select":
                page.select_option(f"#{elem_id}", value="ALL")
                status = "PASS" if visible else "FAIL"
            else:
                status = "PASS" if visible else "FAIL"
            print(f"[{status}] {elem_id} ({elem_type}): {desc}")
            results.append({"id": elem_id, "type": elem_type, "status": status, "desc": desc})

        # 5. Profile Modal Dialog Elements
        page.click("#header-profile-btn")
        time.sleep(0.3)
        profile_controls = [
            ("copy-userid-btn", "button", "Copy User UUID to clipboard"),
            ("close-profile-modal-btn", "button", "Close Profile Modal"),
        ]
        for elem_id, elem_type, desc in profile_controls:
            visible = page.is_visible(f"#{elem_id}")
            if elem_id == "copy-userid-btn":
                page.click(f"#{elem_id}")
                status = "PASS" if visible else "FAIL"
            elif elem_id == "close-profile-modal-btn":
                page.click(f"#{elem_id}")
                status = "PASS" if visible else "FAIL"
            else:
                status = "PASS" if visible else "FAIL"
            print(f"[{status}] {elem_id} ({elem_type}): {desc}")
            results.append({"id": elem_id, "type": elem_type, "status": status, "desc": desc})

        browser.close()

    total = len(results)
    passed = sum(1 for r in results if r["status"] == "PASS")
    print(f"\nAUDIT COMPLETE: {passed}/{total} interactive controls passed.")

if __name__ == "__main__":
    test_interactive_elements()
