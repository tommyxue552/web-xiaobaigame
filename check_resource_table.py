# -*- coding: utf-8 -*-
import sys
sys.stdout.reconfigure(encoding='utf-8')

with open(r"C:\Users\xueta\Documents\web-xiaobaigame\admin\js\main.js", "r", encoding="utf-8") as f:
    content = f.read()

# Find the providerLabel function and its usage in the resource table
idx = content.find('function providerLabel')
if idx >= 0:
    line_end = content.find('\n', idx)
    print("providerLabel function:")
    print(content[idx:line_end+50])
    print()

# Find the resource table row that displays provider
idx = content.find("provider-tag provider-")
if idx >= 0:
    print("Resource table provider display:")
    print(content[idx-50:idx+150])
