
import sys
sys.stdout.reconfigure(encoding="utf-8")
path = r"C:\Users\xueta\Documents\web-xiaobaigame\fixed_section.js"
with open(path, "r", encoding="utf-8") as f:
    data = f.read()

# Find count info line
for i, line in enumerate(data.split("\n")):
    if "total +" in line and ("?" in line or "\u5171" in line):
        print(f"Line {i}: {line.strip()}")
    if "page-info" in line:
        print(f"Line {i}: {line.strip()}")

