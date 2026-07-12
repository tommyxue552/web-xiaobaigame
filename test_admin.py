
import urllib.request, json, sys
sys.stdout.reconfigure(encoding="utf-8")

# Login and get token, then serve admin page
d = json.dumps({"username": "admin", "password": "admin123"}).encode()
req = urllib.request.Request("http://localhost:8000/api/admin/login", data=d, headers={"Content-Type": "application/json"})
token = json.loads(urllib.request.urlopen(req).read())["data"]["token"]
print("Token obtained")

# Check if admin page is accessible
try:
    req2 = urllib.request.Request("http://localhost:8000/admin/")
    resp2 = urllib.request.urlopen(req2)
    print("Admin page status:", resp2.status)
    html = resp2.read().decode("utf-8", errors="replace")
    print("Admin page size:", len(html))
    print("Has main.js:", "main.js" in html)
except Exception as e:
    print("Error:", e)

