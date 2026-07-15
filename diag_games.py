import sys
sys.stdout.reconfigure(encoding='utf-8')
from playwright.sync_api import sync_playwright
import time

BASE = "http://localhost:8000"

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    context = browser.new_context(viewport={"width": 1280, "height": 800})
    page = context.new_page()
    
    console_msgs = []
    page.on("console", lambda msg: console_msgs.append(f"[{msg.type}] {msg.text}"))
    page.on("pageerror", lambda err: console_msgs.append(f"PAGE_ERROR: {err}"))
    
    # ----- /games -----
    print("=" * 60)
    print("DIAGNOSTIC: /games")
    print("=" * 60)
    page.goto(f"{BASE}/games", wait_until="domcontentloaded", timeout=15000)
    time.sleep(0.5)
    
    html = page.content()
    print(f"DOM HTML length: {len(html)}")
    print(f"DOM HTML first 500 chars: {html[:500]}")
    print(f"DOM body.inner_text length: {len(page.inner_text('body'))}")
    
    print("\nConsole messages:")
    for m in console_msgs:
        print(f"  {m}")
    
    # Check if there are any elements at all
    all_elems = page.locator("*").count()
    print(f"\nTotal DOM elements: {all_elems}")
    
    # Check specific elements
    for sel in ["body", "head", "#game-grid", "#category-filter", "header", "script"]:
        count = page.locator(sel).count()
        print(f"  {sel}: {count}")
    
    browser.close()
