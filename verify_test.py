import asyncio
import json
import os
from datetime import datetime
from pathlib import Path
from playwright.async_api import async_playwright

BASE = "http://localhost:8000"
SCREENSHOTS = Path(r"C:\Users\xueta\Documents\web-xiaobaigame\screenshots\v081a_verify")
SCREENSHOTS.mkdir(parents=True, exist_ok=True)

class TestResult:
    def __init__(self, name):
        self.name = name
        self.passed = False
        self.errors = []
        self.warnings = []
        self.notes = []

results = []

async def test(name, fn, page):
    r = TestResult(name)
    print(f"\n{'='*60}")
    print(f"TEST: {name}")
    js_errors = []
    errors_404 = []
    errors_500 = []

    def on_console(msg):
        if msg.type == "error":
            js_errors.append(msg.text)

    def on_response(resp):
        status = resp.status
        url = resp.url
        if "localhost" in url:
            if status == 404:
                errors_404.append(url)
            elif status >= 500:
                errors_500.append(f"{status}: {url}")

    page.on("console", on_console)
    page.on("response", on_response)

    try:
        await fn(page)
        r.passed = True
        print(f"  RESULT: PASS")
    except Exception as e:
        r.errors.append(str(e))
        print(f"  RESULT: FAIL - {e}")
    
    page.remove_listener("console", on_console)
    page.remove_listener("response", on_response)

    for err in js_errors:
        if "favicon" not in err.lower() and "steamstatic" not in err.lower():
            r.errors.append(f"JS ERROR: {err}")
            r.passed = False
    
    for url in errors_404:
        r.errors.append(f"404: {url}")
        r.passed = False
    
    for e in errors_500:
        r.errors.append(f"SERVER ERROR: {e}")
        r.passed = False

    results.append(r)
    return r

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            viewport={"width": 1440, "height": 900},
            locale="zh-CN"
        )
        page = await context.new_page()

        # ===== TEST 1: Homepage / =====
        async def t1(page):
            resp = await page.goto(f"{BASE}/", wait_until="networkidle", timeout=15000)
            assert resp.status == 200, f"Status: {resp.status}"
            body = await page.inner_text("body")
            assert len(body) > 50, f"Body too short ({len(body)} chars)"
            await page.screenshot(path=str(SCREENSHOTS / "01_homepage.png"), full_page=True)
            print(f"  Body text: {body[:150]}...")
        await test("01 Homepage /", t1, page)

        # ===== TEST 2: /games page =====
        async def t2(page):
            resp = await page.goto(f"{BASE}/games", wait_until="networkidle", timeout=15000)
            assert resp.status == 200, f"Status: {resp.status}"
            body = await page.inner_text("body")
            assert len(body) > 50, f"Body too short ({len(body)} chars)"
            await page.screenshot(path=str(SCREENSHOTS / "02_games.png"), full_page=True)
            print(f"  Body text: {body[:150]}...")
        await test("02 /games Page", t2, page)

        # ===== TEST 3: /game/1 =====
        async def t3(page):
            resp = await page.goto(f"{BASE}/game/1", wait_until="networkidle", timeout=15000)
            assert resp.status == 200, f"Status: {resp.status}"
            body = await page.inner_text("body")
            assert len(body) > 50, f"Body too short ({len(body)} chars)"
            await page.screenshot(path=str(SCREENSHOTS / "03_game_detail.png"), full_page=True)
            print(f"  Body text: {body[:150]}...")
        await test("03 /game/1 Detail", t3, page)

        # ===== TEST 4: /api/games JSON =====
        async def t4(page):
            resp = await page.goto(f"{BASE}/api/games?page=1&page_size=3", wait_until="networkidle")
            assert resp.status == 200
            data = await resp.json()
            assert data["code"] == 0
            games = data.get("data", {}).get("games", [])
            assert len(games) > 0, "No games"
            print(f"  {len(games)} games, first: {games[0].get('title','')}")
        await test("04 API /api/games", t4, page)

        # ===== TEST 5: /api/categories =====
        async def t5(page):
            resp = await page.goto(f"{BASE}/api/categories", wait_until="networkidle")
            assert resp.status == 200
            data = await resp.json()
            cats = data.get("data", data.get("categories", []))
            print(f"  {len(cats)} categories")
        await test("05 API /api/categories", t5, page)

        # ===== TEST 6: /admin -> redirect to login =====
        async def t6(page):
            resp = await page.goto(f"{BASE}/admin", wait_until="networkidle", timeout=15000)
            assert "/admin/login" in page.url, f"Expected login redirect, got: {page.url}"
            await page.screenshot(path=str(SCREENSHOTS / "06_admin_redirect.png"), full_page=True)
        await test("06 /admin Redirect", t6, page)

        # ===== TEST 7: /admin/login page =====
        async def t7(page):
            resp = await page.goto(f"{BASE}/admin/login", wait_until="networkidle", timeout=15000)
            assert resp.status == 200
            assert await page.query_selector("#username"), "No username input"
            assert await page.query_selector("#password"), "No password input"
            assert await page.query_selector("#login-btn"), "No login button"
            await page.screenshot(path=str(SCREENSHOTS / "07_login_page.png"), full_page=True)
        await test("07 /admin/login Page", t7, page)

        # ===== TEST 8: Login Flow =====
        async def t8(page):
            await page.fill("#username", "admin")
            await page.fill("#password", "admin123")
            await page.click("#login-btn")
            await page.wait_for_url(f"{BASE}/admin", timeout=10000)
            token = await page.evaluate("localStorage.getItem('admin_token')")
            assert token, "No token"
            print(f"  Token OK: {token[:20]}...")
            await page.screenshot(path=str(SCREENSHOTS / "08_dashboard.png"), full_page=True)
        await test("08 Admin Login Flow", t8, page)

        # ===== TEST 9: Admin Dashboard Renders =====
        async def t9(page):
            await page.wait_for_selector(".sidebar", timeout=5000)
            sidebar_html = await page.inner_html(".sidebar")
            assert len(sidebar_html) > 100, "Sidebar too short"
            main_html = await page.query_selector(".main-body")
            assert main_html, "No .main-body"
            # Try getting text content without encoding issues
            try:
                content = await page.evaluate("document.querySelector('.main-body').textContent")
                print(f"  Dashboard: {content[:200]}")
            except Exception as e:
                print(f"  (text extraction: {e})")
            await page.screenshot(path=str(SCREENSHOTS / "09_dashboard_loaded.png"), full_page=True)
        await test("09 Admin Dashboard Renders", t9, page)

        # ===== TEST 10: Admin Stats API (with token) =====
        async def t10(page):
            token = await page.evaluate("localStorage.getItem('admin_token')")
            api_page = await context.new_page()
            await api_page.set_extra_http_headers({"Authorization": f"Bearer {token}"})
            resp = await api_page.goto(f"{BASE}/api/admin/stats", wait_until="networkidle")
            assert resp.status == 200, f"Stats API status: {resp.status}"
            data = await resp.json()
            assert data["code"] == 0
            s = data["data"]
            print(f"  games={s.get('total_games')} cats={s.get('category_count')} tags={s.get('tag_count')} resources={s.get('resource_count')} downloads={s.get('download_count')}")
            await api_page.close()
        await test("10 Admin Stats API", t10, page)

        # ===== TEST 11: Admin Games CRUD =====
        async def t11(page):
            token = await page.evaluate("localStorage.getItem('admin_token')")
            api_page = await context.new_page()
            await api_page.set_extra_http_headers({"Authorization": f"Bearer {token}"})
            resp = await api_page.goto(f"{BASE}/api/admin/games?page=1&page_size=5", wait_until="networkidle")
            assert resp.status == 200
            data = await resp.json()
            assert data["code"] == 0
            games = data["data"]["items"]
            print(f"  {len(games)} games, total={data['data']['total']}")
            # Get single game
            if games:
                gid = games[0]["id"]
                resp2 = await api_page.goto(f"{BASE}/api/admin/game/{gid}", wait_until="networkidle")
                assert resp2.status == 200
                gdata = await resp2.json()
                print(f"  Game {gid}: {gdata['data'].get('title','')}")
            await api_page.close()
        await test("11 Admin Games CRUD", t11, page)

        # ===== TEST 12: Admin Categories CRUD =====
        async def t12(page):
            token = await page.evaluate("localStorage.getItem('admin_token')")
            api_page = await context.new_page()
            await api_page.set_extra_http_headers({"Authorization": f"Bearer {token}"})
            resp = await api_page.goto(f"{BASE}/api/admin/categories", wait_until="networkidle")
            assert resp.status == 200
            data = await resp.json()
            cats = data["data"]
            print(f"  {len(cats)} categories")
            # Get first category
            if cats:
                cid = cats[0]["id"]
                resp2 = await api_page.goto(f"{BASE}/api/admin/category/{cid}", wait_until="networkidle")
                # 404 on category detail is ok if route doesn't exist
                print(f"  Category {cid} detail: {resp2.status}")
            await api_page.close()
        await test("12 Admin Categories", t12, page)

        # ===== TEST 13: Admin Tags CRUD =====
        async def t13(page):
            token = await page.evaluate("localStorage.getItem('admin_token')")
            api_page = await context.new_page()
            await api_page.set_extra_http_headers({"Authorization": f"Bearer {token}"})
            resp = await api_page.goto(f"{BASE}/api/admin/tags", wait_until="networkidle")
            assert resp.status == 200
            data = await resp.json()
            tags = data["data"]
            print(f"  {len(tags)} tags")
            # Get active tags
            resp2 = await api_page.goto(f"{BASE}/api/admin/tags/active", wait_until="networkidle")
            assert resp2.status == 200
            await api_page.close()
        await test("13 Admin Tags", t13, page)

        # ===== TEST 14: Admin Download Resources =====
        async def t14(page):
            token = await page.evaluate("localStorage.getItem('admin_token')")
            api_page = await context.new_page()
            await api_page.set_extra_http_headers({"Authorization": f"Bearer {token}"})
            # Try download resources
            resp = await api_page.goto(f"{BASE}/api/admin/download-resources", wait_until="networkidle")
            print(f"  /api/admin/download-resources: {resp.status}")
            # Try download providers
            resp2 = await api_page.goto(f"{BASE}/api/admin/download-providers", wait_until="networkidle")
            print(f"  /api/admin/download-providers: {resp2.status}")
            await api_page.close()
        await test("14 Admin Download APIs", t14, page)

        # ===== TEST 15: 401 without token =====
        async def t15(page):
            api_page = await context.new_page()
            resp = await api_page.goto(f"{BASE}/api/admin/stats", wait_until="networkidle")
            assert resp.status == 401, f"Expected 401, got {resp.status}"
            resp2 = await api_page.goto(f"{BASE}/api/admin/games", wait_until="networkidle")
            assert resp2.status == 401, f"Expected 401, got {resp2.status}"
            resp3 = await api_page.goto(f"{BASE}/api/admin/categories", wait_until="networkidle")
            assert resp3.status == 401, f"Expected 401, got {resp3.status}"
            await api_page.close()
        await test("15 Auth Required (401)", t15, page)

        await browser.close()

    # Print summary
    print(f"\n{'='*60}")
    print("FINAL SUMMARY")
    print(f"{'='*60}")
    passed = sum(1 for r in results if r.passed)
    failed = sum(1 for r in results if not r.passed)
    for r in results:
        status = "PASS" if r.passed else "FAIL"
        print(f"  [{status}] {r.name}")
        for e in r.errors:
            print(f"         ERR: {e}")
    print(f"\n  TOTAL: {len(results)} | PASS: {passed} | FAIL: {failed}")

    # Save report
    report_path = SCREENSHOTS / "report.json"
    report = {
        "time": datetime.now().isoformat(),
        "total": len(results),
        "passed": passed,
        "failed": failed,
        "tests": [{"name": r.name, "passed": r.passed, "errors": r.errors} for r in results]
    }
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    print(f"\nReport: {report_path}")

    if failed > 0:
        raise SystemExit(1)

asyncio.run(main())
