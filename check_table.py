
import sqlite3, sys
sys.stdout.reconfigure(encoding="utf-8")
db_path = r"C:\Users\xueta\Documents\web-xiaobaigame\database\xiaobaigame.db"
conn = sqlite3.connect(db_path)
cursor = conn.execute("PRAGMA table_info(download_resources)")
print("download_resources columns:")
for col in cursor.fetchall():
    print(f"  {col[1]} ({col[2]})")
# Also check data
cursor2 = conn.execute("SELECT * FROM download_resources")
rows = cursor2.fetchall()
print(f"Row count: {len(rows)}")
if rows:
    for r in rows:
        print(r)
conn.close()

