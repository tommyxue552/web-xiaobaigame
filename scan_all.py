import sys, re
sys.stdout.reconfigure(encoding="utf-8")

with open("admin/js/main.js", "r", encoding="utf-8") as f:
    lines = f.readlines()

# Find ALL lines starting with " (JS string building) or containing = "..." with HTML
# that might have unescaped HTML attr quotes
for i, line in enumerate(lines, 1):
    s = line.rstrip("\n")
    # Skip comments
    if s.strip().startswith("//"):
        continue
    
    # Check for double-quote JS strings containing HTML tags
    # Pattern: the line uses " for JS string AND has HTML tags
    has_html = any(tag in s for tag in ["<div", "<span", "<button", "<input", "<table", "<tr", "<td", "<th", "<h", "<p ", "<label", "<select", "<option", "<a ", "<form", "<textarea", "<img", "<li", "<ul", "<ol"])
    
    if not has_html:
        continue
    
    # Does line use double-quotes for JS strings?
    if not ('"' in s):
        continue
    
    # Check for unescaped HTML attr quotes: pattern = followed by unescaped "
    # Find all =\" patterns (already escaped - these are OK)
    # Find all =" patterns (these are unescaped HTML attrs - check if in a JS double-quoted context)
    
    # Heuristic: if line starts with " or has =" where = is not preceded by \
    # and the line doesn't have single-quote JS strings, it could be broken
    
    # Lines that use single quotes for JS are fine
    if s.strip().startswith("'"):
        continue
    if "= '" in s or "+ '" in s or "('" in s:
        continue
    
    # Now check for = followed by unescaped " within what looks like HTML
    # Pattern: something="something" inside a JS double-quoted string
    unescaped_eq_quotes = re.findall(r'(?<!\\)="', s)
    if unescaped_eq_quotes:
        # Check if these are inside a JS double-quoted string
        # If the line starts with " or has "+ or has >" it uses " for JS
        uses_dq_js = (s.strip().startswith('"') or '"+' in s or '>"' in s or '";' in s or '")' in s)
        if uses_dq_js:
            print(f"L{i} [UNESCAPED ATTR]: {s[:150]}")

print("\n--- DONE ---")
