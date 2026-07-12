with open(r"C:\Users\xueta\Documents\web-xiaobaigame\admin\js\main.js", "r", encoding="utf-8") as f:
    content = f.read()

# Find the boundary - search for deleteResource end
idx = content.find("async function deleteResource")
if idx > 0:
    # Find the matching closing brace
    end = content.find("// ==================== 涓嬭浇娓犻亾绠＄悊", idx)
    if end > 0:
        print("=== deleteResource end to providers start ===")
        print(repr(content[end-100:end+200]))
