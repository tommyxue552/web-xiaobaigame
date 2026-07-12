import sys, os
sys.stdout.reconfigure(encoding='utf-8')

def t3(s):
    '''Triple-UTF-8 encode: utf8 -> latin1 -> utf8 -> latin1 -> utf8'''
    return s.encode('utf-8').decode('latin-1').encode('utf-8').decode('latin-1').encode('utf-8')

# Read new JS code
with open(r'C:\Users\xueta\Documents\web-xiaobaigame\new_resource_section.js', 'r', encoding='utf-8') as f:
    js_code = f.read()

# Encode the whole thing as triple-UTF-8 to match main.js
encoded_js = t3(js_code)
print(f'New section: {len(js_code)} chars -> {len(encoded_js)} bytes')

# Read main.js
main_path = r'C:\Users\xueta\Documents\web-xiaobaigame\admin\js\main.js'
with open(main_path, 'rb') as f:
    raw = f.read()

print(f'Original main.js: {len(raw)} bytes')

# 1. Replace menu label
old_menu_label = t3('资源管理')
new_menu_label = t3('下载资源')
print(f'Old menu label bytes: {old_menu_label.hex()}')
print(f'New menu label bytes: {new_menu_label.hex()}')
count = raw.count(old_menu_label)
print(f'Menu label occurrences: {count}')
raw = raw.replace(old_menu_label, new_menu_label, 1)

# 2. Replace the resource management section
# Old section: bytes 37689-40063
old_section_start = 37689
old_section_end = 40063
# Recalculate after menu label replacement (may shift by a few bytes)
# Let's find the section comment again
section_marker = b'===\r\n    function renderResourceManagement(body)'
idx = raw.find(section_marker)
# Go back to find the start of the line
line_start = raw.rfind(b'\n', 0, idx) + 1
# Also include the comment line before if it exists
comment_start = raw.rfind(b'// ===', 0, line_start - 1)
if comment_start < 0:
    section_start = line_start
else:
    # Find the beginning of that line
    section_start = raw.rfind(b'\n', 0, comment_start) + 1

# Find where the section ends - the next '====' after the function
next_section = raw.find(b'// ===', idx + 100)
if next_section < 0:
    next_section = raw.find(b'function renderSettings', idx)
    if next_section >= 0:
        next_section = raw.rfind(b'\n', 0, next_section) + 1

print(f'Section start: {section_start}, end: {next_section}')
print(f'Old section length: {next_section - section_start} bytes')

# Build the new section
new_section = encoded_js
print(f'New section length: {len(new_section)} bytes')

# Replace
new_raw = raw[:section_start] + new_section + raw[next_section:]

print(f'New main.js: {len(new_raw)} bytes (was {len(raw)})')

# Write back
with open(main_path, 'wb') as f:
    f.write(new_raw)

print('Done! main.js updated successfully.')
