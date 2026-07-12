# -*- coding: utf-8 -*-
import sys
sys.stdout.reconfigure(encoding='utf-8')

with open(r"C:\Users\xueta\Documents\web-xiaobaigame\admin\js\main.js", "r", encoding="utf-8") as f:
    content = f.read()

# Check key sections
checks = [
    ('MENUS providers', 'id: "providers"'),
    ('Switch providers', 'case "providers": renderProviderManagement'),
    ('Dynamic select', 'provider_id'),
    ('editResource provider_id', 'r.provider_id'),
    ('saveResource provider_id', 'parseInt(document.getElementById("res-provider")'),
    ('loadProviderDropdown', 'function loadProviderDropdown'),
    ('renderProviderManagement', 'function renderProviderManagement'),
    ('providerState', 'var providerState'),
]
for label, pattern in checks:
    found = pattern in content
    print(f"{'[OK]' if found else '[FAIL]'} {label}: {pattern}")

print(f"\nTotal length: {len(content)} chars")
