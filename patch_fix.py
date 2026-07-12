import sys

# Step 1: Read fixed_section.js with proper UTF-8
with open("fixed_section.js", "r", encoding="utf-8") as f:
    content = f.read()

# Step 2: Fix the two "?" placeholders
# Line: if (info) info.textContent = "? " + total + " ?";
old1 = 'info.textContent = "? " + total + " ?"'
new1 = 'info.textContent = "\u5171 " + total + " \u6761"'
content = content.replace(old1, new1)

# Line: phtml += '<span class="page-info">?' + s.page + '/' + totalPages + ' ?</span>';
old2 = "'<span class=\"page-info\">?' + s.page + '/' + totalPages + ' ?</span>'"
new2 = "'<span class=\"page-info\">\u7b2c' + s.page + '/' + totalPages + ' \u9875</span>'"
content = content.replace(old2, new2)

print("Fixed content length:", len(content))
print("Check old1 still present:", old1 in content)
print("Check old2 still present:", old2 in content)
print("Check new1 present:", new1 in content)
print("Check new2 present:", new2 in content)

# Step 3: Triple-UTF-8 encode to match main.js encoding
# UTF-8 -> latin1 -> UTF-8 -> latin1 -> UTF-8
def t3(s):
    # First encode normal UTF-8
    b1 = s.encode('utf-8')
    # Decode as latin-1, then re-encode as UTF-8
    s2 = b1.decode('latin-1')
    b2 = s2.encode('utf-8')
    # Decode as latin-1 again, then re-encode as UTF-8
    s3 = b2.decode('latin-1')
    b3 = s3.encode('utf-8')
    return b3

encoded_bytes = t3(content)

# Also encode the section comment prefix for finding boundaries in main.js
# The fixed_section.js starts with "    // ==================== "
# In triple-encoded form, the ASCII part stays ASCII, but let me encode the full first line prefix
first_line_prefix = "    // ==================== "
encoded_prefix = t3(first_line_prefix)

print("Encoded prefix bytes:", encoded_prefix.hex())
print("Encoded total bytes:", len(encoded_bytes))

# Step 4: Find the section in main.js
with open("admin/js/main.js", "rb") as f:
    main_bytes = f.read()

# Find the start of the section
# Search for the encoded first line prefix
start_pos = main_bytes.find(encoded_prefix)
print("Start position:", start_pos)

if start_pos < 0:
    print("Could not find section start!")
    # Try searching for just "// ===================="
    ascii_prefix = b"    // ==================== "
    start_pos = main_bytes.find(ascii_prefix)
    print("ASCII prefix position:", start_pos)

# Find the end - search for the next "function renderSettings" or end of IIFE
# The section ends before "function renderSettings"
# Search for "function renderSettings" (should be ascii in triple-encoding)
settings_marker = b"function renderSettings"
end_pos = main_bytes.find(settings_marker, start_pos if start_pos > 0 else 0)
print("renderSettings position:", end_pos)

if start_pos >= 0 and end_pos > start_pos:
    # Also find the content before and after to preserve any whitespace/newlines
    # We want to replace from the section start to just before renderSettings
    new_main = main_bytes[:start_pos] + encoded_bytes + b"\r\n\r\n    " + main_bytes[end_pos:]
    with open("admin/js/main.js", "wb") as f:
        f.write(new_main)
    print("Successfully patched main.js, new size:", len(new_main))
else:
    print("Could not locate section boundaries!")
