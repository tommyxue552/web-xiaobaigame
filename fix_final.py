
import sys, re
sys.stdout.reconfigure(encoding="utf-8")
path = r"C:\Users\xueta\Documents\web-xiaobaigame\fixed_section.js"
with open(path, "r", encoding="utf-8") as f:
    data = f.read()

# Fix pagination: ? -> 第 and 页
# Find: page-info">? + s.page
data = data.replace("page-info\"\u003e?" + chr(39) + " + s.page", "page-info\"\u003e\u7b2c" + chr(39) + " + s.page")
# Find: totalPages + ?</span>
data = data.replace("totalPages + " + chr(39) + " ?</span>", "totalPages + " + chr(39) + " \u9875</span>")

# Fix count info: " ?" + total + " ?" -> "共 " + total + " 条"
data = data.replace("\" ?\" + total + \" ?\"", "\"\u5171 \" + total + \" \u6761\"")

print("Pagination has di:", "\u7b2c" in data)
print("Pagination has ye:", "\u9875" in data)
print("Count has gong:", "\u5171" in data)
print("Count has tiao:", "\u6761" in data)

# Check remaining stray ?
for m in re.finditer(chr(0x3f), data):
    pos = m.start()
    ctx = data[max(0,pos-3):pos+4]
    # Skip ternary operators and URL query strings
    before = data[max(0,pos-1):pos]
    after = data[pos+1:pos+2] if pos+1 < len(data) else ""
    if before in ["?", " ", ":", "="] or after in [" ", ":", "?", "&"]:
        continue
    if any(kw in data[max(0,pos-10):pos+10] for kw in ["http", "?>", "?."]):
        continue
    print("STRAY ?:", repr(ctx))

with open(path, "w", encoding="utf-8") as f:
    f.write(data)
print("Fixed and saved")

