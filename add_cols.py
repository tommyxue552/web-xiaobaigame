
import sqlite3, sys
sys.stdout.reconfigure(encoding="utf-8")
db_path = r"C:\Users\xueta\Documents\web-xiaobaigame\database\xiaobaigame.db"
conn = sqlite3.connect(db_path)
conn.execute("ALTER TABLE download_resources ADD COLUMN remark TEXT DEFAULT ''")
conn.execute("ALTER TABLE download_resources ADD COLUMN display_order INTEGER DEFAULT 0")
conn.commit()
print("Added remark and display_order columns")
# Verify
cursor = conn.execute("PRAGMA table_info(download_resources)")
for col in cursor.fetchall():
    print(f"  {col[1]} ({col[2]})")
conn.close()

