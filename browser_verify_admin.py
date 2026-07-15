from playwright.sync_api import sync_playwright
import json, os

BASE = "http://localhost:8000"
screenshot_dir = r"C:\Users\xueta\Documents\web-xiaobaigame\screenshots\v081a_final"

results = []

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    context = browser.new_context(viewport={"width": 1440, "height": 900})

    # 4. /admin - redirect to login
    print("=== 4. /admin redirect ===")
    page = context.new_page()
    errors = []
    page.on("console", lambda msg: errors.append(f"[{msg.type}] {msg.text}") if msg.type == "error" else None)
    resp = page.goto(f"{BASE}/admin", wait_until="networkidle", timeout=30000)
    page.wait_for_timeout(2000)
    final_url = page.url
    title = page.title()
    body_text = page.locator("body").inner_text()[:500]
    has_login = "login" in final_url.lower() or "登录" in body_text or "login" in body_text.lower()
    page.screenshot(path=os.path.join(screenshot_dir, "04_admin_redirect.png"), full_page=True)
    results.append({"name": "04 /admin Redirect to Login", "url": final_url, "has_login": has_login, "title": title, "console_errors": errors[:10], "passed": has_login and len(errors) == 0})
    print("  Final URL:", final_url, "Title:", title, "Has login:", has_login, "Errors:", len(errors))
    if errors:
        for e in errors[:5]:
            print("    ", e)
    page.close()

    # 5. /admin/login - login page
    print("=== 5. /admin/login ===")
    page = context.new_page()
    errors = []
    page.on("console", lambda msg: errors.append(f"[{msg.type}] {msg.text}") if msg.type == "error" else None)
    resp = page.goto(f"{BASE}/admin/login", wait_until="networkidle", timeout=30000)
    page.wait_for_timeout(2000)
    title = page.title()
    body_text = page.locator("body").inner_text()[:500]
    has_form = "username" in body_text.lower() or "password" in body_text.lower()
    page.screenshot(path=os.path.join(screenshot_dir, "05_login_page.png"), full_page=True)
    results.append({"name": "05 /admin/login Page", "status": resp.status, "title": title, "has_form": has_form, "console_errors": errors[:10], "passed": resp.status == 200 and has_form and len(errors) == 0})
    print("  Status:", resp.status, "Title:", title, "Has form:", has_form, "Errors:", len(errors))
    if errors:
        for e in errors[:5]:
            print("    ", e)
    page.close()

    # 6. Login flow
    print("=== 6. Admin Login ===")
    page = context.new_page()
    errors = []
    page.on("console", lambda msg: errors.append(f"[{msg.type}] {msg.text}") if msg.type == "error" else None)
    resp = page.goto(f"{BASE}/admin/login", wait_until="networkidle", timeout=30000)
    page.wait_for_timeout(1000)

    # Fill login form
    try:
        page.fill('input[name="username"]', "admin")
        page.fill('input[name="password"]', "admin123")
        page.click('button[type="submit"]')
        page.wait_for_timeout(3000)
        final_url = page.url
        title = page.title()
        logged_in = "/admin" in final_url and "login" not in final_url.lower()
        page.screenshot(path=os.path.join(screenshot_dir, "06_after_login.png"), full_page=True)
        results.append({"name": "06 Admin Login Flow", "final_url": final_url, "title": title, "logged_in": logged_in, "console_errors": errors[:10], "passed": logged_in and len(errors) == 0})
        print("  Final URL:", final_url, "Title:", title, "Logged in:", logged_in, "Errors:", len(errors))
    except Exception as e:
        results.append({"name": "06 Admin Login Flow", "error": str(e), "console_errors": errors[:10], "passed": False})
        print("  Login error:", e)
    if errors:
        for e in errors[:5]:
            print("    ", e)
    page.close()

    browser.close()

# Summary
print()
print("=" * 60)
print("ADMIN BROWSER VERIFICATION")
print("=" * 60)
passed = sum(1 for r in results if r["passed"])
for r in results:
    s = "PASS" if r["passed"] else "FAIL"
    print(f"[{s}] {r['name']}")
    if not r["passed"] and "error" in r:
        print("       Error:", r["error"])
print(f"Total: {passed}/{len(results)} passed")

report_path = os.path.join(screenshot_dir, "report_admin.json")
with open(report_path, "w", encoding="utf-8") as f:
    json.dump(results, f, indent=2, ensure_ascii=False)
print(f"Report saved: {report_path}")
