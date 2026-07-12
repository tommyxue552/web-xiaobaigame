
import urllib.request, json

# Login
data = json.dumps({"username":"admin","password":"admin123"}).encode()
req = urllib.request.Request("http://localhost:8000/api/admin/login", data=data, headers={"Content-Type":"application/json"})
resp = urllib.request.urlopen(req)
token = json.loads(resp.read())["data"]["token"]

# Delete test resource (id=3)
req = urllib.request.Request("http://localhost:8000/api/admin/download-resources/3", method="DELETE", headers={"Authorization":"Bearer "+token})
resp = urllib.request.urlopen(req)
print("Deleted test resource:", json.loads(resp.read()))

# Verify usage counts back to normal
req = urllib.request.Request("http://localhost:8000/api/admin/download-providers/1", headers={"Authorization":"Bearer "+token})
resp = urllib.request.urlopen(req)
print("Provider 1 usage back to:", json.loads(resp.read())["data"]["usage_count"])

