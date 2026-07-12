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

    # Listen for console messages
    page.on("console", lambda msg: print("CONSOLE:", msg.type, msg.text))
    page.on("pageerror", lambda err: print("PAGE ERROR:", err))

    page.goto("http://localhost:8000/admin/index.html", wait_until="domcontentloaded")
    js_code = "localStorage.setItem(\"admin_token\", \"" + token + "\"); localStorage.setItem(\"admin_username\", \"admin\");"
    page.evaluate(js_code)
    page.goto("http://localhost:8000/admin/index.html", wait_until="domcontentloaded")
    time.sleep(3)

    # Check what nav items exist
    items = page.evaluate("""() => {
        var navItems = document.querySelectorAll(".nav-item");
        var result = [];
        navItems.forEach(function(item, i) {
            result.push(i + ": " + item.textContent.trim() + " (hidden: " + item.classList.contains("hidden-menu") + ")");
        });
        return result;
    }""")
    print("Nav items found:")
    for item in items:
        print("  ", item)

    page.screenshot(path=r"C:\Users\xueta\Documents\web-xiaobaigame\screenshot_dashboard.png")
    print("Dashboard done")

    # Try using page.get_by_text
    page.get_by_text("下载渠道").click()
    time.sleep(2)
    page.screenshot(path=r"C:\Users\xueta\Documents\web-xiaobaigame\screenshot_providers_list.png")
    print("Providers done")

    browser.close()
