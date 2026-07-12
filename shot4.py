from playwright.sync_api import sync_playwright
import time, urllib.request, json

# Get token via API
data = json.dumps({"username":"admin","password":"admin123"}).encode()
req = urllib.request.Request("http://localhost:8000/api/admin/login", data=data,
    headers={"Content-Type":"application/json"})
resp = urllib.request.urlopen(req)
token = json.loads(resp.read())["data"]["token"]
print("Token obtained")

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(viewport={"width": 1400, "height": 900})
    page.set_default_timeout(15000)

    # Set auth in localStorage
    page.goto("http://localhost:8000/admin/index.html", wait_until="domcontentloaded")
    js_code = "localStorage.setItem(\"admin_token\", \"" + token + "\"); localStorage.setItem(\"admin_username\", \"admin\");"
    page.evaluate(js_code)
    page.goto("http://localhost:8000/admin/index.html", wait_until="domcontentloaded")
    time.sleep(3)
    print("URL:", page.url)

    # Screenshot: Dashboard
    page.screenshot(path=r"C:\Users\xueta\Documents\web-xiaobaigame\screenshot_dashboard.png")
    print("1. Dashboard done")

    # Click "下载渠道" nav item using text
    page.click("text=下载渠道")
    time.sleep(2)
    page.screenshot(path=r"C:\Users\xueta\Documents\web-xiaobaigame\screenshot_providers_list.png")
    print("2. Providers list done")

    # Click add provider button
    page.click("#add-provider-btn")
    time.sleep(1)
    page.screenshot(path=r"C:\Users\xueta\Documents\web-xiaobaigame\screenshot_providers_add.png")
    print("3. Add provider modal done")

    # Close modal
    page.click(".prov-modal-close")
    time.sleep(0.5)

    # Click "下载资源" nav
    page.click("text=下载资源")
    time.sleep(2)
    page.screenshot(path=r"C:\Users\xueta\Documents\web-xiaobaigame\screenshot_resources_list.png")
    print("4. Resources list done")

    # Open add resource modal
    page.click("#add-resource-btn")
    time.sleep(2)
    page.screenshot(path=r"C:\Users\xueta\Documents\web-xiaobaigame\screenshot_resources_add.png")
    print("5. Add resource modal done")

    browser.close()
    print("All screenshots captured!")
