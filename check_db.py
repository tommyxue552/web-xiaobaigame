import sqlite3
conn = sqlite3.connect("C:/Users/xueta/Documents/web-xiaobaigame/database/xiaobaigame.db")
cur = conn.cursor()
cur.execute("SELECT sql FROM sqlite_master WHERE name='download_providers'")
print(cur.fetchone()[0])
print("---")
cur.execute("SELECT id, code, name, status, display_order FROM download_providers ORDER BY display_order, id")
for r in cur.fetchall():
    print(r)
print("---")
cur.execute("SELECT sql FROM sqlite_master WHERE name='download_resources'")
print(cur.fetchone()[0])
print("---")
cur.execute("SELECT id, game_id, provider, provider_id, title, status, display_order FROM download_resources")
for r in cur.fetchall():
    print(r)
conn.close()
