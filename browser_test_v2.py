# -*- coding: utf-8 -*-
"""v0.8.1A Browser Acceptance Test with full diagnostics"""
import os, sys, json, time
sys.stdout.reconfigure(encoding='utf-8')

from playwright.sync_api import sync_playwright

BASE = "http://localhost:8000"
OUT_DIR = r"C:\Users\xueta\Documents\web-xiaobaigame\screenshots\v081a_test"
os.makedirs(OUT_DIR, exist_ok=True)

results = []

def test_page(name, url, checks=None):
    """Test a page: screenshot, console errors, network failures, content checks."""
    entry = {"name": name, "url": url, "passed": True, "errors": []}
    console_msgs = []
    network_fails = []
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1280, "height": 800})
        page = context.new_page()
        
        page.on("console", lambda msg: console_msgs.append(f"[{msg.type}] {msg.text}"))
        page.on("pageerror", lambda err: entry["errors"].append(f"PAGE ERROR: {err}"))
        page.on("requestfailed", lambda req: network_fails.append(f"FAILED: {req.url} - {req.failure}"))
        
        try:
            resp = page.goto(url, wait_until="networkidle", timeout=15000)
            time.sleep(1)
        except Exception as e:
            entry["passed"] = False
            entry["errors"].append(f"GOTO FAILED: {e}")
            browser.close()
            results.append(entry)
            return entry
        
        entry["http_status"] = resp.status if resp else "N/A"
        
        # Capture console errors
        errors = [m for m in console_msgs if m.startswith("[error]")]
        warnings = [m for m in console_msgs if m.startswith("[warning]")]
        entry["console_errors"] = errors
        entry["console_warnings"] = warnings
        if errors:
            entry["passed"] = False
            entry["errors"].extend(errors)
        
        # Capture network failures
        entry["network_fails"] = network_fails
        if network_fails:
            entry["passed"] = False
            entry["errors"].extend(network_fails)
        
        # Screenshot
        safe_name = name.replace("/", "_").replace(" ", "_")
        screenshot_path = os.path.join(OUT_DIR, f"{safe_name}.png")
        page.screenshot(path=screenshot_path, full_page=False)
        entry["screenshot"] = screenshot_path
        entry["screenshot_size"] = os.path.getsize(screenshot_path)
        
        # Run content checks
        if checks:
            for check_desc, check_fn in checks:
                try:
                    result = check_fn(page)
                    if not result:
                        entry["passed"] = False
                        entry["errors"].append(f"CONTENT CHECK FAILED: {check_desc}")
                except Exception as e:
                    entry["passed"] = False
                    entry["errors"].append(f"CHECK ERROR '{check_desc}': {e}")
        
        # Body text length
        try:
            body_text = page.inner_text("body")
            entry["body_text_length"] = len(body_text)
            entry["body_text_preview"] = body_text[:200] if body_text else "(empty)"
        except:
            entry["body_text_length"] = 0
            entry["body_text_preview"] = "(error reading body)"
        
        browser.close()
    
    results.append(entry)
    return entry

# ============================================================
# TEST 1: Homepage /
# ============================================================
print("=" * 60)
print("TEST 1: Homepage /")
test_page("01_Homepage", f"{BASE}/", checks=[
    ("Has game cards", lambda p: p.locator(".game-card").count() > 0 or p.locator("[class*=game]").count() > 0),
    ("Has header nav", lambda p: p.locator("header").count() > 0),
])

# ============================================================
# TEST 2: /games
# ============================================================
print("TEST 2: /games")
test_page("02_Games", f"{BASE}/games", checks=[
    ("Has game-grid container", lambda p: p.locator("#game-grid").count() > 0),
    ("Has category filter", lambda p: p.locator("#category-filter").count() > 0),
    ("Has body text", lambda p: len(p.inner_text("body").strip()) > 50),
])

# ============================================================
# TEST 3: /game/1
# ============================================================
print("TEST 3: /game/1")
test_page("03_GameDetail_1", f"{BASE}/game/1", checks=[
    ("Has game title", lambda p: len(p.inner_text("body").strip()) > 30),
])

# ============================================================
# TEST 4: /game/2
# ============================================================
print("TEST 4: /game/2")
test_page("04_GameDetail_2", f"{BASE}/game/2", checks=[
    ("Has game title", lambda p: len(p.inner_text("body").strip()) > 30),
])

# ============================================================
# TEST 5: /admin (should redirect to /admin/login)
# ============================================================
print("TEST 5: /admin (redirect check)")
with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    context = browser.new_context(viewport={"width": 1280, "height": 800})
    page = context.new_page()
    resp = page.goto(f"{BASE}/admin", wait_until="networkidle", timeout=15000)
    time.sleep(1)
    final_url = page.url
    entry = {
        "name": "05_Admin_Redirect",
        "url": f"{BASE}/admin",
        "final_url": final_url,
        "passed": True,
        "errors": []
    }
    if "/admin/login" in final_url:
        print(f"  OK: Redirected to {final_url}")
    else:
        entry["passed"] = False
        entry["errors"].append(f"Expected redirect to /admin/login, got {final_url}")
        print(f"  FAIL: Not redirected. Got {final_url}")
    
    screenshot_path = os.path.join(OUT_DIR, "05_Admin_Redirect.png")
    page.screenshot(path=screenshot_path, full_page=False)
    entry["screenshot"] = screenshot_path
    entry["screenshot_size"] = os.path.getsize(screenshot_path)
    entry["body_text_length"] = len(page.inner_text("body")) if page.locator("body").count() > 0 else 0
    browser.close()
    results.append(entry)

# ============================================================
# TEST 6: /admin/login
# ============================================================
print("TEST 6: /admin/login")
test_page("06_AdminLogin", f"{BASE}/admin/login", checks=[
    ("Has username field", lambda p: p.locator("#username").count() > 0 or p.locator("input[name='username']").count() > 0),
    ("Has password field", lambda p: p.locator("#password").count() > 0 or p.locator("input[name='password']").count() > 0),
    ("Has login button", lambda p: p.locator("button[type='submit']").count() > 0),
])

# ============================================================
# TEST 7: Admin Login + Access Dashboard
# ============================================================
print("TEST 7: Admin Login Flow + Dashboard")
with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    context = browser.new_context(viewport={"width": 1280, "height": 800})
    page = context.new_page()
    entry = {"name": "07_AdminLoginFlow", "url": f"{BASE}/admin/login", "passed": True, "errors": []}
    
    try:
        page.goto(f"{BASE}/admin/login", wait_until="networkidle", timeout=15000)
        time.sleep(1)
        
        # Check form elements exist
        uname = page.locator("#username")
        pwd = page.locator("#password")
        btn = page.locator("button[type='submit']")
        
        if uname.count() == 0:
            entry["passed"] = False
            entry["errors"].append("Username field not found")
        if pwd.count() == 0:
            entry["passed"] = False
            entry["errors"].append("Password field not found")
        if btn.count() == 0:
            entry["passed"] = False
            entry["errors"].append("Submit button not found")
        
        if entry["passed"]:
            uname.fill("admin")
            pwd.fill("admin123")
            btn.click()
            
            time.sleep(2)
            final_url = page.url
            entry["final_url"] = final_url
            
            if "/admin" in final_url and "/login" not in final_url:
                print(f"  OK: Logged in, now at {final_url}")
            else:
                entry["passed"] = False
                entry["errors"].append(f"Login may have failed, still at {final_url}")
                
            # Take screenshot of dashboard
            screenshot_path = os.path.join(OUT_DIR, "07_AdminDashboard.png")
            page.screenshot(path=screenshot_path, full_page=False)
            entry["screenshot"] = screenshot_path
            entry["screenshot_size"] = os.path.getsize(screenshot_path)
            entry["body_text_length"] = len(page.inner_text("body")) if page.locator("body").count() > 0 else 0
        else:
            screenshot_path = os.path.join(OUT_DIR, "07_AdminDashboard.png")
            page.screenshot(path=screenshot_path, full_page=False)
            entry["screenshot"] = screenshot_path
            entry["screenshot_size"] = os.path.getsize(screenshot_path)
            
    except Exception as e:
        entry["passed"] = False
        entry["errors"].append(f"EXCEPTION: {e}")
    
    browser.close()
    results.append(entry)

# ============================================================
# TEST 8: Admin API without auth (should return 401)
# ============================================================
print("TEST 8: Admin API auth check")
with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    context = browser.new_context()
    page = context.new_page()
    entry = {"name": "08_AdminAPI_Auth", "url": f"{BASE}/api/admin/games", "passed": True, "errors": []}
    
    try:
        resp = page.goto(f"{BASE}/api/admin/games", timeout=10000)
        if resp:
            status = resp.status
            entry["http_status"] = status
            if status == 401:
                print(f"  OK: {status} Unauthorized")
            else:
                entry["passed"] = False
                entry["errors"].append(f"Expected 401, got {status}")
        else:
            entry["passed"] = False
            entry["errors"].append("No response")
    except Exception as e:
        entry["passed"] = False
        entry["errors"].append(f"EXCEPTION: {e}")
    
    browser.close()
    results.append(entry)

# ============================================================
# TEST 9: API /api/games
# ============================================================
print("TEST 9: Public API /api/games")
with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    context = browser.new_context()
    page = context.new_page()
    entry = {"name": "09_PublicAPI_Games", "url": f"{BASE}/api/games?page=1&page_size=12", "passed": True, "errors": []}
    
    try:
        resp = page.goto(f"{BASE}/api/games?page=1&page_size=12", timeout=10000)
        if resp:
            body = page.inner_text("body")
            entry["body_preview"] = body[:200]
            if resp.status == 200 and "code" in body:
                print(f"  OK: API returns valid JSON")
            else:
                entry["passed"] = False
                entry["errors"].append(f"Unexpected response: status={resp.status}")
    except Exception as e:
        entry["passed"] = False
        entry["errors"].append(f"EXCEPTION: {e}")
    
    browser.close()
    results.append(entry)

# ============================================================
# TEST 10: API /api/categories
# ============================================================
print("TEST 10: Public API /api/categories")
with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    context = browser.new_context()
    page = context.new_page()
    entry = {"name": "10_PublicAPI_Categories", "url": f"{BASE}/api/categories", "passed": True, "errors": []}
    
    try:
        resp = page.goto(f"{BASE}/api/categories", timeout=10000)
        if resp:
            body = page.inner_text("body")
            entry["body_preview"] = body[:200]
            if resp.status == 200:
                print(f"  OK: {resp.status}")
            else:
                entry["passed"] = False
                entry["errors"].append(f"Expected 200, got {resp.status}")
    except Exception as e:
        entry["passed"] = False
        entry["errors"].append(f"EXCEPTION: {e}")
    
    browser.close()
    results.append(entry)

# ============================================================
# SUMMARY
# ============================================================
print("\n" + "=" * 60)
print("BROWSER TEST REPORT - v0.8.1A")
print("=" * 60)

passed = 0
failed = 0
for r in results:
    status = "PASS" if r["passed"] else "FAIL"
    if r["passed"]:
        passed += 1
    else:
        failed += 1
    
    extra = ""
    if "http_status" in r:
        extra += f" HTTP={r['http_status']}"
    if "screenshot_size" in r:
        extra += f" Screenshot={r['screenshot_size']}B"
    if "body_text_length" in r:
        extra += f" BodyLen={r['body_text_length']}"
    if "final_url" in r:
        extra += f" -> {r['final_url']}"
    
    print(f"  [{status}] {r['name']}{extra}")
    
    if not r["passed"] and r.get("errors"):
        for err in r["errors"]:
            print(f"         ERROR: {err}")

print(f"\nResults: {passed} passed, {failed} failed, {len(results)} total")

# Write detailed report
report_path = os.path.join(OUT_DIR, "report.json")
with open(report_path, "w", encoding="utf-8") as f:
    json.dump(results, f, ensure_ascii=False, indent=2)
print(f"\nDetailed report saved to: {report_path}")

