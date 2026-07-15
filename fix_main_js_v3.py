import sys
sys.stdout.reconfigure(encoding="utf-8")

with open("admin/js/main.js", "r", encoding="utf-8") as f:
    content = f.read()

fixes = []

# The pattern: inside JS double-quoted strings, HTML attr quotes like
# class="xxx" should be class=\"xxx\" (escaped for JS)
# But the JS string delimiter " at start/end of concatenation should stay

# Line 863: status badge span
old = '<td><span class="badge " + statusClass + "">"'
new = '<td><span class=\\"badge " + statusClass + "\\">"'
if old in content:
    content = content.replace(old, new)
    fixes.append("863: status badge class attr")

# Line 865: edit button - class, onclick, title
old = '<button class="btn btn-sm" onclick="editProvider(" + p.id + ")" title="\u7f16\u8f91">'
new = '<button class=\\"btn btn-sm\\" onclick=\\"editProvider(" + p.id + ")\\" title=\\"\u7f16\u8f91\\">'
if old in content:
    content = content.replace(old, new)
    fixes.append("865: edit button attrs")

# Line 866: delete button
old = '<button class="btn btn-sm btn-danger" onclick="deleteProvider(" + p.id + ")" title="\u5220\u9664">'
new = '<button class=\\"btn btn-sm btn-danger\\" onclick=\\"deleteProvider(" + p.id + ")\\" title=\\"\u5220\u9664\\">'
if old in content:
    content = content.replace(old, new)
    fixes.append("866: delete button attrs")

# Line 871: panel div
old = '<div class="panel">"'
new = '<div class=\\"panel\\">"'
if old in content:
    content = content.replace(old, new)
    fixes.append("871: panel div")

# Line 872: panel header
old = '<div class="panel-header"><h3>\u4e0b\u8f7d\u6e20\u9053\u7ba1\u7406</h3><button class="btn btn-primary" onclick="showProviderForm()">'
new = '<div class=\\"panel-header\\"><h3>\u4e0b\u8f7d\u6e20\u9053\u7ba1\u7406</h3><button class=\\"btn btn-primary\\" onclick=\\"showProviderForm()\\">'
if old in content:
    content = content.replace(old, new)
    fixes.append("872: panel header")

# Line 873: panel body
old = '<div class="panel-body" style="padding:0;">"'
new = '<div class=\\"panel-body\\" style=\\"padding:0;\\">"'
if old in content:
    content = content.replace(old, new)
    fixes.append("873: panel body")

# Line 874: data table
old = '<table class="data-table">"'
new = '<table class=\\"data-table\\">"'
if old in content:
    content = content.replace(old, new)
    fixes.append("874: data table")

# Line 878: tbody with colspan
old = '<td colspan="6" style="text-align:center;color:#888;">'
new = '<td colspan=\\"6\\" style=\\"text-align:center;color:#888;\\">'
if old in content:
    content = content.replace(old, new)
    fixes.append("878: colspan/style in tbody")

# Line 882: error state
old = '<div class="empty-state"><p>\u52a0\u8f7d\u5931\u8d25: "'
new = '<div class=\\"empty-state\\"><p>\u52a0\u8f7d\u5931\u8d25: "'
if old in content:
    content = content.replace(old, new)
    fixes.append("882: empty state")

# Line 889: modal div
old = '<div class="modal">"'
new = '<div class=\\"modal\\">"'
if old in content:
    content = content.replace(old, new)
    fixes.append("889: modal div")

# Line 890: modal header
old = '<div class="modal-header"><h3>" + title + "</h3><button class="modal-close-btn" onclick="closeModal()">'
new = '<div class=\\"modal-header\\"><h3>" + title + "</h3><button class=\\"modal-close-btn\\" onclick=\\"closeModal()\\">'
if old in content:
    content = content.replace(old, new)
    fixes.append("890: modal header")

# Line 891: modal body
old = '<div class="modal-body"><form id="provider-form">"'
new = '<div class=\\"modal-body\\"><form id=\\"provider-form\\">"'
if old in content:
    content = content.replace(old, new)
    fixes.append("891: modal body")

# Line 892: hidden input
old = '<input type="hidden" name="id" value="" + (id || "") + "">"'
new = '<input type=\\"hidden\\" name=\\"id\\" value=\\"" + (id || "") + "\\">"'
if old in content:
    content = content.replace(old, new)
    fixes.append("892: hidden input")

# Line 893: form-row 1
old = '<div class="form-row">"'
cnt_before = content.count(old)
new = '<div class=\\"form-row\\">"'
content = content.replace(old, new)
cnt_after = content.count(old)
if cnt_before > cnt_after:
    fixes.append(f"893: form-row 1 ({cnt_before - cnt_after}x)")

# Line 894: form-group name
old = '<div class="form-group"><label>\u540d\u79f0 *</label><input name="name" required placeholder="\u6e20\u9053\u540d\u79f0">'
new = '<div class=\\"form-group\\"><label>\u540d\u79f0 *</label><input name=\\"name\\" required placeholder=\\"\u6e20\u9053\u540d\u79f0\\">'
if old in content:
    content = content.replace(old, new)
    fixes.append("894: name form-group")

# Line 895: form-group code
old = '<div class="form-group"><label>\u4ee3\u7801 *</label><input name="code" required placeholder="provider-code">'
new = '<div class=\\"form-group\\"><label>\u4ee3\u7801 *</label><input name=\\"code\\" required placeholder=\\"provider-code\\">'
if old in content:
    content = content.replace(old, new)
    fixes.append("895: code form-group")

# Line 897: base_url
old = '<div class="form-group"><label>\u57fa\u5740URL</label><input name="base_url" placeholder="https://...">'
new = '<div class=\\"form-group\\"><label>\u57fa\u5740URL</label><input name=\\"base_url\\" placeholder=\\"https://...\\">'
if old in content:
    content = content.replace(old, new)
    fixes.append("897: base_url form-group")

# Line 898: description
old = '<div class="form-group"><label>\u63cf\u8ff0</label><textarea name="description" rows="3" placeholder="\u63cf\u8ff0">'
new = '<div class=\\"form-group\\"><label>\u63cf\u8ff0</label><textarea name=\\"description\\" rows=\\"3\\" placeholder=\\"\u63cf\u8ff0\\">'
if old in content:
    content = content.replace(old, new)
    fixes.append("898: description textarea")

# Line 899: form-row 2
old = '<div class="form-row">"'
cnt_before2 = content.count(old)
content = content.replace(old, new)
cnt_after2 = content.count(old)
if cnt_before2 > cnt_after2:
    fixes.append(f"899: form-row 2 ({cnt_before2 - cnt_after2}x)")

# Line 900: sort_order
old = '<div class="form-group"><label>\u6392\u5e8f</label><input name="sort_order" type="number" value="0">'
new = '<div class=\\"form-group\\"><label>\u6392\u5e8f</label><input name=\\"sort_order\\" type=\\"number\\" value=\\"0\\">'
if old in content:
    content = content.replace(old, new)
    fixes.append("900: sort_order form-group")

# Line 901: is_active select
old = '<div class="form-group"><label>\u72b6\u6001</label><select name="is_active"><option value="1">\u542f\u7528</option><option value="0">\u7981\u7528</option>'
new = '<div class=\\"form-group\\"><label>\u72b6\u6001</label><select name=\\"is_active\\"><option value=\\"1\\">\u542f\u7528</option><option value=\\"0\\">\u7981\u7528</option>'
if old in content:
    content = content.replace(old, new)
    fixes.append("901: is_active select")

# Line 903: form-actions
old = '<div class="form-actions">"'
new = '<div class=\\"form-actions\\">"'
if old in content:
    content = content.replace(old, new)
    fixes.append("903: form-actions")

# Line 904: cancel button
old = '<button type="button" class="btn" onclick="closeModal()">\u53d6\u6d88</button>"'
new = '<button type=\\"button\\" class=\\"btn\\" onclick=\\"closeModal()\\">\u53d6\u6d88</button>"'
if old in content:
    content = content.replace(old, new)
    fixes.append("904: cancel button")

# Line 905: submit button
old = '<button type="submit" class="btn btn-primary">\u4fdd\u5b58</button>"'
new = '<button type=\\"submit\\" class=\\"btn btn-primary\\">\u4fdd\u5b58</button>"'
if old in content:
    content = content.replace(old, new)
    fixes.append("905: submit button")

# Line 882: closing div for error
old = '></p></div>"'
new = '></p></div>"'
# already handled above

print(f"Applied {len(fixes)} fixes:")
for f in fixes:
    print(f"  - {f}")

with open("admin/js/main.js", "w", encoding="utf-8") as f:
    f.write(content)

print("\nWritten to admin/js/main.js")
