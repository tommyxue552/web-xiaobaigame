import sys
sys.stdout.reconfigure(encoding="utf-8")

with open("admin/js/main.js", "r", encoding="utf-8") as f:
    lines = f.readlines()

# Find all lines with innerHTML = "..." or similar patterns that have unescaped HTML attrs
for i, line in enumerate(lines, 1):
    s = line.strip()
    # Look for lines with innerHTML or html that set HTML with attr=value patterns
    if ("innerHTML" in s or "html " in s or "html=" in s or "html =" in s) and s.count('"') >= 4:
        # Count potential HTML attribute patterns with unescaped quotes
        # Pattern like: ="xxx" inside a JS string
        # If line has HTML tag-like content
        if any(tag in s for tag in ["<div", "<span", "<button", "<input", "<table", "<tr", "<td", "<th", "<h", "<p", "<label", "<select", "<option", "<a ", "<form", "<textarea"]):
            # Check if HTML attr quotes are escaped
            # Quick check: does it have =\"  patterns?
            if '=\\"' not in s and s.count('="') > 0:
                print(f"L{i} [UNESCAPED]: {s[:150]}")
            elif '=\\"' not in s:
                # Has HTML tags but maybe all quotes are JS delimiters
                pass
            else:
                # Has some escaped quotes - check for mixed
                # Count unescaped ="
                import re
                unescaped_attr = re.findall(r'(?<!\\)="', s)
                if unescaped_attr:
                    print(f"L{i} [MIXED] ({len(unescaped_attr)} unescaped attr): {s[:150]}")

print("\n--- DONE ---")
