import sys

# 1. Read fixed_section.js and fix the two "?" placeholders
with open("fixed_section.js", "r", encoding="utf-8") as f:
    content = f.read()

# Fix count info
old1 = 'info.textContent = "? " + total + " ?"'
new1 = 'info.textContent = "\u5171 " + total + " \u6761"'
content = content.replace(old1, new1)
assert old1 not in content, "Fix 1 failed"

# Fix pagination
old2 = "'<span class=\"page-info\">?' + s.page + '/' + totalPages + ' ?</span>'"
new2 = "'<span class=\"page-info\">\u7b2c' + s.page + '/' + totalPages + ' \u9875</span>'"
content = content.replace(old2, new2)
assert old2 not in content, "Fix 2 failed"

# Also fix "原始URLURL" -> "原始URL"
content = content.replace("原始URLURL", "原始URL")

print("Fixed section OK, length:", len(content))

# 2. Read main.js as binary
with open("admin/js/main.js", "rb") as f:
    main = bytearray(f.read())

print("Original main.js size:", len(main))

# 3. Fix MENU label: "资源管理" -> "下载资源"
# "资源管理" UTF-8 bytes at offset 2325 (in the context of label: ")
old_label = "资源管理".encode("utf-8")
new_label = "下载资源".encode("utf-8")
# Find exact position
search = b'label: "' + old_label + b'"'
pos = main.find(search)
if pos >= 0:
    label_start = pos + len(b'label: "')
    print(f"MENU label found at byte {label_start}, old: {old_label.hex()}, new: {new_label.hex()}")
    # Replace just the Chinese bytes
    main[label_start:label_start + len(old_label)] = new_label
else:
    print("WARNING: MENU label not found!")

# 4. Replace old renderResourceManagement section
# Old section: from byte 31779 (section comment start) to just before renderSettings at 33898
old_section_start = 31779
old_section_end = 33898  # exclusive (renderSettings starts here)

# Verify the old section
old_section = bytes(main[old_section_start:old_section_end])
old_str = old_section.decode("utf-8", errors="replace")
if "资源管理（下载链接）" in old_str or "renderResourceManagement" in old_str:
    print("Old section verified OK")
else:
    print("WARNING: Old section content unexpected!")

# Encode new section as UTF-8
new_section = content.encode("utf-8")
print(f"New section size: {len(new_section)} bytes (old was {old_section_end - old_section_start})")

# Replace
main[old_section_start:old_section_end] = new_section

# Adjust for size difference
# Since old was 2119 bytes and new is different, the bytearray handles this automatically

print(f"Final main.js size: {len(main)}")

# 5. Write back
with open("admin/js/main.js", "wb") as f:
    f.write(main)

print("Done! main.js patched successfully.")
