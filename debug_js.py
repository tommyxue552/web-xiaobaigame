import sys
sys.stdout.reconfigure(encoding='utf-8')

with open(r"C:\Users\xueta\Documents\web-xiaobaigame\admin\js\main.js", "r", encoding="utf-8") as f:
    content = f.read()

# Find the issue - the marker before renderSettings should be
# "function renderSettings" - check what's around it
idx = content.find("function renderSettings")
if idx > 0:
    # Show 30 chars before and after
    start = max(0, idx - 30)
    end = min(len(content), idx + 30)
    print("Context around renderSettings:")
    print(repr(content[start:end]))

# Also check if there's a missing closing brace before function renderSettings
idx2 = content.find("}function renderSettings")
if idx2 >= 0:
    print("\nOriginal pattern '}function renderSettings' found - OK")
else:
    print("\nMissing '}function renderSettings' - need to add closing brace!")

# Check the exact replacement
idx3 = content.find("loadProviderDropdown();")
if idx3 >= 0:
    end = min(len(content), idx3 + 200)
    print("\nAround loadProviderDropdown end:")
    print(repr(content[idx3-10:end]))
