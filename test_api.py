
import urllib.request, json, sys
sys.stdout.reconfigure(encoding="utf-8")
data = json.dumps({"username": "admin", "password": "admin123"}).encode()
req = urllib.request.Request("http://localhost:8000/api/admin/login", data=data, headers={"Content-Type": "application/json"})
resp = urllib.request.urlopen(req)
token = json.loads(resp.read())["data"]["token"]
h = {"Content-Type": "application/json", "Authorization": "Bearer " + token}
r2 = urllib.request.Request("http://localhost:8000/api/admin/download-resources?page=1&page_size=10", headers=h)
d2 = json.loads(urllib.request.urlopen(r2).read())
print("List code:", d2["code"], "total:", d2["data"]["total"])
item = d2["data"]["items"][0]
print("game_title:", item.get("game_title"))
print("provider_label:", item.get("provider_label"))
print("remark:", repr(item.get("remark")))
print("display_order:", item.get("display_order"))

