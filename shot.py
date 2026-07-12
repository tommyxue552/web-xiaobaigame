from playwright.sync_api import sync_playwright
import time, urllib.request, json

# Get token via API
data = json.dumps({"username":"admin","password":"admin123"}).encode()
req = urllib.request.Request("http://localhost:8000/api/admin/login", data=data,
    headers={"Content-Type":"application/json"})
resp = urllib.request.urlopen(req)
token = json.loads(resp.read())["data"]["token"]

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(viewport={"width": 1400, "height": 900})

    # Set auth in localStorage before navigating  
    page.goto("http://localhost:8000/admin/index.html")
    js = "localStorage.setItem('admin_token', '" + token + "'); localStorage.setItem('admin_username', 'admin');"
    page.evaluate(js)
    page.goto("http://localhost:8000/admin/index.html")
    time.sleep(3)
    print("Logged in, URL:", page.url)

    page.screenshot(path="C:/Users/xueta/Documents/web-xiaobaigame/screenshot_dashboard.png")
    print("Screenshot: dashboard")

    # Click providers nav
    page.click(".nav-item:nth-child(4)")
    time.sleep(1.5)
    page.screenshot(path="C:/Users/xueta/Documents/web-xiaobaigame/screenshot_providers_list.png")
    print("Screenshot: providers list")

    browser.close()
    print("Done")
