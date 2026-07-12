# -*- coding: utf-8 -*-
import sys, re
sys.stdout.reconfigure(encoding='utf-8')

with open(r"C:\Users\xueta\Documents\web-xiaobaigame\admin\js\main.js", "r", encoding="utf-8") as f:
    content = f.read()

print("File length:", len(content))
print("Has MENUS:", "var MENUS =" in content)

# Check what the resources menu line looks like
idx = content.find('id: "resources"')
if idx >= 0:
    print("resources menu around idx", idx)
    print(repr(content[idx:idx+100]))
else:
    print("resources menu NOT FOUND")
