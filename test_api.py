import urllib.request
import json

def test_json(url, label):
    try:
        req = urllib.request.Request(url)
        resp = urllib.request.urlopen(req, timeout=5)
        data = json.loads(resp.read())
        print(f"[OK] {label}: code={data.get('code')}")
        return data
    except Exception as e:
        print(f"[FAIL] {label}: {e}")
        return None

def test_root(url, label):
    try:
        req = urllib.request.Request(url)
        resp = urllib.request.urlopen(req, timeout=5)
        body = resp.read()
        print(f"[OK] {label}: status={resp.status}, type={resp.headers.get('content-type','?')[:20]}")
        return True
    except Exception as e:
        print(f"[FAIL] {label}: {e}")
        return None

# Test 1: Root (returns HTML, not JSON)
test_root("http://localhost:8000/", "Root")

# Test 2: Login
login_data = json.dumps({"username": "admin", "password": "admin123"}).encode()
req = urllib.request.Request("http://localhost:8000/api/admin/login", data=login_data, headers={"Content-Type": "application/json"})
resp = urllib.request.urlopen(req, timeout=5)
login = json.loads(resp.read())
token = login["data"]["token"]
print(f"[OK] Login: token={token[:20]}...")

# Test 3: Get games list
games = test_json("http://localhost:8000/api/games", "Games list")

# Test 4: Get game download (best resource)
if games and games["data"]["games"]:
    game_id = games["data"]["games"][0]["id"]
    download = test_json(f"http://localhost:8000/api/game/{game_id}/download", f"Game {game_id} download")
    if download:
        d = download["data"]
        print(f"  resource_id={d['resource_id']}, provider={d['provider_name']}, priority={d['priority']}")

# Test 5: Get admin download-resources list
req2 = urllib.request.Request(
    "http://localhost:8000/api/admin/download-resources?page_size=5",
    headers={"Authorization": f"Bearer {token}"}
)
resp2 = urllib.request.urlopen(req2, timeout=5)
dr_data = json.loads(resp2.read())
if dr_data["code"] == 0:
    items = dr_data["data"]["items"]
    print(f"[OK] Download resources list: {len(items)} items (sorted by priority DESC)")
    if items:
        item = items[0]
        print(f"  id={item['id']}, priority={item.get('priority')}, is_primary={item.get('is_primary')}, success={item.get('success_count')}, fail={item.get('fail_count')}")

        # Test 6: Update priority
        prio_data = json.dumps({"priority": 200}).encode()
        req3 = urllib.request.Request(
            f"http://localhost:8000/api/admin/download-resource/{item['id']}/priority",
            data=prio_data,
            headers={"Content-Type": "application/json", "Authorization": f"Bearer {token}"},
            method="PUT"
        )
        resp3 = urllib.request.urlopen(req3, timeout=5)
        prio_resp = json.loads(resp3.read())
        print(f"[OK] Priority update: code={prio_resp['code']}, new_priority={prio_resp['data']['priority']}")

        # Test 7: Set primary
        prim_data = json.dumps({"is_primary": True}).encode()
        req4 = urllib.request.Request(
            f"http://localhost:8000/api/admin/download-resource/{item['id']}/primary",
            data=prim_data,
            headers={"Content-Type": "application/json", "Authorization": f"Bearer {token}"},
            method="PUT"
        )
        resp4 = urllib.request.urlopen(req4, timeout=5)
        prim_resp = json.loads(resp4.read())
        print(f"[OK] Primary set: is_primary={prim_resp['data']['is_primary']}")

        # Test 8: Unset primary
        prim_data2 = json.dumps({"is_primary": False}).encode()
        req5 = urllib.request.Request(
            f"http://localhost:8000/api/admin/download-resource/{item['id']}/primary",
            data=prim_data2,
            headers={"Content-Type": "application/json", "Authorization": f"Bearer {token}"},
            method="PUT"
        )
        resp5 = urllib.request.urlopen(req5, timeout=5)
        prim_resp2 = json.loads(resp5.read())
        print(f"[OK] Primary unset: is_primary={prim_resp2['data']['is_primary']}")

        # Reset priority back
        prio_data2 = json.dumps({"priority": 100}).encode()
        req6 = urllib.request.Request(
            f"http://localhost:8000/api/admin/download-resource/{item['id']}/priority",
            data=prio_data2,
            headers={"Content-Type": "application/json", "Authorization": f"Bearer {token}"},
            method="PUT"
        )
        urllib.request.urlopen(req6, timeout=5)
        print("[OK] Priority reset to 100")

# Test 9: Verify priority sort ordering
req7 = urllib.request.Request(
    "http://localhost:8000/api/admin/download-resources?page_size=10",
    headers={"Authorization": f"Bearer {token}"}
)
resp7 = urllib.request.urlopen(req7, timeout=5)
sorted_data = json.loads(resp7.read())
if sorted_data["code"] == 0:
    items2 = sorted_data["data"]["items"]
    priorities = [i.get("priority", 0) for i in items2]
    is_sorted = all(priorities[i] >= priorities[i+1] for i in range(len(priorities)-1))
    print(f"[{'OK' if is_sorted else 'FAIL'}] Priority sort: priorities={priorities}, sorted_desc={is_sorted}")

print()
print("=== All tests complete! ===")
