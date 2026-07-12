
import urllib.request, json

data = json.dumps({"username":"admin","password":"admin123"}).encode()
req = urllib.request.Request("http://localhost:8000/api/admin/login", data=data, headers={"Content-Type":"application/json"})
resp = urllib.request.urlopen(req)
result = json.loads(resp.read())
print(json.dumps(result, indent=2, ensure_ascii=False))

