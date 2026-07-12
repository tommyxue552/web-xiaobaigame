
import sys
sys.stdout.reconfigure(encoding="utf-8")
path = r"C:\Users\xueta\Documents\web-xiaobaigame\fixed_section.js"
with open(path, "r", encoding="utf-8") as f:
    data = f.read()

# The count info line has: "? " + total + " ?"
# Let me check the exact bytes
idx = data.find("info.textContent = ")
print(repr(data[idx:idx+50]))

idx2 = data.find("page-info")
print(repr(data[idx2:idx2+60]))

