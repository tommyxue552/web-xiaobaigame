
import sys, os
sys.stdout.reconfigure(encoding="utf-8")
# Check for db files
base = r"C:\Users\xueta\Documents\web-xiaobaigame\backend"
for root, dirs, files in os.walk(base):
    for f in files:
        if f.endswith(".db") or f.endswith(".sqlite") or f.endswith(".sqlite3"):
            full = os.path.join(root, f)
            size = os.path.getsize(full)
            print(f"Found: {full} ({size} bytes)")

