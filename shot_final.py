import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
from playwright.sync_api import sync_playwright
import time, urllib.request, json

data = json.dumps({"username":"admin","password":"admin123"}).encode()
req = urllib.request.Request("http://localhost:8000/api/admin/login", data=data,
    headers={"Content-Type":"application/json"})
resp = urllib.request.urlopen(req)
token = json.loads(resp.read())["data"]["token"]

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(viewport={"width": 1400, "height": 900})
    page.set_default_timeout(15000)

    page.on("pageerror", lambda err: print("PAGE ERROR:", err))

    page.goto("http://localhost:8000/admin/index.html", wait_until="domcontentloaded")
    js_code = "localStorage.setItem(\"admin_token\", \"" + token + "\"); localStorage.setItem(\"admin_username\", \"admin\");"
    page.evaluate(js_code)
    page.goto("http://localhost:8000/admin/index.html", wait_until="domcontentloaded")
    time.sleep(3)

    # Screenshot 1: Dashboard
    page.screenshot(path=r"C:\Users\xueta\Documents\web-xiaobaigame\screenshot_1_dashboard.png")
    print("1. Dashboard")

    # Click providers
    page.get_by_text("下载渠道").click()
    time.sleep(2)
    page.screenshot(path=r"C:\Users\xueta\Documents\web-xiaobaigame\screenshot_2_providers_list.png")
    print("2. Providers list")

    # Add provider modal
    page.click("#add-provider-btn")
    time.sleep(1)
    page.screenshot(path=r"C:\Users\xueta\Documents\web-xiaobaigame\screenshot_3_providers_add.png")
    print("3. Add provider modal")

    page.click(".prov-modal-close")
    time.sleep(0.5)

    # Go to resources
    page.get_by_text("下载资源").click()
    time.sleep(2)
    page.screenshot(path=r"C:\Users\xueta\Documents\web-xiaobaigame\screenshot_4_resources_list.png")
    print("4. Resources list")

    # Add resource modal
    page.click("#add-resource-btn")
    time.sleep(2)
    page.screenshot(path=r"C:\Users\xueta\Documents\web-xiaobaigame\screenshot_5_resources_add.png")
    print("5. Add resource modal")

    browser.close()
    print("All screenshots captured!")
