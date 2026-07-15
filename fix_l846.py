import sys
sys.stdout.reconfigure(encoding="utf-8")

with open("admin/js/main.js", "r", encoding="utf-8") as f:
    content = f.read()

# Fix line 846
old = 'body.innerHTML = "<div style="padding:40px;text-align:center;color:#888;">加载中...</div>";'
new = 'body.innerHTML = "<div style=\\"padding:40px;text-align:center;color:#888;\\">加载中...</div>";'
if old in content:
    content = content.replace(old, new)
    print("Fixed L846: renderProviderManagement innerHTML")
else:
    print("L846 pattern not found - checking partial...")
    # Try partial match
    if 'style="padding' in content:
        print("  partial match found, need different approach")

with open("admin/js/main.js", "w", encoding="utf-8") as f:
    f.write(content)
