import sqlite3
conn = sqlite3.connect("database/xiaobaigame.db")
c = conn.cursor()
c.execute("SELECT name FROM sqlite_master WHERE type='table'")
print("Tables:", [t[0] for t in c.fetchall()])
c.execute("PRAGMA table_info(download_providers)")
print("\ndownload_providers columns:")
for row in c.fetchall():
    print("  ", row)
c.execute("PRAGMA table_info(download_resources)")
print("\ndownload_resources columns:")
for row in c.fetchall():
    print("  ", row)
c.execute("SELECT * FROM download_providers")
print("\nProviders:")
for row in c.fetchall():
    print("  ", row)
c.execute("SELECT id, game_id, provider, provider_id, title FROM download_resources")
print("\nResources:")
for row in c.fetchall():
    print("  ", row)
conn.close()
