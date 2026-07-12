from playwright.sync_api import sync_playwright
import time, urllib.request, json

# Get token via API
data = json.dumps({"username":"admin","password":"admin123"}).encode()
req = urllib.request.Request("http://localhost:8000/api/admin/login", data=data,
    headers={"Content-Type":"application/json"})
resp = urllib.request.urlopen(req)
token = json.loads(resp.read())["data"]["token"]
print("Token:", token[:20] + "...")

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(viewport={"width": 1400, "height": 900})
    page.set_default_timeout(10000)

    # Set auth in localStorage
    page.goto("http://localhost:8000/admin/index.html", wait_until="domcontentloaded")
    js_code = "localStorage.setItem(\"admin_token\", \"" + token + "\"); localStorage.setItem(\"admin_username\", \"admin\");"
    page.evaluate(js_code)
    print("Token set in localStorage")

    # Reload page
    page.goto("http://localhost:8000/admin/index.html", wait_until="domcontentloaded")
    time.sleep(3)
    print("URL after reload:", page.url)

    page.screenshot(path=r"C:\Users\xueta\Documents\web-xiaobaigame\screenshot_dashboard.png")
    print("Dashboard screenshot taken")

    # Click providers nav - the 4th nav item
    page.click(".nav-item:nth-child(4)")
    time.sleep(2)
    page.screenshot(path=r"C:\Users\xueta\Documents\web-xiaobaigame\screenshot_providers_list.png")
    print("Providers list screenshot taken")

    # Click add provider button
    page.click("#add-provider-btn")
    time.sleep(1)
    page.screenshot(path=r"C:\Users\xueta\Documents\web-xiaobaigame\screenshot_providers_add.png")
    print("Add provider modal screenshot taken")

    # Close modal and go to resources
    page.click(".prov-modal-close")
    time.sleep(0.5)
    page.click(".nav-item:nth-child(3)")
    time.sleep(2)
    page.screenshot(path=r"C:\Users\xueta\Documents\web-xiaobaigame\screenshot_resources_list.png")
    print("Resources list screenshot taken")

    # Open add resource modal
    page.click("#add-resource-btn")
    time.sleep(2)
    page.screenshot(path=r"C:\Users\xueta\Documents\web-xiaobaigame\screenshot_resources_add.png")
    print("Add resource modal screenshot taken")

    browser.close()
    print("All screenshots captured!")
