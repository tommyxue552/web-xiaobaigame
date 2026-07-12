from playwright.sync_api import sync_playwright
import time, os

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(viewport={"width": 1440, "height": 900})
    
    # Login
    page.goto("http://localhost:8000/admin/login.html")
    page.fill('input[name="username"]', "admin")
    page.fill('input[name="password"]', "admin123")
    page.click('button[type="submit"]')
    page.wait_for_url("**/admin/index.html**", timeout=10000)
    
    # Navigate to download resources by clicking menu
    # First wait for page to load
    page.wait_for_timeout(2000)
    
    # Try clicking on the "下载资源" menu item
    menu_items = page.query_selector_all('.menu-item, .sidebar-item, nav a, nav button, [data-menu]')
    for item in menu_items:
        text = item.inner_text()
        if '下载资源' in text or '下载' in text:
            item.click()
            break
    
    page.wait_for_timeout(2000)
    
    # Take screenshot
    screenshot_path = r"C:\Users\xueta\Documents\web-xiaobaigame\screenshot_admin_resources.png"
    page.screenshot(path=screenshot_path, full_page=False)
    print(f"Screenshot saved to {screenshot_path}")
    
    browser.close()
