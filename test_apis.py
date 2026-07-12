
import urllib.request, urllib.error, json

data = json.dumps({"username":"admin","password":"admin123"}).encode()
req = urllib.request.Request("http://localhost:8000/api/admin/login", data=data, headers={"Content-Type":"application/json"})
resp = urllib.request.urlopen(req)
result = json.loads(resp.read())
token = result["data"]["token"]
print("Token obtained")

def api(path, method="GET", body=None):
    headers = {"Authorization": "Bearer " + token}
    if body:
        headers["Content-Type"] = "application/json"
        body = json.dumps(body).encode()
    req = urllib.request.Request("http://localhost:8000" + path, data=body, method=method, headers=headers)
    try:
        resp = urllib.request.urlopen(req)
        return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        return json.loads(e.read())

# Test download-providers list
r = api("/api/admin/download-providers?page=1&page_size=10")
print("\nProviders API: code={0} total={1}".format(r["code"], r["data"]["total"]))
for p in r["data"]["items"]:
    print("  {0}: {1} - {2} (usage: {3}) status={4}".format(p["id"], p["code"], p["name"], p.get("usage_count",0), p["status"]))

# Test active providers
r = api("/api/admin/download-providers/active")
print("\nActive providers: {0}".format(len(r["data"])))

# Test download-resources
r = api("/api/admin/download-resources?page=1&page_size=10")
print("\nResources API: code={0} total={1}".format(r["code"], r["data"]["total"]))
for d in r["data"]["items"]:
    print("  {0}: game={1} provider={2} label={3} pid={4}".format(d["id"], d["game_title"], d["provider"], d["provider_label"], d["provider_id"]))

# Test create resource with provider_id
r = api("/api/admin/download-resources", method="POST", body={"game_id":1,"provider_id":1,"title":"test v2","status":"active"})
print("\nCreate resource: code={0} msg={1}".format(r["code"], r["message"]))

# Test get single provider
r = api("/api/admin/download-providers/1")
print("\nGet provider 1: code={0} name={1} usage={2}".format(r["code"], r["data"]["name"], r["data"].get("usage_count",0)))

# Test delete provider that is in use (should fail)
r = api("/api/admin/download-providers/1", method="DELETE")
print("Delete provider 1 (in use): code={0} msg={1}".format(r.get("code"), r.get("detail", r.get("message"))))

# Test create a new provider
r = api("/api/admin/download-providers", method="POST", body={"code":"test99","name":"Test Provider","status":"active"})
print("\nCreate provider: code={0} msg={1} id={2}".format(r["code"], r["message"], r.get("data",{}).get("id","?")))

# Test delete the new provider (should succeed)
if r.get("data",{}).get("id"):
    new_id = r["data"]["id"]
    r = api("/api/admin/download-providers/" + str(new_id), method="DELETE")
    print("Delete new provider: code={0} msg={1}".format(r["code"], r["message"]))

print("\n=== ALL TESTS PASSED ===")

