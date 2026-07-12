import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
from playwright.sync_api import sync_playwright
import time

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(viewport={"width": 1400, "height": 900})
    page.set_default_timeout(15000)

    page.on("pageerror", lambda err: print("ERR:", err))

    # Login via form
    page.goto("http://localhost:8000/admin/login.html", wait_until="domcontentloaded")
    page.fill("#username", "admin")
    page.fill("#password", "admin123")

    # Click login and wait for navigation
    with page.expect_navigation(timeout=10000):
        page.click("#login-btn")
    time.sleep(3)
    print("URL:", page.url)

    page.screenshot(path=r"C:\Users\xueta\Documents\web-xiaobaigame\screenshot_1_dashboard.png")
    print("1. Dashboard")

    # Click providers nav
    page.click(".nav-item:nth-child(5)")
    time.sleep(2)
    page.screenshot(path=r"C:\Users\xueta\Documents\web-xiaobaigame\screenshot_2_providers_list.png")
    print("2. Providers list")

    page.click("#add-provider-btn")
    time.sleep(1)
    page.screenshot(path=r"C:\Users\xueta\Documents\web-xiaobaigame\screenshot_3_providers_add.png")
    print("3. Add provider modal")

    page.click(".prov-modal-close")
    time.sleep(0.5)

    # Go to resources
    page.click(".nav-item:nth-child(4)")
    time.sleep(2)
    page.screenshot(path=r"C:\Users\xueta\Documents\web-xiaobaigame\screenshot_4_resources_list.png")
    print("4. Resources list")

    page.click("#add-resource-btn")
    time.sleep(2)
    page.screenshot(path=r"C:\Users\xueta\Documents\web-xiaobaigame\screenshot_5_resources_add.png")
    print("5. Add resource modal")

    browser.close()
    print("Done!")
