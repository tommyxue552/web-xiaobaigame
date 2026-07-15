import sys
sys.stdout.reconfigure(encoding="utf-8")

with open("admin/js/main.js", "r", encoding="utf-8") as f:
    content = f.read()

# Track all fixes
fixes = []

# Fix 1: Line 865 - class attr closing quote
# "<td><span class=\"badge " + statusClass + "">" + statusText +
# Should be: \" after statusClass + closes the HTML class attr
old = '<span class=\\\"badge " + statusClass + "">"'
new = '<span class=\\\"badge " + statusClass + "\\\\\">"'
if old in content:
    content = content.replace(old, new)
    fixes.append("L865: badge class attr closing quote")

# Fix 2: Line 867 - button class then onclick
old = 'class=\\\"btn btn-sm" onclick='
new = 'class=\\\"btn btn-sm\\\\\" onclick='
if old in content:
    content = content.replace(old, new)
    fixes.append("L867: btn-sm class closing quote")

# Fix 3: Line 867 - editProvider closing quote
old = 'editProvider(" + p.id + ")" title='
new = 'editProvider(" + p.id + ")\\\" title='
if old in content:
    content = content.replace(old, new)
    fixes.append("L867: editProvider onclick closing quote")

# Fix 4: Line 868 - btn-danger class
old = 'class=\\\"btn btn-sm btn-danger" onclick='
new = 'class=\\\"btn btn-sm btn-danger\\\\\" onclick='
if old in content:
    content = content.replace(old, new)
    fixes.append("L868: btn-danger class closing quote")

# Fix 5: Line 868 - deleteProvider closing quote
old = 'deleteProvider(" + p.id + ")" title='
new = 'deleteProvider(" + p.id + ")\\\" title='
if old in content:
    content = content.replace(old, new)
    fixes.append("L868: deleteProvider onclick closing quote")

# Fix 6: Line 874 - btn-primary in panel header
old = 'class=\\\"btn btn-primary" onclick='
new = 'class=\\\"btn btn-primary\\\\\" onclick='
if old in content:
    content = content.replace(old, new)
    fixes.append("L874: btn-primary class closing quote")

# Fix 7: Line 880 - colspan attr
old = 'colspan=\\\\"6" style='
new = 'colspan=\\\\"6\\\\\" style='
if old in content:
    content = content.replace(old, new)
    fixes.append("L880: colspan closing quote")

# Fix 8: Line 892 - modal-close-btn
old = 'class=\\\"modal-close-btn" onclick='
new = 'class=\\\"modal-close-btn\\\\\" onclick='
if old in content:
    content = content.replace(old, new)
    fixes.append("L892: modal-close-btn class closing quote")

# Fix 9: Line 894 - hidden input name and value
old = 'type=\\\"hidden" name=\\\"id" value='
new = 'type=\\\"hidden\\\\\" name=\\\"id\\\\\" value='
if old in content:
    content = content.replace(old, new)
    fixes.append("L894: hidden input attrs")

# Fix 10: Line 900 - textarea rows and placeholder
old = 'rows=\\\\"3" placeholder='
new = 'rows=\\\\"3\\\\\" placeholder='
if old in content:
    content = content.replace(old, new)
    fixes.append("L900: textarea rows closing quote")

# Fix 11: Line 902 - number input
old = 'type=\\\"number" value='
new = 'type=\\\"number\\\\\" value='
if old in content:
    content = content.replace(old, new)
    fixes.append("L902: number type closing quote")

# Fix 12: Line 907 - submit button type
old = 'type=\\\"submit" class='
new = 'type=\\\"submit\\\\\" class='
if old in content:
    content = content.replace(old, new)
    fixes.append("L907: submit type closing quote")

# Fix 13: Line 873 - panel div (odd count, but let's check)
# "<div class=\"panel">" +  - this has 3 raw quotes: opening ", \" (escaped), and closing "
# Wait, " at start, \" inside, " at end. That's 2 raw + 2 in pair. Hmm.
# Actually: "<div class=\"panel">" - the \" is an escaped quote inside, and the outer quotes are the JS string delimiters
# So raw quotes: first " (opens JS), last " (closes JS before +). That's 2 raw quotes - even. This is fine.

# Fix 14: Line 895, 901, 905 - form-row and form-actions
# "<div class=\"form-row">" - same pattern as above, should be fine
# These have just the outer "" for JS string + the \" inside. That's correct.

# Fix 15: Check for remaining issues
# Line 900 has name=\"description" - let me check
old = 'name=\\\"description" rows='
new = 'name=\\\"description\\\\\" rows='
if old in content:
    content = content.replace(old, new)
    fixes.append("L900: description name closing quote")

# Line 902 has name=\\\"sort_order" - check
old = 'name=\\\"sort_order" type='
new = 'name=\\\"sort_order\\\\\" type='
if old in content:
    content = content.replace(old, new)
    fixes.append("L902: sort_order name closing quote")

print(f"Applied {len(fixes)} fixes:")
for f in fixes:
    print(f"  - {f}")

with open("admin/js/main.js", "w", encoding="utf-8") as f:
    f.write(content)

print("Written to admin/js/main.js")
