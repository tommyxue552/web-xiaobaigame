import sys
sys.stdout.reconfigure(encoding="utf-8")

with open("admin/js/main.js", "r", encoding="utf-8") as f:
    content = f.read()

# Line 1212: comment and code merged on same line
# Current: // garbled comment        var hash = window.location.hash.replace("#", "");
# Fix: split into comment line + code line
old = '        // \ufffd\ufffd\ufffd URL hash \u05f4\u05f4\u05f4\ufffd\ufffd\ufffd\ufffd\ufffd\ufffd        var hash = window.location.hash.replace("#", "");'
new = '        // Initialize from URL hash\n        var hash = window.location.hash.replace("#", "");'

if old in content:
    content = content.replace(old, new)
    print("Fixed: hash init line split")
else:
    # Try with raw bytes approach
    print("Exact match not found, trying alternative...")
    # Find the line by pattern
    import re
    pattern = r'// .*?var hash = window\.location\.hash\.replace\("#", ""\)'
    match = re.search(pattern, content)
    if match:
        print(f"  Pattern matched: {match.group()[:80]}...")
        replacement = '        // Initialize from URL hash\n        var hash = window.location.hash.replace("#", "");'
        content = content.replace(match.group(), replacement)
        print("  Fixed via regex")
    else:
        print("  No match found")

with open("admin/js/main.js", "w", encoding="utf-8") as f:
    f.write(content)
