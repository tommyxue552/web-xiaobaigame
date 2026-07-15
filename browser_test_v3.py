# -*- coding: utf-8 -*-
"""v0.8.1A Final Browser Acceptance Test - v3"""
import os, sys, json, time
sys.stdout.reconfigure(encoding='utf-8')

from playwright.sync_api import sync_playwright

BASE = "http://localhost:8000"
OUT_DIR = r"C:\Users\xueta\Documents\web-xiaobaigame\screenshots\v081a_test"
os.makedirs(OUT_DIR, exist_ok=True)

results = []

def test_page(name, url, checks=None, external_ok=True):
    """Test a page with screenshot, console errors, content checks."""
    entry = {"name": name, "url": url, "passed": True, "errors": [], "warnings": []}
    console_msgs = []
    network_fails = []
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1280, "height": 800})
        page = context.new_page()
        
        page.on("console", lambda msg: console_msgs.append(f"[{msg.type}] {msg.text}")
)
        page.on("pageerror", lambda err: entry["errors"].append(f"JS ERROR: {err}"))
        page.on("requestfailed", lambda req: network_fails.append(req.url))
        
        try:
            resp = page.goto(url, wait_until="networkidle", timeout=15000)
            time.sleep(0.5)
        except Exception as e:
            entry["passed"] = False
            entry["errors"].append(f"GOTO FAILED: {e}")
            browser.close()
            results.append(entry)
            return entry
        
        entry["http_status"] = resp.status if resp else "N/A"
        
        # Console errors
        errors = [m for m in console_msgs if m.startswith("[error]")]
        if errors:
            entry["passed"] = False
            entry["errors"].extend(errors)
        
        # Network failures - external URLs are warnings, internal are errors
        for nf in network_fails:
            if "localhost" in nf or "127.0.0.1" in nf:
                entry["passed"] = False
                entry["errors"].append(f"INTERNAL FAIL: {nf}")
            else:
                entry["warnings"].append(f"EXTERNAL BLOCKED: {nf}")
        
        # Screenshot
        safe_name = name.replace("/", "_").replace(" ", "_").replace(":", "")
        screenshot_path = os.path.join(OUT_DIR, f"{safe_name}.png")
        page.screenshot(path=screenshot_path, full_page=False)
        entry["screenshot"] = screenshot_path
        entry["screenshot_size"] = os.path.getsize(screenshot_path)
        
        # Content checks
        if checks:
            for check_desc, check_fn in checks:
                try:
                    result = check_fn(page)
                    if not result:
                        entry["passed"] = False
                        entry["errors"].append(f"CONTENT CHECK: {check_desc}")
                except Exception as e:
                    entry["passed"] = False
                    entry["errors"].append(f"CHECK FAILED: {check_desc} - {e}")
        
        # Body text
        try:
            body_text = page.inner_text("body")
            entry["body_text_length"] = len(body_text)
            entry["body_text_preview"] = body_text[:100] if body_text else "(empty)"
        except:
            entry["body_text_length"] = 0
            entry["body_text_preview"] = "(error)"
        
        browser.close()
    
    results.append(entry)
    return entry

# ============================================================
# TEST 1-4: Public pages
# ============================================================
print("=" * 60)
print("TESTING PUBLIC PAGES")
print("=" * 60)

test_page("01_Homepage", f"{BASE}/", checks=[
    ("Has game cards or content", lambda p: p.locator(".game-card, [class*=game]").count() > 0 or len(p.inner_text("body").strip()) > 100),
])

test_page("02_Games", f"{BASE}/games", checks=[
    ("Has #game-grid", lambda p: p.locator("#game-grid").count() > 0),
    ("Has body text > 50 chars", lambda p: len(p.inner_text("body").strip()) > 50),
])

test_page("03_GameDetail_1", f"{BASE}/game/1", checks=[
    ("Has body text > 50 chars", lambda p: len(p.inner_text("body").strip()) > 50),
])

test_page("04_GameDetail_2", f"{BASE}/game/2", checks=[
    ("Has body text > 50 chars", lambda p: len(p.inner_text("body").strip()) > 50),
])

# ============================================================
# TEST 5: Admin redirect
# ============================================================
print("\n" + "=" * 60)
print("TESTING ADMIN AUTH")
print("=" * 60)

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    context = browser.new_context(viewport={"width": 1280, "height": 800})
    page = context.new_page()
    
    resp = page.goto(f"{BASE}/admin", wait_until="networkidle", timeout=15000)
    time.sleep(0.5)
    entry = {
        "name": "05_Admin_Redirect",
        "url": f"{BASE}/admin",
        "final_url": page.url,
        "passed": "/admin/login" in page.url,
        "errors": [] if "/admin/login" in page.url else ["Expected redirect to /admin/login"]
    }
    print(f"  Redirect: {page.url} - {'PASS' if entry['passed'] else 'FAIL'}")
    
    spath = os.path.join(OUT_DIR, "05_Admin_Redirect.png")
    page.screenshot(path=spath, full_page=False)
    entry["screenshot"] = spath
    entry["screenshot_size"] = os.path.getsize(spath)
    entry["body_text_length"] = len(page.inner_text("body")) if page.locator("body").count() > 0 else 0
    browser.close()
    results.append(entry)

# ============================================================
# TEST 6: Admin login page renders
# ============================================================
test_page("06_AdminLogin", f"{BASE}/admin/login", checks=[
    ("Has #username", lambda p: p.locator("#username").count() > 0),
    ("Has #password", lambda p: p.locator("#password").count() > 0),
    ("Has submit button", lambda p: p.locator("button[type='submit']").count() > 0),
])

# ============================================================
# TEST 7: Admin login flow + dashboard
# ============================================================
print("\nTEST 7: Admin Login Flow")
with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    context = browser.new_context(viewport={"width": 1280, "height": 800})
    page = context.new_page()
    entry = {"name": "07_AdminLoginFlow", "url": f"{BASE}/admin/login", "passed": True, "errors": []}
    console_errors = []
    page.on("pageerror", lambda err: console_errors.append(str(err)))
    
    try:
        page.goto(f"{BASE}/admin/login", wait_until="networkidle", timeout=15000)
        
        if page.locator("#username").count() == 0:
            entry["passed"] = False
            entry["errors"].append("Username field not found")
        elif page.locator("#password").count() == 0:
            entry["passed"] = False
            entry["errors"].append("Password field not found")
        else:
            page.fill("#username", "admin")
            page.fill("#password", "admin123")
            
            with page.expect_navigation(wait_until="networkidle", timeout=10000):
                page.click("button[type='submit']")
            
            time.sleep(1)
            entry["final_url"] = page.url
            
            if "/admin" in page.url and "/login" not in page.url:
                token = page.evaluate("() => !!localStorage.getItem('admin_token')")
                print(f"  Logged in: {page.url}, has_token={token} - PASS")
                entry["dashboard_body"] = page.inner_text("body")[:200]
            else:
                entry["passed"] = False
                entry["errors"].append(f"Login failed, still at {page.url}")
                print(f"  FAIL: {page.url}")
            
            if console_errors:
                entry["errors"].extend([f"JS: {e}" for e in console_errors])
            
            spath = os.path.join(OUT_DIR, "07_AdminDashboard.png")
            page.screenshot(path=spath, full_page=False)
            entry["screenshot"] = spath
            entry["screenshot_size"] = os.path.getsize(spath)
            entry["body_text_length"] = len(page.inner_text("body")) if page.locator("body").count() > 0 else 0
            
            # Save auth state for CRUD tests
            entry["_storage_state"] = context.storage_state()
    
    except Exception as e:
        entry["passed"] = False
        entry["errors"].append(f"EXCEPTION: {e}")
        spath = os.path.join(OUT_DIR, "07_AdminDashboard.png")
        page.screenshot(path=spath, full_page=False)
        entry["screenshot"] = spath
    
    browser.close()
    results.append(entry)

# ============================================================
# TEST 8: Admin API without auth
# ============================================================
print("\nTEST 8: Admin API Auth")
with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    context = browser.new_context()
    page = context.new_page()
    entry = {"name": "08_AdminAPI_Auth", "passed": True, "errors": []}
    
    try:
        resp = page.goto(f"{BASE}/api/admin/games", timeout=10000)
        status = resp.status if resp else 0
        entry["http_status"] = status
        if status == 401:
            print(f"  {status} Unauthorized - PASS")
        else:
            entry["passed"] = False
            entry["errors"].append(f"Expected 401, got {status}")
    except Exception as e:
        entry["passed"] = False
        entry["errors"].append(str(e))
    
    browser.close()
    results.append(entry)

# ============================================================
# TEST 9-10: Public API tests
# ============================================================
print("\nTEST 9-10: Public APIs")
for name, url in [("09_API_Games", "/api/games?page=1&page_size=12"), ("10_API_Categories", "/api/categories")]:
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()
        entry = {"name": name, "url": f"{BASE}{url}", "passed": True, "errors": []}
        
        try:
            resp = page.goto(f"{BASE}{url}", timeout=10000)
            entry["http_status"] = resp.status if resp else 0
            if resp and resp.status == 200:
                body = page.inner_text("body")
                entry["body_preview"] = body[:100]
                if "code" in body:
                    print(f"  {name}: 200 - PASS")
                else:
                    entry["passed"] = False
                    entry["errors"].append("Invalid JSON response")
            else:
                entry["passed"] = False
                entry["errors"].append(f"Status: {entry['http_status']}")
        except Exception as e:
            entry["passed"] = False
            entry["errors"].append(str(e))
        
        browser.close()
        results.append(entry)

# ============================================================
# SUMMARY
# ============================================================
print("\n" + "=" * 60)
print("FINAL BROWSER TEST REPORT - v0.8.1A")
print("=" * 60)

passed = sum(1 for r in results if r["passed"])
failed = sum(1 for r in results if not r["passed"])

for r in results:
    status = "PASS" if r["passed"] else "FAIL"
    extra_parts = []
    if "http_status" in r:
        extra_parts.append(f"HTTP={r['http_status']}")
    if "screenshot_size" in r:
        extra_parts.append(f"Img={r['screenshot_size']}B")
    if "body_text_length" in r:
        extra_parts.append(f"Body={r['body_text_length']}c")
    if "final_url" in r:
        extra_parts.append(f"-> {r['final_url']}")
    extra = " ".join(extra_parts)
    print(f"  [{status}] {r['name']} {extra}")
    
    for err in r.get("errors", []):
        print(f"         ERROR: {err}")
    for w in r.get("warnings", []):
        print(f"         WARN: {w}")

print(f"\nResults: {passed}/{len(results)} passed, {failed} failed")

report_path = os.path.join(OUT_DIR, "report_v3.json")
with open(report_path, "w", encoding="utf-8") as f:
    clean_results = [{k: v for k, v in r.items() if not k.startswith("_")} for r in results]
    json.dump(clean_results, f, ensure_ascii=False, indent=2)

