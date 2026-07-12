with open(r"C:\Users\xueta\Documents\web-xiaobaigame\admin\js\main.js", "r", encoding="utf-8") as f:
    content = f.read()

# Show context around providerState definition
idx = content.find("providerState")
if idx > 0:
    print("=== Around providerState (offset", idx, ") ===")
    print(content[idx:idx+200])

# Show context around renderProviderManagement function
idx2 = content.find("function renderProviderManagement")
if idx2 > 0:
    print("\n=== Around renderProviderManagement function ===")
    print(content[idx2:idx2+100])

# Also check the end of the previous function  
print("\n=== Before providerState ===")
print(content[idx-200:idx])
