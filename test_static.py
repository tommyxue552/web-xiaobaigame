
import urllib.request, sys
sys.stdout.reconfigure(encoding="utf-8")
# Check main.js
try:
    req = urllib.request.Request("http://localhost:8000/admin/js/main.js")
    resp = urllib.request.urlopen(req)
    js = resp.read()
    print("main.js size:", len(js), "bytes")
    # Check for the new functions
    print("Has downloadResourceState:", b"downloadResourceState" in js)
    print("Has providerLabel:", b"providerLabel" in js)
    print("Has renderResourceManagement:", b"renderResourceManagement" in js)
except Exception as e:
    print("Error:", e)

