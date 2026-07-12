import sys
sys.stdout.reconfigure(encoding="utf-8")

with open(r"C:\Users\xueta\Documents\web-xiaobaigame\admin\js\main.js", "r", encoding="utf-8") as f:
    c = f.read()

# Fix hash bug (pre-existing)
old = "var hash = window.location.hash.replace"
idx = c.find(old)
print("hash line index:", idx)
if idx > 0:
    line_start = c.rfind("\n", 0, idx) + 1
    line_end = c.find("\n", idx)
    print("Current line:", repr(c[line_start:line_end]))

# Check brace balance before renderProviderManagement
func_idx = c.find("function renderProviderManagement")
before = c[:func_idx]
opens = before.count("{")
closes = before.count("}")
print("Braces before renderProviderManagement: open={0} close={1} diff={2}".format(opens, closes, opens-closes))

# Also check function renderSettings
rs_idx = c.find("function renderSettings")
before2 = c[:rs_idx]
opens2 = before2.count("{")
closes2 = before2.count("}")
print("Braces before renderSettings: open={0} close={1} diff={2}".format(opens2, closes2, opens2-closes2))
