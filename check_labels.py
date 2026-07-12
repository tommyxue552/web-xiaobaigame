
import sys
sys.stdout.reconfigure(encoding="utf-8")
with open(r"C:\Users\xueta\Documents\web-xiaobaigame\backend\app\api\download_resources.py", "r", encoding="utf-8") as f:
    content = f.read()
idx = content.find("PROVIDER_LABELS")
print(content[idx:idx+200])

