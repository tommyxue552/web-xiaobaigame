import sys
sys.stdout.reconfigure(encoding="utf-8")

with open(r"C:\Users\xueta\Documents\web-xiaobaigame\admin\js\main.js", "r", encoding="utf-8") as f:
    c = f.read()

# Show the context just before the provider code
idx = c.find("// ==================== 下载渠道管理")
print("=== Before provider management ===")
for i, line in enumerate(c[idx-200:idx+300].split("\n")):
    print("{0:4d}: {1}".format(i, line))
