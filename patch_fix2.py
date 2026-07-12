import sys

# Step 1: Read fixed_section.js with proper UTF-8
with open("fixed_section.js", "r", encoding="utf-8") as f:
    content = f.read()

# Step 2: Fix the two "?" placeholders
old1 = 'info.textContent = "? " + total + " ?"'
new1 = 'info.textContent = "\u5171 " + total + " \u6761"'
content = content.replace(old1, new1)

old2 = "'<span class=\"page-info\">?' + s.page + '/' + totalPages + ' ?</span>'"
new2 = "'<span class=\"page-info\">\u7b2c' + s.page + '/' + totalPages + ' \u9875</span>'"
content = content.replace(old2, new2)

print("Fixes applied, old1 gone:", old1 not in content)
print("Fixes applied, old2 gone:", old2 not in content)

# Step 3: Triple-UTF-8 encode
def t3(s):
    b1 = s.encode('utf-8')
    s2 = b1.decode('latin-1')
    b2 = s2.encode('utf-8')
    s3 = b2.decode('latin-1')
    b3 = s3.encode('utf-8')
    return b3

encoded_bytes = t3(content)
print("Encoded section size:", len(encoded_bytes))

# Step 4: Find the section in main.js using a UNIQUE marker
# "var downloadResourceState" is all ASCII, unique in the file
# But we need to find the exact section start
# Use the triple-encoded first line comment with Chinese
# The prefix before Chinese is: "    // ==================== "
# The Chinese chars "下载资源管理" triple-encoded
with open("admin/js/main.js", "rb") as f:
    main_bytes = f.read()

# Create the triple-encoded first line of the section
first_line = "    // ==================== \u4e0b\u8f7d\u8d44\u6e90\u7ba1\u7406 ===================="
encoded_first_line = t3(first_line)

# Find this specific sequence
start_pos = main_bytes.find(encoded_first_line)
print("Searching for encoded first line, found at:", start_pos)

if start_pos < 0:
    # Try without the leading spaces
    alt_first = "// ==================== \u4e0b\u8f7d\u8d44\u6e90\u7ba1\u7406 ===================="
    encoded_alt = t3(alt_first)
    start_pos = main_bytes.find(encoded_alt)
    print("Alt search found at:", start_pos)

if start_pos < 0:
    # Last resort: search for triple-encoded "下载资源管理"
    keyword = t3("\u4e0b\u8f7d\u8d44\u6e90\u7ba1\u7406")
    start_pos = main_bytes.find(keyword)
    if start_pos >= 0:
        # Go back to find the start of the line
        # Find the preceding "// " or start of the comment block
        line_start = main_bytes.rfind(b"\n", 0, start_pos)
        section_marker = main_bytes.rfind(b"// =====", 0, start_pos)
        start_pos = section_marker if section_marker > line_start else line_start + 1
    print("Keyword search, adjusted to:", start_pos)

# Find the next section marker after our section
# Search for "function renderSettings" which is ASCII
settings_marker = b"function renderSettings"
end_pos = main_bytes.find(settings_marker, start_pos)
print("renderSettings at:", end_pos)

if start_pos >= 0 and end_pos > start_pos:
    # Include any whitespace before the section  
    # Back up to include the leading newline/whitespace
    while start_pos > 0 and main_bytes[start_pos - 1:start_pos] in (b'\n', b'\r'):
        start_pos -= 1
    
    new_main = main_bytes[:start_pos] + b"\r\n" + encoded_bytes + b"\r\n\r\n    " + main_bytes[end_pos:]
    with open("admin/js/main.js", "wb") as f:
        f.write(new_main)
    print("Successfully patched main.js")
    print("Old size:", len(main_bytes), "New size:", len(new_main))
else:
    print("Could not locate section boundaries!")
    print("start_pos:", start_pos, "end_pos:", end_pos)
