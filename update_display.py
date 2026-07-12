# -*- coding: utf-8 -*-
import sys
sys.stdout.reconfigure(encoding='utf-8')

PATH_JS = r"C:\Users\xueta\Documents\web-xiaobaigame\admin\js\main.js"
PATH_CSS = r"C:\Users\xueta\Documents\web-xiaobaigame\admin\css\style.css"

# === Update resource table provider display ===
with open(PATH_JS, "r", encoding="utf-8") as f:
    content = f.read()

old_display = "'<td><span class=\"provider-tag provider-' + r.provider + '\">' + providerLabel(r.provider) + '</span></td>'"
new_display = "'<td><span class=\"provider-tag provider-' + r.provider + '\">' + escHtml(r.provider_label || r.provider || \"\") + '</span></td>'"
if old_display in content:
    content = content.replace(old_display, new_display)
    print("JS: Updated resource table to use provider_label")

with open(PATH_JS, "w", encoding="utf-8") as f:
    f.write(content)

# === Update CSS: add new provider tag colors ===
with open(PATH_CSS, "r", encoding="utf-8") as f:
    css = f.read()

old_prov_css = """.provider-115 { background: #fce4ec; color: #c62828; }
/* game select dropdown */"""

new_prov_css = """.provider-115 { background: #fce4ec; color: #c62828; }
.provider-xunlei { background: #e8eaf6; color: #283593; }
.provider-uc { background: #fff8e1; color: #e65100; }
.provider-mobile { background: #e0f2f1; color: #00695c; }
.provider-tianyi { background: #f3e5f5; color: #6a1b9a; }
/* game select dropdown */"""

if old_prov_css in css:
    css = css.replace(old_prov_css, new_prov_css)
    print("CSS: Added 4 new provider tag styles")

with open(PATH_CSS, "w", encoding="utf-8") as f:
    f.write(css)

print("Done")
