# -*- coding: utf-8 -*-
"""Fix main.js syntax errors by converting HTML strings from double to single quotes."""
import sys, io, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

filepath = r"C:\Users\xueta\Documents\web-xiaobaigame\admin\js\main.js"

with open(filepath, 'r', encoding='utf-8-sig') as f:
    content = f.read()

# Fix 1: literal `n -> newline
content = content.replace('`n', '\n')

# Fix 2: Find all cases where a double-quoted JS string contains 
# unescaped HTML attributes (pattern: ="word")
# Strategy: for lines that have both "< and >" inside a JS string,
# if the line also has =" pattern (HTML attribute), the string is broken.
# Convert the outer string quotes from " to '

lines = content.split('\n')
fixed_lines = []
fixes_count = 0

for line in lines:
    stripped = line.strip()
    
    # Skip comments and empty lines
    if not stripped or stripped.startswith('//') or stripped.startswith('*') or stripped.startswith('/*'):
        fixed_lines.append(line)
        continue
    
    # Check if this line has a broken double-quoted string pattern
    # Pattern: "<...="word"...>" or "...<...="...>..."
    # The issue is: double quotes used for both JS string and HTML attributes
    
    # Detect: line has "=" but not \"= (escaped equals inside string)
    # This indicates HTML attributes inside a JS string
    
    # Simple heuristic: if line has '<' and '>' and contains ="... 
    # without the backslash, the quotes are likely broken
    
    if '<' in stripped and '>' in stripped:
        # Has HTML-like content
        # Check for ="... pattern where " is not escaped
        # Find all occurrences of =" where " is not preceded by backslash
        has_broken = False
        i = 0
        while i < len(stripped):
            idx = stripped.find('="', i)
            if idx < 0:
                break
            # Check if preceded by backslash (escaped)
            if idx > 0 and stripped[idx-1] == '\\':
                i = idx + 2
                continue
            # This is an unescaped =" in an HTML context
            # Check if the line also has other quotes that suggest JS strings
            has_broken = True
            break
        
        if has_broken:
            # Fix: replace outer double quotes with single quotes
            # But this is complex... let me just fix specific patterns
            
            # Pattern: class="xxx" inside "..." -> class='xxx' inside '...'
            # Replace =" with =' and then fix the closing " to ' 
            
            # Simpler: just escape the HTML attribute quotes
            # Replace =" with =\" 
            new_line = line
            i = 0
            while True:
                idx = new_line.find('="', i)
                if idx < 0:
                    break
                # Check if preceded by backslash
                if idx > 0 and new_line[idx-1] == '\\':
                    i = idx + 2
                    continue
                # Check if this is inside an HTML tag (look for < before, > after)
                lt_idx = new_line.rfind('<', 0, idx)
                gt_idx = new_line.find('>', idx)
                if lt_idx >= 0 and gt_idx > idx:
                    # This is =" inside an HTML tag - escape it
                    new_line = new_line[:idx] + '=\\"' + new_line[idx+2:]
                    fixes_count += 1
                    i = idx + 3  # skip past the new characters
                else:
                    i = idx + 2
            
            if new_line != line:
                fixed_lines.append(new_line)
                continue
    
    fixed_lines.append(line)

content = '\n'.join(fixed_lines)

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)

print(f"Fixed {fixes_count} unescaped HTML attribute quotes")
print("Done")
