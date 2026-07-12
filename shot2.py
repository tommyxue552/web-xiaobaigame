from playwright.sync_api import sync_playwright
import time

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(viewport={"width": 1400, "height": 900})
    page.set_default_timeout(10000)

    page.goto("http://localhost:8000/admin/login.html", wait_until="domcontentloaded")
    print("Login page loaded")
    page.fill("#username", "admin")
    page.fill("#password", "admin123")
    page.click("#login-btn")
    time.sleep(3)
    print("After login click, URL:", page.url)

    if "index.html" in page.url:
        page.screenshot(path=r"C:\Users\xueta\Documents\web-xiaobaigame\screenshot_dashboard.png")
        print("Dashboard screenshot taken")

        # Click providers nav (4th nav item)
        page.click(".nav-item:nth-child(4)")
        time.sleep(2)
        page.screenshot(path=r"C:\Users\xueta\Documents\web-xiaobaigame\screenshot_providers_list.png")
        print("Providers screenshot taken")
    else:
        print("Login may have failed")
        page.screenshot(path=r"C:\Users\xueta\Documents\web-xiaobaigame\screenshot_debug.png")

    browser.close()
    print("Done")
