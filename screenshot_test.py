
from playwright.sync_api import sync_playwright
import time

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(viewport={"width": 1400, "height": 900})

    # Go to admin main page - if not logged in, redirects to login
    page.goto("http://localhost:8000/admin/index.html")
    time.sleep(1)

    # Check if we are on login page
    if page.url.endswith("login.html"):
        page.fill("#username", "admin")
        page.fill("#password", "admin123")
        page.click("#login-btn")
        page.wait_for_url("**/admin/index.html**", timeout=10000)
        time.sleep(2)
    print("Logged in, current URL:", page.url)

    # Navigate to providers page
    page.evaluate("""() => {
        var items = document.querySelectorAll(".nav-item");
        items.forEach(function(el) {
            if (el.textContent.includes("涓嬭浇娓犻亾")) el.click();
        });
    }""")
    time.sleep(2)
    page.screenshot(path="screenshot_providers_list.png", full_page=False)
    print("Screenshot: providers list")

    # Open add provider modal
    page.click("#add-provider-btn")
    time.sleep(0.8)
    page.screenshot(path="screenshot_providers_add.png", full_page=False)
    print("Screenshot: add provider modal")

    # Close modal
    page.click(".prov-modal-close")
    time.sleep(0.5)

    # Navigate to resources
    page.evaluate("""() => {
        var items = document.querySelectorAll(".nav-item");
        items.forEach(function(el) {
            if (el.textContent.includes("涓嬭浇璧勬簮")) el.click();
        });
    }""")
    time.sleep(2)
    page.screenshot(path="screenshot_resources_list.png", full_page=False)
    print("Screenshot: resources list")

    # Open add resource modal
    page.click("#add-resource-btn")
    time.sleep(2)  # Wait for provider dropdown AJAX
    page.screenshot(path="screenshot_resources_add.png", full_page=False)
    print("Screenshot: add resource modal")

    browser.close()
    print("All screenshots captured")

