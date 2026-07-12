with open(r"C:\Users\xueta\Documents\web-xiaobaigame\admin\js\main.js", "r", encoding="utf-8") as f:
    content = f.read()

# Check if renderProviderManagement exists
idx = content.find("renderProviderManagement")
print("renderProviderManagement found at:", idx)

# Check if providerState exists
idx2 = content.find("providerState")
print("providerState found at:", idx2)

# Check for "hash is not defined" - search for "hash"
# Look for potential hash issues
for i, line in enumerate(content.split('\n'), 1):
    if 'hash' in line and ('hash =' in line or 'hash=' in line or ' hash ' in line):
        print(f"Line {i}: {line.strip()[:100]}")
