import sys
sys.stdout.reconfigure(encoding="utf-8")

with open("admin/js/main.js", "r", encoding="utf-8") as f:
    lines = f.readlines()

# We know the error is at line 865. Let's look at the broader context.
# The real issue: unescaped double quotes inside JS double-quoted strings
# Pattern: "..." breaks because HTML attr has " instead of \"

# Check each line for potential quote issues in string building
for i, line in enumerate(lines, 1):
    s = line.rstrip("\n")
    if not s.strip().startswith('"'):
        continue
    # Count raw (non-escaped) double-quote pairs
    # A JS string line should have an even number of raw double quotes
    # (the opening " and closing "+ or just " for continuation)
    
    # But we need to be smarter: count how many " are JS string delimiters vs HTML
    # Let's just look at lines that have HTML tags in them
    if not any(tag in s for tag in ["<td", "<tr", "<th", "<button", "<span", "<div", "<input", "<select", "<option", "<a ", "<li", "<h", "<label"]):
        continue
    
    # Count \" (escaped) vs " (raw)
    raw_quotes = 0
    j = 0
    while j < len(s):
        if s[j:j+2] == '\\"':
            j += 2
            continue
        if s[j] == '"':
            raw_quotes += 1
        j += 1
    
    if raw_quotes % 2 != 0:
        print(f"ODD [{raw_quotes}] L{i}: {s[:150]}")

print("--- DONE ---")
