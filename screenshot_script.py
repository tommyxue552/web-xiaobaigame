import urllib.request, json, ssl
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

# Login
data = json.dumps({"username": "admin", "password": "admin123"}).encode()
req = urllib.request.Request("http://localhost:8000/api/admin/login", data=data, headers={"Content-Type": "application/json"})
resp = urllib.request.urlopen(req, context=ctx)
result = json.loads(resp.read())
token = result["data"]["token"]
print(f"Got token: {token[:30]}...")

from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(viewport={"width": 1440, "height": 900})
    
    # First navigate to admin page to set domain
    page.goto("http://localhost:8000/admin/index.html")
    
    # Set auth token in localStorage
    page.evaluate(f'localStorage.setItem("xiaobai_token", "{token}")')
    page.evaluate('localStorage.setItem("xiaobai_user", "admin")')
    
    # Reload the page to pick up the token
    page.goto("http://localhost:8000/admin/index.html")
    page.wait_for_timeout(3000)
    
    page.screenshot(path="C:/Users/xueta/Documents/web-xiaobaigame/screenshots/dashboard_new.png", full_page=False)
    
    browser.close()
    print("Screenshot saved")
