import os
import sys
import time
from playwright.sync_api import sync_playwright

EVIDENCE_DIR = "C:/Users/Snuhith/projects/TrustVault/playwright_evidence/responsive"
os.makedirs(EVIDENCE_DIR, exist_ok=True)

VIEWPORTS = [
    {"name": "320px_mobile_legacy", "width": 320, "height": 568},
    {"name": "375px_mobile_se", "width": 375, "height": 667},
    {"name": "390px_mobile_iphone14", "width": 390, "height": 844},
    {"name": "430px_mobile_promax", "width": 430, "height": 932},
    {"name": "768px_tablet_portrait", "width": 768, "height": 1024},
    {"name": "1024px_tablet_landscape", "width": 1024, "height": 768},
    {"name": "1280px_desktop_standard", "width": 1280, "height": 800},
    {"name": "1440px_desktop_wide", "width": 1440, "height": 900},
    {"name": "1920px_desktop_fhd", "width": 1920, "height": 1080},
]

results = []

def test_viewports():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        
        for vp in VIEWPORTS:
            context = browser.new_context(viewport={"width": vp["width"], "height": vp["height"]})
            page = context.new_page()

            # 1. Test Auth Screen
            page.goto("http://127.0.0.1:5173", wait_until="networkidle")
            scroll_width = page.evaluate("() => document.documentElement.scrollWidth")
            inner_width = page.evaluate("() => window.innerWidth")
            overflow = scroll_width > inner_width
            page.screenshot(path=f"{EVIDENCE_DIR}/{vp['name']}_auth.png")

            # 2. Login as Admin
            page.click("#quick-admin-btn")
            page.click("#login-submit-btn")
            if vp["width"] < 768:
                page.wait_for_selector("#mobile-menu-btn", timeout=10000)
            else:
                page.wait_for_selector("#nav-tab-vault", timeout=10000)

            vault_scroll = page.evaluate("() => document.documentElement.scrollWidth")
            vault_overflow = vault_scroll > inner_width
            page.screenshot(path=f"{EVIDENCE_DIR}/{vp['name']}_vault.png")

            # 3. Test Mobile Drawer if on mobile (<768px)
            if vp["width"] < 768:
                assert page.is_visible("#mobile-menu-btn"), f"Mobile hamburger missing on {vp['name']}"
                page.click("#mobile-menu-btn")
                page.wait_for_selector("#mobile-nav-vault")
                page.screenshot(path=f"{EVIDENCE_DIR}/{vp['name']}_drawer.png")
                page.click("#mobile-menu-btn")

            status = "PASS" if not overflow and not vault_overflow else "FAIL"
            details = f"Auth scrollWidth={scroll_width} (target={inner_width}), Vault scrollWidth={vault_scroll}"
            print(f"[{status}] {vp['name']}: {details}")
            results.append({
                "viewport": vp["name"],
                "width": vp["width"],
                "height": vp["height"],
                "status": status,
                "overflow_auth": overflow,
                "overflow_vault": vault_overflow,
                "details": details
            })

            context.close()
        browser.close()

if __name__ == "__main__":
    test_viewports()
