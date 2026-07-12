
import sqlite3, sys, os
sys.stdout.reconfigure(encoding="utf-8")
db_path = r"C:\Users\xueta\Documents\web-xiaobaigame\database\xiaobaigame.db"
print("Exists:", os.path.exists(db_path))
if os.path.exists(db_path):
    print("Size:", os.path.getsize(db_path))
    conn = sqlite3.connect(db_path)
    cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()
    print("Tables:")
    for t in tables:
        print(" ", t[0])
    conn.close()

