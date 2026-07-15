"""v0.8.1A Browser Acceptance Test"""
import json, os, time
from playwright.sync_api import sync_playwright

BASE = "http://localhost:8000"
SCREENSHOT_DIR = "screenshots/v081a_test"
os.makedirs(SCREENSHOT_DIR, exist_ok=True)

results = []
console_errors = []
network_errors = []

def run_test(name, path, checks=None, login_first=False):
    """Navigate to page and collect diagnostics."""
    global console_errors, network_errors
    
    page_errors = []
    page_404s = []
    page_500s = []
    
    def on_console(msg):
        if msg.type == "error":
            page_errors.append(f"[CONSOLE] {msg.text[:200]}")
            console_errors.append(f"{name}: {msg.text[:200]}")
    
    def on_response(response):
        status = response.status
        url = response.url
        if status == 404:
            page_404s.append(f"[404] {url}")
            network_errors.append(f"{name}: 404 - {url}")
        elif status >= 500:
            page_500s.append(f"[{status}] {url}")
            network_errors.append(f"{name}: {status} - {url}")
    
    page.on("console", on_console)
    page.on("response", on_response)
    
    try:
        # Navigate
        response = page.goto(f"{BASE}{path}", wait_until="networkidle", timeout=15000)
        http_status = response.status if response else 0
        
        # Wait a moment for any async JS
        page.wait_for_timeout(1500)
        
        # Check if page is blank (no meaningful content)
        body_text = page.inner_text("body").strip()
        body_html = page.content()
        is_blank = len(body_text) < 20 and "登录" not in body_text and "login" not in body_html.lower()
        
        # Take screenshot
        safe_name = name.replace("/", "_").replace(" ", "_")
        screenshot_path = f"{SCREENSHOT_DIR}/{safe_name}.png"
        page.screenshot(path=screenshot_path, full_page=True)
        
        # Get page title
        title = page.title()
        
        # Build result
        result = {
            "name": name,
            "path": path,
            "status": http_status,
            "title": title[:80],
            "body_length": len(body_text),
            "is_blank": is_blank,
            "console_errors": page_errors,
            "network_404s": page_404s,
            "network_500s": page_500s,
            "screenshot": screenshot_path,
            "passed": True
        }
        
        # Run custom checks
        if checks:
            for check_name, check_fn in checks.items():
                try:
                    check_result = check_fn(page)
                    if not check_result:
                        result["passed"] = False
                        result.setdefault("failed_checks", []).append(check_name)
                        page_errors.append(f"[CHECK FAIL] {check_name}")
                except Exception as e:
                    result["passed"] = False
                    result.setdefault("failed_checks", []).append(check_name)
                    page_errors.append(f"[CHECK ERROR] {check_name}: {str(e)[:100]}")
        
        if page_errors or page_404s or page_500s:
            result["passed"] = False
        
        results.append(result)
        return result
        
    except Exception as e:
        result = {
            "name": name,
            "path": path,
            "status": 0,
            "error": str(e)[:200],
            "passed": False
        }
        results.append(result)
        return result
    finally:
        page.remove_listener("console", on_console)
        page.remove_listener("response", on_response)

# ===== Start =====
with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    context = browser.new_context(
        viewport={"width": 1280, "height": 800},
        ignore_https_errors=True
    )
    page = context.new_page()
    
    print("=" * 60)
    print("v0.8.1A BROWSER ACCEPTANCE TEST")
    print("=" * 60)
    
    # ---- Test 1: Homepage / ----
    print("\n[1/6] Testing Homepage /")
    r = run_test("Homepage /", "/", checks={
        "Has game cards": lambda p: p.query_selector(".game-card") is not None,
        "Has category tabs": lambda p: p.query_selector(".category-tab") is not None,
        "Has search box": lambda p: p.query_selector("#keyword-input") is not None,
    })
    print(f"  Status: {r['status']}, Title: {r['title']}")
    print(f"  Body: {r['body_length']} chars, Blank: {r['is_blank']}")
    
    # ---- Test 2: /games ----
    print("\n[2/6] Testing /games")
    r = run_test("Games List /games", "/games", checks={
        "Has game grid": lambda p: p.query_selector("#game-grid") is not None,
        "Has pagination": lambda p: p.query_selector("#pagination") is not None,
        "Not blank": lambda p: len(p.inner_text("body").strip()) > 100,
    })
    print(f"  Status: {r['status']}, Title: {r['title']}")
    print(f"  Body: {r['body_length']} chars, Blank: {r['is_blank']}")
    
    # ---- Test 3: /game/{id} ----
    print("\n[3/6] Testing Game Detail /game/1")
    r = run_test("Game Detail /game/1", "/game/1", checks={
        "Has game title": lambda p: p.query_selector(".detail-title") is not None or p.query_selector("h1") is not None,
        "Not blank": lambda p: len(p.inner_text("body").strip()) > 200,
    })
    print(f"  Status: {r['status']}, Title: {r['title']}")
    print(f"  Body: {r['body_length']} chars, Blank: {r['is_blank']}")
    
    # ---- Test 4: /admin (should redirect to login) ----
    print("\n[4/6] Testing /admin (no auth)")
    response = page.goto(f"{BASE}/admin", wait_until="networkidle", timeout=10000)
    final_url = page.url
    has_login_form = page.query_selector("#login-form") is not None or page.query_selector('input[name="username"]') is not None
    print(f"  Final URL: {final_url}")
    print(f"  Has login form: {has_login_form}")
    page.screenshot(path=f"{SCREENSHOT_DIR}/admin_redirect.png", full_page=True)
    results.append({
        "name": "Admin Redirect /admin",
        "path": "/admin",
        "final_url": final_url,
        "has_login_form": has_login_form,
        "passed": has_login_form and "login" in final_url.lower(),
        "screenshot": f"{SCREENSHOT_DIR}/admin_redirect.png"
    })
    
    # ---- Test 5: /admin/login (login form) ----
    print("\n[5/6] Testing /admin/login")
    page.goto(f"{BASE}/admin/login", wait_until="networkidle", timeout=10000)
    has_username = page.query_selector('input[name="username"]') is not None
    has_password = page.query_selector('input[name="password"]') is not None
    has_submit = page.query_selector('button[type="submit"]') is not None
    title = page.title()
    page.screenshot(path=f"{SCREENSHOT_DIR}/admin_login.png", full_page=True)
    print(f"  Title: {title}")
    print(f"  Has username: {has_username}, password: {has_password}, submit: {has_submit}")
    results.append({
        "name": "Admin Login /admin/login",
        "path": "/admin/login",
        "title": title,
        "has_username": has_username,
        "has_password": has_password,
        "has_submit": has_submit,
        "passed": has_username and has_password and has_submit,
        "screenshot": f"{SCREENSHOT_DIR}/admin_login.png"
    })
    
    # ---- Test 6: Login and test dashboard ----
    print("\n[6/6] Testing Login + Dashboard")
    # Fill login form
    page.fill('input[name="username"]', "admin")
    page.fill('input[name="password"]', "admin123")
    
    # Capture network and console during login
    login_errors = []
    def on_login_console(msg):
        if msg.type == "error":
            login_errors.append(msg.text[:200])
    page.on("console", on_login_console)
    
    page.click('button[type="submit"]')
    page.wait_for_timeout(3000)
    
    final_url = page.url
    has_dashboard = "仪表盘" in page.content() or "stats-grid" in page.content()
    
    page.screenshot(path=f"{SCREENSHOT_DIR}/admin_dashboard.png", full_page=True)
    
    print(f"  Final URL: {final_url}")
    print(f"  Has dashboard: {has_dashboard}")
    print(f"  Login console errors: {len(login_errors)}")
    
    # Check stat cards
    stat_cards = page.query_selector_all(".stat-card")
    print(f"  Stat cards visible: {len(stat_cards)}")
    
    results.append({
        "name": "Dashboard (after login)",
        "path": "/admin",
        "final_url": final_url,
        "has_dashboard": has_dashboard,
        "stat_cards": len(stat_cards),
        "login_errors": login_errors,
        "passed": has_dashboard and len(stat_cards) > 0 and len(login_errors) == 0,
        "screenshot": f"{SCREENSHOT_DIR}/admin_dashboard.png"
    })
    
    page.remove_listener("console", on_login_console)
    
    browser.close()

# ===== Print Summary =====
print("\n" + "=" * 60)
print("TEST RESULTS SUMMARY")
print("=" * 60)

all_pass = True
for r in results:
    status = "PASS" if r.get("passed") else "FAIL"
    name = r.get("name", "?")
    if not r.get("passed"):
        all_pass = False
    print(f"  [{status}] {name}")
    if r.get("console_errors"):
        for e in r["console_errors"]:
            print(f"         Console: {e}")
    if r.get("network_404s"):
        for e in r["network_404s"]:
            print(f"         Network: {e}")
    if r.get("network_500s"):
        for e in r["network_500s"]:
            print(f"         Network: {e}")
    if r.get("failed_checks"):
        for c in r["failed_checks"]:
            print(f"         Check Failed: {c}")
    if r.get("error"):
        print(f"         Error: {r['error']}")

print(f"\nTotal network errors (404/500): {len(network_errors)}")
for ne in network_errors:
    print(f"  NET: {ne}")

print(f"\nOverall: {'ALL PASSED' if all_pass else 'SOME FAILURES'}")
print(f"Screenshots saved to: {os.path.abspath(SCREENSHOT_DIR)}")
