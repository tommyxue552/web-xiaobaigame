
import urllib.request, json, sys
sys.stdout.reconfigure(encoding="utf-8")

# Login
d = json.dumps({"username": "admin", "password": "admin123"}).encode()
req = urllib.request.Request("http://localhost:8000/api/admin/login", data=d, headers={"Content-Type": "application/json"})
token = json.loads(urllib.request.urlopen(req).read())["data"]["token"]
h = {"Content-Type": "application/json", "Authorization": "Bearer " + token}

# Clean up old data
r = urllib.request.Request("http://localhost:8000/api/admin/download-resources?page=1&page_size=100", headers=h)
items = json.loads(urllib.request.urlopen(r).read())["data"]["items"]
for item in items:
    rd = urllib.request.Request("http://localhost:8000/api/admin/download-resources/" + str(item["id"]), headers=h, method="DELETE")
    urllib.request.urlopen(rd)
print("Cleaned up", len(items), "items")

# Create a new resource
payload = json.dumps({
    "game_id": 1,
    "provider": "baidu",
    "title": "游戏本体 v1.2",
    "origin_url": "https://pan.baidu.com/s/original123",
    "my_share_url": "https://pan.baidu.com/s/myshare456",
    "extract_code": "abcd",
    "remark": "测试备注: 包含DLC",
    "display_order": 1,
    "status": "active"
}).encode()
r = urllib.request.Request("http://localhost:8000/api/admin/download-resources", data=payload, headers=h)
result = json.loads(urllib.request.urlopen(r).read())
print("Create:", result["code"], result.get("message",""))
item = result["data"]
print("  game_title:", item["game_title"])
print("  provider_label:", item["provider_label"])
print("  remark:", item.get("remark"))

# List
r = urllib.request.Request("http://localhost:8000/api/admin/download-resources?page=1&page_size=10", headers=h)
result = json.loads(urllib.request.urlopen(r).read())
print("List:", "total=" + str(result["data"]["total"]))
for i in result["data"]["items"]:
    print("  #" + str(i["id"]), i["provider_label"], i["status"], i["game_title"])

# Get by ID
r = urllib.request.Request("http://localhost:8000/api/admin/download-resources/" + str(item["id"]), headers=h)
detail = json.loads(urllib.request.urlopen(r).read())
print("Get:", detail["code"], "title:", detail["data"]["title"])

# Update
payload2 = json.dumps({"title": "Updated Title v2.0", "status": "disabled", "display_order": 99}).encode()
r = urllib.request.Request("http://localhost:8000/api/admin/download-resources/" + str(item["id"]), data=payload2, headers=h, method="PUT")
upd = json.loads(urllib.request.urlopen(r).read())
print("Update:", upd["code"], upd["data"]["title"], "status:", upd["data"]["status"], "order:", upd["data"]["display_order"])

# Delete
r = urllib.request.Request("http://localhost:8000/api/admin/download-resources/" + str(item["id"]), headers=h, method="DELETE")
dl = json.loads(urllib.request.urlopen(r).read())
print("Delete:", dl["code"], dl.get("message",""))

print("ALL TESTS PASSED!")

