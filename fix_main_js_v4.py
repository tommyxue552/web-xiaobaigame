import sys
sys.stdout.reconfigure(encoding="utf-8")

with open("admin/js/main.js", "r", encoding="utf-8") as f:
    content = f.read()

original_line = '    case "dlstats": renderDownloadStats(body); break;`n        case "tags": renderTagManagement(body); break;`n        case "settings": renderSettings(body); break;'
replacement = '''    case "dlstats": renderDownloadStats(body); break;
        case "tags": renderTagManagement(body); break;
        case "settings": renderSettings(body); break;'''

if original_line in content:
    content = content.replace(original_line, replacement)
    print("Fixed: `n literals -> actual newlines in switch cases")
else:
    print("Pattern not found for `n fix")

with open("admin/js/main.js", "w", encoding="utf-8") as f:
    f.write(content)
