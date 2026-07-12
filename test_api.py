import asyncio, aiohttp

async def test():
    async with aiohttp.ClientSession() as s:
        resp = await s.post("http://localhost:8000/api/admin/login", json={"username": "admin", "password": "admin123"})
        data = await resp.json()
        token = data.get("data", {}).get("token", "")
        headers = {"Authorization": f"Bearer {token}"}
        print(f"Login: {resp.status}, token={'OK' if token else 'FAIL'}")

        resp = await s.get("http://localhost:8000/api/admin/download-providers", headers=headers)
        data = await resp.json()
        print(f"GET /download-providers: {resp.status}, total={data.get('data',{}).get('total',0)}")

        resp = await s.get("http://localhost:8000/api/admin/download-providers/active", headers=headers)
        data = await resp.json()
        print(f"GET /download-providers/active: {resp.status}, count={len(data.get('data',[]))}")

        resp = await s.get("http://localhost:8000/api/admin/download-resources", headers=headers)
        data = await resp.json()
        print(f"GET /download-resources: {resp.status}, total={data.get('data',{}).get('total',0)}")

        resp = await s.get("http://localhost:8000/api/admin/download-resources-games", headers=headers)
        data = await resp.json()
        print(f"GET /download-resources-games: {resp.status}, count={len(data.get('data',[]))}")

        # Provider CRUD
        resp = await s.post("http://localhost:8000/api/admin/download-providers", headers=headers, json={"code": "test_prov", "name": "Test", "status": "active"})
        data = await resp.json()
        print(f"POST /download-providers: {resp.status}, id={data.get('data',{}).get('id','?')}")
        new_id = data.get("data", {}).get("id")
        if new_id:
            resp = await s.put(f"http://localhost:8000/api/admin/download-providers/{new_id}", headers=headers, json={"name": "Test Updated"})
            data = await resp.json()
            print(f"PUT /download-providers/{new_id}: {resp.status}")
            resp = await s.delete(f"http://localhost:8000/api/admin/download-providers/{new_id}", headers=headers)
            data = await resp.json()
            print(f"DELETE /download-providers/{new_id}: {resp.status}")

        # Try delete a used provider
        resp = await s.delete("http://localhost:8000/api/admin/download-providers/1", headers=headers)
        data = await resp.json()
        print(f"DELETE /download-providers/1 (used): {resp.status}, detail={data.get('detail','OK')}")

        # Resource CRUD
        resp = await s.post("http://localhost:8000/api/admin/download-resources", headers=headers, json={"game_id": 1, "provider_id": 1, "title": "Test"})
        data = await resp.json()
        print(f"POST /download-resources: {resp.status}, id={data.get('data',{}).get('id','?')}")
        new_rid = data.get("data", {}).get("id")
        if new_rid:
            resp = await s.put(f"http://localhost:8000/api/admin/download-resources/{new_rid}", headers=headers, json={"title": "Test Updated"})
            data = await resp.json()
            print(f"PUT /download-resources/{new_rid}: {resp.status}")
            resp = await s.delete(f"http://localhost:8000/api/admin/download-resources/{new_rid}", headers=headers)
            data = await resp.json()
            print(f"DELETE /download-resources/{new_rid}: {resp.status}")

asyncio.run(test())
