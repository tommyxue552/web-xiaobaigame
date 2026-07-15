from playwright.sync_api import sync_playwright
import json, time, os

BASE = "http://localhost:8000"
screenshot_dir = r"C:\Users\xueta\Documents\web-xiaobaigame\screenshots\v081a_final"
os.makedirs(screenshot_dir, exist_ok=True)

results = []

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    context = browser.new_context(viewport={"width": 1440, "height": 900})

    # 1. Homepage
    print("=== 1. Homepage ===")
    page = context.new_page()
    errors = []
    page.on("console", lambda msg: errors.append(f"[{msg.type}] {msg.text}") if msg.type == "error" else None)
    resp = page.goto(f"{BASE}/", wait_until="networkidle", timeout=30000)
    page.wait_for_timeout(2000)
    title = page.title()
    body_text = page.locator("body").inner_text()[:500]
    has_content = len(body_text.strip()) > 50
    page.screenshot(path=os.path.join(screenshot_dir, "01_homepage.png"), full_page=True)
    results.append({"name": "01 Homepage /", "status": resp.status, "title": title, "has_content": has_content, "body_length": len(body_text.strip()), "console_errors": errors[:10], "passed": resp.status == 200 and has_content and len(errors) == 0})
    print("  Status:", resp.status, "Title:", title, "Body:", len(body_text.strip()), "Errors:", len(errors))
    if errors:
        for e in errors[:5]:
            print("    ", e)
    page.close()

    # 2. /games
    print("=== 2. /games ===")
    page = context.new_page()
    errors = []
    page.on("console", lambda msg: errors.append(f"[{msg.type}] {msg.text}") if msg.type == "error" else None)
    resp = page.goto(f"{BASE}/games", wait_until="networkidle", timeout=30000)
    page.wait_for_timeout(2000)
    title = page.title()
    body_text = page.locator("body").inner_text()[:500]
    has_content = len(body_text.strip()) > 50
    page.screenshot(path=os.path.join(screenshot_dir, "02_games.png"), full_page=True)
    results.append({"name": "02 /games Page", "status": resp.status, "title": title, "has_content": has_content, "body_length": len(body_text.strip()), "console_errors": errors[:10], "passed": resp.status == 200 and has_content and len(errors) == 0})
    print("  Status:", resp.status, "Title:", title, "Body:", len(body_text.strip()), "Errors:", len(errors))
    if errors:
        for e in errors[:5]:
            print("    ", e)
    page.close()

    # 3. /game/1 Detail
    print("=== 3. /game/1 ===")
    page = context.new_page()
    errors = []
    page.on("console", lambda msg: errors.append(f"[{msg.type}] {msg.text}") if msg.type == "error" else None)
    resp = page.goto(f"{BASE}/game/1", wait_until="networkidle", timeout=30000)
    page.wait_for_timeout(2000)
    title = page.title()
    body_text = page.locator("body").inner_text()[:500]
    has_content = len(body_text.strip()) > 50
    page.screenshot(path=os.path.join(screenshot_dir, "03_game_detail.png"), full_page=True)
    results.append({"name": "03 /game/1 Detail", "status": resp.status, "title": title, "has_content": has_content, "body_length": len(body_text.strip()), "console_errors": errors[:10], "passed": resp.status == 200 and has_content and len(errors) == 0})
    print("  Status:", resp.status, "Title:", title, "Body:", len(body_text.strip()), "Errors:", len(errors))
    if errors:
        for e in errors[:5]:
            print("    ", e)
    page.close()

    browser.close()

# Summary
print()
print("=" * 60)
print("BROWSER VERIFICATION RESULTS")
print("=" * 60)
passed = sum(1 for r in results if r["passed"])
for r in results:
    s = "PASS" if r["passed"] else "FAIL"
    print(f"[{s}] {r['name']}: status={r['status']}, errors={len(r['console_errors'])}")
    if r["console_errors"]:
        for e in r["console_errors"][:5]:
            print("       " + e)
print(f"Total: {passed}/{len(results)} passed")

# Save report
report_path = os.path.join(screenshot_dir, "report_frontend.json")
with open(report_path, "w", encoding="utf-8") as f:
    json.dump(results, f, indent=2, ensure_ascii=False)
print(f"Report saved: {report_path}")
