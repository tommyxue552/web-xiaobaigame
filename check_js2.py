# -*- coding: utf-8 -*-
import sys
sys.stdout.reconfigure(encoding='utf-8')

with open(r"C:\Users\xueta\Documents\web-xiaobaigame\admin\js\main.js", "r", encoding="utf-8") as f:
    content = f.read()

# Find key patterns
search_items = [
    'id: "resources"',
    'case "resources"',
    'case "settings"',
    'name="provider"',
    'res-provider',
    'function renderResourceManagement',
    'function renderSettings',
    'function openResourceModal',
    'document.getElementById("res-provider").value = r.provider',
    'provider: document.getElementById("res-provider").value',
]
for s in search_items:
    idx = content.find(s)
    if idx >= 0:
        line_start = content.rfind('\n', 0, idx) + 1
        line_end = content.find('\n', idx)
        print(f"--- Found '{s}' at offset {idx} ---")
        print(content[line_start:line_end])
    else:
        print(f"--- NOT FOUND: '{s}' ---")
