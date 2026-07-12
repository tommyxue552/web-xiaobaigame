with open(r"C:\Users\xueta\Documents\web-xiaobaigame\admin\js\main.js", "rb") as f:
    raw = f.read()

# Decode with error handling
text = raw.decode("utf-8", errors="replace")
lines = text.split("\n")

# Check resource-related lines (lines 480-780)
print("=== Checking resource management code for corruption ===")
for i in range(479, min(len(lines), 780)):
    if '\ufffd' in lines[i]:
        # Show the line with corruption
        line = lines[i].strip()
        if line:
            print(f"Line {i+1}: ...{line[:120]}...")

print()
print("=== Checking MENUS area ===")
for i in range(44, 57):
    if i < len(lines):
        line = lines[i].strip()
        if line:
            print(f"Line {i+1}: {line[:120]}")
